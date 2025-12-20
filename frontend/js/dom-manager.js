// frontend/js/dom-manager.js
// DOM元素管理
let currentMode = 'chat';

export const messagesBox = document.getElementById('messagesBox');
export const userInput = document.getElementById('userInput');
export const sendBtn = document.getElementById('sendBtn');

// 模式管理
export function getCurrentMode() {
    return currentMode;
}

export function setCurrentMode(mode) {
    currentMode = mode;
}

// DOM工具函数
export function getElement(selector) {
    return document.querySelector(selector);
}

export function getAllElements(selector) {
    return document.querySelectorAll(selector);
}

export function createElement(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content) element.textContent = content;
    return element;
}