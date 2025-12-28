import { ref, computed, watch } from 'vue'
import type { ChartOption } from '@/types'
import * as echarts from 'echarts'

export function useCharts() {
  // 图表颜色
  const chartColors = [
    '#3498db',
    '#2ecc71',
    '#e74c3c',
    '#f39c12',
    '#9b59b6',
    '#1abc9c',
    '#d35400',
    '#34495e',
    '#16a085',
    '#c0392b',
    '#8e44ad',
    '#27ae60',
    '#2980b9',
    '#f1c40f',
    '#e67e22',
  ]

  // 根据图表类型和配置生成图表选项
  const generateChartOption = (data: any[], chartType: string, config: ChartOption = {}) => {
    console.log('获取的数据是', data)
    switch (chartType) {
      case 'bar_chart':
        return generateBarChartOption(data, config)
      case 'line_chart':
        return generateLineChartOption(data, config)
      case 'pie_chart':
        return generatePieChartOption(data, config)
      case 'scatter_chart':
        return generateScatterChartOption(data, config)
      case 'area_chart':
        return generateAreaChartOption(data, config)
      default:
        return {}
    }
  }

  // 柱状图配置
  const generateBarChartOption = (data: any[], config: ChartOption) => {
    const xAxis = config.x_axis || getDefaultXAxis(data)
    const yAxis = config.y_axis || getDefaultYAxis(data)
    const title = config.title || `${yAxis} 按 ${xAxis} 统计`

    // 提取数据
    const xData = data.map((item) => {
      const value = item[xAxis]
      return value !== null && value !== undefined ? String(value) : '未知'
    })

    const yData = data.map((item) => {
      const value = item[yAxis]
      return convertToNumber(value)
    })

    // 排序
    if (config.sorted) {
      const combined = xData.map((x, i) => ({ x, y: yData[i] }))
      combined.sort((a, b) => {
        if (config.sortOrder === 'asc') {
          return a.y - b.y
        } else {
          return b.y - a.y
        }
      })

      xData.length = 0
      yData.length = 0
      combined.forEach((item) => {
        xData.push(item.x)
        yData.push(item.y)
      })
    }

    // 限制数据数量
    if (config.limit && xData.length > config.limit) {
      xData.splice(config.limit)
      yData.splice(config.limit)
    }

    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          color: '#2c3e50',
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const param = params[0]
          return `${param.name}<br/>${yAxis}: <b>${param.value}</b>`
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          rotate: xData.length > 8 ? 45 : 0,
          interval: 0,
          fontSize: 12,
        },
      },
      yAxis: {
        type: 'value',
        name: yAxis,
        axisLabel: {
          formatter: (value: number) => formatNumber(value),
        },
      },
      series: [
        {
          name: yAxis,
          type: 'bar',
          data: yData,
          itemStyle: {
            color:
              config.color ||
              new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#3498db' },
                { offset: 0.5, color: '#2980b9' },
                { offset: 1, color: '#1f618d' },
              ]),
            borderRadius: [4, 4, 0, 0],
          },
          barWidth: Math.max(20, Math.min(50, 400 / xData.length)),
          label: {
            show: config.showValues || xData.length <= 15,
            position: 'top',
            formatter: (params: any) => formatNumber(params.value),
          },
          emphasis: {
            itemStyle: {
              shadowColor: 'rgba(0, 0, 0, 0.5)',
              shadowBlur: 10,
            },
          },
        },
      ],
    }
  }

  // 折线图配置
  const generateLineChartOption = (data: any[], config: ChartOption) => {
    const xField = config.x_axis || getDefaultXAxis(data) // 改为 xField 表示X轴字段名
    const yField = config.y_axis || getDefaultYAxis(data) // 改为 yField 表示Y轴字段名
    const title = config.title || `${yField} 趋势图`

    // 提取数据 - 使用正确的字段名
    const xData = data.map((item) => {
      const value = item[xField] // 使用 xField 作为键
      return value !== null && value !== undefined ? String(value) : '未知'
    })

    const yData = data.map((item) => {
      const value = item[yField] // 使用 yField 作为键
      return convertToNumber(value)
    })

    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          color: '#2c3e50',
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'line' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: xData,
        boundaryGap: false,
        axisLabel: {
          rotate: xData.length > 8 ? 45 : 0,
          interval: 0,
          fontSize: 12,
        },
      },
      yAxis: {
        type: 'value',
        name: yField, // 使用 yField 作为Y轴名称
        axisLabel: {
          formatter: (value: number) => formatNumber(value),
        },
      },
      series: [
        {
          name: yField, // 使用 yField 作为系列名称
          type: 'line',
          data: yData,
          smooth: true,
          lineStyle: {
            width: 3,
            color: config.color || '#ff4d4f',
          },
          itemStyle: {
            color: config.color || '#ff4d4f',
          },
          symbol: 'circle',
          symbolSize: 8,
          emphasis: {
            focus: 'series',
          },
        },
      ],
    }
  }

  // 饼图配置
  const generatePieChartOption = (data: any[], config: ChartOption) => {
    const nameCol = config.name_col || getDefaultXAxis(data)
    const valueCol = config.value_col || getDefaultYAxis(data)
    const title = config.title || `${nameCol} 分布`

    console.log('data', data)
    console.log('config', config)

    // 提取饼图数据
    const pieData = data
      .map((item) => {
        const name = String(item[nameCol] || '未知')
        const value = convertToNumber(item[valueCol])
        return { name, value }
      })
      .filter((item) => item.value > 0)

    if (pieData.length === 0) {
      throw new Error('没有有效数据用于饼图')
    }

    // 排序
    if (config.sorted) {
      pieData.sort((a, b) => {
        if (config.sortOrder === 'asc') {
          return a.value - b.value
        } else {
          return b.value - a.value
        }
      })
    }

    // 限制数量
    if (config.limit && pieData.length > config.limit) {
      pieData.splice(config.limit)
    }

    // 简单图例配置
    const showLegend = config.showLegend !== false
    const dataCount = pieData.length

    const legendConfig = {
      show: showLegend,
      data: pieData.map((item) => item.name),
    }

    // 根据数据量调整布局
    if (dataCount <= 5) {
      Object.assign(legendConfig, {
        orient: 'vertical',
        left: 'left',
        top: 'middle',
      })
    } else if (dataCount <= 10) {
      Object.assign(legendConfig, {
        orient: 'horizontal',
        left: 'center',
        top: 'top',
      })
    } else {
      Object.assign(legendConfig, {
        type: 'scroll',
        orient: 'horizontal',
        left: 'center',
        top: 'top',
      })
    }

    // 简单标签配置
    const showLabel = config.showValues !== false
    let labelConfig = {
      show: showLabel,
      position: 'outside',
      formatter: '{b}: {d}%',
    }

    if (dataCount > 8) {
      Object.assign(labelConfig, {
        position: 'inside',
        formatter: '{d}%',
        color: '#fff',
      })
    }

    // 返回完整配置
    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          color: '#2c3e50',
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const { name, value, percent } = params
          return `${name}<br/>数值: ${formatNumber(value)}<br/>占比: ${percent}%`
        },
      },
      legend: legendConfig,
      series: [
        {
          name: title,
          type: 'pie',
          radius: '70%',
          center: ['50%', '55%'],
          data: pieData,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: labelConfig,
          labelLine: {
            show: dataCount <= 8,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '14',
              fontWeight: 'bold',
            },
            scale: true,
            scaleSize: 8,
          },
        },
      ],
    }
  }

  // 散点图配置
  const generateScatterChartOption = (data: any[], config: ChartOption) => {
    const xAxis = config.x_axis || getDefaultXAxis(data)
    const yAxis = config.y_axis || getDefaultYAxis(data)
    const title = config.title || `${yAxis} 与 ${xAxis} 关系`

    // 提取数据
    const scatterData = data.map((item) => ({
      name: item.name || '',
      value: [convertToNumber(item[xAxis]), convertToNumber(item[yAxis])],
    }))

    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          color: '#2c3e50',
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const point = params.value
          const name = params.name || ''
          const nameText = name ? `分类: ${name}<br/>` : ''
          return `${nameText}${xAxis}: ${point[0]}<br/>${yAxis}: ${point[1]}`
        },
      },
      grid: {
        left: '3%',
        right: '7%',
        bottom: '10%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'value',
        name: xAxis,
        scale: true,
        axisLabel: {
          formatter: (value: number) => formatNumber(value),
        },
      },
      yAxis: {
        type: 'value',
        name: yAxis,
        scale: true,
        axisLabel: {
          formatter: (value: number) => formatNumber(value),
        },
      },
      series: [
        {
          name: '数据点',
          type: 'scatter',
          data: scatterData,
          symbolSize: (value: number[]) => {
            return Math.sqrt(value[1]) / 5 + 8
          },
          itemStyle: {
            color: (params: any) => {
              const index = params.dataIndex % chartColors.length
              return chartColors[index]
            },
          },
          emphasis: {
            label: {
              show: true,
              formatter: (params: any) => `${params.dataIndex + 1}`,
              position: 'top',
            },
          },
        },
      ],
    }
  }

  // 面积图配置
  const generateAreaChartOption = (data: any[], config: ChartOption) => {
    const lineOption = generateLineChartOption(data, config)
    if (lineOption.series && lineOption.series[0]) {
      lineOption.series[0].areaStyle = {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(58, 77, 233, 0.8)' },
          { offset: 1, color: 'rgba(58, 77, 233, 0.1)' },
        ]),
      }
    }
    return lineOption
  }

  // 辅助方法
  const getDefaultXAxis = (data: any[]) => {
    if (!data || data.length === 0) return ''
    const columns = Object.keys(data[0])
    return columns[0]
  }

  const getDefaultYAxis = (data: any[]) => {
    if (!data || data.length === 0) return ''
    const columns = Object.keys(data[0])
    const numericCols = getNumericColumns(data)
    return numericCols.length > 0 ? numericCols[0] : columns.length > 1 ? columns[1] : columns[0]
  }

  const getNumericColumns = (data: any[]) => {
    if (!data || data.length === 0) return []
    const columns = Object.keys(data[0])
    return columns.filter((col) => {
      const value = data[0][col]
      if (typeof value === 'number') return true
      if (typeof value === 'string') {
        return !isNaN(parseFloat(value))
      }
      return false
    })
  }

  const convertToNumber = (value: any): number => {
    if (value === null || value === undefined) return 0
    if (typeof value === 'number') return value
    if (typeof value === 'string') {
      const num = parseFloat(value.replace(/[^\d.-]/g, ''))
      return isNaN(num) ? 0 : num
    }
    return 0
  }

  const formatNumber = (value: number) => {
    if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
    if (value >= 1000) return (value / 1000).toFixed(1) + 'K'
    return value.toLocaleString()
  }

  // 数据预处理
  const preprocessChartData = (data: any[], chartType: string) => {
    if (!data || data.length === 0) return data

    const processedData = JSON.parse(JSON.stringify(data))

    processedData.forEach((row: any) => {
      Object.keys(row).forEach((key) => {
        const value = row[key]
        if (value === null || value === undefined) {
          row[key] = 0
        } else if (typeof value === 'string') {
          const num = parseFloat(value)
          if (!isNaN(num)) {
            row[key] = num
          }
        }
      })
    })

    return processedData
  }

  return {
    generateChartOption,
    preprocessChartData,
    chartColors,
  }
}
