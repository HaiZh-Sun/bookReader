import client from './client'

export function listNovels() {
  return client.get('/novels')
}

export function getNovel(id) {
  return client.get(`/novels/${id}`)
}

export function uploadNovel(file, title = '', author = '') {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)
  if (author) form.append('author', author)
  return client.post('/novels/upload', form)
}

export function deleteNovel(id) {
  return client.delete(`/novels/${id}`)
}

export function getChapter(novelId, chapterId) {
  return client.get(`/novels/${novelId}/chapters/${chapterId}`)
}
