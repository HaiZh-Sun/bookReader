<template>
  <div class="voice-library">
    <h2>音色管理</h2>

    <div class="upload-section card">
      <h3>上传音色文件</h3>
      <p class="hint">支持 .wav / .mp3 格式，用于本地 TTS 模型音色克隆</p>
      <input type="file" accept=".wav,.mp3" @change="onFileChange" />
      <button @click="upload" :disabled="!selectedFile || uploading">
        {{ uploading ? '上传中...' : '上传' }}
      </button>
    </div>

    <div class="voice-list">
      <div v-for="v in voices" :key="v.name" class="voice-item card">
        <span class="name">{{ v.name }}</span>
        <span class="size">({{ (v.size / 1024).toFixed(1) }} KB)</span>
        <audio :src="getVoiceUrl(v.path)" controls></audio>
      </div>
      <div v-if="!voices.length" class="empty">暂无音色文件</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listVoices, uploadVoice } from '../api/tts'

const voices = ref([])
const selectedFile = ref(null)
const uploading = ref(false)

onMounted(async () => {
  voices.value = await listVoices()
})

function onFileChange(e) {
  selectedFile.value = e.target.files[0] || null
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    await uploadVoice(selectedFile.value)
    selectedFile.value = null
    voices.value = await listVoices()
  } finally {
    uploading.value = false
  }
}

function getVoiceUrl(path) {
  return `/api/tts/voices/download?path=${encodeURIComponent(path)}`
}
</script>

<style scoped>
.upload-section { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.hint { color: #999; font-size: 13px; }
.voice-list { display: flex; flex-direction: column; gap: 12px; }
.voice-item { display: flex; align-items: center; gap: 16px; }
.name { font-weight: 600; }
.size { color: #999; font-size: 13px; }
.empty { text-align: center; padding: 40px; color: #999; }
</style>
