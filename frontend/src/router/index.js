import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/components/Dashboard.vue'
import Map3D from '@/components/3DMap.vue'
import MapDemo from '@/components/MapDemo.vue'
import NapoleonVisualization from '@/components/NapoleonVisualization.vue'

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
  },
  {
    path: '/demo',
    name: 'MapDemo',
    component: MapDemo
  },
  {
    path: '/napoleon',
    name: 'Napoleon',
    component: NapoleonVisualization
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
