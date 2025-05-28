<template>
  <div class="csv-chart">
    <div class="container">
      <div class="header">
        <button @click="goBack" class="back-button">
          ← 대시보드로 돌아가기
        </button>
        <div class="stock-info">
          <h1 class="stock-name">{{ stockName }}</h1>
          <p class="stock-code">CSV 데이터 차트</p>
        </div>
      </div>
      
      <div class="period-selector-top">
        <h3>📅 기간 선택</h3>
        <div class="period-buttons">
          <button 
            v-for="period in periods" 
            :key="period.value"
            @click="changePeriod(period.value)"
            :class="{ active: selectedPeriod === period.value }"
            class="period-btn"
          >
            {{ period.label }}
          </button>
        </div>
      </div>
      
      <div class="chart-container">
        <div class="chart-section">
          <h2>캔들스틱 차트</h2>
          <div class="chart-wrapper">
            <canvas ref="candlestickCanvas" id="candlestickChart"></canvas>
          </div>
        </div>
        
        <div class="volume-section">
          <h2>거래량</h2>
          <div class="chart-wrapper">
            <canvas ref="volumeCanvas" id="volumeChart"></canvas>
          </div>
        </div>
      </div>
      
      <div class="info-section">
        <div class="data-summary">
          <h3>데이터 요약</h3>
          <div class="summary-grid" v-if="latestData">
            <div class="summary-item">
              <span class="label">최신 종가</span>
              <span class="value">{{ formatPrice(latestData.종가) }}원</span>
            </div>
            <div class="summary-item">
              <span class="label">등락률</span>
              <span class="value" :class="getChangeClass(latestData.등락률)">
                {{ formatPercent(latestData.등락률) }}
              </span>
            </div>
            <div class="summary-item">
              <span class="label">거래량</span>
              <span class="value">{{ formatVolume(latestData.거래량) }}</span>
            </div>
            <div class="summary-item">
              <span class="label">시가총액</span>
              <span class="value">{{ formatLargeNumber(latestData.시가총액) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { CandlestickController, CandlestickElement, OhlcController, OhlcElement } from 'chartjs-chart-financial'
import 'chartjs-adapter-date-fns'

Chart.register(...registerables, CandlestickController, CandlestickElement, OhlcController, OhlcElement)

const route = useRoute()
const router = useRouter()
const candlestickCanvas = ref<HTMLCanvasElement>()
const volumeCanvas = ref<HTMLCanvasElement>()

const stockName = ref(decodeURIComponent(route.params.stockName as string))
const csvData = ref<any[]>([])
const selectedPeriod = ref(90) // 기본 90일

const periods = [
  { label: '1개월', value: 30 },
  { label: '3개월', value: 90 },
  { label: '6개월', value: 180 },
  { label: '1년', value: 365 },
  { label: '전체', value: 0 }
]

const filteredData = computed(() => {
  if (selectedPeriod.value === 0) return csvData.value
  return csvData.value.slice(-selectedPeriod.value)
})

const latestData = computed(() => {
  return csvData.value.length > 0 ? csvData.value[csvData.value.length - 1] : null
})

const goBack = () => {
  router.push('/')
}

const changePeriod = (period: number) => {
  selectedPeriod.value = period
  createCharts()
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
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
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
  if (value >= 1000000000000) {
    return `${(value / 1000000000000).toFixed(1)}조`
  } else if (value >= 100000000) {
    return `${(value / 100000000).toFixed(1)}억`
  }
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

const loadCsvData = async () => {
  try {
    // URL에서 종목코드 추출
    const urlParams = new URLSearchParams(window.location.search)
    const stockCode = urlParams.get('code')
    
    if (!stockCode) {
      throw new Error('종목코드가 없습니다.')
    }
    
    // DB에서 데이터 가져오기
    const response = await fetch(`http://localhost:8000/api/collect-stock-chart/${stockCode}?days=365`)
    const chartData = await response.json()
    
    if (!chartData.candlestick || chartData.candlestick.length === 0) {
      throw new Error('차트 데이터가 없습니다.')
    }
    
    // 차트 데이터를 CSV 형식으로 변환
    const data = chartData.candlestick.map((item: any) => ({
      날짜: item.x,
      시가: item.o,
      고가: item.h,
      저가: item.l,
      종가: item.c,
      거래량: chartData.datasets[1].data[chartData.candlestick.indexOf(item)] || 0,
      등락률: 0 // 등락률은 계산해서 추가할 수 있음
    }))
    
    csvData.value = data
  } catch (error) {
    console.error('데이터 로딩 실패:', error)
    alert('데이터를 불러올 수 없습니다.')
  }
}

const createCharts = () => {
  createCandlestickChart()
  createVolumeChart()
}

const createCandlestickChart = () => {
  if (!candlestickCanvas.value || filteredData.value.length === 0) return

  const ctx = candlestickCanvas.value.getContext('2d')
  if (!ctx) return

  // 기존 차트 제거
  Chart.getChart(candlestickCanvas.value)?.destroy()

  const candlestickData = filteredData.value.map(row => ({
    x: new Date(row.날짜).getTime(),
    o: parseFloat(row.시가),
    h: parseFloat(row.고가),
    l: parseFloat(row.저가),
    c: parseFloat(row.종가)
  }))

  new Chart(ctx, {
    type: 'candlestick',
    data: {
      datasets: [{
        label: `${stockName.value} 주가`,
        data: candlestickData,
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
            displayFormats: {
              day: 'MM/dd'
            }
          },
          title: {
            display: true,
            text: '날짜'
          }
        },
        y: {
          title: {
            display: true,
            text: '주가 (원)'
          },
          ticks: {
            callback: function(value: any) {
              return new Intl.NumberFormat('ko-KR').format(value) + '원'
            }
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        title: {
          display: true,
          text: `${stockName.value} 캔들스틱 차트`
        },
        tooltip: {
          callbacks: {
            label: function(context: any) {
              const data = context.raw
              return [
                `시가: ${formatPrice(data.o)}원`,
                `고가: ${formatPrice(data.h)}원`,
                `저가: ${formatPrice(data.l)}원`,
                `종가: ${formatPrice(data.c)}원`
              ]
            }
          }
        }
      }
    }
  })
}

const createVolumeChart = () => {
  if (!volumeCanvas.value || filteredData.value.length === 0) return

  const ctx = volumeCanvas.value.getContext('2d')
  if (!ctx) return

  // 기존 차트 제거
  Chart.getChart(volumeCanvas.value)?.destroy()

  const volumeData = filteredData.value.map(row => ({
    x: new Date(row.날짜).getTime(),
    y: parseFloat(row.거래량) || 0
  }))

  new Chart(ctx, {
    type: 'bar',
    data: {
      datasets: [{
        label: '거래량',
        data: volumeData,
        backgroundColor: 'rgba(102, 126, 234, 0.6)',
        borderColor: '#667eea',
        borderWidth: 1
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
            displayFormats: {
              day: 'MM/dd'
            }
          },
          title: {
            display: true,
            text: '날짜'
          }
        },
        y: {
          title: {
            display: true,
            text: '거래량'
          },
          ticks: {
            callback: function(value: any) {
              if (value >= 1000000) {
                return `${(value / 1000000).toFixed(1)}M`
              } else if (value >= 1000) {
                return `${(value / 1000).toFixed(1)}K`
              }
              return value.toString()
            }
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        title: {
          display: true,
          text: `${stockName.value} 거래량`
        },
        tooltip: {
          callbacks: {
            label: function(context: any) {
              return `거래량: ${formatVolume(context.raw.y)}`
            }
          }
        }
      }
    }
  })
}

const goToCsvChart = (fileName: string) => {
  // 종목명_종목코드.csv 형식에서 종목명만 추출
  const stockName = fileName.replace('.csv', '').split('_')[0]
  router.push(`/csv-chart/${encodeURIComponent(stockName)}`)
}

onMounted(async () => {
  await loadCsvData()
  await nextTick()
  createCharts()
})
</script>

<style scoped>
.csv-chart {
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

/* 맨 위 기간 선택 필터 스타일 */
.period-selector-top {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.period-selector-top h3 {
  color: #333;
  font-size: 1.2rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.period-selector-top .period-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.period-selector-top .period-btn {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #e9ecef;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.period-selector-top .period-btn:hover {
  background: #e9ecef;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.period-selector-top .period-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.chart-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-section,
.volume-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.chart-section h2,
.volume-section h2 {
  color: #333;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.chart-wrapper {
  height: 400px;
  position: relative;
}

.info-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.data-summary,
.period-selector {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.data-summary h3,
.period-selector h3 {
  color: #333;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.label {
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.value {
  color: #333;
  font-weight: 600;
  font-size: 1.1rem;
}

.positive {
  color: #dc3545;
}

.negative {
  color: #007bff;
}

.neutral {
  color: #6c757d;
}

@media (max-width: 1200px) {
  .chart-container {
    grid-template-columns: 1fr;
  }
  
  .info-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .period-selector-top {
    padding: 1rem 1.5rem;
  }
  
  .period-selector-top .period-buttons {
    gap: 0.5rem;
  }
  
  .period-selector-top .period-btn {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style> 