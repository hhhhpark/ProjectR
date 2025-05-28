<template>
  <div class="stock-detail">
    <div class="container">
      <!-- 헤더 -->
      <div class="header">
        <button @click="goBack" class="back-button">
          ← 대시보드로 돌아가기
        </button>
        <div class="stock-info">
          <h1 class="stock-name">{{ stockName }}</h1>
          <p class="stock-code">{{ stockCode }}</p>
        </div>
      </div>
      
      <!-- 로딩 상태 -->
      <div v-if="isLoadingData" class="loading-section">
        <div class="loading-spinner"></div>
        <p>데이터를 불러오는 중...</p>
      </div>
      
      <!-- 데이터 요약 -->
      <div v-else-if="latestData" class="summary-section">
        <h2>📊 데이터 요약</h2>
        <div class="summary-cards">
          <div class="summary-card">
            <h3>최신 종가</h3>
            <p class="value">{{ formatPrice(latestData.close_price) }}원</p>
          </div>
          <div class="summary-card">
            <h3>등락률</h3>
            <p class="value" :class="getChangeClass(latestData.change_rate)">
              {{ formatPercent(latestData.change_rate) }}
            </p>
          </div>
          <div class="summary-card">
            <h3>거래량</h3>
            <p class="value">{{ formatVolume(latestData.volume) }}</p>
          </div>
          <div class="summary-card">
            <h3>시가총액</h3>
            <p class="value">{{ formatLargeNumber(latestData.market_cap) }}</p>
          </div>
        </div>
      </div>

      <!-- 차트 섹션 -->
      <div v-if="stockData.length > 0" class="charts-section">
        <!-- 캔들스틱 차트 -->
        <div class="chart-container">
          <h2>🕯️ 캔들스틱 차트</h2>
          <div class="chart-wrapper">
            <canvas ref="candlestickCanvas" id="candlestickChart"></canvas>
          </div>
        </div>
        
        <!-- 거래량 차트 -->
        <div class="chart-container">
          <h2>📊 거래량 추이</h2>
          <div class="chart-wrapper">
            <canvas ref="volumeCanvas" id="volumeChart"></canvas>
          </div>
        </div>
      </div>

      <!-- 데이터 테이블 -->
      <div v-if="stockData.length > 0" class="table-section">
        <div class="table-header">
          <h2>📋 상세 데이터 ({{ stockData.length }}개)</h2>
        </div>
        
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>날짜</th>
                <th>시가</th>
                <th>고가</th>
                <th>저가</th>
                <th>종가</th>
                <th>거래량</th>
                <th>등락률</th>
                <th>시가총액</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(row, index) in stockData.slice(0, 50)" 
                :key="index"
                class="table-row"
              >
                <td>{{ formatDate(row.date) }}</td>
                <td>{{ formatPrice(row.open_price) }}</td>
                <td>{{ formatPrice(row.high_price) }}</td>
                <td>{{ formatPrice(row.low_price) }}</td>
                <td>{{ formatPrice(row.close_price) }}</td>
                <td>{{ formatVolume(row.volume) }}</td>
                <td :class="getChangeClass(row.change_rate)">{{ formatPercent(row.change_rate) }}</td>
                <td>{{ formatLargeNumber(row.market_cap) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- 에러 상태 -->
      <div v-else-if="!isLoadingData" class="error-section">
        <h2>⚠️ 데이터를 불러올 수 없습니다</h2>
        <p>종목코드: {{ stockCode }}</p>
        <button @click="loadStockData" class="retry-button">다시 시도</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { CandlestickController, CandlestickElement, OhlcController, OhlcElement } from 'chartjs-chart-financial'
import 'chartjs-adapter-date-fns'
import axios from 'axios'

Chart.register(...registerables, CandlestickController, CandlestickElement, OhlcController, OhlcElement)

// 즉시 실행되는 디버깅 로그
console.log('🎯 StockDetailView component loaded!')
console.log('Current URL:', window.location.href)
console.log('Timestamp:', new Date().toISOString())

const route = useRoute()
const router = useRouter()
const candlestickCanvas = ref<HTMLCanvasElement>()
const volumeCanvas = ref<HTMLCanvasElement>()

const stockCode = ref('')
const stockName = ref('')
const stockData = ref<any[]>([])
const isLoadingData = ref(false)

// axios 설정
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
})

// 컴포넌트 마운트
onMounted(async () => {
  console.log('🚀 StockDetailView mounted!')
  console.log('Route params:', route.params)
  
  // 라우트 파라미터에서 값 추출
  const routeStockCode = route.params.stockCode as string
  const routeStockName = route.params.stockName as string
  
  console.log('Extracted params:', { routeStockCode, routeStockName })
  
  if (routeStockCode && routeStockName) {
    stockCode.value = routeStockCode
    stockName.value = decodeURIComponent(routeStockName)
    
    console.log('✅ Valid params, loading data...')
    console.log('Stock Code:', stockCode.value)
    console.log('Stock Name:', stockName.value)
    
    // 데이터 로드
    await loadStockData()
  } else {
    console.error('❌ Invalid route params')
  }
})

// 데이터 로드 함수
const loadStockData = async () => {
  if (!stockCode.value) {
    console.error('❌ No stock code available')
    return
  }
  
  console.log('=== loadStockData START ===')
  console.log('Loading data for:', stockCode.value)
  
  try {
    isLoadingData.value = true
    
    const apiUrl = `/api/collect-stock-data/${stockCode.value}?limit=1000`
    console.log('📡 Making axios request to:', apiUrl)
    
    const startTime = performance.now()
    const response = await api.get(apiUrl)
    const endTime = performance.now()
    
    console.log('📥 Response received:', {
      status: response.status,
      responseTime: `${(endTime - startTime).toFixed(2)}ms`,
      dataLength: response.data?.data?.length || 0
    })
    
    stockData.value = response.data.data || []
    console.log('✅ Data loaded:', stockData.value.length, 'records')
    
    // 차트 생성
    if (stockData.value.length > 0) {
      await nextTick()
      setTimeout(() => {
        createCharts()
      }, 300)
    }
    
  } catch (error) {
    console.error('❌ Failed to load data:', error)
    
    if (axios.isAxiosError(error)) {
      console.error('Axios error:', {
        message: error.message,
        status: error.response?.status,
        code: error.code
      })
    }
  } finally {
    isLoadingData.value = false
    console.log('=== loadStockData END ===')
  }
}

// 차트 생성
const createCharts = () => {
  try {
    console.log('🎨 Creating charts...')
    
    if (stockData.value.length === 0) {
      console.warn('No data for charts')
      return
    }
    
    // 기존 차트 제거
    destroyCharts()
    
    // 캔들스틱 차트 생성
    createCandlestickChart()
    
    // 거래량 차트 생성
    createVolumeChart()
    
    console.log('✅ Charts created successfully')
  } catch (error) {
    console.error('❌ Chart creation failed:', error)
  }
}

// 차트 제거
const destroyCharts = () => {
  try {
    if (candlestickCanvas.value) {
      const chart = Chart.getChart(candlestickCanvas.value)
      if (chart) chart.destroy()
    }
    
    if (volumeCanvas.value) {
      const chart = Chart.getChart(volumeCanvas.value)
      if (chart) chart.destroy()
    }
  } catch (error) {
    console.error('Chart destroy error:', error)
  }
}

// 캔들스틱 차트 생성
const createCandlestickChart = () => {
  if (!candlestickCanvas.value || stockData.value.length === 0) return
  
  const ctx = candlestickCanvas.value.getContext('2d')
  if (!ctx) return
  
  const chartData = stockData.value.slice(-90).reverse().map(row => ({
    x: new Date(row.date).getTime(),
    o: parseFloat(row.open_price) || 0,
    h: parseFloat(row.high_price) || 0,
    l: parseFloat(row.low_price) || 0,
    c: parseFloat(row.close_price) || 0
  }))
  
  new Chart(ctx, {
    type: 'candlestick',
    data: {
      datasets: [{
        label: `${stockName.value} 주가`,
        data: chartData,
        borderColor: '#26a69a',
        backgroundColor: 'rgba(38, 166, 154, 0.8)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'day',
            displayFormats: { day: 'MM/dd' }
          }
        },
        y: {
          title: { display: true, text: '주가 (원)' }
        }
      }
    }
  })
}

// 거래량 차트 생성
const createVolumeChart = () => {
  if (!volumeCanvas.value || stockData.value.length === 0) return
  
  const ctx = volumeCanvas.value.getContext('2d')
  if (!ctx) return
  
  const chartData = stockData.value.slice(-90).reverse()
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: chartData.map(row => formatDate(row.date)),
      datasets: [{
        label: '거래량',
        data: chartData.map(row => parseFloat(row.volume) || 0),
        backgroundColor: 'rgba(34, 197, 94, 0.6)',
        borderColor: '#22c55e',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          title: { display: true, text: '거래량' }
        }
      }
    }
  })
}

// 계산된 속성
const latestData = computed(() => {
  return stockData.value.length > 0 ? stockData.value[0] : null
})

// 유틸리티 함수들
const goBack = () => {
  router.push('/')
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ko-KR')
}

const formatPrice = (price: string | number) => {
  if (!price || price === 'None' || price === '') return '-'
  const num = typeof price === 'string' ? parseFloat(price) : price
  if (isNaN(num)) return '-'
  return new Intl.NumberFormat('ko-KR').format(num)
}

const formatVolume = (volume: string | number) => {
  if (!volume || volume === 'None' || volume === '') return '-'
  const num = typeof volume === 'string' ? parseFloat(volume) : volume
  if (isNaN(num)) return '-'
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

const formatPercent = (percent: string | number) => {
  if (!percent || percent === 'None' || percent === '') return '-'
  const num = typeof percent === 'string' ? parseFloat(percent) : percent
  if (isNaN(num)) return '-'
  return `${num.toFixed(2)}%`
}

const formatLargeNumber = (num: string | number) => {
  if (!num || num === 'None' || num === '') return '-'
  const value = typeof num === 'string' ? parseFloat(num) : num
  if (isNaN(value)) return '-'
  if (value >= 1000000000000) return `${(value / 1000000000000).toFixed(1)}조`
  if (value >= 100000000) return `${(value / 100000000).toFixed(1)}억`
  return formatPrice(value)
}

const getChangeClass = (change: string | number) => {
  if (!change || change === 'None' || change === '') return 'neutral'
  const num = typeof change === 'string' ? parseFloat(change) : change
  if (isNaN(num)) return 'neutral'
  if (num > 0) return 'positive'
  if (num < 0) return 'negative'
  return 'neutral'
}

// 정리
onUnmounted(() => {
  console.log('🧹 StockDetailView unmounting...')
  destroyCharts()
})
</script>

<style scoped>
.stock-detail {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 2rem;
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.container {
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem;
}

.back-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  margin-right: 2rem;
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(-5px);
}

.stock-info {
  color: white;
}

.stock-name {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.stock-code {
  font-size: 1rem;
  opacity: 0.8;
  margin: 0;
}

.loading-section {
  text-align: center;
  padding: 4rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.summary-section {
  margin-bottom: 2rem;
}

.summary-section h2 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.summary-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-5px);
}

.summary-card h3 {
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.summary-card .value {
  color: #333;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.chart-container h2 {
  color: #333;
  font-size: 1.3rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.chart-wrapper {
  height: 350px;
  position: relative;
}

.table-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.table-header h2 {
  color: #333;
  font-size: 1.3rem;
  margin: 0 0 1rem 0;
  font-weight: 600;
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  max-height: 500px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.data-table th,
.data-table td {
  padding: 0.75rem 0.5rem;
  text-align: right;
  border-bottom: 1px solid #e9ecef;
  font-size: 0.9rem;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table td:first-child,
.data-table th:first-child {
  text-align: left;
}

.table-row:hover {
  background: #f8f9fa;
}

.positive { color: #dc3545; }
.negative { color: #007bff; }
.neutral { color: #6c757d; }

.error-section {
  text-align: center;
  padding: 4rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
}

.retry-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1rem;
  transition: all 0.3s ease;
}

.retry-button:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
}

@media (max-width: 1400px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .back-button {
    margin-right: 0;
  }
  
  .summary-cards {
    grid-template-columns: 1fr 1fr;
  }
}
</style> 