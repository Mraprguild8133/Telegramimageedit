// Bot status management
let statusInterval;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize status check
    updateBotStatus();
    
    // Set up periodic status updates
    statusInterval = setInterval(updateBotStatus, 5000);
    
    // Set up image processing form
    setupImageProcessing();
    
    // Check for bot token and AI APIs
    checkBotToken();
    checkAIStatus();
});

function updateBotStatus() {
    fetch('/api/bot/status')
        .then(response => response.json())
        .then(data => {
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            const usersCount = document.getElementById('users-count');
            const messagesCount = document.getElementById('messages-count');
            const startBtn = document.getElementById('start-bot-btn');
            const stopBtn = document.getElementById('stop-bot-btn');
            
            // Update status badge
            if (data.running) {
                statusBadge.className = 'badge bg-success fs-6';
                statusText.textContent = 'Online';
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                statusBadge.className = 'badge bg-danger fs-6';
                statusText.textContent = 'Offline';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
            
            // Update counters
            if (usersCount) usersCount.textContent = data.users || 0;
            if (messagesCount) messagesCount.textContent = data.messages_processed || 0;
        })
        .catch(error => {
            console.error('Error fetching bot status:', error);
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            
            statusBadge.className = 'badge bg-warning fs-6';
            statusText.textContent = 'Error';
        });
}

function startBot() {
    const startBtn = document.getElementById('start-bot-btn');
    const originalText = startBtn.innerHTML;
    
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Starting...';
    
    fetch('/api/bot/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        showNotification(data.message, data.status === 'starting' ? 'info' : 'success');
        setTimeout(updateBotStatus, 2000); // Update status after 2 seconds
    })
    .catch(error => {
        console.error('Error starting bot:', error);
        showNotification('Failed to start bot', 'danger');
    })
    .finally(() => {
        startBtn.innerHTML = originalText;
        startBtn.disabled = false;
    });
}

function stopBot() {
    const stopBtn = document.getElementById('stop-bot-btn');
    const originalText = stopBtn.innerHTML;
    
    stopBtn.disabled = true;
    stopBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Stopping...';
    
    fetch('/api/bot/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        showNotification(data.message, 'info');
        updateBotStatus();
    })
    .catch(error => {
        console.error('Error stopping bot:', error);
        showNotification('Failed to stop bot', 'danger');
    })
    .finally(() => {
        stopBtn.innerHTML = originalText;
        stopBtn.disabled = false;
    });
}

function setupImageProcessing() {
    const form = document.getElementById('image-test-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const resultDiv = document.getElementById('processing-result');
        
        // Show processing indicator
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-hourglass-split"></i> Processing image...
            </div>
        `;
        
        fetch('/api/test-image', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'processed_image.jpg';
            
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> Image processed successfully!
                    <br><br>
                    <a href="${url}" download="processed_image.jpg" class="btn btn-success btn-sm">
                        <i class="bi bi-download"></i> Download Result
                    </a>
                </div>
            `;
            
            // Auto-click to download
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Clean up URL after a delay
            setTimeout(() => window.URL.revokeObjectURL(url), 1000);
        })
        .catch(error => {
            console.error('Error processing image:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> Error: ${error.error || 'Failed to process image'}
                </div>
            `;
        });
    });
}

function checkBotToken() {
    // This would normally check if the token is set
    // For now, we'll just show a placeholder
    const tokenStatus = document.getElementById('token-status');
    if (tokenStatus) {
        // This is just a visual indicator
        tokenStatus.innerHTML = '<span class="badge bg-warning">Check Environment</span>';
    }
}

function checkAIStatus() {
    fetch('/api/ai-status')
        .then(response => response.json())
        .then(data => {
            const aiStatusDiv = document.getElementById('ai-api-status');
            if (aiStatusDiv) {
                let statusHTML = '<div class="row text-center">';
                
                // Remove.bg status
                const removebgStatus = data.removebg.available ? 
                    '<span class="badge bg-success">Connected</span>' : 
                    '<span class="badge bg-warning">API Key Needed</span>';
                statusHTML += `<div class="col-6"><small><strong>Remove.bg:</strong><br>${removebgStatus}</small></div>`;
                
                // PhotoRoom status  
                const photoroomStatus = data.photoroom.available ? 
                    '<span class="badge bg-success">Connected</span>' : 
                    '<span class="badge bg-warning">API Key Needed</span>';
                statusHTML += `<div class="col-6"><small><strong>PhotoRoom:</strong><br>${photoroomStatus}</small></div>`;
                
                statusHTML += '</div>';
                aiStatusDiv.innerHTML = statusHTML;
            }
        })
        .catch(error => {
            console.error('Error fetching AI status:', error);
            const aiStatusDiv = document.getElementById('ai-api-status');
            if (aiStatusDiv) {
                aiStatusDiv.innerHTML = '<small class="text-danger">Error loading AI status</small>';
            }
        });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
});
