import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import VoiceDesign from '@/views/VoiceDesign.vue'
import VoiceClone from '@/views/VoiceClone.vue'
import OfficialVoice from '@/views/OfficialVoice.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/voice-design',
    name: 'VoiceDesign',
    component: VoiceDesign
  },
  {
    path: '/voice-clone',
    name: 'VoiceClone',
    component: VoiceClone
  },
  {
    path: '/official-voice',
    name: 'OfficialVoice',
    component: OfficialVoice
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
