<template>
  <v-container max-width="900">
    <h1 class="text-h5 font-weight-bold mb-6">Campaign Budget Tracker</h1>

    <v-card class="mb-8">
      <v-data-table
        :headers="headers"
        :items="tableRows"
        :loading="loading"
        no-data-text="No campaigns yet. Add one below."
      >
        <template #item.spendPct="{ item }">
          <v-tooltip :text="`${formatPercent(item.spendPct)} of budget spent`" location="top">
            <template #activator="{ props }">
              <v-chip v-bind="props" :color="statusColour(item.status)" size="small" style="cursor: pointer">
                {{ item.status }}
              </v-chip>
            </template>
          </v-tooltip>
        </template>

        <template #item.budget="{ item }">
          {{ formatCurrency(item.budget) }}
        </template>

        <template #item.spend="{ item }">
          <div v-if="editingId === item.id" class="d-flex align-center gap-2">
            <v-text-field
              v-model="editSpend"
              type="number"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 120px"
            />
            <v-btn icon="mdi-check" size="x-small" color="success" :loading="saving" @click="saveSpend(item)" />
            <v-btn icon="mdi-close" size="x-small" @click="cancelEdit" />
          </div>
          <div v-else class="d-flex align-center gap-2" style="cursor: default">
            {{ formatCurrency(item.spend) }}
            <v-btn icon="mdi-pencil" size="x-small" variant="text" style="cursor: pointer" @click="startEdit(item)" />
          </div>
        </template>
      </v-data-table>
    </v-card>

    <v-card title="Add Campaign" class="pa-4">
      <v-form ref="form" @submit.prevent="submit">
        <v-row>
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="newCampaign.name"
              label="Name"
              :rules="[required]"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="newCampaign.budget"
              label="Budget (£)"
              type="number"
              :rules="[required, positiveNumber]"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="newCampaign.spend"
              label="Spend (£)"
              type="number"
              :rules="[required, positiveNumber]"
              variant="outlined"
              density="compact"
            />
          </v-col>
        </v-row>

        <v-alert v-if="error" type="error" class="mb-4" density="compact">
          {{ error }}
        </v-alert>

        <v-btn type="submit" color="primary" :loading="submitting">
          Add Campaign
        </v-btn>
      </v-form>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'

const API_URL = 'http://localhost:8000/api/campaigns/'

interface Campaign {
  id: number
  name: string
  budget: number
  spend: number
  status: string
}

interface TableRow extends Campaign {
  spendPct: number
}

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Budget', key: 'budget' },
  { title: 'Spend', key: 'spend' },
  { title: 'Status', key: 'spendPct' },
]

const campaigns = ref<Campaign[]>([])
const loading = ref(false)
const submitting = ref(false)
const saving = ref(false)
const error = ref('')
const form = ref()

const newCampaign = ref({ name: '', budget: '', spend: '' })
const editingId = ref<number | null>(null)
const editSpend = ref('')

const tableRows = computed<TableRow[]>(() =>
  campaigns.value.map(c => ({
    ...c,
    spendPct: c.budget > 0 ? (c.spend / c.budget) * 100 : 0,
  }))
)

const required = (v: string) => !!v || 'Required'
const positiveNumber = (v: string) => Number(v) >= 0 || 'Must be 0 or greater'

function statusColour(status: string) {
  const colours: Record<string, string> = {
    'OK': 'success',
    'Warning': 'warning',
    'Budget Reached': 'deep-orange',
    'Overspent': 'error',
  }
  return colours[status] ?? 'default'
}

function formatPercent(value: number) {
  return `${value.toFixed(1)}%`
}

function formatCurrency(value: number) {
  return `£${value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function startEdit(item: Campaign) {
  editingId.value = item.id
  editSpend.value = String(item.spend)
}

function cancelEdit() {
  editingId.value = null
  editSpend.value = ''
}

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

async function submit() {
  const { valid } = await form.value.validate()
  if (!valid) return

  submitting.value = true
  error.value = ''

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCampaign.value),
    })

    if (!res.ok) {
      error.value = 'Failed to add campaign. Please check your inputs.'
      return
    }

    const created = await res.json()
    campaigns.value.unshift(created)
    form.value.reset()
    newCampaign.value = { name: '', budget: '', spend: '' }
  } catch {
    error.value = 'Something went wrong. Is the backend running?'
  } finally {
    submitting.value = false
  }
}

async function saveSpend(item: Campaign) {
  saving.value = true
  try {
    const res = await fetch(`${API_URL}${item.id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spend: editSpend.value }),
    })

    if (!res.ok) return

    const updated = await res.json()
    const index = campaigns.value.findIndex(c => c.id === item.id)
    if (index !== -1) campaigns.value[index] = updated
    cancelEdit()
  } finally {
    saving.value = false
  }
}

onMounted(fetchCampaigns)
</script>
