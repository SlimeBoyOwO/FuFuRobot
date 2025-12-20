// frontend/js/message-manager.js
import { messagesBox } from './dom-manager.js';

const AVATAR_CONFIG = {
    user: './images/user.png',
    ai: './images/robot.png'
};

/**
 * 添加消息到聊天界面
 * @param {string} text - 消息文本内容
 * @param {string} role - 消息发送者角色，'user' 或 'ai'
 */

export function createAvatar(role) {
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    const img = document.createElement('img');
    img.src = role === 'user' ? AVATAR_CONFIG.user : AVATAR_CONFIG.ai;
    img.alt = role;
    
    // 添加错误处理
    img.onerror = function() {
        avatar.innerHTML = role === 'user' ? '👤' : '🤖';
        // 根据角色添加相应的背景样式
        if (role === 'user') {
            avatar.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        } else {
            avatar.style.background = 'linear-gradient(135deg, #3498db 0%, #2c3e50 100%)';
        }
    };
    avatar.appendChild(img);
    return avatar;
}

export function addMessage(text, role) {
    // 创建消息容器元素
    const messageContainer = document.createElement('div');
    messageContainer.className = `message ${role}`;
    
    // 创建头像
    const avatar = createAvatar(role);

    // 创建内容容器
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 创建气泡
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    // 添加时间戳
    const timestamp = document.createElement('div');
    timestamp.className = 'message-time';
    timestamp.textContent = new Date().toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    bubble.appendChild(timestamp);

    // 组装消息
    if (role === 'user') {
        contentDiv.appendChild(bubble);
        messageContainer.appendChild(contentDiv);
        messageContainer.appendChild(avatar);
    } else {
        messageContainer.appendChild(avatar);
        contentDiv.appendChild(bubble);
        messageContainer.appendChild(contentDiv);
    }
    
    messagesBox.appendChild(messageContainer);
    scrollToBottom();
}

export function showLoading() {
    const loadingId = 'loading-' + Date.now();
    const messageContainer = document.createElement('div');
    messageContainer.id = loadingId;
    messageContainer.className = 'message ai';

    const avatar = createAvatar('ai');
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    
    const loadingDots = document.createElement('div');
    loadingDots.className = 'loading-dots';
    loadingDots.innerHTML = '<span></span><span></span><span></span>';
    
    bubble.appendChild(loadingDots);
    contentDiv.appendChild(bubble);
    messageContainer.appendChild(avatar);
    messageContainer.appendChild(contentDiv);
    
    messagesBox.appendChild(messageContainer);
    scrollToBottom();
    
    return loadingId;
}

export function removeLoading(loadingId) {
    const element = document.getElementById(loadingId);
    if (element) {
        element.remove();
    }
}

function scrollToBottom() {
    messagesBox.scrollTo({
        top: messagesBox.scrollHeight,
        behavior: 'smooth'
    });
}