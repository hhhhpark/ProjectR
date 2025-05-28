<template>
  <div class="stock-chart">
    <div class="container">
      <div class="header">
        <button @click="goBack" class="back-button">
          ← 대시보드로 돌아가기
        </button>
        <div class="stock-info">
          <h1 class="stock-name">{{ stockInfo.name || '로딩 중...' }}</h1>
          <p class="stock-code">{{ stockInfo.code }}</p>
        </div>
      </div>
      
      <div class="chart-container">
        <div class="chart-section">
          <h2>주가 차트</h2>
          <div class="chart-wrapper">
            <canvas ref="chartCanvas" id="stockChart"></canvas>
          </div>
        </div>
        
        <div class="info-section">
          <div class="pattern-analysis">
            <h3>패턴 분석 결과</h3>
            <div class="risk-badge" :class="riskLevel.toLowerCase()">
              {{ riskLevel }}
            </div>
            <div class="analysis-details" v-if="patternData">
              <p><strong>위험 점수:</strong> {{ patternData.risk_score }}/10</p>
              <p><strong>분석일:</strong> {{ formatDate(patternData.analysis_date) }}</p>
            </div>
          </div>
          
          <div class="stock-data">
            <h3>최근 주가 정보</h3>
            <div class="data-grid" v-if="latestData">
              <div class="data-item">
                <span class="label">현재가</span>
                <span class="value">{{ formatPrice(latestData.close) }}원</span>
              </div>
              <div class="data-item">
                <span class="label">거래량</span>
                <span class="value">{{ formatVolume(latestData.volume) }}</span>
              </div>
              <div class="data-item">
                <span class="label">시가총액</span>
                <span class="value">{{ formatPrice(latestData.market_cap) }}원</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const route = useRoute()
const router = useRouter()
const chartCanvas = ref<HTMLCanvasElement>()

const stockInfo = ref({
  name: '',
  code: route.params.code as string
})

const riskLevel = ref('NORMAL')
const patternData = ref<any>(null)
const latestData = ref<any>(null)
const chartData = ref<any[]>([])

const goBack = () => {
  router.push('/')
}

const formatPrice = (price: number) => {
  return new Intl.NumberFormat('ko-KR').format(price)
}

const formatVolume = (volume: number) => {
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`
  }
  return volume.toString()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('ko-KR')
}

const fetchStockData = async () => {
  try {
    // 주식 정보 가져오기
    const stockResponse = await fetch(`http://localhost:8000/api/stocks`)
    const stocks = await stockResponse.json()
    const stock = stocks.find((s: any) => s.code === stockInfo.value.code)
    if (stock) {
      stockInfo.value.name = stock.name
    }

    // 차트 데이터 가져오기
    const chartResponse = await fetch(`http://localhost:8000/api/stocks/${stockInfo.value.code}/chart`)
    chartData.value = await chartResponse.json()

    // 패턴 분석 데이터 가져오기
    const patternResponse = await fetch(`http://localhost:8000/api/stocks/${stockInfo.value.code}/pattern`)
    patternData.value = await patternResponse.json()
    riskLevel.value = patternData.value?.risk_level || 'NORMAL'

    // 최신 데이터 가져오기
    const dataResponse = await fetch(`http://localhost:8000/api/stocks/${stockInfo.value.code}/data`)
    const allData = await dataResponse.json()
    if (allData.length > 0) {
      latestData.value = allData[allData.length - 1]
    }

  } catch (error) {
    console.error('데이터 로딩 실패:', error)
  }
}

const createChart = () => {
  if (!chartCanvas.value || chartData.value.length === 0) return

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.value.map(d => new Date(d.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })),
      datasets: [
        {
          label: '종가',
          data: chartData.value.map(d => d.close),
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1
        },
        {
          label: '거래량',
          data: chartData.value.map(d => d.volume / 1000),
          type: 'bar',
          backgroundColor: 'rgba(118, 75, 162, 0.3)',
          borderColor: '#764ba2',
          borderWidth: 1,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: '주가 (원)'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: '거래량 (천주)'
          },
          grid: {
            drawOnChartArea: false,
          },
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        title: {
          display: true,
          text: `${stockInfo.value.name} (${stockInfo.value.code}) 주가 차트`
        }
      }
    }
  })
}

onMounted(async () => {
  await fetchStockData()
  await nextTick()
  createChart()
})
</script>

<style scoped>
.stock-chart {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 2rem;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  gap: 2rem;
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
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.3);
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

.chart-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.chart-section h2 {
  color: #333;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.chart-wrapper {
  height: 500px;
  position: relative;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.pattern-analysis,
.stock-data {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.pattern-analysis h3,
.stock-data h3 {
  color: #333;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.risk-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.risk-badge.normal {
  background: #d1ecf1;
  color: #0c5460;
}

.risk-badge.low {
  background: #d4edda;
  color: #155724;
}

.risk-badge.medium {
  background: #fff3cd;
  color: #856404;
}

.risk-badge.high {
  background: #f8d7da;
  color: #721c24;
}

.analysis-details p {
  margin: 0.5rem 0;
  color: #666;
}

.data-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.label {
  color: #6c757d;
  font-size: 0.9rem;
}

.value {
  color: #333;
  font-weight: 600;
}

@media (max-width: 768px) {
  .chart-container {
    grid-template-columns: 1fr;
  }
  
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style> 