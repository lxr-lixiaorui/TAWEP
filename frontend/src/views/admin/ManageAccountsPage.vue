<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Ban, Bell, KeyRound, Plus, RefreshCw, Search, Trash2, UserPlus, X } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AdminShell from '../../components/AdminShell.vue'
import { apiDelete, apiGet, apiPatch, apiPost } from '../../api/client'
import { useAuthStore } from '../../stores/auth'

type Account = {
  id: string
  email: string
  alias: string
  role: 'user' | 'admin'
  status: 'active' | 'pending' | 'banned'
  credit: number
  email_verified_at: string | null
  created_at: string
}

const auth = useAuthStore()
const message = useMessage()
const rows = ref<Account[]>([])
const loading = ref(true)
const search = ref('')
const createOpen = ref(false)
const deleteTarget = ref<Account | null>(null)
const deleteConfirmation = ref('')
const submitting = ref(false)
const createForm = reactive({ email: '', alias: '', password: '', role: 'user', preferred_locale: 'en' })

const filteredRows = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return rows.value
  return rows.value.filter((row) => `${row.email} ${row.alias} ${row.role} ${row.status}`.toLowerCase().includes(query))
})

function generatePassword() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%'
  const values = crypto.getRandomValues(new Uint32Array(18))
  createForm.password = Array.from(values, (value) => alphabet[value % alphabet.length]).join('')
}

function resetCreateForm() {
  Object.assign(createForm, { email: '', alias: '', password: '', role: 'user', preferred_locale: 'en' })
  generatePassword()
}

function openCreate() {
  resetCreateForm()
  createOpen.value = true
}

async function loadAccounts() {
  loading.value = true
  try {
    rows.value = await apiGet<Account[]>('/admin/accounts')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to load accounts')
  } finally {
    loading.value = false
  }
}

async function createAccount() {
  submitting.value = true
  try {
    const created = await apiPost<Account>('/admin/accounts', createForm)
    rows.value.unshift(created)
    createOpen.value = false
    message.success(`Created ${created.email}`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to create account')
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(row: Account) {
  try {
    if (row.status === 'banned') {
      await apiPatch(`/admin/accounts/${row.id}/unban`)
      row.status = row.email_verified_at ? 'active' : 'pending'
      message.success(`Restored ${row.email}`)
    } else {
      await apiPatch(`/admin/accounts/${row.id}/ban`, { comment: 'Changed in account administration' })
      row.status = 'banned'
      message.success(`Banned ${row.email}`)
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to change account status')
  }
}

async function notify(row: Account) {
  try {
    await apiPost(`/admin/accounts/${row.id}/messages`, {
      title: 'TAWEP notice',
      body: 'A system message from the TAWEP administrator.'
    })
    message.success(`Message sent to ${row.email}`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to send message')
  }
}

function openDelete(row: Account) {
  deleteTarget.value = row
  deleteConfirmation.value = ''
}

async function deleteAccount() {
  const target = deleteTarget.value
  if (!target) return
  submitting.value = true
  try {
    await apiDelete(`/admin/accounts/${target.id}`, { confirm_email: deleteConfirmation.value })
    rows.value = rows.value.filter((row) => row.id !== target.id)
    deleteTarget.value = null
    message.success(`Deleted ${target.email}`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to delete account')
  } finally {
    submitting.value = false
  }
}

onMounted(loadAccounts)
</script>

<template>
  <AdminShell>
    <header class="admin-page-head">
      <div>
        <p class="eyebrow">Administration</p>
        <h1>Accounts</h1>
        <p>Manage access, roles, account status, and permanent deletion.</p>
      </div>
      <button class="btn primary" @click="openCreate"><UserPlus :size="17" />Add account</button>
    </header>

    <section class="admin-account-tools">
      <label class="admin-search"><Search :size="16" /><input v-model="search" placeholder="Search email, alias, role, or status" /></label>
      <span>{{ filteredRows.length }} accounts</span>
    </section>

    <section class="panel admin-account-table-wrap">
      <table class="data-table admin-account-table">
        <thead><tr><th>Account</th><th>Role</th><th>Status</th><th>Credits</th><th>Created</th><th aria-label="Actions"></th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="muted">Loading accounts...</td></tr>
          <tr v-else-if="!filteredRows.length"><td colspan="6" class="muted">No accounts match this search.</td></tr>
          <tr v-for="row in filteredRows" :key="row.id">
            <td><strong>{{ row.alias }}</strong><small>{{ row.email }}</small></td>
            <td><span class="admin-role" :class="row.role">{{ row.role }}</span></td>
            <td><span class="admin-status" :class="row.status">{{ row.status }}</span></td>
            <td>{{ row.credit }}</td>
            <td>{{ new Date(row.created_at).toLocaleDateString() }}</td>
            <td>
              <div class="admin-row-actions">
                <button class="btn ghost small icon-btn" title="Send inbox message" aria-label="Send inbox message" @click="notify(row)"><Bell :size="15" /></button>
                <button class="btn ghost small icon-btn" :disabled="row.id === auth.user?.id" :title="row.status === 'banned' ? 'Restore account' : 'Ban account'" :aria-label="row.status === 'banned' ? 'Restore account' : 'Ban account'" @click="toggleStatus(row)">
                  <RefreshCw v-if="row.status === 'banned'" :size="15" /><Ban v-else :size="15" />
                </button>
                <button class="btn danger small icon-btn" :disabled="row.id === auth.user?.id" title="Delete account" aria-label="Delete account" @click="openDelete(row)"><Trash2 :size="15" /></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <n-modal v-model:show="createOpen">
      <div class="panel admin-dialog" role="dialog" aria-modal="true" aria-labelledby="create-account-title">
        <header><div><p class="eyebrow">New account</p><h2 id="create-account-title">Add a user</h2></div><button class="btn ghost small icon-btn" title="Close" aria-label="Close" @click="createOpen = false"><X :size="17" /></button></header>
        <form @submit.prevent="createAccount">
          <label class="form-field"><span>Email</span><input v-model="createForm.email" class="input" type="email" autocomplete="off" required /></label>
          <label class="form-field"><span>Alias</span><input v-model="createForm.alias" class="input" maxlength="80" required /></label>
          <div class="form-grid compact">
            <label class="form-field"><span>Role</span><select v-model="createForm.role" class="select"><option value="user">User</option><option value="admin">Administrator</option></select></label>
            <label class="form-field"><span>Language</span><select v-model="createForm.preferred_locale" class="select"><option value="en">English</option><option value="zh">中文</option></select></label>
          </div>
          <label class="form-field"><span>Temporary password</span><span class="admin-password-input"><input v-model="createForm.password" class="input" minlength="10" maxlength="128" required /><button type="button" class="btn ghost small icon-btn" title="Generate password" aria-label="Generate password" @click="generatePassword"><KeyRound :size="15" /></button></span></label>
          <p class="admin-dialog-note">The account is activated immediately. Send the temporary password through a secure channel.</p>
          <footer><button class="btn" type="button" @click="createOpen = false">Cancel</button><button class="btn primary" type="submit" :disabled="submitting"><Plus :size="16" />Create account</button></footer>
        </form>
      </div>
    </n-modal>

    <n-modal :show="Boolean(deleteTarget)" @update:show="(show: boolean) => { if (!show) deleteTarget = null }">
      <div class="panel admin-dialog danger-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-account-title">
        <header><div><p class="eyebrow">Permanent action</p><h2 id="delete-account-title">Delete account</h2></div><button class="btn ghost small icon-btn" title="Close" aria-label="Close" @click="deleteTarget = null"><X :size="17" /></button></header>
        <p>This permanently removes <strong>{{ deleteTarget?.email }}</strong>, including sessions, reports, credits, and inbox messages.</p>
        <form @submit.prevent="deleteAccount">
          <label class="form-field"><span>Type the email address to confirm</span><input v-model="deleteConfirmation" class="input" type="email" autocomplete="off" required /></label>
          <footer><button class="btn" type="button" @click="deleteTarget = null">Cancel</button><button class="btn danger" type="submit" :disabled="submitting || deleteConfirmation.toLowerCase() !== deleteTarget?.email.toLowerCase()"><Trash2 :size="16" />Delete permanently</button></footer>
        </form>
      </div>
    </n-modal>
  </AdminShell>
</template>
