<template>
  <div class="dashboard">
    <div class="container">
      <!-- 헤더 -->
      <div class="header">
        <h1>K-Stock Pattern Insight</h1>
        <p class="subtitle">실시간 주식 데이터 분석 및 패턴 감지 시스템</p>
      </div>

      <!-- 통계 카드 섹션 -->
      <div class="stats-section">
        <div class="stats-grid">
          <!-- 전체 수집 종목 카드 -->
          <div class="stats-card">
            <div class="card-content">
              <div class="card clickable" @click="toggleCsvData">
                <h3>전체 수집 종목</h3>
                <p class="count">{{ collectStocks.length }}</p>
                <span class="click-hint">최근 3년간 종목별 상세 데이터 확인</span>
              </div>
            </div>
          </div>

          <!-- 작전주 의심 리스트 -->
          <div class="stats-card">
            <div class="card-content">
              <div class="card clickable" @click="toggleSuspectData">
                <h3>작전주 리스트</h3>
                <p class="count">{{ suspectStocks.length }}</p>
                <span class="click-hint">과거 시세조종 의심 종목</span>
              </div>
            </div>
          </div>

           <!-- 이상 거래 종목 카드 -->
           <div class="stats-card">
            <div class="card-content">
              <div class="card clickable" @click="toggleAnomalousData">
                <h3>이상 거래 종목</h3>
                <p class="count">{{ anomalousStocks.length }}</p>
                <span class="click-hint">패턴 분석 결과 확인</span>
              </div>
            </div>
          </div>
          
        </div>
      </div>

      <!-- 데이터 테이블 섹션 -->
      <div v-if="showCsvData" class="data-section">
        <div class="section-header">
          <h2>📋 전체 수집 종목 ({{ collectStocks.length }}개)</h2>
          <div class="header-actions">
            <button @click="showAddStockModal = true" class="add-stock-btn">
              + 종목 추가
            </button>
            <button @click="showCsvData = false" class="close-btn">✕</button>
          </div>
        </div>
        <div class="stock-list">
          <div 
            v-for="(stock, index) in collectStocks" 
            :key="index" 
            class="stock-item clickable"
            @click="openStockDetail(stock)"
          >
            {{ stock.stock_name }}({{ stock.stock_code }})
          </div>
        </div>
      </div>

      <!-- 이상 거래 종목 테이블 -->
      <div v-if="showAnomalousData" class="data-section">
        <div class="section-header">
          <h2>⚠️ 이상 거래 종목 ({{ anomalousStocks.length }}개)</h2>
          <button @click="showAnomalousData = false" class="close-btn">✕</button>
        </div>
        <AnomalousStockTable />
      </div>

      <!-- 의심 종목 테이블 -->
      <div v-if="showSuspectData" class="data-section">
        <div class="section-header">
          <h2>🔍 의심 종목 ({{ suspectStocks.length }}개)</h2>
          <button @click="showSuspectData = false" class="close-btn">✕</button>
        </div>
        <div class="stock-list">
          <div 
            v-for="(stock, index) in suspectStocks" 
            :key="index" 
            class="stock-item clickable"
            @click="openSuspectDetail(stock)"
          >
            {{ stock.stock_name }}{{ stock.stock_code ? `(${stock.stock_code})` : '' }}
          </div>
        </div>
      </div>
    </div>

    <!-- 종목 추가 모달 -->
    <div v-if="showAddStockModal" class="modal-overlay" @click="closeAddStockModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>📈 새 종목 추가</h2>
          <button @click="closeAddStockModal" class="close-btn">✕</button>
        </div>
        
        <!-- 단계 표시기 -->
        <div class="step-indicator">
          <div class="step" :class="{ active: addStockStep >= 1, completed: addStockStep > 1 }">
            <span class="step-number">1</span>
            <span class="step-label">종목코드 입력</span>
          </div>
          <div class="step" :class="{ active: addStockStep >= 2, completed: addStockStep > 2 }">
            <span class="step-number">2</span>
            <span class="step-label">종목 확인</span>
          </div>
          <div class="step" :class="{ active: addStockStep >= 3 }">
            <span class="step-number">3</span>
            <span class="step-label">추가 진행</span>
          </div>
        </div>

        <!-- 1단계: 종목코드 입력 -->
        <div v-if="addStockStep === 1" class="modal-body">
          <div class="input-section">
            <label for="stockCode">종목코드</label>
            <div class="search-container">
              <input 
                id="stockCode"
                v-model="newStockCode" 
                type="text" 
                placeholder="예: 005930 (삼성전자)"
                @keyup.enter="lookupStockName"
                :disabled="isLoadingStockName"
              >
              <button 
                @click="lookupStockName" 
                class="search-btn"
                :disabled="!newStockCode || isLoadingStockName"
              >
                <span v-if="isLoadingStockName">🔄</span>
                <span v-else>🔍</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 2단계: 종목 확인 -->
        <div v-if="addStockStep === 2" class="modal-body">
          <div class="stock-info-card">
            <h3>종목 정보 확인</h3>
            <div class="stock-details">
              <p><strong>종목코드:</strong> {{ newStockCode }}</p>
              <p><strong>종목명:</strong> {{ newStockName }}</p>
            </div>
            <div class="button-group">
              <button @click="goBackToInput" class="back-btn">이전</button>
              <button @click="confirmAddStock" class="confirm-btn">종목추가</button>
            </div>
          </div>
        </div>

        <!-- 3단계: 추가 진행 상황 -->
        <div v-if="addStockStep === 3" class="modal-body">
          <div class="progress-section">
            <h3>종목 추가 진행 중...</h3>
            <div class="progress-list">
              <div class="progress-item" :class="{ completed: dataCollectionCompleted }">
                <div class="progress-icon">
                  <span v-if="dataCollectionCompleted">✅</span>
                  <div v-else class="spinner"></div>
                </div>
                <span>데이터 수집</span>
              </div>
              <div class="progress-item" :class="{ completed: patternAnalysisCompleted }">
                <div class="progress-icon">
                  <span v-if="patternAnalysisCompleted">✅</span>
                  <div v-else class="spinner"></div>
                </div>
                <span>패턴 분석</span>
              </div>
              <div class="progress-item" :class="{ completed: dataCollectionCompleted && patternAnalysisCompleted }">
                <div class="progress-icon">
                  <span v-if="dataCollectionCompleted && patternAnalysisCompleted">✅</span>
                  <div v-else class="spinner"></div>
                </div>
                <span>완료</span>
              </div>
            </div>
            
            <div v-if="dataCollectionCompleted && patternAnalysisCompleted" class="success-message">
              <p>✅ 종목이 성공적으로 추가되었습니다!</p>
              <button @click="closeAddStockModal" class="close-success-btn">확인</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 종목 상세 모달 -->
    <div v-if="showStockDetailModal" class="modal-overlay" @click="closeStockDetailModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h2>📊 {{ selectedStock?.stock_name }} ({{ selectedStock?.stock_code }})</h2>
          <button @click="closeStockDetailModal" class="close-btn">✕</button>
        </div>
        
        <!-- 기간 필터 -->
        <div class="filter-section">
          <label for="periodFilter">조회 기간:</label>
          <select id="periodFilter" v-model="selectedPeriod" @change="loadStockDetailData">
            <option value="30">최근 30일</option>
            <option value="90">최근 3개월</option>
            <option value="180">최근 6개월</option>
            <option value="365">최근 1년</option>
            <option value="1095">최근 3년</option>
          </select>
        </div>

        <div v-if="isLoadingStockDetail" class="loading-section">
          <div class="loading-spinner"></div>
          <p>데이터를 불러오는 중...</p>
        </div>

        <div v-else-if="stockDetailData.length > 0" class="modal-body">
          <!-- 차트 섹션 -->
          <div class="charts-section">
            <!-- 캔들스틱 차트 -->
            <div class="chart-container">
              <h3>🕯️ 캔들스틱 차트</h3>
              <div class="chart-wrapper">
                <canvas ref="candlestickCanvas" id="candlestickChart"></canvas>
              </div>
            </div>
            
            <!-- 거래량 차트 -->
            <div class="chart-container">
              <h3>📊 거래량 추이</h3>
              <div class="chart-wrapper">
                <canvas ref="volumeCanvas" id="volumeChart"></canvas>
              </div>
            </div>
          </div>

          <!-- 데이터 테이블 -->
          <div class="table-section">
            <h3>📋 상세 데이터 ({{ stockDetailData.length }}개)</h3>
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
                  <tr v-for="(row, index) in stockDetailData.slice(0, 50)" :key="index" class="table-row">
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
        </div>

        <div v-else class="error-section">
          <h3>⚠️ 데이터를 불러올 수 없습니다</h3>
          <p>종목코드: {{ selectedStock?.stock_code }}</p>
          <button @click="loadStockDetailData" class="retry-button">다시 시도</button>
        </div>
      </div>
    </div>

    <!-- 의심 종목 상세 모달 -->
    <div v-if="showSuspectDetailModal" class="modal-overlay" @click="closeSuspectDetailModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h2>🔍 의심 종목 상세 정보 - {{ selectedSuspectStock?.stock_name }} ({{ selectedSuspectStock?.stock_code }})</h2>
          <button @click="closeSuspectDetailModal" class="close-btn">✕</button>
        </div>
        
        <div class="modal-body">
          <!-- 상세 정보 테이블 -->
          <div class="suspect-detail-table">
            <h3>📋 상세 정보</h3>
            <table class="info-table">
              <tbody>
                <tr>
                  <td class="info-label">의심 기간</td>
                  <td class="info-value">{{ selectedSuspectStock?.suspected_period }}</td>
                </tr>
                <tr>
                  <td class="info-label">테마/이유</td>
                  <td class="info-value">{{ selectedSuspectStock?.theme_reason }}</td>
                </tr>
                <tr>
                  <td class="info-label">활동 기간</td>
                  <td class="info-value">{{ selectedSuspectStock?.active_duration }}</td>
                </tr>
                <tr>
                  <td class="info-label">매수 패턴</td>
                  <td class="info-value">{{ selectedSuspectStock?.buy_side_pattern }}</td>
                </tr>
                <tr>
                  <td class="info-label">3년 전 가격</td>
                  <td class="info-value">{{ formatPrice(selectedSuspectStock?.price_3y_ago) }}원</td>
                </tr>
                <tr>
                  <td class="info-label">최고가</td>
                  <td class="info-value peak">{{ formatPrice(selectedSuspectStock?.price_peak) }}원</td>
                </tr>
                <tr>
                  <td class="info-label">현재가</td>
                  <td class="info-value">{{ formatPrice(selectedSuspectStock?.price_current) }}원</td>
                </tr>
                <tr>
                  <td class="info-label">최고 수익률</td>
                  <td class="info-value" :class="selectedSuspectStock?.peak_return >= 0 ? 'positive' : 'negative'">
                    {{ selectedSuspectStock?.peak_return }}%
                  </td>
                </tr>
                <tr>
                  <td class="info-label">현재 수익률</td>
                  <td class="info-value" :class="selectedSuspectStock?.current_return >= 0 ? 'positive' : 'negative'">
                    {{ selectedSuspectStock?.current_return }}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 차트 섹션 -->
          <div class="chart-section">
            <h3>📈 주가 및 거래량 추이</h3>
            <div v-if="isLoadingSuspectDetail" class="loading-section">
              <div class="loading-spinner"></div>
              <p>차트 데이터를 불러오는 중...</p>
            </div>
            <div v-else class="chart-container">
              <canvas ref="suspectCombinedCanvas" id="suspectCombinedChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { CandlestickController, CandlestickElement, OhlcController, OhlcElement } from 'chartjs-chart-financial'
import 'chartjs-adapter-date-fns'
import { useRouter } from 'vue-router'
import AnomalousStockTable from '@/components/AnomalousStockTable.vue'

Chart.register(...registerables, CandlestickController, CandlestickElement, OhlcController, OhlcElement)

// 기본 상태 변수들
const collectStocks = ref<any[]>([])
const anomalousStocks = ref<any[]>([])
const suspectStocks = ref<any[]>([])

const showCsvData = ref(false)
const showAnomalousData = ref(false)
const showSuspectData = ref(false)

// 종목 추가 모달 관련 변수들
const showAddStockModal = ref(false)
const newStockCode = ref('')
const newStockName = ref('')
const isLoadingStockName = ref(false)
const addStockStep = ref(1)
const addStockProgress = ref(0)
const showConfirmation = ref(false)
const dataCollectionCompleted = ref(false)
const patternAnalysisCompleted = ref(false)

// 종목 상세 모달 관련 변수들
const showStockDetailModal = ref(false)
const selectedStock = ref<any>(null)
const stockDetailData = ref<any[]>([])
const isLoadingStockDetail = ref(false)
const selectedPeriod = ref('365')
const candlestickCanvas = ref<HTMLCanvasElement>()
const volumeCanvas = ref<HTMLCanvasElement>()

// 의심 종목 상세 모달 관련 변수들
const showSuspectDetailModal = ref(false)
const selectedSuspectStock = ref<any>(null)
const suspectDetailData = ref<any[]>([])
const isLoadingSuspectDetail = ref(false)
const suspectCombinedCanvas = ref<HTMLCanvasElement>()

// 차트 인스턴스들
let candlestickChart: Chart | null = null
let volumeChart: Chart | null = null
let suspectCombinedChart: Chart | null = null

// 데이터 토글 함수들
const toggleCsvData = () => {
  showCsvData.value = !showCsvData.value
  showAnomalousData.value = false
  showSuspectData.value = false
  if (showCsvData.value && collectStocks.value.length === 0) {
    fetchCollectStocks()
  }
}

const toggleAnomalousData = () => {
  showAnomalousData.value = !showAnomalousData.value
  showCsvData.value = false
  showSuspectData.value = false
  if (showAnomalousData.value && anomalousStocks.value.length === 0) {
    fetchAnomalousStocks()
  }
}

const toggleSuspectData = () => {
  showSuspectData.value = !showSuspectData.value
  showCsvData.value = false
  showAnomalousData.value = false
  if (showSuspectData.value && suspectStocks.value.length === 0) {
    fetchSuspectStocks()
  }
}

// 데이터 가져오기 함수들
const fetchCollectStocks = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/collect-stocks')
    collectStocks.value = await response.json()
  } catch (error) {
    console.error('수집 종목 데이터 로딩 실패:', error)
  }
}

const fetchAnomalousStocks = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/anomalous-stocks')
    anomalousStocks.value = await response.json()
  } catch (error) {
    console.error('이상 거래 종목 데이터 로딩 실패:', error)
  }
}

const fetchSuspectStocks = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/suspect-stocks')
    const data = await response.json()
    suspectStocks.value = data
    console.log('의심 종목 데이터:', data) // 디버깅용
  } catch (error) {
    console.error('의심 종목 데이터 로딩 실패:', error)
  }
}

// 종목 상세 모달 관련 함수들
const openStockDetail = (stock: any) => {
  console.log('선택된 종목:', stock) // 디버깅용
  selectedStock.value = stock
  showStockDetailModal.value = true
  loadStockDetailData()
}

const closeStockDetailModal = () => {
  showStockDetailModal.value = false
  selectedStock.value = null
  stockDetailData.value = []
  destroyCharts()
}

const loadStockDetailData = async () => {
  if (!selectedStock.value?.stock_code) {
    console.error('종목코드가 없습니다:', selectedStock.value)
    return
  }
  
  console.log('종목 상세 데이터 로딩 시작:', selectedStock.value.stock_code, '기간:', selectedPeriod.value)
  isLoadingStockDetail.value = true
  stockDetailData.value = []
  
  try {
    const url = `http://localhost:8000/api/collect-stock-data/${selectedStock.value.stock_code}?limit=${selectedPeriod.value}`
    console.log('API 호출 URL:', url)
    
    const response = await fetch(url)
    console.log('API 응답 상태:', response.status)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('API 응답 데이터:', data)
    
    // 새로운 API 응답 형식 처리
    if (data.error) {
      throw new Error(data.error)
    }
    
    if (data.message && (!data.data || data.data.length === 0)) {
      console.warn('데이터 없음:', data.message)
      alert(data.message)
      return
    }
    
    // API 응답 구조 변경에 따른 처리
    let allData = data.data || data || []
    stockDetailData.value = allData
    console.log('설정된 stockDetailData 길이:', stockDetailData.value.length)
    
    if (stockDetailData.value.length > 0) {
      console.log('데이터 샘플:', stockDetailData.value.slice(0, 3))
      
      // DOM이 업데이트될 때까지 기다림
      await nextTick()
      console.log('nextTick 완료, 차트 생성 시작')
      
      // 추가 지연을 통해 DOM이 완전히 렌더링되도록 함
      setTimeout(() => {
        console.log('차트 생성 함수 호출')
        createCharts()
      }, 500)
    } else {
      console.warn('데이터가 없습니다')
    }
  } catch (error) {
    console.error('종목 상세 데이터 로딩 실패:', error)
    if (error instanceof Error) {
      console.error(error.message); // ✅ 안전하게 타입 확인 후 사용
      alert('데이터를 불러오는 중 오류가 발생했습니다: ' + error.message)
    } else {
      console.error("Unknown error", error);
      alert('데이터를 불러오는 중 알 수 없는 오류가 발생했습니다.')
    }
  } finally {
    isLoadingStockDetail.value = false
    console.log('로딩 상태 해제')
  }
}

// 차트 생성 및 제거 함수들
const createCharts = () => {
  try {
    console.log('차트 생성 시작, 데이터 길이:', stockDetailData.value.length)
    if (stockDetailData.value.length === 0) {
      console.log('데이터가 없어서 차트 생성 중단')
      return
    }
    
    destroyCharts()
    
    // DOM 요소가 준비될 때까지 기다림
    nextTick(() => {
      setTimeout(() => {
        console.log('캔들스틱 차트 생성 시도')
        createCandlestickChart()
        console.log('거래량 차트 생성 시도')
        createVolumeChart()
      }, 100)
    })
  } catch (error) {
    console.error('차트 생성 실패:', error)
  }
}

const destroyCharts = () => {
  try {
    if (candlestickChart) {
      candlestickChart.destroy()
      candlestickChart = null
      console.log('캔들스틱 차트 제거됨')
    }
    
    if (volumeChart) {
      volumeChart.destroy()
      volumeChart = null
      console.log('거래량 차트 제거됨')
    }
  } catch (error) {
    console.error('차트 제거 실패:', error)
  }
}

const createCandlestickChart = () => {
  console.log('캔들스틱 차트 생성 함수 시작')
  console.log('Canvas 요소:', candlestickCanvas.value)
  console.log('데이터 길이:', stockDetailData.value.length)
  
  if (!candlestickCanvas.value) {
    console.error('캔들스틱 캔버스 요소를 찾을 수 없음')
    return
  }
  
  if (stockDetailData.value.length === 0) {
    console.error('차트 데이터가 없음')
    return
  }
  
  const ctx = candlestickCanvas.value.getContext('2d')
  if (!ctx) {
    console.error('캔버스 컨텍스트를 가져올 수 없음')
    return
  }
  
  // 데이터 준비
  const chartData = stockDetailData.value.slice(-90).reverse().map((row, index) => {
    const dataPoint = {
      x: new Date(row.date).getTime(),
      o: parseFloat(row.open_price) || 0,
      h: parseFloat(row.high_price) || 0,
      l: parseFloat(row.low_price) || 0,
      c: parseFloat(row.close_price) || 0
    }
    if (index < 5) console.log('차트 데이터 샘플:', dataPoint)
    return dataPoint
  })
  
  console.log('차트 데이터 준비 완료, 길이:', chartData.length)
  
  try {
    candlestickChart = new Chart(ctx, {
      type: 'candlestick',
      data: {
        datasets: [{
          label: `${selectedStock.value?.stock_name || ''} 주가`,
          data: chartData,
          borderColor: '#26a69a',
          backgroundColor: 'rgba(38, 166, 154, 0.8)'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              displayFormats: { day: 'MM/dd' }
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
            }
          }
        }
      }
    })
    console.log('캔들스틱 차트 생성 완료')
  } catch (error) {
    console.error('캔들스틱 차트 생성 중 오류:', error)
  }
}

const createVolumeChart = () => {
  console.log('거래량 차트 생성 함수 시작')
  console.log('Canvas 요소:', volumeCanvas.value)
  
  if (!volumeCanvas.value) {
    console.error('거래량 캔버스 요소를 찾을 수 없음')
    return
  }
  
  if (stockDetailData.value.length === 0) {
    console.error('차트 데이터가 없음')
    return
  }
  
  const ctx = volumeCanvas.value.getContext('2d')
  if (!ctx) {
    console.error('캔버스 컨텍스트를 가져올 수 없음')
    return
  }
  
  const chartData = stockDetailData.value.slice(-90).reverse()
  console.log('거래량 차트 데이터 준비 완료, 길이:', chartData.length)
  
  try {
    volumeChart = new Chart(ctx, {
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
        plugins: {
          legend: {
            display: true
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: '날짜'
            }
          },
          y: {
            title: { 
              display: true, 
              text: '거래량' 
            }
          }
        }
      }
    })
    console.log('거래량 차트 생성 완료')
  } catch (error) {
    console.error('거래량 차트 생성 중 오류:', error)
  }
}

// 종목 추가 모달 관련 함수들
const closeAddStockModal = () => {
  showAddStockModal.value = false
  newStockCode.value = ''
  newStockName.value = ''
  addStockStep.value = 1
  addStockProgress.value = 0
  showConfirmation.value = false
  dataCollectionCompleted.value = false
  patternAnalysisCompleted.value = false
}

const lookupStockName = async () => {
  if (!newStockCode.value || newStockCode.value.length !== 6) {
    alert('6자리 종목코드를 입력해주세요.')
    return
  }

  try {
    isLoadingStockName.value = true
    
    const response = await fetch(`http://localhost:8000/api/stock-name/${newStockCode.value}`)
    
    if (response.ok) {
      const data = await response.json()
      newStockName.value = data.stock_name
      addStockStep.value = 2
    } else {
      alert('종목을 찾을 수 없습니다. 종목코드를 확인해주세요.')
    }
  } catch (error) {
    console.error('종목명 조회 오류:', error)
    alert('종목명 조회 중 오류가 발생했습니다.')
  } finally {
    isLoadingStockName.value = false
  }
}

const confirmAddStock = async () => {
  try {
    addStockStep.value = 3
    dataCollectionCompleted.value = false
    patternAnalysisCompleted.value = false
    
    const response = await fetch('http://localhost:8000/api/add-stock', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        stock_code: newStockCode.value,
        stock_name: newStockName.value
      })
    })

    if (response.ok) {
      // 진행 상황 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1500))
      dataCollectionCompleted.value = true
      
      await new Promise(resolve => setTimeout(resolve, 1500))
      patternAnalysisCompleted.value = true
      
      // 데이터 새로고침
      if (showCsvData.value) {
        await fetchCollectStocks()
      }
    } else {
      const errorData = await response.json()
      alert(errorData.detail || '종목 추가에 실패했습니다.')
    }
  } catch (error) {
    console.error('종목 추가 오류:', error)
    alert('종목 추가 중 오류가 발생했습니다.')
  }
}

const goBackToInput = () => {
  addStockStep.value = 1
  showConfirmation.value = false
  newStockName.value = ''
}

// 포맷팅 함수들
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const formatPrice = (price: number) => {
  if (!price) return '-'
  return price.toLocaleString()
}

const formatVolume = (volume: number) => {
  if (!volume) return '-'
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`
  }
  return volume.toLocaleString()
}

const formatPercent = (percent: number) => {
  if (percent === null || percent === undefined) return '-'
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const formatLargeNumber = (num: number) => {
  if (!num) return '-'
  if (num >= 1000000000000) {
    return `${(num / 1000000000000).toFixed(1)}조`
  } else if (num >= 100000000) {
    return `${(num / 100000000).toFixed(1)}억`
  } else if (num >= 10000) {
    return `${(num / 10000).toFixed(1)}만`
  }
  return num.toLocaleString()
}

const getChangeClass = (changeRate: number) => {
  if (!changeRate) return ''
  if (changeRate > 0) return 'positive'
  if (changeRate < 0) return 'negative'
  return ''
}

// 의심 종목 상세 모달 관련 함수들
const openSuspectDetail = (stock: any) => {
  console.log('선택된 의심 종목:', stock) // 디버깅용
  selectedSuspectStock.value = stock
  showSuspectDetailModal.value = true
  loadSuspectDetailData()
}

const closeSuspectDetailModal = () => {
  showSuspectDetailModal.value = false
  selectedSuspectStock.value = null
  suspectDetailData.value = []
  destroySuspectChart()
}

const loadSuspectDetailData = async () => {
  if (!selectedSuspectStock.value?.stock_code) {
    console.error('종목코드 없음:', selectedSuspectStock.value)
    return
  }
  
  console.log('의심 종목 데이터 로딩 시작:', selectedSuspectStock.value.stock_code)
  isLoadingSuspectDetail.value = true
  suspectDetailData.value = []
  
  try {
    // 의심 기간 파싱
    const suspectedPeriod = selectedSuspectStock.value.suspected_period
    console.log('의심 기간:', suspectedPeriod)
    
    let startDate, endDate
    
    // 의심 기간에서 날짜 추출 (예: "2023~2024", "2024.2~2025.5", "2023.10~2023.11")
    if (suspectedPeriod) {
      const periodMatch = suspectedPeriod.match(/(\d{4})(?:\.(\d{1,2}))?[~-](\d{4})(?:\.(\d{1,2}))?/)
      if (periodMatch) {
        const [, startYear, startMonth, endYear, endMonth] = periodMatch
        
        // 시작일: 의심 기간 시작 6개월 전
        const suspectStart = new Date(parseInt(startYear), (parseInt(startMonth) || 1) - 1, 1)
        startDate = new Date(suspectStart)
        startDate.setMonth(startDate.getMonth() - 6)
        
        // 종료일: 의심 기간 끝 6개월 후
        const suspectEnd = new Date(parseInt(endYear), (parseInt(endMonth) || 12) - 1, 1)
        endDate = new Date(suspectEnd)
        endDate.setMonth(endDate.getMonth() + 6)
        
        console.log('계산된 기간:', {
          suspectStart: suspectStart.toISOString().split('T')[0],
          suspectEnd: suspectEnd.toISOString().split('T')[0],
          chartStart: startDate.toISOString().split('T')[0],
          chartEnd: endDate.toISOString().split('T')[0]
        })
      }
    }
    
    // 기본값: 최근 2년
    if (!startDate || !endDate) {
      endDate = new Date()
      startDate = new Date()
      startDate.setFullYear(startDate.getFullYear() - 2)
    }
    
    const response = await fetch(`http://localhost:8000/api/collect-stock-data/${selectedSuspectStock.value.stock_code}?limit=1095`)
    console.log('API 응답 상태:', response.status)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('받은 데이터:', data)
    
    // 새로운 API 응답 형식 처리
    if (data.error) {
      throw new Error(data.error)
    }
    
    if (data.message && (!data.data || data.data.length === 0)) {
      console.warn('데이터 없음:', data.message)
      alert(data.message)
      return
    }
    
    // API 응답 구조 변경에 따른 처리
    let allData = data.data || data || []
    
    // 날짜 범위로 필터링
    if (startDate && endDate) {
      allData = allData.filter((row: any) => {
        const rowDate = new Date(row.date)
        return rowDate >= startDate && rowDate <= endDate
      })
    }
    
    suspectDetailData.value = allData
    console.log('필터링된 데이터 길이:', suspectDetailData.value.length)
    
    if (suspectDetailData.value.length > 0) {
      await nextTick()
      console.log('nextTick 후 차트 생성 시작')
      setTimeout(() => {
        createSuspectCombinedChart()
      }, 100)
    } else {
      console.log('데이터가 없음')
    }
  } catch (error) {
    console.error('의심 종목 상세 데이터 로딩 실패:', error)
    if (error instanceof Error) {
      console.error(error.message); // ✅ 안전하게 타입 확인 후 사용
      alert('데이터를 불러오는 중 오류가 발생했습니다: ' + error.message)
    } else {
      console.error("Unknown error", error);
      alert('데이터를 불러오는 중 알 수 없는 오류가 발생했습니다.')
    }
  } finally {
    isLoadingSuspectDetail.value = false
  }
}

const destroySuspectChart = () => {
  try {
    if (suspectCombinedChart) {
      suspectCombinedChart.destroy()
      suspectCombinedChart = null
    }
  } catch (error) {
    console.error('의심 종목 차트 제거 실패:', error)
  }
}

const createSuspectCombinedChart = () => {
  console.log('차트 생성 시작:', {
    canvas: !!suspectCombinedCanvas.value,
    dataLength: suspectDetailData.value.length,
    stockCode: selectedSuspectStock.value?.stock_code
  })
  
  if (!suspectCombinedCanvas.value || suspectDetailData.value.length === 0) {
    console.log('차트 생성 조건 불충족')
    return
  }
  
  const ctx = suspectCombinedCanvas.value.getContext('2d')
  if (!ctx) {
    console.log('Canvas context 없음')
    return
  }
  
  destroySuspectChart()
  
  // 데이터 정렬 (날짜 순)
  const sortedData = suspectDetailData.value.slice().sort((a: any, b: any) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  )
  
  console.log('정렬된 데이터 샘플:', {
    first: sortedData[0]?.date,
    last: sortedData[sortedData.length - 1]?.date,
    length: sortedData.length
  })
  
  const labels = sortedData.map((row: any) => row.date)
  const priceData = sortedData.map((row: any) => parseFloat(row.close_price) || 0)
  const volumeData = sortedData.map((row: any) => parseFloat(row.volume) || 0)
  
  try {
    suspectCombinedChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: `${selectedSuspectStock.value?.stock_name || ''} 종가`,
            type: 'line',
            data: priceData,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderWidth: 2,
            fill: false,
            yAxisID: 'y',
            tension: 0.1,
            pointRadius: 1,
            pointHoverRadius: 4
          },
          {
            label: '거래량',
            type: 'bar',
            data: volumeData,
            backgroundColor: 'rgba(34, 197, 94, 0.3)',
            borderColor: '#22c55e',
            borderWidth: 1,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        scales: {
          x: {
            title: {
              display: true,
              text: '날짜'
            },
            ticks: {
              maxTicksLimit: 10
            }
          },
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
              text: '거래량'
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
          tooltip: {
            mode: 'index',
            intersect: false,
          }
        }
      }
    })
    
    console.log('차트 생성 완료')
  } catch (error) {
    console.error('차트 생성 중 오류:', error)
  }
}

// 컴포넌트 마운트 시 데이터 로딩
onMounted(async () => {
  await Promise.all([
    fetchCollectStocks(),
    fetchAnomalousStocks(),
    fetchSuspectStocks()
  ])
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.container {
  max-width: 1800px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
}

.header h1 {
  color: white;
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.2rem;
}

.stats-section {
  margin-bottom: 3rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stats-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-5px);
}

.card {
  text-align: center;
  cursor: pointer;
}

.card h3 {
  color: #6c757d;
  font-size: 1rem;
  margin-bottom: 1rem;
  font-weight: 500;
}

.count {
  color: #333;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.click-hint {
  color: #667eea;
  font-size: 0.85rem;
  font-weight: 500;
}

.data-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
}

.section-header h2 {
  color: #333;
  font-size: 1.5rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.add-stock-btn {
  background: transparent;
  color: #6c757d;
  border: 1px solid #e9ecef;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.add-stock-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.close-btn {
  background: transparent;
  color: #6c757d;
  border: 1px solid #e9ecef;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f8f9fa;
  color: #495057;
  border-color: #dee2e6;
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
  padding: 1rem;
  text-align: left;
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

.table-row:hover {
  background: #f8f9fa;
}

.detail-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.2s ease;
}

.detail-btn:hover {
  background: #5a6fd8;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-content.large {
  max-width: 1200px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.modal-body {
  padding: 2rem;
  max-height: 70vh;
  overflow-y: auto;
}

.step-indicator {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
  gap: 2rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s ease;
}

.step.active .step-number {
  background: #667eea;
  color: white;
}

.step.completed .step-number {
  background: #28a745;
  color: white;
}

.step-label {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

.input-section {
  margin-bottom: 1.5rem;
}

.input-section label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.search-container {
  display: flex;
  gap: 0.5rem;
}

.search-container input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 1rem;
}

.search-btn {
  background: #ffd93d;
  color: #333;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.2s ease;
}

.search-btn:hover {
  background: #ffcd02;
}

.search-btn:disabled {
  background: #e9ecef;
  cursor: not-allowed;
}

.stock-info-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.stock-info-card h3 {
  color: #333;
  margin-bottom: 1rem;
}

.stock-details {
  margin-bottom: 1.5rem;
}

.stock-details p {
  margin: 0.5rem 0;
  color: #666;
}

.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.back-btn {
  background: linear-gradient(135deg, #ffd93d 0%, #ff8c42 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s ease;
  width: 100px;
}

.back-btn:hover {
  transform: translateY(-2px);
}

.confirm-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s ease;
  width: 100px;
}

.confirm-btn:hover {
  transform: translateY(-2px);
}

.progress-section {
  text-align: center;
}

.progress-section h3 {
  color: #333;
  margin-bottom: 2rem;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.progress-item.completed {
  background: #d4edda;
  border: 1px solid #c3e6cb;
}

.progress-icon {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.success-message {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.success-message p {
  color: #155724;
  margin-bottom: 1rem;
  font-weight: 600;
}

.close-success-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.filter-section {
  padding: 1rem 2rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.filter-section label {
  margin-right: 1rem;
  font-weight: 600;
  color: #333;
}

.filter-section select {
  padding: 0.5rem;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  font-size: 0.9rem;
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.5rem;
  min-height: 400px;
}

.chart-container h3 {
  color: #333;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.chart-wrapper {
  height: 300px;
  width: 100%;
  position: relative;
  display: block;
}

.chart-wrapper canvas {
  width: 100% !important;
  height: 100% !important;
  display: block;
}

.table-section {
  margin-top: 2rem;
}

.table-section h3 {
  color: #333;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.error-section {
  text-align: center;
  padding: 3rem;
}

.error-section h3 {
  color: #dc3545;
  margin-bottom: 1rem;
}

.retry-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 1rem;
}

.positive {
  color: #dc3545;
  font-weight: 600;
}

.negative {
  color: #007bff;
  font-weight: 600;
}

.stock-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.stock-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s ease;
  font-weight: 500;
  color: #333;
}

.stock-item:hover {
  background: #e3f2fd;
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.stock-item.clickable {
  cursor: pointer;
}

.suspect-detail-table {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.suspect-detail-table h3 {
  color: #333;
  margin-bottom: 1rem;
  text-align: center;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-table td {
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.info-table tr:last-child td {
  border-bottom: none;
}

.info-table .info-label {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
  width: 30%;
  text-align: center;
}

.info-table .info-value {
  color: #333;
  font-weight: 500;
  text-align: center;
}

.info-table .info-value.peak {
  color: #ff6b35;
  font-weight: 700;
}

.info-table .info-value.positive {
  color: #28a745;
  font-weight: 700;
}

.info-table .info-value.negative {
  color: #dc3545;
  font-weight: 700;
}

.chart-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.chart-section h3 {
  color: #333;
  margin-bottom: 1rem;
  text-align: center;
}

.chart-section .chart-container {
  background: white;
  border-radius: 6px;
  padding: 1rem;
  height: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-section .chart-container canvas {
  width: 100% !important;
  height: 100% !important;
}

@media (max-width: 768px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}
</style> 