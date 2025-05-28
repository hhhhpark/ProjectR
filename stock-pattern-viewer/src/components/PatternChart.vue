<template>
  <div class="pattern-chart">
    <div class="chart-info">
      <h4>{{ getChartTitle() }}</h4>
      <p class="pattern-dates">{{ getPatternDates() }}</p>
    </div>
    
    <div class="chart-wrapper">
      <canvas ref="chartCanvas" width="800" height="400"></canvas>
      
      <!-- 줌 리셋 버튼만 오른쪽 위에 배치 -->
      <div class="chart-controls">
        <button @click="resetZoom" class="reset-zoom-btn">줌 리셋</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'

Chart.register(...registerables, zoomPlugin)

interface Props {
  chartData: any
  pattern: string
  stock: any
}

const props = defineProps<Props>()
const chartCanvas = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null

const getChartTitle = () => {
  switch (props.pattern) {
    case 'surge': return '급등빈발 패턴 분석'
    case 'extreme': return '극심한급등 패턴 분석'
    case 'volume': return '거래량급증 패턴 분석'
    default: return '패턴 분석'
  }
}

const getPatternDates = (): string => {
  const patternDates: string[] = getPatternDatesArray()
  
  if (patternDates.length === 0) {
    return '패턴 발생 날짜 없음'
  }
  
  // 모든 날짜를 표시 (... 처리 없이)
  return `패턴 발생 날짜: ${patternDates.join(', ')} (총 ${patternDates.length}일)`
}

const getPatternDatesArray = (): string[] => {
  // 백엔드에서 받은 실제 패턴 발생 날짜 배열 사용
  const patternKey = props.pattern === 'surge' ? '급등_발생날짜' : 
                    props.pattern === 'extreme' ? '최대등락률_발생날짜' : 
                    '거래량급증_발생날짜'
  
  const patternDates = props.stock[patternKey]
  
  console.log(`패턴 키: ${patternKey}, 패턴 날짜:`, patternDates)
  
  if (Array.isArray(patternDates)) {
    // 날짜 형식 통일 (YYYY-MM-DD)
    return patternDates.map((date: string) => {
      const d = new Date(date)
      return d.toISOString().split('T')[0]
    })
  } else if (typeof patternDates === 'string' && patternDates) {
    // 단일 날짜인 경우 (극심한급등)
    const d = new Date(patternDates)
    return [d.toISOString().split('T')[0]]
  }
  
  // 백업: 기간 문자열에서 날짜 추출
  const dateString: string = props.pattern === 'surge' ? props.stock.급등빈발_기간 :
                            props.pattern === 'extreme' ? props.stock.극심한급등_기간 :
                            props.stock.거래량급증빈발_기간 || ''
  
  if (!dateString) return []
  
  const matches: RegExpMatchArray | null = dateString.match(/\d{4}-\d{2}-\d{2}/g)
  return matches || []
}

const resetZoom = () => {
  if (chartInstance) {
    chartInstance.resetZoom()
  }
}

const createChart = () => {
  if (!chartCanvas.value || !props.chartData) return

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  // 기존 차트 제거
  if (chartInstance) {
    chartInstance.destroy()
  }

  // 백엔드에서 받은 데이터 구조 처리
  const labels = props.chartData.labels || []
  const candlestickData = props.chartData.candlestick || []
  const patternDates = getPatternDatesArray()

  console.log('차트 라벨:', labels)
  console.log('패턴 날짜:', patternDates)

  // 날짜 형식 통일 (YYYY-MM-DD)
  const normalizedLabels = labels.map((label: string) => {
    const date = new Date(label)
    return date.toISOString().split('T')[0]
  })
  
  const normalizedPatternDates = patternDates.map((date: string) => {
    const d = new Date(date)
    return d.toISOString().split('T')[0]
  })

  console.log('정규화된 라벨:', normalizedLabels)
  console.log('정규화된 패턴 날짜:', normalizedPatternDates)

  // 마킹된 날짜 확인
  const markedIndices = normalizedLabels.map((label: string, index: number) => {
    const isMarked = normalizedPatternDates.includes(label)
    if (isMarked) {
      console.log(`마킹된 날짜: ${label} (인덱스: ${index})`)
    }
    return isMarked
  })
  
  console.log('마킹 결과:', markedIndices.filter(Boolean).length, '개 날짜가 마킹됨')

  if (props.pattern === 'volume') {
    // 거래량급증: 바 차트
    const volumeData = props.chartData.datasets?.find((d: any) => d.label === '거래량')?.data || []
    const backgroundColors = normalizedLabels.map((label: string) => 
      normalizedPatternDates.includes(label) ? 'rgba(255, 99, 132, 0.8)' : 'rgba(54, 162, 235, 0.5)'
    )
    const borderColors = normalizedLabels.map((label: string) => 
      normalizedPatternDates.includes(label) ? 'rgba(255, 99, 132, 1)' : 'rgba(54, 162, 235, 1)'
    )

    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: normalizedLabels,
        datasets: [{
          label: '거래량',
          data: volumeData,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: '거래량 급증 패턴'
          },
          legend: {
            display: false
          },
          zoom: {
            zoom: {
              wheel: {
                enabled: true,
              },
              pinch: {
                enabled: true
              },
              mode: 'x',
            },
            pan: {
              enabled: true,
              mode: 'x',
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: '거래량'
            }
          },
          x: {
            title: {
              display: true,
              text: '날짜'
            },
            ticks: {
              maxTicksLimit: 10
            }
          }
        }
      }
    })
  } else {
    // 급등빈발, 극심한급등: 라인 차트
    const pointBackgroundColors = normalizedLabels.map((label: string) => 
      normalizedPatternDates.includes(label) ? 'rgba(255, 99, 132, 1)' : 'rgba(54, 162, 235, 0.5)'
    )
    const pointRadius = normalizedLabels.map((label: string) => 
      normalizedPatternDates.includes(label) ? 8 : 3
    )

    let chartData, yAxisLabel
    if (props.pattern === 'surge') {
      // 급등빈발: 등락률 계산 (전일 대비)
      chartData = candlestickData.map((item: any, index: number) => {
        if (index === 0) return 0
        const prevClose = candlestickData[index - 1].c
        const currentClose = item.c
        return prevClose > 0 ? ((currentClose - prevClose) / prevClose * 100) : 0
      })
      yAxisLabel = '등락률 (%)'
    } else {
      // 극심한급등: 종가 사용
      chartData = candlestickData.map((item: any) => item.c)
      yAxisLabel = '주가'
    }

    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: normalizedLabels,
        datasets: [{
          label: yAxisLabel,
          data: chartData,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          pointBackgroundColor: pointBackgroundColors,
          pointBorderColor: pointBackgroundColors,
          pointRadius: pointRadius,
          pointHoverRadius: 10,
          tension: 0.1,
          fill: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: props.pattern === 'surge' ? '급등빈발 패턴' : '극심한급등 패턴'
          },
          legend: {
            display: false
          },
          zoom: {
            zoom: {
              wheel: {
                enabled: true,
              },
              pinch: {
                enabled: true
              },
              mode: 'x',
            },
            pan: {
              enabled: true,
              mode: 'x',
            }
          }
        },
        scales: {
          y: {
            title: {
              display: true,
              text: yAxisLabel
            }
          },
          x: {
            title: {
              display: true,
              text: '날짜'
            },
            ticks: {
              maxTicksLimit: 10
            }
          }
        }
      }
    })
  }
}

onMounted(() => {
  createChart()
})

watch(() => props.chartData, () => {
  createChart()
})
</script>

<style scoped>
.pattern-chart {
  width: 100%;
  height: 100%;
}

.chart-info {
  margin-bottom: 20px;
  text-align: center;
}

.chart-info h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1.2rem;
}

.pattern-dates {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
  background: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
  display: inline-block;
}

.chart-wrapper {
  width: 100%;
  height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

canvas {
  max-width: 100%;
  max-height: 100%;
}

.chart-controls {
  position: absolute;
  top: 0px;
  right: 5px;
  z-index: 10;
}

.reset-zoom-btn {
  padding: 4px 8px;
  font-size: 0.75rem;
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s ease;
}

.reset-zoom-btn:hover {
  background-color: #0056b3;
}
</style> 