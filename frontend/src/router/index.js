import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/components/Dashboard.vue'
import Map3D from '@/components/3DMap.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/3d',
    name: '3DMap',
    component: Map3D
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
