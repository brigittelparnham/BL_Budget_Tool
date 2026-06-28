<template>
  <v-container max-width="920" class="py-2">

    <!-- Header -->
    <div class="d-flex align-center mb-6" style="gap: 13px">
      <div class="tracker-logo">
        <v-icon color="white" size="22">mdi-chart-timeline-variant</v-icon>
      </div>
      <div>
        <h1 class="text-h6 font-weight-bold" style="letter-spacing: -0.02em; line-height: 1.15">
          Campaign Budget Tracker
        </h1>
        <div class="text-body-2 text-medium-emphasis">
          Spend against budget, across every campaign.
        </div>
      </div>
    </div>

    <!-- DESKTOP / TABLET: data table -->
    <v-card class="d-none d-sm-block mb-8 table-card" style="border-radius: 14px; border-color: #E6EAE3; overflow: hidden">
      <v-data-table
        :headers="headers"
        :items="tableRows"
        :loading="loading"
        no-data-text="No campaigns yet. Add one below."
      >
        <template #item="{ item }">
          <tr class="campaign-row">
            <td class="font-weight-bold">{{ item.name }}</td>
            <td>{{ formatCurrency(item.budget) }}</td>
            <td>
              <div v-if="editingId === item.id" class="d-flex align-center" style="gap: 6px">
                <v-text-field
                  v-model="editSpend"
                  type="number"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="max-width: 120px"
                />
                <v-btn icon="mdi-check" size="x-small" color="success" :loading="saving" @click="saveSpend(item)" />
                <v-btn icon="mdi-close" size="x-small" variant="outlined" @click="cancelEdit" />
              </div>
              <div v-else class="d-flex align-center" style="gap: 8px; cursor: default">
                {{ formatCurrency(item.spend) }}
                <button class="edit-btn" @click="startEdit(item)">
                  <v-icon size="13">mdi-pencil</v-icon>
                </button>
              </div>
            </td>
            <td>
              <div class="d-flex align-center" style="gap: 8px">
                <v-tooltip :text="`${formatPercent(item.spendPct)} of budget spent`" location="top">
                  <template #activator="{ props }">
                    <div
                      v-bind="props"
                      class="status-chip"
                      :style="{ background: statusColour(item.status), color: statusTextColour(item.status) }"
                    >
                      <span class="status-dot" :style="{ background: statusTextColour(item.status) }" />
                      {{ item.status }}
                    </div>
                  </template>
                </v-tooltip>
                <span class="text-caption text-medium-emphasis">{{ formatPercent(item.spendPct) }}</span>
              </div>
            </td>
          </tr>
          <tr class="progress-row">
            <td colspan="4" style="padding: 0; border: none; height: 3px">
              <div
                class="progress-bar"
                :style="{
                  width: `${Math.min(item.spendPct, 100)}%`,
                  background: statusBarColour(item.status),
                }"
              />
            </td>
          </tr>
        </template>
      </v-data-table>
    </v-card>

    <!-- MOBILE: card list -->
    <div class="d-block d-sm-none mb-8">
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4" rounded />
      <v-card v-if="!tableRows.length && !loading" class="pa-4 text-center text-medium-emphasis text-body-2">
        No campaigns yet. Add one below.
      </v-card>

      <v-card v-for="item in tableRows" :key="item.id" class="mb-3 pa-4" style="border-radius: 14px; border-color: #E6EAE3">
        <div class="d-flex align-center justify-space-between mb-3" style="gap: 10px">
          <span class="text-subtitle-1 font-weight-bold text-truncate">{{ item.name }}</span>
          <v-tooltip :text="`${formatPercent(item.spendPct)} of budget spent`" location="top">
            <template #activator="{ props }">
              <div
                v-bind="props"
                class="status-chip"
                :style="{ background: statusColour(item.status), color: statusTextColour(item.status) }"
              >
                <span class="status-dot" :style="{ background: statusTextColour(item.status) }" />
                {{ item.status }}
              </div>
            </template>
          </v-tooltip>
        </div>

        <div class="d-flex" style="gap: 10px">
          <div class="bl-field flex-1-1">
            <div class="bl-field-label">Budget</div>
            <div class="text-body-1 font-weight-medium">{{ formatCurrency(item.budget) }}</div>
          </div>
          <div class="bl-field flex-1-1">
            <div class="bl-field-label">Spend</div>
            <div v-if="editingId === item.id" class="d-flex align-center gap-2 mt-1">
              <v-text-field v-model="editSpend" type="number" density="compact" variant="outlined" hide-details />
              <v-btn icon="mdi-check" size="x-small" color="success" :loading="saving" @click="saveSpend(item)" />
              <v-btn icon="mdi-close" size="x-small" @click="cancelEdit" />
            </div>
            <div v-else class="d-flex align-center justify-space-between gap-2">
              <span class="text-body-1 font-weight-medium">{{ formatCurrency(item.spend) }}</span>
              <button class="edit-btn" @click="startEdit(item)">
                <v-icon size="13">mdi-pencil</v-icon>
              </button>
            </div>
          </div>
        </div>

        <div class="d-flex align-center mt-3" style="gap: 10px">
          <v-progress-linear
            :model-value="Math.min(item.spendPct, 100)"
            :color="statusTextColour(item.status)"
            height="6"
            rounded
            bg-color="grey-lighten-3"
          />
          <span class="text-caption text-medium-emphasis">{{ formatPercent(item.spendPct) }}</span>
        </div>
      </v-card>
    </div>

    <!-- ADD CAMPAIGN FORM -->
    <v-card class="add-card" style="border-radius: 14px; border-color: #E6EAE3; overflow: hidden">
      <div class="pa-5">
        <div class="text-subtitle-1 font-weight-bold mb-4">Add campaign</div>
        <v-form ref="form" @submit.prevent="submit">
          <v-row>
            <v-col cols="12" sm="4">
              <div class="form-label">Name</div>
              <v-text-field
                v-model="newCampaign.name"
                placeholder="e.g. Summer Flash Sale"
                :rules="[required]"
                variant="outlined"
                density="compact"
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12" sm="4">
              <div class="form-label">Budget (£)</div>
              <v-text-field
                v-model="newCampaign.budget"
                placeholder="0.00"
                type="number"
                :rules="[required, positiveNumber]"
                variant="outlined"
                density="compact"
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12" sm="4">
              <div class="form-label">Spend (£)</div>
              <v-text-field
                v-model="newCampaign.spend"
                placeholder="0.00"
                type="number"
                :rules="[required, positiveNumber]"
                variant="outlined"
                density="compact"
                hide-details="auto"
              />
            </v-col>
          </v-row>

          <v-alert v-if="error" type="error" class="mt-3 mb-1" density="compact">{{ error }}</v-alert>

          <v-btn type="submit" color="primary" prepend-icon="mdi-plus" :loading="submitting" class="mt-4">
            Add campaign
          </v-btn>
        </v-form>
      </div>
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
  { title: 'Campaign', key: 'name' },
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

const statusStyles: Record<string, { bg: string; color: string; bar: string }> = {
  OK:               { bg: '#E4F3EA', color: '#14935E', bar: '#6DC49A' },
  Warning:          { bg: '#FBEFD4', color: '#8C6206', bar: '#E8C254' },
  'Budget Reached': { bg: '#FCE7D6', color: '#A24E1A', bar: '#E89B6A' },
  Overspent:        { bg: '#FBE0DF', color: '#AE3936', bar: '#E07774' },
}

function statusColour(status: string) {
  return statusStyles[status]?.bg ?? '#E6EAE3'
}

function statusTextColour(status: string) {
  return statusStyles[status]?.color ?? '#1B211D'
}

function statusBarColour(status: string) {
  return statusStyles[status]?.bar ?? '#9AA39D'
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

<style scoped>
.tracker-logo {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgb(var(--v-theme-primary));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 6px 16px -8px rgb(var(--v-theme-primary));
}

/* Table header and footer grey background */
.table-card :deep(thead tr) {
  background: #F7F9F5;
}
.table-card :deep(thead th) {
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: #9AA39D !important;
  border-bottom: 1px solid #E6EAE3 !important;
}
.table-card :deep(.v-data-table-footer) {
  background: #F7F9F5;
  border-top: 1px solid #E6EAE3;
  font-size: 13px;
  color: #6A736E;
}

/* Row styles */
.campaign-row td {
  padding: 14px 16px;
  border-bottom: none;
  font-size: 14.5px;
}
.progress-row td {
  padding: 0 !important;
  height: 3px;
  border-bottom: 1px solid #E6EAE3;
}
.progress-bar {
  height: 3px;
  transition: width 0.4s ease;
}

/* Status chip */
.status-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 5px;
  flex-shrink: 0;
}

/* Edit pencil button */
.edit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  border: 1.5px solid #E0E5DD;
  background: #fff;
  color: #6A736E;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.15s, background 0.15s;
}
.edit-btn:hover {
  border-color: #9AA39D;
  background: #F7F9F5;
}

/* Form */
.form-label {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #9AA39D;
  margin-bottom: 5px;
}

/* Mobile card fields */
.flex-1-1 {
  flex: 1 1 0;
  min-width: 0;
}
.bl-field {
  background: #F7F9F5;
  border-radius: 10px;
  padding: 10px 12px;
}
.bl-field-label {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #9AA39D;
  margin-bottom: 2px;
}
</style>
