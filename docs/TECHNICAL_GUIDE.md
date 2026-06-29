# Technical Guide

This document explains how the application works end to end — frontend, backend, and tests — including why certain approaches were chosen over alternatives. Written as a reference for discussing the code in interview.

---

## How it all fits together

When a user opens the app in a browser, the Vue frontend loads and immediately makes an HTTP request to the Django backend asking for all campaigns. Django reads them from the SQLite database, computes a status for each one, and sends them back as JSON. Vue renders them in the table. When the user adds a campaign or updates a spend figure, Vue sends another HTTP request to Django, which saves the change and responds with the updated data.

```
Browser (Vue) ──── HTTP/JSON ──── Django API ──── SQLite
```

The two services run independently in Docker containers and communicate over the Docker network.

---

## Backend

### Django project structure

```
backend/
  core/           ← Django project (settings, URLs, config)
  campaigns/      ← Django app (model, serializer, views, URLs, tests)
  manage.py
  requirements.txt
```

Django separates a **project** from **apps**. The project (`core`) holds global config. The app (`campaigns`) holds everything specific to campaign tracking. This is standard Django convention — if we later added user authentication, it would live in its own separate app alongside `campaigns`.

### The model

```python
class Campaign(models.Model):
    name = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

`budget` and `spend` use `DecimalField` rather than `FloatField`. This matters for money — floats use binary arithmetic which causes rounding errors (`0.1 + 0.2 = 0.30000000000000004`). Decimals are exact. `created_at` is used to order campaigns newest-first in the API response.

**Status is not stored.** It is derived from `spend` and `budget` at read time. If we stored it, it could go out of sync — a campaign could show `OK` even after spend was updated to exceed the budget. Computing it on the fly means it is always accurate.

### The serializer

The serializer sits between the model and the API. It controls what data goes in and out, and handles validation.

```python
class CampaignSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    budget = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    spend = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
```

`coerce_to_string=False` tells DRF to return `budget` and `spend` as JSON numbers (`1000.00`) rather than strings (`"1000.00"`). By default DRF serialises decimals as strings to avoid precision loss in JSON — but modern JSON parsers handle decimal numbers fine, and returning numbers makes the frontend cleaner.

`SerializerMethodField` lets us add computed fields that don't exist on the model. The `get_status` method runs every time a campaign is serialised:

```python
def get_status(self, obj):
    if obj.budget <= 0:
        return 'OK'
    if obj.spend > obj.budget:
        return 'Overspent'
    if obj.spend == obj.budget:
        return 'Budget Reached'
    if float(obj.spend) / float(obj.budget) >= 0.9:
        return 'Warning'
    return 'OK'
```

We convert to `float` for the percentage comparison because Django's `DecimalField` returns Python `Decimal` objects, and comparing `Decimal` against a float literal like `0.9` produces unexpected results due to type mismatch.

### Validation

```python
def validate_budget(self, value):
    if value < 0:
        raise serializers.ValidationError('Budget cannot be negative.')
    return value
```

Validation lives in the serializer, not the model. This means it runs on every API request, regardless of where the request comes from. The model layer could also have constraints, but serializer validation is the right place for API input rules — it returns a clean 400 error with a message if the rule is broken.

### The view

```python
class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().order_by('-created_at')
    serializer_class = CampaignSerializer
```

`ModelViewSet` is DRF's full CRUD viewset. Those two lines give us:

| HTTP method | URL | Action |
|---|---|---|
| GET | `/api/campaigns/` | List all campaigns |
| POST | `/api/campaigns/` | Create a campaign |
| GET | `/api/campaigns/{id}/` | Retrieve one campaign |
| PUT | `/api/campaigns/{id}/` | Full update |
| PATCH | `/api/campaigns/{id}/` | Partial update (we use this for spend) |
| DELETE | `/api/campaigns/{id}/` | Delete |

**Why ViewSet over individual views?** We could have written separate function-based views for each endpoint. A ViewSet is more concise and follows DRF conventions — a reviewer familiar with Django will immediately understand what it does. The tradeoff is slightly less flexibility, but for standard CRUD that's never an issue.

### CORS

CORS (Cross-Origin Resource Sharing) is a browser security rule that blocks JavaScript on one domain from making requests to a different domain. Our Vue app runs on `localhost:3000` and the Django API on `localhost:8000` — different ports counts as different origins. Without `django-cors-headers`, every API request would be blocked by the browser.

The middleware intercepts requests and adds the appropriate headers to tell the browser the request is permitted.

### URLs

```python
# core/urls.py
path('api/', include('campaigns.urls')),

# campaigns/urls.py
router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
```

The DRF router automatically generates all the URL patterns for the ViewSet. The `api/` prefix keeps things clean and makes it clear these are API endpoints, not HTML pages.

---

## Frontend

### Vue 3 Composition API

The entire UI lives in one file: `src/components/CampaignTracker.vue`. Vue single-file components combine template, script, and styles in one place.

We use `<script setup>` which is Vue 3's Composition API syntax. It's more concise than the Options API (Vue 2 style) and keeps related logic together rather than splitting it across `data`, `methods`, and `computed` sections.

**Why one component?** The app is a single page with a table and a form. Splitting into multiple components (`CampaignTable.vue`, `AddCampaignForm.vue`) would add indirection without benefit at this scale. If the app grew — multiple pages, shared state, reusable form components — splitting would make sense.

### Fetching data

```typescript
async function fetchCampaigns() {
  loading.value = true
  try {
    const res = await fetch(API_URL)
    campaigns.value = await res.json()
  } catch {
    error.value = 'Failed to load campaigns.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchCampaigns)
```

`onMounted` runs once when the component is first rendered. We use the native `fetch` API rather than a library like Axios — for simple GET/POST/PATCH requests there is no need for an additional dependency.

**Why not a state management library like Pinia?** Pinia (or Vuex before it) makes sense when multiple components need to share and react to the same data. Here, all data lives in one component. Adding a store would be over-engineering.

### Computed values

```typescript
const tableRows = computed<TableRow[]>(() =>
  campaigns.value.map(c => ({
    ...c,
    spendPct: c.budget > 0 ? (c.spend / c.budget) * 100 : 0,
  }))
)
```

`computed` values recalculate automatically when their dependencies change. `spendPct` is derived from `spend` and `budget` — we don't store it, we calculate it. This is used for two things: sorting the table by how close each campaign is to its limit, and showing the percentage in the tooltip and progress bar.

### Responsive layout

```html
<v-card class="d-none d-sm-block">  <!-- hidden on mobile, shown on sm+ -->
<div class="d-block d-sm-none">     <!-- shown on mobile, hidden on sm+ -->
```

We use Vuetify's CSS display utility classes rather than JavaScript breakpoint detection (`useDisplay()`). CSS media queries are more reliable — they react instantly to window resizing without needing a JavaScript event listener to fire. `sm` in Vuetify's grid is 600px, which is the standard tablet/phone boundary.

### TypeScript

```typescript
interface Campaign {
  id: number
  name: string
  budget: number
  spend: number
  status: string
}
```

TypeScript catches type errors at compile time. Because we set `coerce_to_string=False` in the serializer, `budget` and `spend` arrive as numbers from the API, and the interface reflects that. If we accidentally tried to use them as strings the type checker would flag it before the code ran.

---

## Testing

### What we test and why

The test suite is split into three classes:

**`CampaignStatusTests`** — unit tests for the status logic. These test the serializer's `get_status` method directly without making HTTP requests. Fast, isolated, and test every boundary:
- 50% spend → OK
- Exactly 90% → Warning (the threshold boundary)
- 95% → Warning
- 100% → Budget Reached
- 101% → Overspent
- Zero budget → OK (guards against division by zero)

**`CampaignAPITests`** — integration tests that make real HTTP requests through Django's test client. These test the full stack: URL routing → view → serializer → database → response. They verify that listing, creating, and updating campaigns works end to end, and that the status field is returned correctly in the response.

**`CampaignValidationTests`** — tests that bad input is rejected with a 400 error. Negative budget, negative spend, missing required fields. These verify the serializer validation is wired up correctly.

### Why not mock the database?

Django's test runner creates a real temporary SQLite database for each test run and destroys it afterwards. We don't mock the database. Mocking gives you tests that pass even when the real database interaction is broken — a false sense of security. Using a real database means the tests reflect what actually happens in production.

### Running the tests

```bash
python manage.py test campaigns
```

Django's test runner discovers all classes that extend `TestCase` in `tests.py`, runs them in isolation (each test gets a clean database state via transactions), and reports results.

### CI with GitHub Actions

`.github/workflows/ci.yml` runs the test suite automatically on every push to `main` and on every pull request. This means:
- You get immediate feedback if a change breaks something
- The green tick on a commit means the tests passed at that point in time
- No one can merge broken code to `main` without noticing

The workflow installs Python 3.13, installs dependencies from `requirements.txt`, and runs the same `manage.py test` command you'd run locally — no difference between local and CI.

---

## Docker

### Why Docker?

Without Docker, a reviewer cloning the repo would need to manually install Python, create a virtual environment, install pip packages, install Node, install pnpm, and start two servers in the right order. Docker packages all of that into containers that run identically on any machine.

### Two containers

```yaml
services:
  backend:   # Django on port 8000
  frontend:  # Vite on port 3000
```

The two services run independently. `depends_on: backend` means Docker starts the backend container first, though it doesn't wait for Django to be fully ready — just for the container to start.

### The build process

**Backend:**
1. Start from `python:3.13-slim` (a minimal Python image)
2. Install pip dependencies from `requirements.txt`
3. Copy the Django project files
4. Run database migrations
5. Start Django's development server on `0.0.0.0:8000` (not `127.0.0.1` — inside a container, `127.0.0.1` only accepts connections from within the container itself)

**Frontend:**
1. Start from `node:20-slim`
2. Install pnpm
3. Install npm dependencies from `pnpm-lock.yaml`
4. Copy the Vue project files
5. Start Vite dev server with `--host` flag (same reason — needed to accept connections from outside the container)

### Volume mounts

```yaml
volumes:
  - .:/app              # mount local source files into container
  - /app/node_modules   # keep container's node_modules separate
  - db_data:/app/db.sqlite3  # persist the database
```

The source file mount means changes to Vue files hot-reload in the browser without rebuilding the container. The `node_modules` mount prevents the host machine's `node_modules` (compiled for Mac) from overwriting the container's `node_modules` (compiled for Linux).

The `db_data` named volume persists the SQLite database file across container restarts. Without this, stopping Docker would wipe all campaign data.

### `.dockerignore`

Both services have `.dockerignore` files that exclude `venv/`, `node_modules/`, and `__pycache__` from being copied into the image. Without these, the build would copy hundreds of megabytes of dependencies that are then immediately reinstalled anyway — significantly slower builds.
