// frontend/js/chart-renderer.js
// 图表管理器 - 支持多图表类型和用户控制
class ChartManager {
    constructor() {
        this.chartInstances = new Map();
        this.chartColors = [
            '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
            '#1abc9c', '#d35400', '#34495e', '#16a085', '#c0392b',
            '#8e44ad', '#27ae60', '#2980b9', '#f1c40f', '#e67e22'
        ];
    }

    /**
     * 渲染图表主函数
     */
    renderChart(domId, data, chartType, chartConfig) {
        const chartDom = document.getElementById(domId);
        if (!chartDom) {
            console.error(`找不到图表容器: ${domId}`);
            return null;
        }
        if (chartType === 'pie_chart') {
        chartConfig = this.adjustPieChartConfig(data, chartConfig);
}
        try {
            // 清除现有内容
            chartDom.innerHTML = '';
            
            // 创建图表容器
            const chartContainer = document.createElement('div');
            chartContainer.style.width = '100%';
            chartContainer.style.height = chartConfig.height || '350px';
            chartContainer.id = `echart-${domId}`;
            chartDom.appendChild(chartContainer);
            
            // 初始化ECharts
            const myChart = echarts.init(chartContainer);
            this.chartInstances.set(domId, myChart);
            
            // 预处理数据
            const processedData = this.preprocessData(data, chartType, chartConfig);
            
            // 生成图表配置
            const option = this.createChartOption(processedData, chartType, chartConfig);
            
            // 设置配置
            myChart.setOption(option);
            
            // 添加响应式支持
            window.addEventListener('resize', () => {
                myChart.resize();
            });
            
            // 添加图表工具栏（如果配置允许）
            if (chartConfig.show_toolbox !== false) {
                this.addChartToolbar(chartDom, myChart, option, data, chartType, chartConfig);
            }
            
            return myChart;
            
        } catch (error) {
            this.handleChartError(error, chartDom);
            return null;
        }
    }

    /**
     * 根据图表类型创建配置
     */
    createChartOption(data, chartType, config) {
        // 基础选项
        const baseOption = {
            backgroundColor: '#fff',
            animation: true,
            animationDuration: 1000,
            animationEasing: 'cubicOut'
        };
        
        // 根据图表类型创建特定配置
        let chartOption;
        switch(chartType) {
            case 'bar_chart':
                chartOption = this.createBarChartOption(data, config);
                break;
            case 'multi_bar_chart':
                chartOption = this.createMultiBarChartOption(data, config);
                break;
            case 'line_chart':
                chartOption = this.createLineChartOption(data, config);
                break;
            case 'pie_chart':
                chartOption = this.createPieChartOption(data, config);
                break;
            case 'scatter_chart':
                chartOption = this.createScatterChartOption(data, config);
                break;
            case 'radar_chart':
                chartOption = this.createRadarChartOption(data, config);
                break;
            case 'heatmap':
                chartOption = this.createHeatmapOption(data, config);
                break;
            case 'gauge':
                chartOption = this.createGaugeOption(data, config);
                break;
            case 'area_chart':
                chartOption = this.createAreaChartOption(data, config);
                break;
            case 'stacked_bar_chart':
                chartOption = this.createStackedBarChartOption(data, config);
                break;
            default:
                throw new Error(`不支持的图表类型: ${chartType}`);
        }
        
        // 合并基础选项和图表特定选项
        return { ...baseOption, ...chartOption };
    }

    /**
     * 柱状图配置
     */
    createBarChartOption(data, config) {
        const xAxis = config.x_axis || this.getDefaultXAxis(data);
        const yAxis = config.y_axis || this.getDefaultYAxis(data);
        const title = config.title || `${yAxis} 按 ${xAxis} 统计`;
        
        // 提取数据
        const xData = data.map(item => {
            const value = item[xAxis];
            return value !== null && value !== undefined ? String(value) : '未知';
        });
        
        const yData = data.map(item => {
            const value = item[yAxis];
            return this.convertToNumber(value);
        });
        
        // 排序（如果配置要求）
        if (config.sorted) {
            const combined = xData.map((x, i) => ({ x, y: yData[i] }));
            combined.sort((a, b) => {
                if (config.sort_order === 'asc') {
                    return a.y - b.y;
                } else {
                    return b.y - a.y;
                }
            });
            
            xData.length = 0;
            yData.length = 0;
            combined.forEach(item => {
                xData.push(item.x);
                yData.push(item.y);
            });
        }
        
        // 限制数据数量
        if (config.limit && xData.length > config.limit) {
            xData.splice(config.limit);
            yData.splice(config.limit);
        }
        
        return {
            title: this.createTitleOption(title),
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: (params) => {
                    const param = params[0];
                    return `${param.name}<br/>${yAxis}: <b>${param.value}</b>`;
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xData,
                axisLabel: {
                    rotate: xData.length > 8 ? 45 : 0,
                    interval: 0,
                    fontSize: 12
                }
            },
            yAxis: {
                type: 'value',
                name: yAxis,
                axisLabel: {
                    formatter: (value) => this.formatNumber(value)
                }
            },
            series: [{
                name: yAxis,
                type: 'bar',
                data: yData,
                itemStyle: {
                    color: config.color || new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#3498db' },
                        { offset: 0.5, color: '#2980b9' },
                        { offset: 1, color: '#1f618d' }
                    ]),
                    borderRadius: [4, 4, 0, 0]
                },
                barWidth: Math.max(20, Math.min(50, 400 / xData.length)),
                label: {
                    show: config.show_values || xData.length <= 15,
                    position: 'top',
                    formatter: (params) => this.formatNumber(params.value)
                },
                emphasis: {
                    itemStyle: {
                        shadowColor: 'rgba(0, 0, 0, 0.5)',
                        shadowBlur: 10
                    }
                }
            }]
        };
    }

    /**
     * 多系列柱状图配置
     */
    createMultiBarChartOption(data, config) {
        const xAxis = config.x_axis || this.getDefaultXAxis(data);
        const yAxes = config.y_axes || this.getNumericColumns(data).slice(0, 3);
        const title = config.title || '多维度对比';
        
        // 提取x轴数据
        const xData = data.map(item => {
            const value = item[xAxis];
            return value !== null && value !== undefined ? String(value) : '未知';
        });
        
        // 准备系列数据
        const series = yAxes.map((yAxis, index) => ({
            name: yAxis,
            type: 'bar',
            data: data.map(item => this.convertToNumber(item[yAxis])),
            itemStyle: {
                color: this.getChartColor(index)
            },
            barWidth: 25,
            label: {
                show: config.show_values && data.length <= 10,
                position: 'top',
                fontSize: 11
            }
        }));
        
        return {
            title: this.createTitleOption(title),
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            legend: {
                data: yAxes,
                top: 30,
                textStyle: { color: '#666' }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '12%',
                top: '20%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xData,
                axisLabel: {
                    rotate: xData.length > 5 ? 45 : 0,
                    fontSize: 12,
                    interval: 0
                }
            },
            yAxis: {
                type: 'value',
                name: '数值',
                axisLabel: {
                    formatter: (value) => this.formatNumber(value)
                }
            },
            series: series
        };
    }

    /**
     * 折线图配置
     */
    createLineChartOption(data, config) {
        const xAxis = config.x_axis || this.getDefaultXAxis(data);
        const yAxis = config.y_axis || this.getDefaultYAxis(data);
        const title = config.title || `${yAxis} 趋势图`;
        
        // 提取数据
        const xData = data.map(item => {
            const value = item[xAxis];
            return value !== null && value !== undefined ? String(value) : '未知';
        });
        
        const yData = data.map(item => {
            const value = item[yAxis];
            return this.convertToNumber(value);
        });
        
        return {
            title: this.createTitleOption(title),
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'line' }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xData,
                boundaryGap: false,
                axisLabel: {
                    rotate: xData.length > 8 ? 45 : 0,
                    interval: 0,
                    fontSize: 12
                }
            },
            yAxis: {
                type: 'value',
                name: yAxis,
                axisLabel: {
                    formatter: (value) => this.formatNumber(value)
                }
            },
            series: [{
                name: yAxis,
                type: 'line',
                data: yData,
                smooth: config.smooth !== false,
                lineStyle: {
                    width: 3,
                    color: config.color || '#ff4d4f'
                },
                itemStyle: {
                    color: config.color || '#ff4d4f'
                },
                areaStyle: config.area_style ? {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(255, 77, 79, 0.6)' },
                        { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
                    ])
                } : null,
                symbol: 'circle',
                symbolSize: 8,
                emphasis: {
                    focus: 'series'
                }
            }]
        };
    }

/**
 * 饼图配置
 */
createPieChartOption(data, config) {
    const nameCol = config.name_col || this.getDefaultXAxis(data);
    const valueCol = config.value_col || this.getDefaultYAxis(data);
    const title = config.title || `${nameCol} 分布`;
    
    // 提取饼图数据
    const pieData = data.map(item => {
        const name = String(item[nameCol] || '未知');
        const value = this.convertToNumber(item[valueCol]);
        return { name, value };
    }).filter(item => item.value > 0);
    
    if (pieData.length === 0) {
        throw new Error('没有有效数据用于饼图');
    }
    
    // 排序
    if (config.sorted) {
        pieData.sort((a, b) => {
            if (config.sort_order === 'asc') {
                return a.value - b.value;
            } else {
                return b.value - a.value;
            }
        });
    }
    
    // 限制数量
    if (config.limit && pieData.length > config.limit) {
        pieData.splice(config.limit);
    }
    
    // 简单图例配置
    const showLegend = config.show_legend !== false;
    const dataCount = pieData.length;
    
    const legendConfig = {
        show: showLegend,
        data: pieData.map(item => item.name)  // 关键：必须设置图例数据
    };
    
    // 根据数据量调整布局
    if (dataCount <= 5) {
        legendConfig.orient = 'vertical';
        legendConfig.left = 'left';
        legendConfig.top = 'middle';
    } else if (dataCount <= 10) {
        legendConfig.orient = 'horizontal';
        legendConfig.left = 'center';
        legendConfig.top = 'top';
    } else {
        legendConfig.type = 'scroll';
        legendConfig.orient = 'horizontal';
        legendConfig.left = 'center';
        legendConfig.top = 'top';
    }
    
    // 简单标签配置
    const showLabel = config.show_label !== false;
    let labelConfig = {
        show: showLabel,
        position: 'outside',
        formatter: '{b}: {d}%'
    };
    
    if (dataCount > 8) {
        labelConfig.position = 'inside';
        labelConfig.formatter = '{d}%';
        labelConfig.color = '#fff';
    }
    
    // 返回完整配置
    return {
        title: this.createTitleOption(title),
        tooltip: {
            trigger: 'item',
            formatter: (params) => {
                const { name, value, percent } = params;
                return `${name}<br/>数值: ${this.formatNumber(value)}<br/>占比: ${percent}%`;
            }
        },
        legend: legendConfig,
        series: [{
            name: title,
            type: 'pie',
            radius: '70%',
            center: ['50%', '55%'],
            data: pieData,
            itemStyle: {
                borderRadius: 8,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: labelConfig,
            labelLine: {
                show: dataCount <= 8
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: '14',
                    fontWeight: 'bold'
                },
                scale: true,
                scaleSize: 8
            }
        }]
    };
}
/**
 * 饼图自动调整配置 - 简化版
 */
adjustPieChartConfig(data, config) {
    const adjustedConfig = { ...config };
    const dataCount = data.length;
    
    // 简单调整
    if (dataCount > 15) {
        adjustedConfig.show_legend = false;
        adjustedConfig.show_label = false;
    } else if (dataCount > 10) {
        adjustedConfig.scrollable_legend = true;
    }
    
    return adjustedConfig;
}

    /**
     * 散点图配置
     */
    createScatterChartOption(data, config) {
        const xAxis = config.x_axis || this.getDefaultXAxis(data);
        const yAxis = config.y_axis || this.getDefaultYAxis(data);
        const colorBy = config.color_by;
        const title = config.title || `${yAxis} 与 ${xAxis} 关系`;
        
        // 提取数据
        const scatterData = data.map(item => ({
            name: item[colorBy] || '',
            value: [
                this.convertToNumber(item[xAxis]),
                this.convertToNumber(item[yAxis])
            ]
        }));
        
        return {
            title: this.createTitleOption(title),
            tooltip: {
                trigger: 'item',
                formatter: (params) => {
                    const point = params.value;
                    const name = params.name || '';
                    const nameText = name ? `分类: ${name}<br/>` : '';
                    return `${nameText}${xAxis}: ${point[0]}<br/>${yAxis}: ${point[1]}`;
                }
            },
            grid: {
                left: '3%',
                right: '7%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                name: xAxis,
                scale: true,
                axisLabel: {
                    formatter: (value) => this.formatNumber(value)
                }
            },
            yAxis: {
                type: 'value',
                name: yAxis,
                scale: true,
                axisLabel: {
                    formatter: (value) => this.formatNumber(value)
                }
            },
            series: [{
                name: '数据点',
                type: 'scatter',
                data: scatterData,
                symbolSize: (value) => {
                    return Math.sqrt(value[1]) / 5 + 8;
                },
                itemStyle: {
                    color: (params) => {
                        if (colorBy) {
                            const index = params.dataIndex % this.chartColors.length;
                            return this.chartColors[index];
                        }
                        return '#3498db';
                    }
                },
                emphasis: {
                    label: {
                        show: true,
                        formatter: (params) => `${params.dataIndex + 1}`,
                        position: 'top'
                    }
                }
            }]
        };
    }

    /**
     * 面积图配置
     */
    createAreaChartOption(data, config) {
        const lineOption = this.createLineChartOption(data, config);
        lineOption.series[0].areaStyle = lineOption.series[0].areaStyle || {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(58, 77, 233, 0.8)' },
                { offset: 1, color: 'rgba(58, 77, 233, 0.1)' }
            ])
        };
        return lineOption;
    }

    /**
     * 堆叠柱状图配置
     */
    createStackedBarChartOption(data, config) {
        const multiBarOption = this.createMultiBarChartOption(data, config);
        multiBarOption.series.forEach(series => {
            series.stack = 'total';
        });
        return multiBarOption;
    }

    /**
     * 雷达图配置
     */
    createRadarChartOption(data, config) {
        const indicators = config.indicators || this.getNumericColumns(data).slice(0, 6);
        const title = config.title || '雷达图分析';
        
        const seriesData = data.slice(0, 3).map((item, index) => ({
            name: item.name || `系列${index + 1}`,
            value: indicators.map(indicator => this.convertToNumber(item[indicator])),
            itemStyle: {
                color: this.getChartColor(index)
            }
        }));
        
        return {
            title: this.createTitleOption(title),
            tooltip: {},
            radar: {
                indicator: indicators.map(indicator => ({
                    name: indicator,
                    max: Math.max(...data.map(item => this.convertToNumber(item[indicator]))) * 1.2
                }))
            },
            series: [{
                type: 'radar',
                data: seriesData
            }]
        };
    }

    /**
     * 热力图配置
     */
    createHeatmapOption(data, config) {
        // 简单实现，实际需要更复杂的数据处理
        return {
            title: this.createTitleOption('热力图'),
            tooltip: {},
            xAxis: {
                type: 'category',
                data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            },
            yAxis: {
                type: 'category',
                data: ['Morning', 'Afternoon', 'Evening']
            },
            visualMap: {
                min: 0,
                max: 10,
                calculable: true,
                orient: 'horizontal',
                left: 'center',
                bottom: '15%'
            },
            series: [{
                name: '热度',
                type: 'heatmap',
                data: [],
                label: {
                    show: true
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        };
    }

    /**
     * 仪表盘配置
     */
    createGaugeOption(data, config) {
        const value = data.length > 0 ? this.convertToNumber(data[0][Object.keys(data[0])[0]]) : 0;
        const title = config.title || '仪表盘';
        
        return {
            title: this.createTitleOption(title),
            tooltip: {
                formatter: '{a} <br/>{b} : {c}'
            },
            series: [{
                name: '指标',
                type: 'gauge',
                detail: { formatter: '{value}' },
                data: [{ value, name: '数值' }],
                axisLine: {
                    lineStyle: {
                        width: 10,
                        color: [
                            [0.3, '#67e0e3'],
                            [0.7, '#37a2da'],
                            [1, '#fd666d']
                        ]
                    }
                }
            }]
        };
    }

    /**
     * 添加图表工具栏
     */
    addChartToolbar(chartDom, chartInstance, option, data, chartType, config) {
        const toolbar = document.createElement('div');
        toolbar.className = 'chart-toolbar';
        toolbar.style.cssText = `
            display: flex;
            justify-content: flex-end;
            padding: 8px;
            gap: 8px;
            border-bottom: 1px solid #eee;
            background: #f8f9fa;
        `;
        
        // 下载按钮
        const downloadBtn = this.createToolbarButton('下载图表', '📥');
        downloadBtn.onclick = () => this.downloadChart(chartInstance, config.title || 'chart');
        
        // 刷新按钮
        const refreshBtn = this.createToolbarButton('刷新', '🔄');
        refreshBtn.onclick = () => {
            chartInstance.clear();
            chartInstance.setOption(option);
        };
        
        // 切换图表类型（仅支持部分切换）
        if (['bar_chart', 'line_chart', 'pie_chart'].includes(chartType)) {
            const switchBtn = this.createToolbarButton('切换类型', '🔄');
            switchBtn.onclick = () => this.switchChartType(chartDom.id, data, chartType, config);
        }
        
        toolbar.appendChild(downloadBtn);
        toolbar.appendChild(refreshBtn);
        
        chartDom.prepend(toolbar);
    }

    createToolbarButton(text, icon) {
        const button = document.createElement('button');
        button.innerHTML = `${icon} ${text}`;
        button.style.cssText = `
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
        `;
        return button;
    }

    /**切换图表类型的方法 */
    switchChartType(domId, data, currentType, config) {
        const typeMap = {
            'bar_chart': 'line_chart',
            'line_chart': 'pie_chart',
            'pie_chart': 'bar_chart'
        };
        
        const newType = typeMap[currentType];
        if (newType) {
            this.renderChart(domId, data, newType, config);
        }
    }

    downloadChart(chartInstance, filename = 'chart') {
        const url = chartInstance.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff'
        });
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `${filename}_${new Date().getTime()}.png`;
        link.click();
    }

    /**
     * 数据预处理
     */
    preprocessData(data, chartType, config) {
        if (!data || data.length === 0) return data;
        
        const processedData = JSON.parse(JSON.stringify(data));
        
        processedData.forEach(row => {
            Object.keys(row).forEach(key => {
                const value = row[key];
                if (value === null || value === undefined) {
                    row[key] = 0;
                } else if (typeof value === 'string') {
                    const num = parseFloat(value);
                    if (!isNaN(num)) {
                        row[key] = num;
                    } else if (chartType === 'pie_chart') {
                        row[key] = 0;
                    }
                } else if (typeof value !== 'number' && chartType === 'pie_chart') {
                    row[key] = 0;
                }
            });
        });
        
        return processedData;
    }

    /**
     * 辅助方法
     */
    createTitleOption(text) {
        return {
            text: text,
            left: 'center',
            textStyle: {
                color: '#2c3e50',
                fontSize: 16,
                fontWeight: 'bold'
            },
            subtext: '',
            subtextStyle: {
                color: '#7f8c8d',
                fontSize: 12
            }
        };
    }

    getDefaultXAxis(data) {
        if (!data || data.length === 0) return '';
        const columns = Object.keys(data[0]);
        return columns[0];
    }

    getDefaultYAxis(data) {
        if (!data || data.length === 0) return '';
        const columns = Object.keys(data[0]);
        const numericCols = this.getNumericColumns(data);
        return numericCols.length > 0 ? numericCols[0] : (columns.length > 1 ? columns[1] : columns[0]);
    }

    getNumericColumns(data) {
        if (!data || data.length === 0) return [];
        const columns = Object.keys(data[0]);
        return columns.filter(col => {
            const value = data[0][col];
            if (typeof value === 'number') return true;
            if (typeof value === 'string') {
                return !isNaN(parseFloat(value));
            }
            return false;
        });
    }

    getChartColor(index) {
        return this.chartColors[index % this.chartColors.length];
    }

    convertToNumber(value) {
        if (value === null || value === undefined) return 0;
        if (typeof value === 'number') return value;
        if (typeof value === 'string') {
            const num = parseFloat(value.replace(/[^\d.-]/g, ''));
            return isNaN(num) ? 0 : num;
        }
        return 0;
    }

    formatNumber(value) {
        if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
        if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
        return value.toLocaleString();
    }

    handleChartError(error, chartDom) {
        console.error('图表渲染失败:', error);
        chartDom.innerHTML = `
            <div style="padding: 40px 20px; text-align: center; color: #e74c3c;">
                <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                <h3 style="margin: 0 0 10px 0;">图表渲染失败</h3>
                <p style="color: #666; margin: 0 0 20px 0;">${error.message}</p>
                <button onclick="location.reload()" style="
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                ">刷新页面</button>
            </div>
        `;
    }

    /**
     * 清理图表实例
     */
    disposeChart(domId) {
        const chart = this.chartInstances.get(domId);
        if (chart) {
            chart.dispose();
            this.chartInstances.delete(domId);
        }
    }

    disposeAll() {
        this.chartInstances.forEach((chart, domId) => {
            chart.dispose();
        });
        this.chartInstances.clear();
    }
}

// 创建单例实例
const chartManager = new ChartManager();

export function renderChart(domId, data, chartType, chartConfig) {
    return chartManager.renderChart(domId, data, chartType, chartConfig);
}

export function preprocessChartData(data, chartType) {
    return chartManager.preprocessData(data, chartType, {});
}

export function getChartManager() {
    return chartManager;
}

export function createCustomChart(domId, customOption) {
    const chartDom = document.getElementById(domId);
    if (!chartDom) return null;
    
    const chart = echarts.init(chartDom);
    chart.setOption(customOption);
    return chart;
}

export default chartManager;