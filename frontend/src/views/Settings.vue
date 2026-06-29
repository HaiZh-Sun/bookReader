<template>
  <div class="settings">
    <h2>系统设置</h2>

    <div class="card section" v-if="settings">
      <h3>语言模型 (LLM)</h3>
      <div class="field">
        <label>Provider</label>
        <select v-model="llmForm.provider">
          <option v-for="p in providers.llm" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="field">
        <label>API Base</label>
        <input v-model="llmForm.api_base" />
      </div>
      <div class="field">
        <label>Model</label>
        <input v-model="llmForm.model" />
      </div>
      <div class="field">
        <label>API Key</label>
        <input v-model="llmForm.api_key" type="password" :placeholder="settings.llm.api_key_set ? '已设置(留空不修改)' : '输入 API Key'" />
      </div>
      <button @click="saveLLM">保存 LLM 设置</button>
    </div>

    <div class="card section" v-if="settings">
      <h3>语音合成 (TTS)</h3>
      <div class="field">
        <label>Provider</label>
        <select v-model="ttsForm.provider">
          <option v-for="p in providers.tts" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>

      <template v-if="ttsForm.provider === 'edge_tts'">
        <div class="field">
          <label>默认音色</label>
          <select v-model="ttsForm.edge_voice">
            <option v-for="v in edgeVoices" :key="v" :value="v">{{ v }}</option>
          </select>
        </div>
      </template>

      <template v-if="ttsForm.provider === 'cosyvoice'">
        <div class="field">
          <label>CosyVoice 服务器地址</label>
          <input v-model="ttsForm.cosyvoice_api_base" placeholder="http://192.168.x.x:5000" />
          <p class="hint">运行 CosyVoice 服务的机器地址和端口</p>
        </div>
        <div class="field">
          <label>默认发音人</label>
          <input v-model="ttsForm.cosyvoice_default_voice" placeholder="留空使用模型默认" />
        </div>
      </template>

      <template v-if="ttsForm.provider === 'cosyvoice_gradio'">
        <div class="field">
          <label>CosyVoice 服务器地址</label>
          <input v-model="ttsForm.cosyvoice_api_base" placeholder="http://192.168.x.x:50000" />
          <p class="hint">Gradio WebUI 地址和端口</p>
        </div>
        <div class="field">
          <label>默认音色</label>
          <select v-model="ttsForm.cosyvoice_default_voice">
            <option value="">使用默认</option>
            <option v-for="v in settings.tts.voices" :key="v" :value="v">{{ v }}</option>
          </select>
        </div>
      </template>

      <button @click="saveTTS">保存 TTS 设置</button>
    </div>

    <div class="card section" v-if="settings && settings.tts.voices.length">
      <h3>音色属性配置</h3>
      <p class="hint">设置每个音色对应的年龄段和性别，分析时将自动为角色匹配合适的音色</p>
      <table class="voice-attr-table">
        <thead>
          <tr><th>音色名称</th><th>年龄段</th><th>性别</th><th>描述</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="v in settings.tts.voices" :key="v">
            <td>{{ v }}</td>
            <td>
              <select v-model="voiceAttrForm[v].age_group">
                <option value="少儿">少儿</option>
                <option value="成年">成年</option>
                <option value="老">老</option>
              </select>
            </td>
            <td>
              <select v-model="voiceAttrForm[v].gender">
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </td>
            <td><input v-model="voiceAttrForm[v].description" class="desc-input" placeholder="如: 温柔的女声" /></td>
            <td><button class="preview-btn" @click="listen(v)">试听</button></td>
          </tr>
        </tbody>
      </table>
      <button @click="saveVoiceAttrs">保存音色属性</button>
    </div>

    <div class="card section" v-if="settings">
      <h3>显示选项</h3>
      <label class="toggle-row">
        <input type="checkbox" v-model="showTokenUsage" @change="saveShowToken" />
        <span>分析完成后显示 Token 消耗</span>
      </label>
    </div>

    <p v-if="saved" class="saved">保存成功</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateLLM, updateTTS, updateSettings, updateVoiceAttrs, listProviders } from '../api/settings'
import { previewVoice } from '../api/tts'

const settings = ref(null)
const providers = ref({ llm: ['openai_compatible'], tts: ['edge_tts', 'cosyvoice', 'cosyvoice_gradio'] })
const saved = ref(false)
const showTokenUsage = ref(false)
const edgeVoices = [
  'zh-CN-XiaoxiaoNeural', 'zh-CN-XiaoyiNeural', 'zh-CN-YunjianNeural',
  'zh-CN-YunxiNeural', 'zh-CN-YunxiaNeural', 'zh-CN-YunyangNeural',
  'zh-HK-HiuGaaiNeural', 'zh-HK-HiuMaanNeural', 'zh-HK-WanLungNeural',
  'zh-TW-HsiaoChenNeural', 'zh-TW-HsiaoYuNeural', 'zh-TW-YunJheNeural',
]

const llmForm = ref({ provider: '', api_base: '', model: '', api_key: '' })
const ttsForm = ref({ provider: '', edge_voice: '', cosyvoice_api_base: '', cosyvoice_default_voice: '' })
const voiceAttrForm = ref({})

onMounted(async () => {
  settings.value = await getSettings()
  providers.value = await listProviders()
  llmForm.value = {
    provider: settings.value.llm.provider,
    api_base: settings.value.llm.api_base,
    model: settings.value.llm.model,
    api_key: '',
  }
  ttsForm.value = {
    provider: settings.value.tts.provider,
    edge_voice: settings.value.tts.edge_voice,
    cosyvoice_api_base: settings.value.tts.cosyvoice_api_base,
    cosyvoice_default_voice: settings.value.tts.cosyvoice_default_voice,
  }
  showTokenUsage.value = settings.value.show_token_usage
  voiceAttrForm.value = {}
  for (const [k, v] of Object.entries(settings.value.tts.voice_attrs)) {
    voiceAttrForm.value[k] = { age_group: v.age_group, gender: v.gender, description: v.description || '' }
  }
})

async function saveLLM() {
  saved.value = false
  await updateLLM(llmForm.value)
  saved.value = true
}

async function saveTTS() {
  saved.value = false
  await updateTTS(ttsForm.value)
  saved.value = true
}

function listen(voice) {
  previewVoice(voice).then(blob => {
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.play()
  }).catch(() => {})
}

async function saveVoiceAttrs() {
  saved.value = false
  await updateVoiceAttrs(voiceAttrForm.value)
  saved.value = true
}

async function saveShowToken() {
  saved.value = false
  await updateSettings({ show_token_usage: showTokenUsage.value })
  saved.value = true
}
</script>

<style scoped>
.section { margin-bottom: 24px; }
.field { margin: 12px 0; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.hint { font-size: 12px; color: #999; margin-top: 4px; }
.saved { color: #2e7d32; margin-top: 12px; }
.toggle-row { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; }
.toggle-row input { width: auto; }
.voice-attr-table { width: 100%; border-collapse: collapse; margin: 12px 0; }
.voice-attr-table th, .voice-attr-table td { padding: 6px 8px; border: 1px solid #eee; text-align: left; font-size: 13px; }
.voice-attr-table th { background: #f5f5f7; font-weight: 600; }
.voice-attr-table select { font-size: 12px; padding: 2px 4px; width: 100%; }
.preview-btn { font-size: 12px; padding: 2px 8px; }
.desc-input { font-size: 12px; padding: 2px 4px; width: 120px; }
</style>
