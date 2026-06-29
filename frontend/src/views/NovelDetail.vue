<template>
  <div class="novel-detail" v-if="novel">
    <div class="header">
      <div>
        <h2>{{ novel.title }}</h2>
        <p class="meta">{{ novel.author }} · {{ novel.total_chapters }}章</p>
      </div>
      <div class="actions">
        <button @click="$router.push(`/novels/${novel.id}/analysis/${chapter?.id}`)"
          :disabled="!chapter">分析本章</button>
        <button @click="$router.push(`/voices`)">音色管理</button>
        <button class="danger" @click="del">删除</button>
      </div>
    </div>

    <div class="chapters">
      <h3>章节列表</h3>
      <div v-for="ch in novel.chapters" :key="ch.id"
        class="chapter-item"
        :class="{ active: selectedChapter === ch.id }"
        @click="selectChapter(ch)"
      >
        <div>
          <span class="chapter-title">{{ ch.title }}</span>
          <span class="chapter-meta">{{ ch.word_count }}字</span>
        </div>
        <div class="chapter-actions" v-if="selectedChapter === ch.id">
          <button @click.stop="$router.push(`/novels/${novel.id}/analysis/${ch.id}`)">分析</button>
          <button @click.stop="$router.push(`/novels/${novel.id}/player/${ch.id}`)">生成音频</button>
        </div>
      </div>
    </div>

    <div v-if="chapter" class="preview card">
      <h4>{{ chapter.title }}</h4>
      <p class="content-preview">{{ chapter.content.slice(0, 500) }}...</p>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getNovel, deleteNovel } from '../api/novels'

const route = useRoute()
const router = useRouter()
const novel = ref(null)
const chapter = ref(null)
const selectedChapter = ref(null)

onMounted(async () => {
  novel.value = await getNovel(route.params.id)
})

function selectChapter(ch) {
  chapter.value = ch
  selectedChapter.value = ch.id
}

async function del() {
  if (!confirm('确认删除？')) return
  await deleteNovel(route.params.id)
  router.push('/novels')
}
</script>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.meta { color: #666; font-size: 14px; }
.actions { display: flex; gap: 8px; }
.danger { background: #d32f2f; }
.chapter-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-radius: 8px; cursor: pointer; transition: background .15s;
}
.chapter-item:hover { background: #f0f0f5; }
.chapter-item.active { background: #e8e8f5; }
.chapter-title { font-weight: 500; }
.chapter-meta { color: #999; font-size: 12px; margin-left: 12px; }
.chapter-actions { display: flex; gap: 6px; }
.preview { margin-top: 20px; }
.content-preview { color: #555; font-size: 14px; margin-top: 8px; line-height: 1.8; }
.loading { text-align: center; padding: 60px; color: #999; }
</style>
