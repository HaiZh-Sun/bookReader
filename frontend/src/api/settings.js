import client from './client'

export function getSettings() {
  return client.get('/settings')
}

export function updateLLM(data) {
  return client.patch('/settings/llm', data)
}

export function updateTTS(data) {
  return client.patch('/settings/tts', data)
}

export function listProviders() {
  return client.get('/settings/providers')
}

export function updateSettings(data) {
  return client.patch('/settings', data)
}

export function updateVoiceAttrs(data) {
  return client.patch('/settings/voices/attrs', data)
}
