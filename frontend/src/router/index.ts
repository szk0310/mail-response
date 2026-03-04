import { createRouter, createWebHistory } from 'vue-router'
import InquiryList from '../components/InquiryList.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: InquiryList,
    },
  ],
})

export default router
