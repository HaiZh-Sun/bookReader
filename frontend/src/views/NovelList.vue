<template>
  <div class="novel-list">
    <div class="header">
      <h2>小说列表</h2>
      <button @click="showUpload = true">+ 上传小说</button>
    </div>

    <div v-if="showUpload" class="upload-card card">
      <h3>上传 TXT 小说</h3>
      <input v-model="uploadTitle" placeholder="小说标题（可选）" />
      <input v-model="uploadAuthor" placeholder="作者（可选）" />
      <input type="file" accept=".txt" @change="onFileChange" />
      <div class="actions">
        <button @click="upload" :disabled="!selectedFile || uploading">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
        <button class="secondary" @click="cancelUpload">取消</button>
      </div>
      <p v-if="uploadError" class="error">{{ uploadError }}</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="novels.length === 0" class="empty">暂无小说，点击上方按钮上传</div>
    <div v-else class="grid">
      <div
        v-for="n in novels"
        :key="n.id"
        class="novel-card card"
        @click="$router.push(`/novels/${n.id}`)"
      >
        <h3>{{ n.title }}</h3>
        <p class="meta">{{ n.author || '未知作者' }} · {{ n.total_chapters }}章</p>
        <span class="status" :class="n.status">{{ n.status }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listNovels, uploadNovel } from '../api/novels'

const novels = ref([])
const loading = ref(true)
const showUpload = ref(false)
const uploadTitle = ref('')
const uploadAuthor = ref('')
const selectedFile = ref(null)
const uploading = ref(false)
const uploadError = ref('')

async function load() {
  loading.value = true
  novels.value = await listNovels()
  loading.value = false
}
onMounted(load)

function onFileChange(e) {
  const f = e.target.files[0] || null
  selectedFile.value = f
  if (f && !uploadTitle.value) {
    uploadTitle.value = f.name.replace(/\.[^.]+$/, '')
  }
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    await uploadNovel(selectedFile.value, uploadTitle.value, uploadAuthor.value)
    showUpload.value = false
    selectedFile.value = null
    uploadTitle.value = ''
    uploadAuthor.value = ''
    await load()
  } catch (e) {
    uploadError.value = '上传失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    uploading.value = false
  }
}

function cancelUpload() {
  showUpload.value = false
  uploadTitle.value = ''
  uploadAuthor.value = ''
  selectedFile.value = null
  uploadError.value = ''
}
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.upload-card { margin-bottom: 20px; display: flex; flex-direction: column; gap: 12px; }
.actions { display: flex; gap: 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.novel-card { cursor: pointer; transition: transform .15s; }
.novel-card:hover { transform: translateY(-2px); }
.meta { color: #666; font-size: 13px; margin-top: 8px; }
.status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-top: 8px; }
.status.ready { background: #e8f5e9; color: #2e7d32; }
.status.uploaded { background: #fff3e0; color: #e65100; }
.error { color: #d32f2f; font-size: 13px; }
.loading, .empty { text-align: center; padding: 60px; color: #999; }
</style>
