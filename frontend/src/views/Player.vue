<template>
  <div class="player">
    <div class="header">
      <h2>音频生成与播放</h2>
      <div class="actions">
        <button @click="startGenerate" :disabled="generating || polling">
          {{ generating ? '队列中...' : polling ? '生成中...' : '生成本章音频' }}
        </button>
        <button v-if="polling" @click="doCancel" class="cancel-btn">中断</button>
        <button @click="playAll" :disabled="!canPlayAll">
          {{ playing ? '播放中...' : '播放全部' }}
        </button>
        <button @click="saveAudio" :disabled="!canSave">
          保存音频
        </button>
      </div>
    </div>

    <div class="progress-card card" v-if="polling">
      <h3>生成进度</h3>
      <div class="progress-info">
        <span>{{ progress.completed }}/{{ progress.total }} 句</span>
        <span class="status-tag" :class="progress.status">{{ statusText }}</span>
      </div>
      <div class="bar">
        <div class="fill" :style="{ width: barPercent + '%' }"></div>
      </div>
    </div>

    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <div class="audio-list" v-if="audios.length">
      <div v-for="(a, idx) in audios" :key="a.id" class="audio-item card"
        :class="{ playing: currentPlayIdx === idx }">
        <span class="line-num">{{ idx + 1 }}</span>
        <span :class="'status ' + a.status">{{ a.status }}</span>
        <audio v-if="a.status === 'completed'" :src="getAudioUrl(a.id)" controls
          @play="onSegmentPlay(idx)" @ended="onSegmentEnd(idx)"></audio>
        <span v-if="a.error_message" class="error">{{ a.error_message }}</span>
      </div>
    </div>

    <div class="voice-config card">
      <h3>角色音色配置</h3>
      <p class="hint">前往「对话分析」页面可为每个角色独立配置音色</p>
      <div v-for="c in characters" :key="c.id" class="char-voice">
        <span class="char-name">{{ c.name }}</span>
        <span class="voice-tag">{{ c.voice_tag || '默认音色' }}</span>
      </div>
    </div>

    <audio ref="playerEl" style="display:none" @ended="onSequentialEnd"></audio>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { generateChapter, cancelTTS, getTTSProgress, getTTSResults, getAudioUrl, exportChapterAudio } from '../api/tts'
import { getAnalysis } from '../api/analysis'
import { getSettings } from '../api/settings'

const route = useRoute()
const chapterId = route.params.chapterId
const audios = ref([])
const progress = ref({ status: '', total: 0, completed: 0, failed: 0 })
const ttsProvider = ref('edge_tts')
const generating = ref(false)
const polling = ref(false)
const errorMsg = ref('')
const characters = ref([])
const playerEl = ref(null)
const playing = ref(false)
const currentPlayIdx = ref(-1)
const sequentialQueue = ref([])
const sequentialIdx = ref(0)
let pollTimer = null

const canPlayAll = computed(() => {
  return audios.value.some(a => a.status === 'completed') && !generating.value
})

const canSave = computed(() => {
  return audios.value.some(a => a.status === 'completed') && !generating.value
})

const statusText = computed(() => ({
  pending: '等待中',
  generating: '生成中',
  completed: '已完成',
  error: '出错',
}[progress.value.status] || progress.value.status))

const barPercent = computed(() => {
  const p = progress.value
  if (!p.total) return 0
  return Math.round((p.completed + p.failed) / p.total * 100)
})

onMounted(async () => {
  try {
    const s = await getSettings()
    ttsProvider.value = s.tts.provider
  } catch { }
  try {
    const p = await getTTSProgress(chapterId)
    if (p.total > 0) progress.value = p
    if (p.status === 'completed' || p.status === 'idle') {
      await loadResults()
    }
  } catch { }
  try {
    const result = await getAnalysis(chapterId)
    characters.value = result.characters
  } catch { }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function loadResults() {
  try {
    audios.value = await getTTSResults(chapterId)
  } catch { }
}

async function doCancel() {
  try {
    await cancelTTS(chapterId)
  } catch { }
}

async function startGenerate() {
  generating.value = true
  errorMsg.value = ''
  try {
    const result = await getAnalysis(chapterId)
    characters.value = result.characters
    const overrides = {}
    for (const c of characters.value) {
      if (c.voice_tag) overrides[c.id] = c.voice_tag
    }
    const resp = await generateChapter(chapterId, ttsProvider.value, overrides, 1.0)
    if (resp.error) {
      errorMsg.value = resp.error
      return
    }
    generating.value = false
    polling.value = true
    pollTimer = setInterval(pollProgress, 1000)
  } catch (e) {
    errorMsg.value = e.message || '启动生成失败'
    generating.value = false
  }
}

async function pollProgress() {
  try {
    const p = await getTTSProgress(chapterId)
    progress.value = p
    if (p.status === 'generating') {
      await loadResults()
    } else if (p.status === 'completed') {
      clearInterval(pollTimer)
      pollTimer = null
      polling.value = false
      await loadResults()
    } else if (p.status === 'cancelled') {
      clearInterval(pollTimer)
      pollTimer = null
      polling.value = false
    } else if (p.status === 'error') {
      clearInterval(pollTimer)
      pollTimer = null
      polling.value = false
      errorMsg.value = p.error || '生成出错'
    }
  } catch {
    clearInterval(pollTimer)
    pollTimer = null
    polling.value = false
  }
}

function playAll() {
  const completed = audios.value.filter(a => a.status === 'completed')
  if (!completed.length || !playerEl.value) return
  sequentialQueue.value = completed
  sequentialIdx.value = 0
  playing.value = true
  playSequential()
}

function playSequential() {
  if (sequentialIdx.value >= sequentialQueue.value.length) {
    playing.value = false
    currentPlayIdx.value = -1
    return
  }
  const item = sequentialQueue.value[sequentialIdx.value]
  currentPlayIdx.value = audios.value.indexOf(item)
  playerEl.value.src = getAudioUrl(item.id)
  playerEl.value.play().catch(() => {
    sequentialIdx.value++
    playSequential()
  })
}

function onSequentialEnd() {
  sequentialIdx.value++
  playSequential()
}

function onSegmentPlay(idx) {
  if (!playing.value) currentPlayIdx.value = idx
}

function onSegmentEnd(idx) {
  if (!playing.value && currentPlayIdx.value === idx) currentPlayIdx.value = -1
}

function saveAudio() {
  const url = exportChapterAudio(chapterId)
  const a = document.createElement('a')
  a.href = url
  a.download = `chapter_${chapterId}.mp3`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.header h2 { margin-bottom: 8px; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.progress-card { margin-bottom: 20px; }
.progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 14px; }
.status-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.status-tag.generating { background: #fff3e0; color: #e65100; }
.status-tag.completed { background: #e8f5e9; color: #2e7d32; }
.status-tag.error { background: #ffebee; color: #c62828; }
.bar { height: 8px; background: #e8e8ed; border-radius: 4px; overflow: hidden; }
.fill { height: 100%; background: #1a1a2e; border-radius: 4px; transition: width .3s ease; }
.cancel-btn { background: #d32f2f; color: #fff; }
.cancel-btn:hover { background: #b71c1c; }
.error-banner {
  background: #ffebee; color: #c62828; padding: 12px 16px;
  border-radius: 8px; margin-bottom: 16px; font-size: 14px;
}
.audio-list { display: flex; flex-direction: column; gap: 8px; margin-top: 20px; }
.audio-item {
  display: flex; align-items: center; gap: 12px; transition: background .2s;
}
.audio-item.playing { background: #e8f0fe; }
.line-num { color: #999; font-size: 12px; min-width: 24px; }
.error { color: #d32f2f; font-size: 12px; }
.completed { color: #2e7d32; }
.generating { color: #e65100; }
.pending { color: #999; }
.voice-config { margin-top: 20px; display: flex; flex-direction: column; gap: 12px; }
.hint { color: #999; font-size: 13px; }
.char-voice { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f0f0f0; }
.char-name { font-weight: 600; }
.voice-tag { color: #666; font-size: 13px; }
</style>
