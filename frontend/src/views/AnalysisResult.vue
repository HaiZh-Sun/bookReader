<template>
  <div class="analysis-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h3>{{ novel?.title || '章节列表' }}</h3>
        <router-link :to="`/novels/${novelId}`" class="back-link">返回</router-link>
      </div>
      <div class="chapter-tree">
        <div v-for="ch in chapters" :key="ch.id"
          class="chapter-node"
          :class="{ active: ch.id === currentChapterId }"
          @click="switchChapter(ch.id)">
          <span class="ch-order">{{ ch.order }}</span>
          <span class="ch-title">{{ ch.title }}</span>
          <span class="ch-status" v-if="chapterAnalysisStatus[ch.id] === 'done'" title="已分析">✓</span>
        </div>
        <div v-if="!chapters.length" class="empty-hint">暂无章节</div>
      </div>
    </aside>

    <main class="main-content">
      <div class="header">
        <h2>{{ currentChapter?.title || '对话分析结果' }}</h2>
        <div class="actions">
          <button @click="startAnalysis" :disabled="analyzing || polling">
            {{ analyzing ? '队列中...' : polling ? '分析中...' : '开始分析' }}
          </button>
          <button v-if="polling" @click="doCancel" class="cancel-btn">中断</button>
          <button @click="$router.push(`/novels/${novelId}/player/${currentChapterId}`)"
            :disabled="!analyzed">生成音频</button>
        </div>
      </div>

      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

      <div class="progress-card card" v-if="polling">
        <h3>分析进度</h3>
        <div class="progress-info">
          <span>{{ progress.completed_batches }} / {{ progress.total_batches }} 批</span>
          <span class="status-tag" :class="progress.status">{{ statusText }}</span>
        </div>
        <div class="bar">
          <div class="fill" :style="{ width: barPercent + '%' }"></div>
        </div>
      </div>

      <div class="card token-card" v-if="showTokenUsage && progress.token_usage?.total > 0">
        <h3>Token 消耗</h3>
        <div class="token-grid">
          <div class="token-item"><span class="label">Prompt</span><span class="value">{{ progress.token_usage.prompt }}</span></div>
          <div class="token-item"><span class="label">Completion</span><span class="value">{{ progress.token_usage.completion }}</span></div>
          <div class="token-item"><span class="label">总计</span><span class="value">{{ progress.token_usage.total }}</span></div>
          <div class="token-item"><span class="label">批次数</span><span class="value">{{ progress.total_batches }}</span></div>
        </div>
      </div>

      <div class="characters card" v-if="activeChars.length">
        <div class="section-header">
          <h3>识别角色 ({{ activeChars.length }})</h3>
          <div class="layout-toggle">
            <button :class="{ active: layout === 'card' }" @click="layout = 'card'" title="卡片视图">▦</button>
            <button :class="{ active: layout === 'list' }" @click="layout = 'list'" title="列表视图">☰</button>
          </div>
        </div>
        <div :class="'char-' + layout">
          <div v-for="c in activeChars" :key="c.id" class="char-item"
            :class="{ selected: selectedCharIds.has(c.id) }">
            <input type="checkbox" :checked="selectedCharIds.has(c.id)"
              @change="toggleSelect(c.id)" class="char-checkbox" />
            <span class="char-name">{{ c.name }}</span>
            <span class="char-type">{{ c.speaker_type }}</span>
            <input v-model="c.name" @change="rename(c)" class="rename-input" placeholder="重命名" />
            <select v-model="c.age_group" @change="updateAttrs(c)" class="attr-select">
              <option value="少儿">少儿</option>
              <option value="成年">成年</option>
              <option value="老">老</option>
            </select>
            <select v-model="c.gender" @change="updateAttrs(c)" class="attr-select">
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
            <select v-model="c.voice_tag" @change="setVoice(c)" class="voice-select">
              <option value="">默认</option>
              <option v-for="v in voices" :key="v" :value="v">{{ voiceLabel(v) }}</option>
            </select>
          </div>
        </div>
        <div class="merge-section" v-if="selectedCharIds.size > 0">
          <span class="merge-hint">已选 {{ selectedCharIds.size }} 个 → 合并到 (合并后源角色将隐藏):</span>
          <select v-model="mergeTarget">
            <option value="" disabled>选择目标角色</option>
            <option v-for="c in activeChars" :key="c.id" :value="c.id"
              :disabled="selectedCharIds.has(c.id)">{{ c.name }}</option>
          </select>
          <button @click="mergeSelected" :disabled="!mergeTarget">合并</button>
        </div>
      </div>

      <div class="dialogues card" v-if="lines.length">
        <h3>对话标注 <span class="hint">点击角色名可修改，点击文本可编辑</span></h3>
        <div v-for="(l, idx) in lines" :key="l.id" class="dialogue-block">
          <div class="original-text" v-if="paragraphs[l.paragraph_index]">
            <span class="orig-label">原文:</span>
            <span class="orig-content">{{ paragraphs[l.paragraph_index] }}</span>
          </div>
          <div class="line" :style="{ borderLeftColor: getColor(l.speaker_type) }">
            <div class="speaker-col">
              <select v-model="l.character_id" @change="onCharChange(l)" class="speaker-select">
                <option :value="null">旁白</option>
                <option v-for="c in activeChars" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="text-col">
              <span v-if="editingLine !== l.id" class="text" @click="startEdit(l)">{{ l.text }}</span>
              <textarea v-else v-model="editText" ref="editRef" class="text-input"
                @blur="saveText(l)" @keydown.enter.ctrl="saveText(l)"
                @keydown.escape="cancelEdit"></textarea>
            </div>
            <button class="delete-btn" @click="deleteLine(l)" title="删除此行">×</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getNovel, getChapter } from '../api/novels'
import { getSettings } from '../api/settings'
import { analyzeChapter, cancelAnalysis, getAnalysisProgress, getAnalysis, mergeCharacters, renameCharacter, setCharacterVoice, updateCharacterAttrs, updateDialogueCharacter, updateDialogueText, deleteDialogueLine } from '../api/analysis'

const route = useRoute()
const router = useRouter()
const novelId = computed(() => route.params.id)
const currentChapterId = computed(() => parseInt(route.params.chapterId))

const novel = ref(null)
const chapters = ref([])
const currentChapter = ref(null)
const analyzing = ref(false)
const polling = ref(false)
const analyzed = ref(false)
const characters = ref([])
const lines = ref([])
const mergeTarget = ref('')
const selectedCharIds = ref(new Set())
const errorMsg = ref('')
const editingLine = ref(null)
const editText = ref('')
const editRef = ref(null)
const paragraphs = ref([])
const progress = ref({ status: '', total_batches: 0, completed_batches: 0, token_usage: { prompt: 0, completion: 0, total: 0 } })
const layout = ref('card')
const chapterAnalysisStatus = ref({})
const showTokenUsage = ref(false)
const voices = ref([])
const voiceAttrs = ref({})
let pollTimer = null

const activeChars = computed(() => characters.value.filter(c => !c.is_merged))

const statusText = computed(() => ({
  pending: '等待中',
  analyzing: '分析中',
  completed: '已完成',
  error: '出错',
}[progress.value.status] || progress.value.status))

const barPercent = computed(() => {
  const p = progress.value
  if (!p.total_batches) return 0
  return Math.round(p.completed_batches / p.total_batches * 100)
})

watch(currentChapterId, async () => {
  analyzed.value = false
  characters.value = []
  lines.value = []
  errorMsg.value = ''
  progress.value = { status: '', total_batches: 0, completed_batches: 0 }
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; polling.value = false }
  await loadCurrent()
})

onMounted(async () => {
  try {
    const s = await getSettings()
    showTokenUsage.value = s.show_token_usage
    voices.value = s.tts.voices?.length ? s.tts.voices : [
      'zh-CN-XiaoxiaoNeural', 'zh-CN-XiaoyiNeural', 'zh-CN-YunjianNeural',
      'zh-CN-YunxiNeural', 'zh-CN-YunxiaNeural', 'zh-CN-YunyangNeural',
      'zh-HK-HiuGaaiNeural', 'zh-HK-HiuMaanNeural', 'zh-HK-WanLungNeural',
      'zh-TW-HsiaoChenNeural', 'zh-TW-HsiaoYuNeural', 'zh-TW-YunJheNeural',
    ]
  } catch { }
  await loadNovel()
  await loadCurrent()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function loadNovel() {
  try {
    const n = await getNovel(novelId.value)
    novel.value = n
    chapters.value = n.chapters || []
    await checkAnalysisStatus()
  } catch { }
}

async function checkAnalysisStatus() {
  const status = {}
  for (const ch of chapters.value) {
    try {
      const r = await getAnalysis(ch.id)
      status[ch.id] = r.dialogue_lines?.length > 0 ? 'done' : 'pending'
    } catch {
      status[ch.id] = 'pending'
    }
  }
  chapterAnalysisStatus.value = status
}

async function loadCurrent() {
  try {
    currentChapter.value = chapters.value.find(c => c.id === currentChapterId.value) || null
  } catch { }
  try {
    const result = await getAnalysis(currentChapterId.value)
    if (result.dialogue_lines?.length) {
      characters.value = result.characters
      lines.value = result.dialogue_lines
      voiceAttrs.value = result.voice_attrs || {}
      analyzed.value = true
    }
  } catch { }
  await loadChapterContent()
}

async function loadChapterContent() {
  try {
    const ch = await getChapter(novelId.value, currentChapterId.value)
    paragraphs.value = ch.content.split('\n').filter(p => p.trim())
    currentChapter.value = ch
  } catch { }
}

function switchChapter(chId) {
  if (chId === currentChapterId.value) return
  router.push(`/novels/${novelId.value}/analysis/${chId}`)
}

function apiError(e) {
  return e.response?.data?.detail || e.message || '请求失败'
}

async function doCancel() {
  try {
    await cancelAnalysis(currentChapterId.value)
  } catch { }
}

async function startAnalysis() {
  analyzing.value = true
  errorMsg.value = ''
  try {
    const result = await analyzeChapter(currentChapterId.value)
    if (result.error) {
      errorMsg.value = result.error
      analyzing.value = false
      return
    }
    analyzing.value = false
    polling.value = true
    pollTimer = setInterval(pollProgress, 800)
  } catch (e) {
    errorMsg.value = apiError(e) || '启动分析失败'
    analyzing.value = false
  }
}

async function pollProgress() {
  try {
    const p = await getAnalysisProgress(currentChapterId.value)
    progress.value = p
    if (p.status === 'completed') {
      clearInterval(pollTimer); pollTimer = null; polling.value = false
      await loadResults()
    } else if (p.status === 'error') {
      clearInterval(pollTimer); pollTimer = null; polling.value = false
      errorMsg.value = p.error || '分析出错'
    } else if (p.status === 'cancelled') {
      clearInterval(pollTimer); pollTimer = null; polling.value = false
    }
  } catch {
    clearInterval(pollTimer); pollTimer = null; polling.value = false
  }
}

async function loadResults() {
  try {
    const result = await getAnalysis(currentChapterId.value)
    characters.value = result.characters
    lines.value = result.dialogue_lines
    voiceAttrs.value = result.voice_attrs || {}
    analyzed.value = true
    chapterAnalysisStatus.value[currentChapterId.value] = 'done'
  } catch { }
}

function toggleSelect(charId) {
  const s = new Set(selectedCharIds.value)
  if (s.has(charId)) s.delete(charId); else s.add(charId)
  selectedCharIds.value = s
}

async function mergeSelected() {
  if (!mergeTarget.value) return
  await mergeCharacters(novelId.value, [...selectedCharIds.value], mergeTarget.value)
  selectedCharIds.value = new Set()
  mergeTarget.value = ''
  await loadResults()
}

async function rename(c) { await renameCharacter(c.id, c.name) }
function voiceLabel(v) {
  const a = voiceAttrs.value[v]
  if (!a) return v
  const parts = [a.age_group || '', a.gender || ''].filter(Boolean).join('/')
  const desc = a.description || ''
  return parts || desc ? `${v} [${parts}] ${desc}`.trim() : v
}
async function setVoice(c) { await setCharacterVoice(c.id, c.voice_tag) }
async function updateAttrs(c) { await updateCharacterAttrs(c.id, { age_group: c.age_group, gender: c.gender }) }
async function onCharChange(l) { await updateDialogueCharacter(l.id, l.character_id) }

function startEdit(l) {
  editingLine.value = l.id
  editText.value = l.text
  nextTick(() => { if (editRef.value) editRef.value.focus() })
}

async function deleteLine(l) {
  try {
    await deleteDialogueLine(l.id)
    lines.value = lines.value.filter(x => x.id !== l.id)
  } catch { }
}

async function saveText(l) {
  if (editText.value !== l.text) {
    l.text = editText.value
    await updateDialogueText(l.id, editText.value)
  }
  editingLine.value = null
}
function cancelEdit() { editingLine.value = null }
function getColor(type) { return type === 'narrator' ? '#999' : '#1a1a2e' }
</script>

<style scoped>
.analysis-layout { display: flex; gap: 20px; align-items: flex-start; }

.sidebar {
  width: 240px; flex-shrink: 0; background: #fff; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08); overflow: hidden; position: sticky; top: 24px;
}
.sidebar-header {
  padding: 16px; border-bottom: 1px solid #eee;
  display: flex; justify-content: space-between; align-items: center;
}
.sidebar-header h3 { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.back-link { font-size: 12px; color: #1a1a2e; text-decoration: none; white-space: nowrap; }
.chapter-tree { max-height: calc(100vh - 150px); overflow-y: auto; padding: 8px 0; }
.chapter-node {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  cursor: pointer; transition: background .15s; font-size: 13px;
}
.chapter-node:hover { background: #f5f5f7; }
.chapter-node.active { background: #e8e8f5; font-weight: 600; }
.ch-order {
  width: 22px; height: 22px; border-radius: 50%; background: #e8e8ed;
  display: flex; align-items: center; justify-content: center; font-size: 11px;
  flex-shrink: 0;
}
.chapter-node.active .ch-order { background: #1a1a2e; color: #fff; }
.ch-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ch-status { color: #2e7d32; font-size: 14px; flex-shrink: 0; }
.empty-hint { text-align: center; padding: 24px; color: #999; font-size: 13px; }

.main-content { flex: 1; min-width: 0; }

.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.actions { display: flex; gap: 8px; }
.cancel-btn { background: #d32f2f; color: #fff; }
.cancel-btn:hover { background: #b71c1c; }
.error-banner {
  background: #ffebee; color: #c62828; padding: 12px 16px;
  border-radius: 8px; margin-bottom: 16px; font-size: 14px;
}
.progress-card { margin-bottom: 20px; }
.progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 14px; }
.status-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.status-tag.analyzing { background: #fff3e0; color: #e65100; }
.status-tag.completed { background: #e8f5e9; color: #2e7d32; }
.status-tag.error { background: #ffebee; color: #c62828; }
.bar { height: 8px; background: #e8e8ed; border-radius: 4px; overflow: hidden; }
.fill { height: 100%; background: #1a1a2e; border-radius: 4px; transition: width .3s ease; }
.token-card { margin-bottom: 20px; }
.token-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 8px; }
.token-item { text-align: center; }
.token-item .label { display: block; font-size: 12px; color: #999; }
.token-item .value { display: block; font-size: 20px; font-weight: 700; color: #1a1a2e; }

.section-header { display: flex; justify-content: space-between; align-items: center; }
.layout-toggle { display: flex; gap: 4px; }
.layout-toggle button {
  background: #e8e8ed; color: #555; padding: 4px 10px; font-size: 16px; line-height: 1;
}
.layout-toggle button.active { background: #1a1a2e; color: #fff; }

.char-card {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 12px 0;
}
.char-card .char-item { flex-wrap: wrap; min-width: 0; }
.char-card .rename-input { width: 100%; }
.char-card .voice-select { max-width: none; width: 100%; }

.char-list { display: flex; flex-direction: column; gap: 6px; margin: 12px 0; }
.char-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #f5f5f7; border-radius: 8px;
  border: 2px solid transparent; transition: border-color .15s;
}
.char-list .char-item { border-radius: 6px; }
.char-item.selected { border-color: #1a1a2e; }
.char-checkbox { cursor: pointer; flex-shrink: 0; width: 20px; height: 20px; }
.char-name { font-weight: 600; flex-shrink: 0; min-width: 48px; }
.char-type { font-size: 12px; color: #999; flex-shrink: 0; min-width: 36px; }
.rename-input { font-size: 12px; padding: 4px 8px; width: 90px; flex-shrink: 0; }
.attr-select { font-size: 12px; padding: 4px 8px; width: 60px; flex-shrink: 0; }
.voice-select { font-size: 12px; padding: 4px 8px; flex: 1; min-width: 0; max-width: 200px; }
.merge-section { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 12px; background: #f0f0f5; border-radius: 8px; }
.merge-hint { font-size: 13px; color: #555; white-space: nowrap; }
.dialogue-block { margin-bottom: 12px; }
.original-text {
  display: flex; gap: 8px; padding: 6px 12px; margin-bottom: 2px;
  background: #fafafa; border-radius: 4px; font-size: 12px; color: #888;
  border-left: 3px solid #e0e0e0;
}
.orig-label { white-space: nowrap; font-weight: 600; color: #999; }
.orig-content { line-height: 1.6; }
.line {
  display: flex; gap: 12px; padding: 8px 12px; border-left: 3px solid;
  align-items: center;
}
.delete-btn { background: none; border: none; color: #d32f2f; font-size: 18px; cursor: pointer; padding: 0 4px; line-height: 1; flex-shrink: 0; opacity: 0.4; }
.delete-btn:hover { opacity: 1; }
.speaker-col { min-width: 100px; flex-shrink: 0; }
.speaker-select { font-size: 13px; padding: 2px 4px; width: 100%; }
.text-col { flex: 1; min-width: 0; }
.text { color: #333; cursor: pointer; display: block; line-height: 1.6; }
.text:hover { background: #f0f0f5; border-radius: 4px; }
.text-input { width: 100%; min-height: 60px; font-size: 13px; resize: vertical; }
.hint { font-size: 12px; color: #999; font-weight: normal; }
</style>
