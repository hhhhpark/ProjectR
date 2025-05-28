import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import StockChartView from '@/views/StockChartView.vue'
import CsvChartView from '@/views/CsvChartView.vue'
import StockDetailView from '@/views/StockDetailView.vue'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/stock/:code',
      name: 'stock-chart',
      component: StockChartView
    },
    {
      path: '/csv-chart/:stockName',
      name: 'csv-chart',
      component: CsvChartView
    },
    {
      path: '/stock-detail/:stockCode/:stockName',
      name: 'stock-detail',
      component: StockDetailView
    }
  ]
})

export default router
