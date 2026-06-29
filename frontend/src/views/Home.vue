<template>
  <div class="home">
    <div class="hero">
      <h1>BookReader</h1>
      <p>上传小说，智能分析角色对话，一键生成有声书</p>
      <div class="actions">
        <button @click="$router.push('/novels')">开始使用</button>
        <button class="secondary" @click="$router.push('/settings')">配置服务</button>
      </div>
    </div>
    <div class="stats" v-if="novels.length">
      <div class="stat"><span>{{ novels.length }}</span>本小说</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listNovels } from '../api/novels'

const novels = ref([])
onMounted(async () => {
  novels.value = await listNovels()
})
</script>

<style scoped>
.home { text-align: center; padding-top: 80px; }
.hero h1 { font-size: 48px; margin-bottom: 12px; }
.hero p { color: #666; font-size: 18px; margin-bottom: 32px; }
.actions { display: flex; gap: 12px; justify-content: center; }
.secondary { background: #e8e8ed; color: #1d1d1f; }
.stats { margin-top: 48px; }
.stat { font-size: 18px; color: #666; }
.stat span { font-weight: bold; color: #1a1a2e; font-size: 24px; }
</style>
