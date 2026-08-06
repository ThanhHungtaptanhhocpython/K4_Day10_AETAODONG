function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    const targetTab = document.getElementById(`tab-${tabId}`);
    targetTab.classList.remove('hidden');
    targetTab.classList.add('active');
    
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
}

// Toast Notification System
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? '✅' : '❌';
    toast.innerHTML = `<span class="toast-icon">${icon}</span> <span>${message}</span>`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards';
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// Terminal Simulator
function appendLog(message, type = 'info') {
    const terminal = document.getElementById('terminal-logs');
    const line = document.createElement('div');
    line.className = `log-line log-${type}`;
    const timestamp = new Date().toLocaleTimeString();
    line.innerHTML = `<span style="color: #64748b">[${timestamp}]</span> ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

function clearLogs() {
    document.getElementById('terminal-logs').innerHTML = '';
}

// Fetch dashboard data
async function fetchDashboardData() {
    try {
        const res = await fetch('/api/dashboard-data');
        const data = await res.json();
        
        document.getElementById('raw-count').innerText = data.raw_count || '0';
        
        updateCard('b', data.baseline_quality, data.baseline_metrics);
        updateCard('c', data.corrupted_quality, data.corrupted_metrics);
        updateCard('r', data.repaired_quality, data.repaired_metrics);
        
    } catch (e) {
        console.error("Fetch error", e);
    }
}

function updateCard(prefix, quality, metrics) {
    const qBadge = document.getElementById(`${prefix}-quality`);
    if (quality) {
        qBadge.innerText = quality.passed ? 'PASSED' : 'FAILED';
        qBadge.className = quality.passed ? 'badge pass' : 'badge fail';
    } else {
        qBadge.innerText = 'N/A';
        qBadge.className = 'badge';
    }
    
    if (metrics) {
        document.getElementById(`${prefix}-hit-rate`).innerText = metrics.retrieval_hit_rate ? metrics.retrieval_hit_rate.toFixed(4) : '--';
        document.getElementById(`${prefix}-f1`).innerText = metrics.mean_token_f1 ? metrics.mean_token_f1.toFixed(4) : '--';
    }
}

// Pipeline Execution
function setControlsDisabled(disabled) {
    document.getElementById('btn-phase1').disabled = disabled;
    document.getElementById('btn-phase2').disabled = disabled;
}

async function runPhase1() {
    setControlsDisabled(true);
    clearLogs();
    appendLog('Starting Phase 1 (Baseline Pipeline)...', 'info');
    appendLog('Fetching raw records from Crossref API...', 'info');
    
    // Simulate request progress
    let count = 0;
    const total = 24;
    const interval = setInterval(() => {
        count += 4;
        if (count < total) {
            appendLog(`Processing API request ${count}/${total}...`, 'info');
        } else {
            appendLog(`Processing API request ${total}/${total}...`, 'info');
            clearInterval(interval);
            appendLog('Cleaning data and building embeddings...', 'warn');
        }
    }, 400);
    
    try {
        const res = await fetch('/api/run-phase1', { method: 'POST' });
        const result = await res.json();
        
        // Force complete if backend is faster than simulation
        clearInterval(interval);
        if (count < total) {
            appendLog(`API requests completed rapidly (cached).`, 'info');
            appendLog('Cleaning data and building embeddings...', 'warn');
        }
        
        if(res.ok) {
            appendLog('Phase 1 completed successfully!', 'success');
            showToast('Phase 1 Completed!', 'success');
        } else {
            appendLog(`Error: ${result.detail}`, 'error');
            showToast('Execution Failed', 'error');
        }
        fetchDashboardData();
    } catch (e) {
        clearInterval(interval);
        appendLog('Network error occurred.', 'error');
        showToast('Network Error', 'error');
    }
    setControlsDisabled(false);
}

let phase2Interval;
async function runPhase2() {
    setControlsDisabled(true);
    clearLogs();
    appendLog('Starting Phase 2 (Corruption Flow)...', 'warn');
    appendLog('Injecting data corruptions (drop, noise, truncate, duplicate)...', 'info');
    
    // Simulate request progress for evaluation
    let count = 0;
    const total = 15;
    
    setTimeout(() => appendLog('Evaluating corrupted data impact...', 'warn'), 500);
    
    setTimeout(() => {
        phase2Interval = setInterval(() => {
            count += 3;
            if (count < total) {
                appendLog(`Sending LLM evaluation request ${count}/${total}...`, 'info');
            } else {
                appendLog(`Sending LLM evaluation request ${total}/${total}...`, 'info');
                clearInterval(phase2Interval);
                setTimeout(() => appendLog('Repairing data from raw snapshot...', 'warn'), 500);
            }
        }, 600);
    }, 1000);
    
    try {
        const res = await fetch('/api/run-phase2', { method: 'POST' });
        const result = await res.json();
        
        clearInterval(phase2Interval);
        if (count < total) {
            appendLog('Evaluation completed rapidly (cached).', 'info');
            appendLog('Repairing data from raw snapshot...', 'warn');
        }
        
        if(res.ok) {
            appendLog('Phase 2 completed. Data repaired successfully!', 'success');
            showToast('Phase 2 Completed!', 'success');
        } else {
            appendLog(`Error: ${result.detail}`, 'error');
            showToast('Execution Failed', 'error');
        }
        fetchDashboardData();
    } catch (e) {
        clearInterval(phase2Interval);
        appendLog('Network error occurred.', 'error');
        showToast('Network Error', 'error');
    }
    setControlsDisabled(false);
}

// Chat functions
function handleChatKey(event) {
    if (event.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    const useCorrupted = document.getElementById('use-corrupted-toggle').checked;
    const history = document.getElementById('chat-history');
    
    history.innerHTML += `
        <div class="message user-message">
            <div class="avatar">👤</div>
            <div class="bubble">${msg}</div>
        </div>
    `;
    input.value = '';
    
    // Add typing indicator
    const typingId = 'typing-' + Date.now();
    history.innerHTML += `
        <div class="message ai-message" id="${typingId}">
            <div class="avatar">🤖</div>
            <div class="bubble" style="color: #94a3b8"><i>Thinking...</i></div>
        </div>
    `;
    history.scrollTop = history.scrollHeight;
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, use_corrupted: useCorrupted })
        });
        const data = await res.json();
        
        document.getElementById(typingId).remove();
        
        let aiText = data.response;
        if (!res.ok) aiText = `<span style="color: #fca5a5">Error: ${data.detail}</span>`;
        
        history.innerHTML += `
            <div class="message ai-message">
                <div class="avatar">🤖</div>
                <div class="bubble">${aiText}</div>
            </div>
        `;
    } catch (e) {
        document.getElementById(typingId).remove();
        history.innerHTML += `
            <div class="message ai-message">
                <div class="avatar">🤖</div>
                <div class="bubble"><span style="color: #fca5a5">Network error. Cannot reach the agent.</span></div>
            </div>
        `;
    }
    history.scrollTop = history.scrollHeight;
}

document.addEventListener('DOMContentLoaded', fetchDashboardData);
