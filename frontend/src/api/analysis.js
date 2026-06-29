import client from './client'

export function cancelAnalysis(chapterId) {
  return client.post(`/analysis/chapters/${chapterId}/cancel`)
}

export function analyzeChapter(chapterId) {
  return client.post(`/analysis/chapters/${chapterId}/analyze`)
}

export function getAnalysisProgress(chapterId) {
  return client.get(`/analysis/progress/${chapterId}`)
}

export function getAnalysis(chapterId) {
  return client.get(`/analysis/chapters/${chapterId}`)
}

export function mergeCharacters(novelId, sourceIds, targetId) {
  return client.post(`/analysis/novels/${novelId}/characters/merge`, {
    source_ids: sourceIds,
    target_id: targetId,
  })
}

export function renameCharacter(characterId, name) {
  return client.patch(`/analysis/characters/${characterId}/rename`, { name })
}

export function setCharacterVoice(characterId, voiceTag) {
  return client.patch(`/analysis/characters/${characterId}/voice`, { voice_tag: voiceTag })
}

export function updateCharacterAttrs(characterId, attrs) {
  return client.patch(`/analysis/characters/${characterId}/attrs`, attrs)
}

export function updateDialogueCharacter(lineId, characterId) {
  return client.patch(`/analysis/dialogue-lines/${lineId}/character`, { character_id: characterId })
}

export function updateDialogueText(lineId, text) {
  return client.patch(`/analysis/dialogue-lines/${lineId}/text`, { text })
}

export function deleteDialogueLine(lineId) {
  return client.delete(`/analysis/dialogue-lines/${lineId}`)
}
