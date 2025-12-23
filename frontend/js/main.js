// frontend/js/main.js
import { 
    messagesBox, 
    userInput, 
    sendBtn,
    getCurrentMode,
    setCurrentMode
} from './dom-manager.js';
import { addMessage, showLoading, removeLoading,createAvatar } from './message-manager.js';
import { sendChatMessage, sendChatStream } from './api-service.js'; 
import { generateTable } from './table-renderer.js';
import { renderChart, preprocessChartData } from './chart-renderer.js';

class ChatApplication {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initMode();
        this.showWelcomeMessage();
    }

    bindEvents() {
        // 发送按钮事件
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // 回车发送事件
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 模式切换事件
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleModeChange(e));
        });
    }

    handleModeChange(event) {
        const newMode = event.target.value;
        setCurrentMode(newMode);
        
        // 更新导航项激活状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        event.target.closest('.nav-item').classList.add('active');
        
        // 更新输入框提示
        this.updateInputPlaceholder();
    }

    updateInputPlaceholder() {
        const mode = getCurrentMode();
        
        if (mode === 'chat') {
            userInput.placeholder = "和芙芙聊天，分享你的日常...";
        } else if (mode === 'focus') {
            // 纳西妲的提示语
            userInput.placeholder = "🍃 纳西妲：请告诉我你想要了解的世间真理吧...";
        } else {
            userInput.placeholder = "请输入数据查询指令，如：查询所有学生...";
        }
    }

    async sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        const mode = getCurrentMode();

        // 1. 显示用户消息
        addMessage(text, 'user');
        userInput.value = '';
        userInput.focus();

        // 2. 判断模式
        if (mode === 'focus') {
            // === 深度思考模式走流式处理 ===
            await this.handleStreamFocusMode(text);
        } else {
            // === 其他模式走原来的逻辑 ===
            const loadingId = showLoading();
            try {
                const resData = await sendChatMessage(text, mode);
                removeLoading(loadingId);
                this.handleAIResponse(resData);
            } catch (error) {
                this.handleError(error, loadingId);
            }
        }

        this.scrollToBottom();
    }

    // 处理流式聚焦模式的聊天响应
    // @param {string} text - 用户输入的文本内容
    async handleStreamFocusMode(text) {
            // 1. 手动创建消息容器
            const messageContainer = document.createElement('div');
            messageContainer.className = 'message ai';
            
            // 创建头像
            const avatar = createAvatar('ai');
            
            // 创建内容区
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';

            // 创建气泡
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            
            // =================================================
            // A. 创建思考过程容器 (使用 CSS 类控制样式)
            // =================================================
            const thinkingDetails = document.createElement('details');
            thinkingDetails.className = 'thinking-box'; // 使用 CSS 类
            thinkingDetails.open = true; // 默认展开
            
            const thinkingSummary = document.createElement('summary');
            thinkingSummary.textContent = '🍃 纳西妲来帮忙了...';
            
            const thinkingContent = document.createElement('div');
            thinkingContent.className = 'thinking-content';
            
            thinkingDetails.appendChild(thinkingSummary);
            thinkingDetails.appendChild(thinkingContent);
            
            // =================================================
            // B. 创建最终回答容器 (纳西妲主题)
            // =================================================
            const answerWrapper = document.createElement('div');
            answerWrapper.className = 'nahida-answer'; // 包裹层，用于应用绿色主题
            
            // 可选：添加一个小徽章
            const badge = document.createElement('div');
            badge.className = 'nahida-badge';
            badge.textContent = '小吉祥草王的解答';
            answerWrapper.appendChild(badge);

            const answerDiv = document.createElement('div');
            answerDiv.className = 'markdown-content'; // 内容层
            answerWrapper.appendChild(answerDiv);
            
            // 组装DOM
            bubble.appendChild(thinkingDetails);
            bubble.appendChild(answerWrapper);
            contentDiv.appendChild(bubble);
            messageContainer.appendChild(avatar);
            messageContainer.appendChild(contentDiv);
            
            messagesBox.appendChild(messageContainer);
            this.scrollToBottom();

            // 2. 开始流式请求
            let fullThinking = '';
            let fullAnswer = '';

            await sendChatStream(
                text, 
                'focus', 
                'default', // sessionId
                (data) => {
                    // === 收到数据包的回调 ===
                    if (data.type === 'thinking') {
                        // 更新思考内容
                        fullThinking += data.content;
                        thinkingContent.textContent = fullThinking;
                        
                    } else if (data.type === 'answer') {
                        // 思考结束
                        thinkingSummary.textContent = '🍃 纳西妲思考好了';
                        thinkingDetails.classList.add('completed'); // 添加完成样式
                        
                        // 更新回答内容
                        fullAnswer += data.content;
                        // 使用 marked 解析 Markdown
                        if (typeof marked !== 'undefined') {
                            answerDiv.innerHTML = marked.parse(fullAnswer);
                        } else {
                            answerDiv.textContent = fullAnswer; // 降级处理
                        }
                    } else if (data.type === 'error') {
                        answerDiv.innerHTML += `<br><span style="color:red">[错误: ${data.content}]</span>`;
                    }
                    
                    // 实时滚动到底部
                    this.scrollToBottom();
                },
                () => {
                    // === 完成回调 ===
                    console.log('流式输出结束');
                    if (!fullAnswer) {
                        thinkingSummary.textContent = '🍃 思考结束 (无回答)';
                    }
                },
                (error) => {
                    // === 错误回调 ===
                    answerDiv.innerHTML += `<br><span style="color:red">[网络错误: ${error.message}]</span>`;
                }
            );
        }

    handleAIResponse(resData) {
        // 创建AI消息容器
        const messageContainer = document.createElement('div');
        messageContainer.className = `message ai`;

        // 创建消息内容
        const messageContent = this.createMessageContent(resData);
        messageContainer.appendChild(messageContent);

        // 添加到消息框
        messagesBox.appendChild(messageContainer);

        // 渲染表格（如果有数据且不是操作结果）
        if (resData.data && resData.data.length > 0 && !resData.operation_result) {
            this.renderTable(resData.data, messageContent.querySelector('.bubble'));
        }

        // 渲染图表（如果需要）
        if (resData.chart_type && resData.chart_type !== 'none' && resData.data && resData.data.length > 0) {
            this.renderChart(resData, messageContent.querySelector('.bubble'));
        }
    }

    createMessageContent(resData) {
    // 先创建消息容器
    const messageContainer = document.createElement('div');
    messageContainer.className = `message ai`;
    
    // 创建头像
    const avatar = createAvatar("ai");
    
    // 创建内容容器
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 创建气泡
    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    // 处理消息内容
    if (resData.html) {
        bubble.innerHTML = resData.html;
    } else if (resData.text) {
        bubble.textContent = resData.text;
    } else {
        bubble.textContent = '收到无内容的消息';
    }

    // 添加SQL查询显示
    if (resData.sql) {
        this.addSQLQuery(resData.sql, bubble);
    }

    // 添加操作结果
    if (resData.operation_result) {
        this.addOperationResult(resData, bubble);
    }

    // 添加时间戳
    this.addTimestamp(bubble);

    // 组装消息
    contentDiv.appendChild(bubble);
    messageContainer.appendChild(avatar);
    messageContainer.appendChild(contentDiv);

    return messageContainer;
}
    addSQLQuery(sql, container) {
        const sqlDiv = document.createElement('div');
        sqlDiv.className = 'sql-query';
        sqlDiv.innerHTML = `<strong>执行的SQL查询:</strong><br>
                           <code class="sql-code">${sql}</code>`;
        container.appendChild(sqlDiv);
    }

    addOperationResult(resData, container) {
        const operationDiv = document.createElement('div');
        operationDiv.className = 'operation-result success';
        operationDiv.innerHTML = `
            <p>✅ ${resData.text}</p>
            <div class="operation-details">
                <small>操作详情: ${JSON.stringify(resData.operation_result)}</small>
            </div>
        `;
        container.appendChild(operationDiv);
    }

    addTimestamp(container) {
        const timestamp = document.createElement('div');
        timestamp.className = 'message-time';
        timestamp.textContent = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        container.appendChild(timestamp);
    }

    renderTable(data, container) {
        const tableHtml = generateTable(data);
        const tableContainer = document.createElement('div');
        tableContainer.innerHTML = tableHtml;
        container.appendChild(tableContainer);
    }

    renderChart(resData, container) {
        // 预处理数据
        const processedData = preprocessChartData(resData.data, resData.chart_type);
        
        // 创建图表容器
        const chartId = 'chart-' + Date.now();
        const chartBox = document.createElement('div');
        chartBox.id = chartId;
        chartBox.className = 'chart-box';
        
        // 添加加载状态
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chart-loading';
        loadingDiv.innerHTML = `
            <div class="spinner"></div>
            <div>正在生成图表...</div>
        `;
        chartBox.appendChild(loadingDiv);
        container.appendChild(chartBox);
        
        // 延迟渲染图表
        setTimeout(() => {
            try {
                // 移除加载状态
                chartBox.removeChild(loadingDiv);
                
                // 创建图表画布
                const chartCanvas = document.createElement('div');
                chartCanvas.style.width = '100%';
                chartCanvas.style.height = '320px';
                chartBox.appendChild(chartCanvas);
                
                // 渲染图表
                renderChart(chartId, processedData, resData.chart_type, resData.chart_config || {});
                
            } catch (error) {
                this.handleChartError(error, loadingDiv);
            }
        }, 100);
    }

    handleChartError(error, loadingDiv) {
        loadingDiv.innerHTML = `
            <div style="color: #e74c3c; font-size: 40px; margin-bottom: 10px;">⚠️</div>
            <div style="color: #e74c3c;">图表渲染失败: ${error.message}</div>
            <div style="font-size: 12px; margin-top: 10px;">请检查数据格式或刷新重试</div>
        `;
    }

    handleError(error, loadingId) {
        removeLoading(loadingId);
        addMessage('连接服务器失败，请确认后端服务已运行。错误: ' + error.message, 'ai');
        console.error('API调用错误:', error);
    }

    initMode() {
        const activeMode = document.querySelector('input[name="mode"]:checked');
        if (activeMode) {
            setCurrentMode(activeMode.value);
            activeMode.closest('.nav-item').classList.add('active');
            this.updateInputPlaceholder();
        }
    }

    showWelcomeMessage() {
        setTimeout(() => {
            addMessage(
                `您好！我是芙芙。QAQ我是您的聆听者，是您的小伙伴，还是您的好朋友,o(*￣▽￣*)ブ。

            如果问我很复杂的事情，我就会呼叫纳西妲来帮忙哦~(≧▽≦)/~

            而且呀，我可以帮助您完成以下任务：
            增删改查学生的数据
            生成统计图表

            请选择左侧的模式开始使用！`, 
                'ai'
            );
        }, 500);
    }

    scrollToBottom() {
        messagesBox.scrollTo({
            top: messagesBox.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    new ChatApplication();
});

export default ChatApplication;