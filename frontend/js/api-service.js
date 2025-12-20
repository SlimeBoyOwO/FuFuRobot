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