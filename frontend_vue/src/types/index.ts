// 类型定义文件

export interface Message {
  id?: string
  content: string
  thinking_content?: string
  role: 'user' | 'ai'
  timestamp: Date
  type?: 'text' | 'chart' | 'table' | 'thinking' | 'answer'
  data?: any
  sql?: string
  html?: string
  chartType?: string
  chartConfig?: any
  operationResult?: any
}

export interface ChatMode {
  id: 'chat' | 'focus' | 'text2sql'
  name: string
  icon: string
  description: string
}

export interface ApiResponse {
  text?: string
  html?: string
  data?: any[]
  chart_type?: string
  chart_config?: any
  sql?: string
  operation_result?: any
}

export interface StreamData {
  type: 'thinking' | 'answer' | 'error'
  content: string
}

export interface ChartOption {
  title?: string
  xAxis?: string
  yAxis?: string | string[]
  x_axis?: string
  y_axis?: string | string[]
  name_col?: string
  value_col?: string | string[]
  color?: string
  sorted?: boolean
  sortOrder?: 'asc' | 'desc'
  limit?: number
  showValues?: boolean
  showLegend?: boolean
  height?: string
}
