// Tab switching logic
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`tab-${tabId}`).classList.remove('hidden');
    event.currentTarget.classList.add('active');
}

// Show/Hide loader
function setLoader(show, text = 'Processing...') {
    const loader = document.getElementById('loader');
    const btn1 = document.getElementById('btn-phase1');
    const btn2 = document.getElementById('btn-phase2');
    
    document.getElementById('loader-text').innerText = text;
    if (show) {
        loader.classList.remove('hidden');
        btn1.disabled = true;
        btn2.disabled = true;
    } else {
        loader.classList.add('hidden');
        btn1.disabled = false;
        btn2.disabled = false;
    }
}

// Fetch dashboard data
async function fetchDashboardData() {
    try {
        const res = await fetch('/api/dashboard-data');
        const data = await res.json();
        
        // Raw count
        document.getElementById('raw-count').innerText = data.raw_count || '0';
        
        // Update Baseline
        updateCard('b', data.baseline_quality, data.baseline_metrics);
        // Update Corrupted
        updateCard('c', data.corrupted_quality, data.corrupted_metrics);
        // Update Repaired
        updateCard('r', data.repaired_quality, data.repaired_metrics);
        
    } catch (e) {
        console.error("Failed to fetch dashboard data", e);
    }
}

function updateCard(prefix, quality, metrics) {
    const qBadge = document.getElementById(`${prefix}-quality`);
    if (quality) {
        if (quality.passed) {
            qBadge.innerText = 'Passed';
            qBadge.className = 'badge pass';
        } else {
            qBadge.innerText = 'Failed';
            qBadge.className = 'badge fail';
        }
    } else {
        qBadge.innerText = 'N/A';
        qBadge.className = 'badge';
    }
    
    if (metrics) {
        document.getElementById(`${prefix}-hit-rate`).innerText = metrics.retrieval_hit_rate ? metrics.retrieval_hit_rate.toFixed(4) : '--';
        document.getElementById(`${prefix}-f1`).innerText = metrics.answer_token_f1 ? metrics.answer_token_f1.toFixed(4) : '--';
    } else {
        document.getElementById(`${prefix}-hit-rate`).innerText = '--';
        document.getElementById(`${prefix}-f1`).innerText = '--';
    }
}

// Run pipelines
async function runPhase1() {
    setLoader(true, 'Running Baseline Pipeline...');
    try {
        const res = await fetch('/api/run-phase1', { method: 'POST' });
        const result = await res.json();
        if(res.ok) alert(result.message);
        else alert("Error: " + result.detail);
        fetchDashboardData();
    } catch (e) {
        alert("Network error.");
    }
    setLoader(false);
}

async function runPhase2() {
    setLoader(true, 'Running Corruption Flow...');
    try {
        const res = await fetch('/api/run-phase2', { method: 'POST' });
        const result = await res.json();
        if(res.ok) alert(result.message);
        else alert("Error: " + result.detail);
        fetchDashboardData();
    } catch (e) {
        alert("Network error.");
    }
    setLoader(false);
}

// Chat functions
function handleChatKey(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    const useCorrupted = document.getElementById('use-corrupted-toggle').checked;
    
    // Add user message
    const history = document.getElementById('chat-history');
    history.innerHTML += `
        <div class="message user-message">
            <div class="avatar">👤</div>
            <div class="bubble">${msg}</div>
        </div>
    `;
    input.value = '';
    history.scrollTop = history.scrollHeight;
    
    // Send to API
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, use_corrupted: useCorrupted })
        });
        const data = await res.json();
        
        let aiText = data.response;
        if (!res.ok) aiText = "Error: " + data.detail;
        
        history.innerHTML += `
            <div class="message ai-message">
                <div class="avatar">🤖</div>
                <div class="bubble">${aiText}</div>
            </div>
        `;
        history.scrollTop = history.scrollHeight;
        
    } catch (e) {
        history.innerHTML += `
            <div class="message ai-message">
                <div class="avatar">🤖</div>
                <div class="bubble" style="color: #FCA5A5">Network error failed to reach agent.</div>
            </div>
        `;
    }
}

// Initial fetch
document.addEventListener('DOMContentLoaded', fetchDashboardData);
