<template>
  <v-container max-width="900">
    <h1 class="text-h5 font-weight-bold mb-6">Campaign Budget Tracker</h1>

    <v-card class="mb-8">
      <v-data-table
        :headers="headers"
        :items="campaigns"
        :loading="loading"
        no-data-text="No campaigns yet. Add one below."
      >
        <template #item.status="{ item }">
          <v-chip :color="statusColour(item.status)" size="small">
            {{ item.status }}
          </v-chip>
        </template>

        <template #item.budget="{ item }">
          {{ formatCurrency(item.budget) }}
        </template>

        <template #item.spend="{ item }">
          {{ formatCurrency(item.spend) }}
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
import { ref, onMounted } from 'vue'

const API_URL = 'http://localhost:8000/api/campaigns/'

interface Campaign {
  id: number
  name: string
  budget: string
  spend: string
  status: string
}

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Budget', key: 'budget' },
  { title: 'Spend', key: 'spend' },
  { title: 'Status', key: 'status' },
]

const campaigns = ref<Campaign[]>([])
const loading = ref(false)
const submitting = ref(false)
const error = ref('')
const form = ref()

const newCampaign = ref({ name: '', budget: '', spend: '' })

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

function formatCurrency(value: string) {
  return `£${Number(value).toLocaleString('en-GB', { minimumFractionDigits: 2 })}`
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

onMounted(fetchCampaigns)
</script>
