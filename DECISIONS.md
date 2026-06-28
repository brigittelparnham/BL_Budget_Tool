# Technical Decisions

This document explains the key choices made during development and the reasoning behind them.

---

## Backend

### Django + Django REST Framework
Django was specified in the brief. Django REST Framework (DRF) was added to provide a clean, serializer-based API layer with minimal boilerplate. DRF's `ModelViewSet` gives full CRUD out of the box, meaning the API supports listing, creating, updating, and deleting campaigns without writing individual view functions.

### SQLite
SQLite is Django's default database and is appropriate here — it's a real persistent database, simple to set up, and requires no additional service. The data survives container restarts via a named Docker volume.

In a production environment this would be swapped for PostgreSQL, which handles concurrent writes and scales properly. That would mean adding a `db` service to `docker-compose.yml` and updating `DATABASES` in `settings.py`.

### Status as a computed field
Campaign status (`OK`, `Warning`, `Budget Reached`, `Overspent`) is not stored in the database. It is computed by the serializer on every read, derived from `spend` and `budget`. This avoids the data ever being out of sync — there is no risk of a campaign showing `OK` when the spend has since been updated to exceed the budget.

### Status thresholds
| Status | Condition |
|---|---|
| OK | Spend < 90% of budget |
| Warning | Spend ≥ 90% of budget |
| Budget Reached | Spend = budget exactly |
| Overspent | Spend > budget |

The 90% warning threshold was chosen to give account managers early visibility before a campaign runs over. `Budget Reached` was added as a distinct state from `Overspent` to make it immediately clear when a campaign has hit its limit but not yet exceeded it.

### Input validation
The serializer rejects negative values for both `budget` and `spend`. These are validated at the API level so the constraint is enforced regardless of which client sends the request.

---

## Frontend

### Vue 3 + Vuetify
Vue and Vuetify are the stack used at Brainlabs and were specified in the brief. Vue 3's Composition API with `<script setup>` keeps the component concise. Vuetify provides the data table, form components, and responsive utilities.

### Single component
The entire UI lives in `CampaignTracker.vue`. Given the scope — one page, one table, one form — splitting into multiple components would add indirection without benefit. The component is easy to read top to bottom.

### Spend editing in the UI, delete omitted
The API supports both updating and deleting campaigns. Updating spend is surfaced in the UI via an inline edit because spend changes regularly and account managers need to update it. Delete is available in the API but was not surfaced in the UI as it was not scoped in the brief.

### Responsive layout
Below 600px the data table switches to a card-based layout with a progress bar per campaign. This was not in the brief but is standard practice for any web UI that may be viewed on a phone.

### Status computed on the frontend too
`spendPct` (spend as a percentage of budget) is computed on the frontend for sorting and display. This means the table can be sorted by how close each campaign is to its budget limit — the most useful sort order for an account manager.

---

## Infrastructure

### Docker
Both services are containerised. The frontend runs on port 3000 (Vite dev server), the backend on port 8000 (Django dev server). A named volume (`db_data`) persists the SQLite database across container restarts.

### GitHub Actions CI
A CI workflow runs the backend test suite on every push to `main` and on all pull requests. This ensures the API and status logic are verified automatically before any code is merged.
