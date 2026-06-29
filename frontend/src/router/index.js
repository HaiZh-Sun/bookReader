import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import NovelList from '../views/NovelList.vue'
import NovelDetail from '../views/NovelDetail.vue'
import AnalysisResult from '../views/AnalysisResult.vue'
import Player from '../views/Player.vue'
import Settings from '../views/Settings.vue'
import VoiceLibrary from '../views/VoiceLibrary.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/novels', name: 'NovelList', component: NovelList },
  { path: '/novels/:id', name: 'NovelDetail', component: NovelDetail },
  { path: '/novels/:id/analysis/:chapterId', name: 'AnalysisResult', component: AnalysisResult, props: true },
  { path: '/novels/:id/player/:chapterId', name: 'Player', component: Player, props: true },
  { path: '/settings', name: 'Settings', component: Settings },
  { path: '/voices', name: 'VoiceLibrary', component: VoiceLibrary },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
