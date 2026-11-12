<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useAuth0 } from '@auth0/auth0-vue';
import apiService from '../services/api';
import ConfirmationModal from './ConfirmationModal.vue';

const props = defineProps({
  projectId: { type: [Number, String], required: true },
  // Show the upload, add-link and delete controls. Everyone can see and download.
  canEdit: { type: Boolean, default: false },
});

// Same rules as the backend (project/models.py). The server stays the authority; this only
// saves a round trip for an obviously wrong choice.
const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'pptx', 'png', 'jpg', 'jpeg', 'zip'];
const MAX_FILE_BYTES = 25 * 1024 * 1024;

const { getAccessTokenSilently } = useAuth0();

const attachments = ref([]);
const loading = ref(true);
const loadError = ref('');
const actionError = ref('');
const notice = ref('');
const busy = ref(false);

const fileInput = ref(null);
const selectedFile = ref(null);
const linkUrl = ref('');
const pendingDelete = ref(null);

// Only real files and links belong here; rows that only hold exported email text do not.
const items = computed(() => attachments.value.filter((a) => a.file || a.link));

function fileExtension(name) {
  const dot = String(name || '').lastIndexOf('.');
  return dot === -1 ? '' : name.slice(dot + 1).toLowerCase();
}

function isLink(item) {
  return Boolean(item.link);
}

function displayName(item) {
  if (isLink(item)) return item.title || item.link;
  return item.original_filename || String(item.file).split('/').pop();
}

// Never render a link as a clickable anchor unless it is plain http(s).
function safeHref(item) {
  return /^https?:\/\//i.test(item.link || '') ? item.link : null;
}

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString();
}

function fileProblem(file) {
  if (!ALLOWED_EXTENSIONS.includes(fileExtension(file.name))) {
    return `Files of this type are not allowed. Use one of: ${ALLOWED_EXTENSIONS.join(', ')}.`;
  }
  if (file.size > MAX_FILE_BYTES) {
    return 'That file is larger than 25 MB.';
  }
  return '';
}

function messageFrom(err, fallback) {
  if (err?.response?.status === 413) return 'That file is too large for the server.';
  const data = err?.response?.data;
  if (data && typeof data === 'object') {
    const first = Object.values(data).flat()[0];
    if (typeof first === 'string') return first;
  }
  return fallback;
}

async function ensureToken() {
  apiService.setToken(await getAccessTokenSilently());
}

async function load() {
  loading.value = true;
  loadError.value = '';
  try {
    await ensureToken();
    const data = await apiService.getAttachments(props.projectId);
    attachments.value = Array.isArray(data) ? data : [];
  } catch (err) {
    loadError.value = 'Could not load files and links for this project.';
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.projectId, load);

function onFileChosen(event) {
  actionError.value = '';
  notice.value = '';
  selectedFile.value = event.target.files?.[0] || null;
}

async function upload() {
  actionError.value = '';
  notice.value = '';
  const file = selectedFile.value;
  if (!file) {
    actionError.value = 'Choose a file first.';
    return;
  }
  const problem = fileProblem(file);
  if (problem) {
    actionError.value = problem;
    return;
  }
  busy.value = true;
  try {
    await ensureToken();
    await apiService.uploadAttachment(props.projectId, file);
    selectedFile.value = null;
    if (fileInput.value) fileInput.value.value = '';
    notice.value = `Uploaded ${file.name}.`;
    await load();
  } catch (err) {
    actionError.value = messageFrom(err, 'The file could not be uploaded.');
  } finally {
    busy.value = false;
  }
}

async function addLink() {
  actionError.value = '';
  notice.value = '';
  const value = linkUrl.value.trim();
  if (!/^https?:\/\/\S+$/i.test(value)) {
    actionError.value = 'Enter a link that starts with http:// or https://.';
    return;
  }
  busy.value = true;
  try {
    await ensureToken();
    await apiService.addAttachmentLink(props.projectId, value);
    linkUrl.value = '';
    notice.value = 'Link added.';
    await load();
  } catch (err) {
    actionError.value = messageFrom(err, 'The link could not be added.');
  } finally {
    busy.value = false;
  }
}

async function download(item) {
  actionError.value = '';
  notice.value = '';
  try {
    await ensureToken();
    const blob = await apiService.downloadAttachment(item.id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = displayName(item);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    actionError.value = 'Could not download that file.';
  }
}

async function confirmDelete() {
  const item = pendingDelete.value;
  pendingDelete.value = null;
  if (!item) return;
  actionError.value = '';
  notice.value = '';
  busy.value = true;
  try {
    await ensureToken();
    await apiService.deleteAttachment(item.id);
    notice.value = `Removed ${displayName(item)}.`;
    await load();
  } catch (err) {
    actionError.value = messageFrom(err, 'Could not remove that item.');
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="attachments" aria-label="Files and links">
    <h3>Files and links</h3>

    <p v-if="loading" class="muted">Loading...</p>
    <p v-else-if="loadError" class="problem" role="alert">{{ loadError }}</p>
    <p v-else-if="items.length === 0" class="muted">No files or links yet.</p>

    <ul v-else class="attachment-list">
      <li v-for="item in items" :key="item.id" class="attachment-row">
        <span class="kind">{{ isLink(item) ? 'Link' : 'File' }}</span>
        <span class="name">
          <a v-if="isLink(item) && safeHref(item)" :href="safeHref(item)" target="_blank" rel="noopener noreferrer">
            {{ displayName(item) }}
          </a>
          <template v-else>{{ displayName(item) }}</template>
        </span>
        <span class="date">{{ formatDate(item.created_at) }}</span>
        <button v-if="!isLink(item)" type="button" class="small" @click="download(item)">Download</button>
        <button v-if="canEdit" type="button" class="small danger" :disabled="busy" @click="pendingDelete = item">
          Remove
        </button>
      </li>
    </ul>

    <p v-if="actionError" class="problem" role="alert">{{ actionError }}</p>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>

    <div v-if="canEdit" class="add-forms">
      <form class="add-form" @submit.prevent="upload">
        <label for="attachment-file">Upload a file</label>
        <input
          id="attachment-file"
          ref="fileInput"
          type="file"
          :accept="ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(',')"
          @change="onFileChosen"
        />
        <p class="hint">pdf, docx, pptx, png, jpg or zip, up to 25 MB.</p>
        <button type="submit" :disabled="busy">Upload</button>
      </form>

      <form class="add-form" @submit.prevent="addLink">
        <label for="attachment-link">Or add a link</label>
        <input id="attachment-link" v-model="linkUrl" type="url" placeholder="https://" />
        <button type="submit" :disabled="busy">Add link</button>
      </form>
    </div>

    <ConfirmationModal
      :show="pendingDelete !== null"
      title="Remove this item?"
      :message="pendingDelete ? `${displayName(pendingDelete)} will be removed from the project.` : ''"
      @confirm="confirmDelete"
      @cancel="pendingDelete = null"
    />
  </section>
</template>

<style scoped>
.attachments {
  margin-top: 1rem;
  text-align: left;
}

.attachments h3 {
  margin: 0 0 0.5rem;
}

.attachment-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.attachment-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border-subtle);
}

.kind {
  font-size: 0.75rem;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  color: var(--text-subtle);
  border: 1px solid var(--border-subtle);
}

.name {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--text-default);
}

.date {
  font-size: 0.85rem;
  color: var(--text-subtle);
}

.small {
  padding: 0.25rem 0.6rem;
  font-size: 0.85rem;
}

.danger {
  color: var(--text-negative);
}

.add-forms {
  display: grid;
  gap: 1rem;
  margin-top: 1rem;
}

.add-form {
  display: grid;
  gap: 0.4rem;
}

.add-form label {
  font-weight: 600;
  color: var(--text-default);
}

.hint,
.muted {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-subtle);
}

.problem {
  margin: 0.5rem 0 0;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  color: var(--text-negative);
  background: var(--background-negative);
}

.notice {
  margin: 0.5rem 0 0;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  color: var(--text-positive);
  background: var(--background-positive);
}
</style>
