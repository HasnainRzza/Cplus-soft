// Generate Session ID
const sessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
document.getElementById('session-badge').innerText = sessionId;

// Elements
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const uploadSuccess = document.getElementById('upload-success');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatHistory = document.getElementById('chat-history');

// Scroll to bottom
function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Upload Logic
uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => { 
    e.preventDefault(); 
    uploadZone.style.borderColor = 'var(--text-main)'; 
});
uploadZone.addEventListener('dragleave', () => {
    uploadZone.style.borderColor = 'rgba(15, 23, 42, 0.15)';
});
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'rgba(15, 23, 42, 0.15)';
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleUpload(e.target.files[0]);
});

async function handleUpload(file) {
    if (file.type !== 'application/pdf') {
        alert('Please upload a PDF file.');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadZone.classList.add('hidden');
    uploadStatus.classList.remove('hidden');
    
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        if (res.ok) {
            uploadStatus.classList.add('hidden');
            uploadSuccess.classList.remove('hidden');
        } else {
            throw new Error('Upload failed');
        }
    } catch (err) {
        alert(err.message);
        uploadStatus.classList.add('hidden');
        uploadZone.classList.remove('hidden');
    }
}

// Chat Logic
function appendMessage(role, text, isStream = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const iconClass = role === 'user' ? 'ph-user' : 'ph-robot';
    
    msgDiv.innerHTML = `
        <div class="avatar"><i class="ph ${iconClass}"></i></div>
        <div class="content"></div>
    `;
    
    chatHistory.appendChild(msgDiv);
    const contentDiv = msgDiv.querySelector('.content');
    
    if (!isStream) {
        contentDiv.innerText = text;
    }
    
    scrollToBottom();
    return contentDiv;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;
    
    chatInput.value = '';
    appendMessage('user', query);
    
    const streamContainer = appendMessage('system', '', true);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, query: query })
        });
        
        // Use the Streams API to decode the response chunk-by-chunk
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            streamContainer.innerText += chunk;
            scrollToBottom();
        }
    } catch (err) {
        streamContainer.innerText = "Error: " + err.message;
    }
});
