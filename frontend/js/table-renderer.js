// frontend/js/table-manager.js
export function generateTable(data) {
    if (!data || data.length === 0) return '';
    
    const keys = Object.keys(data[0]);
    
    let html = '<table class="data-table"><thead><tr>';
    keys.forEach(k => html += `<th>${k}</th>`);
    html += '</tr></thead><tbody>';
    
    data.forEach(row => {
        html += '<tr>';
        keys.forEach(k => {
            const value = row[k];
            // 格式化数据
            let displayValue = value;
            if (value === null || value === undefined) {
                displayValue = '-';
            } else if (typeof value === 'number') {
                displayValue = value.toLocaleString();
            } else if (typeof value === 'boolean') {
                displayValue = value ? '是' : '否';
            }
            html += `<td>${displayValue}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

