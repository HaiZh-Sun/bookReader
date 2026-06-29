import client from './client'

export function cancelTTS(chapterId) {
  return client.post(`/tts/cancel/${chapterId}`)
}

export function generateChapter(chapterId, provider = 'edge_tts', voiceOverrides = {}, speed = 1.0) {
  return client.post('/tts/generate', {
    chapter_id: chapterId,
    provider,
    voice_overrides: voiceOverrides,
    speed,
  })
}

export function getTTSProgress(chapterId) {
  return client.get(`/tts/progress/${chapterId}`)
}

export function getTTSResults(chapterId) {
  return client.get(`/tts/results/${chapterId}`)
}

export function downloadAudio(audioId) {
  return `${client.defaults.baseURL}/tts/download/${audioId}`
}

export function uploadVoice(file) {
  const form = new FormData()
  form.append('file', file)
  return client.post('/tts/voices/upload', form)
}

export function listVoices() {
  return client.get('/tts/voices')
}

export function exportChapterAudio(chapterId) {
  return `${client.defaults.baseURL}/tts/export/${chapterId}`
}

export function getAudioUrl(audioId) {
  return `${client.defaults.baseURL}/tts/download/${audioId}`
}

export function previewVoice(voice) {
  return client.post('/tts/preview', { voice }, { responseType: 'blob' })
}
