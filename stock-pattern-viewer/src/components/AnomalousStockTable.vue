<template>
  <div class="anomalous-table-container">
    <table class="anomalous-table">
      <thead>
        <tr>
          <th>종목명</th>
          <th>이상거래 유형</th>
          <th class="clickable">급등빈발 (건수/기간)</th>
          <th class="clickable">극심한급등 (최대등락률)</th>
          <th class="clickable">거래량급증 (건수/기간)</th>
          <th>위험도점수</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in anomalousStocks" :key="row.stock_code">
          <td>{{ row.stock_name }}</td>
          <td>{{ row.manipulation_type }}</td>
          <td class="clickable" @click="showChart('급등빈발', row)">
            {{ row.급등빈발_일수 }}건 / {{ row.급등빈발_기간 || '최근 1년' }}
          </td>
          <td class="clickable" @click="showChart('극심한급등', row)">
            {{ row.극심한급등_최대등락률 ? row.극심한급등_최대등락률.toFixed(2) + '%' : 'N/A' }}
          </td>
          <td class="clickable" @click="showChart('거래량급증', row)">
            {{ row.거래량급증빈발_일수 }}건 / {{ row.거래량급증빈발_기간 || '최근 1년' }}
          </td>
          <td>{{ row.위험도점수 }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Chart Modal -->
    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeModal">&times;</span>
        <h2>{{ selectedStock.stock_name }} - {{ chartTitle }}</h2>
        <div class="pattern-info">
          <p v-if="patternDates.length > 0">
            패턴 발생 날짜: {{ patternDates.join(', ') }} (총 {{ patternDates.length }}일)
          </p>
          <p v-else>패턴 발생 날짜 정보가 없습니다.</p>
        </div>
        <div class="chart-container">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'
import zoomPlugin from 'chartjs-plugin-zoom'
import 'chartjs-adapter-date-fns'

Chart.register(zoomPlugin)

export default {
  name: 'AnomalousStockTable',
  setup() {
    const anomalousStocks = ref([])
    const showModal = ref(false)
    const selectedStock = ref(null)
    const chartTitle = ref('')
    const patternDates = ref([])
    let chart = null

    const fetchAnomalousStocks = async () => {
      try {
        console.log('Fetching anomalous stocks...')
        const response = await fetch('http://localhost:8000/api/anomalous-stocks')
        const data = await response.json()
        console.log('Received anomalous stocks data:', data)
        anomalousStocks.value = data
        console.log('Updated anomalousStocks.value:', anomalousStocks.value)
      } catch (error) {
        console.error('Error fetching anomalous stocks:', error)
      }
    }

    const showChart = async (type, stock) => {
      console.log('Selected stock:', stock)
      console.log('Selected type:', type)
      selectedStock.value = stock
      showModal.value = true
      chartTitle.value = `${type} 패턴 분석`

      try {
        console.log('Fetching stock data for:', stock.stock_code)
        const response = await fetch(`http://localhost:8000/api/collect-stock-data/${stock.stock_code}?limit=1095`)
        const rawData = await response.json()
        console.log('Raw stock data:', rawData)

        // 데이터 정렬 및 형식 변환
        const sortedData = rawData.data.sort((a, b) => new Date(a.date) - new Date(b.date))
        console.log('Sorted data:', sortedData)
        const dates = sortedData.map(item => {
          const date = new Date(item.date)
          return date
        })
        const prices = sortedData.map(item => parseFloat(item.close_price))
        const volumes = sortedData.map(item => parseFloat(item.volume))

        // 급등빈발의 경우 API에서 급등일 정보 가져오기
        let surgeDates = []
        if (type === '급등빈발') {
          try {
            console.log('Fetching surge dates for:', stock.stock_code)
            const surgeResponse = await fetch(`http://localhost:8000/api/stock-surge-dates/${stock.stock_code}`)
            const surgeData = await surgeResponse.json()
            console.log('Surge data:', surgeData)
            
            if (surgeData.surge_dates) {
              surgeDates = surgeData.surge_dates.map(item => item.date)
              console.log('Surge dates found:', surgeDates)
            }
          } catch (error) {
            console.error('Error fetching surge dates:', error)
          }
        }

        // 패턴 발생 날짜 설정
        switch (type) {
          case '급등빈발':
            // API에서 가져온 급등일 사용
            patternDates.value = surgeDates
            break
          case '극심한급등':
            patternDates.value = stock.극심한급등_기간 ? stock.극심한급등_기간.split(',').map(date => date.trim()) : []
            break
          case '거래량급증':
            patternDates.value = stock.거래량급증_기간 ? stock.거래량급증_기간.split(',').map(date => date.trim()) : []
            break
        }

        console.log('Pattern dates:', patternDates.value)

        // 패턴 발생 날짜에 해당하는 포인트 강조
        const pointBackgroundColors = dates.map(date => {
          const dateStr = date.toISOString().split('T')[0]
          const isPatternDate = patternDates.value.some(patternDate => {
            return dateStr === patternDate
          })
          return isPatternDate ? 'red' : 'rgba(75, 192, 192, 0)'
        })

        const pointRadius = dates.map(date => {
          const dateStr = date.toISOString().split('T')[0]
          const isPatternDate = patternDates.value.some(patternDate => {
            return dateStr === patternDate
          })
          return isPatternDate ? 8 : 0  // 급등일은 더 크게 표시
        })

        const pointBorderWidth = dates.map(date => {
          const dateStr = date.toISOString().split('T')[0]
          const isPatternDate = patternDates.value.some(patternDate => {
            return dateStr === patternDate
          })
          return isPatternDate ? 2 : 0
        })

        console.log('Points:', {
          dates: dates.map(d => d.toISOString().split('T')[0]),
          patternDates: patternDates.value,
          pointBackgroundColors: pointBackgroundColors.filter(c => c === 'red').length,
          pointRadius: pointRadius.filter(r => r === 8).length
        })

        // 기존 차트 제거
        if (chart) {
          chart.destroy()
        }

        // 새 차트 생성
        const ctx = document.querySelector('.chart-container canvas')
        chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: dates,
            datasets: [
              {
                label: '종가',
                data: prices,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1,
                yAxisID: 'y',
                pointBackgroundColor: pointBackgroundColors,
                pointBorderColor: 'red',
                pointBorderWidth: pointBorderWidth,
                pointRadius: pointRadius,
                pointHoverRadius: 10,
                fill: true
              },
              {
                label: '거래량',
                data: volumes,
                type: 'bar',
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgb(54, 162, 235)',
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
            plugins: {
              title: {
                display: true,
                text: `${stock.stock_name} 주가 및 거래량 추이${type === '급등빈발' ? ' (빨간 원: 급등일)' : ''}`,
                font: {
                  size: 16,
                  weight: 'bold'
                }
              },
              zoom: {
                pan: {
                  enabled: true,
                  mode: 'x',
                },
                zoom: {
                  wheel: {
                    enabled: true,
                  },
                  pinch: {
                    enabled: true
                  },
                  mode: 'x',
                },
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.dataset.label || '';
                    const value = context.parsed.y;
                    const dateStr = context.parsed.x;
                    
                    if (label === '종가') {
                      // 급등일인지 확인
                      const date = new Date(dateStr).toISOString().split('T')[0]
                      const isSurgeDate = patternDates.value.includes(date)
                      const surgeInfo = isSurgeDate ? ' 🔴 급등일' : ''
                      return `${label}: ${value.toLocaleString()}원${surgeInfo}`;
                    } else {
                      return `${label}: ${value.toLocaleString()}주`;
                    }
                  }
                }
              }
            },
            scales: {
              x: {
                type: 'time',
                time: {
                  unit: 'month',
                  displayFormats: {
                    month: 'yyyy-MM-dd'
                  }
                },
                title: {
                  display: true,
                  text: '날짜'
                }
              },
              y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                  display: true,
                  text: '주가 (원)'
                },
                ticks: {
                  callback: function(value) {
                    return value.toLocaleString() + '원';
                  }
                }
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                  display: true,
                  text: '거래량 (주)'
                },
                grid: {
                  drawOnChartArea: false,
                },
                ticks: {
                  callback: function(value) {
                    return value.toLocaleString() + '주';
                  }
                }
              }
            }
          }
        })

        console.log('Chart created with data:', {
          dates: dates.length,
          prices: prices.length,
          volumes: volumes.length,
          patternDates: patternDates.value
        })
      } catch (error) {
        console.error('Error fetching stock data:', error)
      }
    }

    const closeModal = () => {
      showModal.value = false
      if (chart) {
        chart.destroy()
        chart = null
      }
    }

    onMounted(() => {
      fetchAnomalousStocks()
    })

    return {
      anomalousStocks,
      showModal,
      selectedStock,
      chartTitle,
      patternDates,
      showChart,
      closeModal
    }
  }
}
</script>

<style scoped>
.anomalous-table-container {
  padding: 20px;
}

.anomalous-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.anomalous-table th,
.anomalous-table td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: center;
}

.anomalous-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.anomalous-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.clickable {
  cursor: pointer;
  color: #2c3e50;
}

.clickable:hover {
  background-color: #e9ecef;
  color: #1a2634;
}

/* Modal Styles */
.modal {
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
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 90%;
  max-width: 1200px;
  position: relative;
}

.close {
  position: absolute;
  right: 20px;
  top: 10px;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.close:hover {
  color: #000;
}

.chart-container {
  height: 600px;
  margin-top: 20px;
}

.pattern-info {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin: 15px 0;
  max-height: 100px;
  overflow-y: auto;
}

.pattern-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.5;
  word-break: break-all;
}

h2 {
  margin-top: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}
</style> 