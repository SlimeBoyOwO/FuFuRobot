// frontend/js/api-service.js
// 注意：API路径指向后端API服务器（端口8000）
const API_BASE_URL = 'http://127.0.0.1:8000/api';

export async function sendChatMessage(message, mode) {
    console.log(`调用API: ${API_BASE_URL}/chat, 消息: ${message}, 模式: ${mode}`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ 
                message: message, 
                mode: mode 
            })
        });

        console.log('API响应状态:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}: ${response.statusText}`);
        }

        const resData = await response.json();
        console.log('API响应数据:', resData);
        
        if (!resData) {
            throw new Error('服务器返回空响应');
        }

        return resData;
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

// 测试API连接
export async function testAPIConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.ok;
    } catch (error) {
        console.error('API连接测试失败:', error);
        return false;
    }
}

/**
 * 【新增】流式聊天请求
 * @param {string} message 用户消息
 * @param {string} mode 模式 (focus)
 * @param {string} sessionId 会话ID
 * @param {function} onUpdate 回调函数，每收到一个字都会调用
 * @param {function} onDone 完成时的回调
 * @param {function} onError 出错时的回调
 */
export async function sendChatStream(message, mode, sessionId = 'default', onUpdate, onDone, onError) {
    console.log(`调用流式API: ${API_BASE_URL}/chat/stream`);

    try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream' // 告诉后端我们要流
            },
            body: JSON.stringify({
                message: message,
                mode: mode,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 获取读取器
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // 解码并存入缓冲
            buffer += decoder.decode(value, { stream: true });
            
            // 处理粘包（可能一次收到多行，或者一行没收全）
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // 最后一部分可能不完整，留到下一次

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6); // 去掉 'data: '
                    if (jsonStr.trim() === '[DONE]') {
                        onDone();
                        return;
                    }

                    try {
                        const data = JSON.parse(jsonStr);
                        onUpdate(data); // 调用回调更新UI
                    } catch (e) {
                        console.warn('非JSON数据:', jsonStr);
                    }
                }
            }
        }
        
        onDone(); // 确保结束

    } catch (error) {
        console.error('流式读取失败:', error);
        if (onError) onError(error);
    }
}