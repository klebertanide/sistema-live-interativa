/**
 * JavaScript Principal - Big Brother Moído
 * Gerencia WebSocket, formulários e interações
 */

class LiveSystem {
    constructor() {
        this.socket = null;
        this.currentPoll = null;
        this.userVoted = false;
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.initEventListeners();
        this.loadInitialData();
    }
    
    // ===== WEBSOCKET =====
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('🔌 Conectado ao servidor');
            this.showStatus('Conectado!', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Desconectado do servidor');
            this.showStatus('Conexão perdida. Tentando reconectar...', 'error');
        });
        
        // Eventos de mensagem
        this.socket.on('message_sent', (data) => {
            this.showStatus('Mensagem enviada com sucesso!', 'success');
            this.resetForm();
        });
        
        this.socket.on('message_error', (data) => {
            this.showStatus(data.error, 'error');
            this.enableForm();
        });
        
        // Eventos de enquete
        this.socket.on('new_poll', (data) => {
            this.displayPoll(data);
        });
        
        this.socket.on('poll_vote_update', (data) => {
            this.updatePollResults(data);
        });
        
        this.socket.on('poll_ended', (data) => {
            this.showPollResults(data);
        });
        
        // Eventos de câmera
        this.socket.on('camera_added', (data) => {
            this.addCameraToGrid(data);
        });
        
        this.socket.on('camera_removed', (data) => {
            this.removeCameraFromGrid(data.camera_id);
        });
        
        this.socket.on('camera_status_changed', (data) => {
            this.updateCameraStatus(data);
        });
        
        // Eventos de live
        this.socket.on('live_started', (data) => {
            this.updateLiveEmbed(data.youtube_url);
            this.showStatus('Live iniciada!', 'success');
        });
        
        this.socket.on('live_url_updated', (data) => {
            this.updateLiveEmbed(data.youtube_url);
        });
        
        this.socket.on('live_ended', (data) => {
            this.showLiveEnded();
            this.showStatus('Live finalizada', 'info');
        });
    }
    
    // ===== EVENT LISTENERS =====
    initEventListeners() {
        // Formulário de mensagem
        const messageForm = document.getElementById('messageForm');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }
        
        // Contador de caracteres
        const messageTextarea = document.getElementById('userMessage');
        if (messageTextarea) {
            messageTextarea.addEventListener('input', () => this.updateCharCounter());
        }
        
        // Cliques em opções de enquete
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('poll-option')) {
                this.handlePollVote(e.target);
            }
        });
    }
    
    // ===== MENSAGENS =====
    handleMessageSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const name = formData.get('name').trim();
        const message = formData.get('message').trim();
        
        // Validações
        if (!name || name.length > 50) {
            this.showStatus('Nome deve ter entre 1 e 50 caracteres', 'error');
            return;
        }
        
        if (!message || message.length > 250) {
            this.showStatus('Mensagem deve ter entre 1 e 250 caracteres', 'error');
            return;
        }
        
        // Enviar via WebSocket
        this.socket.emit('send_message', {
            name: name,
            content: message
        });
        
        this.disableForm();
        this.showStatus('Enviando mensagem...', 'info');
    }
    
    updateCharCounter() {
        const textarea = document.getElementById('userMessage');
        const counter = document.getElementById('charCount');
        
        if (textarea && counter) {
            const count = textarea.value.length;
            counter.textContent = count;
            
            // Mudar cor quando próximo do limite
            if (count > 200) {
                counter.style.color = 'var(--warning)';
            } else if (count > 240) {
                counter.style.color = 'var(--error)';
            } else {
                counter.style.color = 'var(--text-muted)';
            }
        }
    }
    
    resetForm() {
        const form = document.getElementById('messageForm');
        if (form) {
            form.reset();
            this.updateCharCounter();
        }
        this.enableForm();
    }
    
    disableForm() {
        const submitBtn = document.querySelector('.submit-btn');
        const inputs = document.querySelectorAll('#messageForm input, #messageForm textarea');
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
        }
        
        inputs.forEach(input => input.disabled = true);
    }
    
    enableForm() {
        const submitBtn = document.querySelector('.submit-btn');
        const inputs = document.querySelectorAll('#messageForm input, #messageForm textarea');
        
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Enviar Mensagem';
        }
        
        inputs.forEach(input => input.disabled = false);
    }
    
    // ===== ENQUETES =====
    displayPoll(pollData) {
        this.currentPoll = pollData;
        this.userVoted = false;
        
        const pollSection = document.getElementById('pollSection');
        const pollContent = document.getElementById('pollContent');
        
        if (!pollSection || !pollContent) return;
        
        pollContent.innerHTML = `
            <div class="poll-question">${pollData.question}</div>
            <div class="poll-options">
                <div class="poll-option" data-option="a" data-poll-id="${pollData.id}">
                    ${pollData.option_a}
                </div>
                <div class="poll-option" data-option="b" data-poll-id="${pollData.id}">
                    ${pollData.option_b}
                </div>
            </div>
            <div class="poll-results" style="display: none;">
                <div class="poll-result-item">
                    <div class="poll-result-label">
                        <span>${pollData.option_a}</span>
                        <span class="votes-a">0 votos</span>
                    </div>
                    <div class="poll-result-bar">
                        <div class="poll-result-fill" data-option="a" style="width: 0%"></div>
                    </div>
                </div>
                <div class="poll-result-item">
                    <div class="poll-result-label">
                        <span>${pollData.option_b}</span>
                        <span class="votes-b">0 votos</span>
                    </div>
                    <div class="poll-result-bar">
                        <div class="poll-result-fill" data-option="b" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        
        pollSection.style.display = 'block';
        pollSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    handlePollVote(optionElement) {
        if (this.userVoted || !this.currentPoll) return;
        
        const option = optionElement.dataset.option;
        const pollId = optionElement.dataset.pollId;
        
        this.socket.emit('vote_poll', {
            poll_id: parseInt(pollId),
            option: option
        });
        
        // Marcar como votado
        optionElement.classList.add('voted');
        this.userVoted = true;
        
        // Desabilitar outras opções
        document.querySelectorAll('.poll-option').forEach(el => {
            if (el !== optionElement) {
                el.style.opacity = '0.5';
                el.style.cursor = 'not-allowed';
            }
        });
    }
    
    updatePollResults(data) {
        const totalVotes = data.votes_a + data.votes_b;
        
        if (totalVotes === 0) return;
        
        const percentA = (data.votes_a / totalVotes) * 100;
        const percentB = (data.votes_b / totalVotes) * 100;
        
        // Atualizar barras de progresso
        const fillA = document.querySelector('.poll-result-fill[data-option="a"]');
        const fillB = document.querySelector('.poll-result-fill[data-option="b"]');
        
        if (fillA) fillA.style.width = `${percentA}%`;
        if (fillB) fillB.style.width = `${percentB}%`;
        
        // Atualizar contadores
        const votesA = document.querySelector('.votes-a');
        const votesB = document.querySelector('.votes-b');
        
        if (votesA) votesA.textContent = `${data.votes_a} votos`;
        if (votesB) votesB.textContent = `${data.votes_b} votos`;
        
        // Mostrar resultados se usuário votou
        if (this.userVoted) {
            const resultsDiv = document.querySelector('.poll-results');
            if (resultsDiv) {
                resultsDiv.style.display = 'block';
            }
        }
    }
    
    showPollResults(data) {
        const pollContent = document.getElementById('pollContent');
        if (!pollContent) return;
        
        const totalVotes = data.votes_a + data.votes_b;
        const winner = data.winner;
        
        let winnerText = '';
        if (winner === 'tie') {
            winnerText = 'Empate!';
        } else {
            const winnerOption = winner === 'a' ? data.option_a : data.option_b;
            winnerText = `Vencedor: ${winnerOption}`;
        }
        
        pollContent.innerHTML += `
            <div class="poll-final-result">
                <h4>${winnerText}</h4>
                <p>Total de votos: ${totalVotes}</p>
            </div>
        `;
        
        // Ocultar enquete após 10 segundos
        setTimeout(() => {
            const pollSection = document.getElementById('pollSection');
            if (pollSection) {
                pollSection.style.display = 'none';
            }
        }, 10000);
    }
    
    // ===== CÂMERAS =====
    addCameraToGrid(cameraData) {
        const grid = document.getElementById('camerasGrid');
        if (!grid) return;
        
        // Remover mensagem "nenhuma câmera"
        const noCamera = grid.querySelector('.no-cameras');
        if (noCamera) {
            noCamera.remove();
        }
        
        const cameraElement = document.createElement('div');
        cameraElement.className = 'camera-item';
        cameraElement.dataset.cameraId = cameraData.id;
        
        cameraElement.innerHTML = `
            <div class="camera-container">
                <div class="camera-placeholder">
                    <div class="camera-info">
                        <span class="camera-name">${cameraData.name || 'Câmera ' + cameraData.id}</span>
                        <span class="camera-status">● AO VIVO</span>
                    </div>
                </div>
            </div>
        `;
        
        grid.appendChild(cameraElement);
    }
    
    removeCameraFromGrid(cameraId) {
        const cameraElement = document.querySelector(`[data-camera-id="${cameraId}"]`);
        if (cameraElement) {
            cameraElement.remove();
        }
        
        // Verificar se não há mais câmeras
        const grid = document.getElementById('camerasGrid');
        if (grid && grid.children.length === 0) {
            grid.innerHTML = '<div class="no-cameras"><p>Nenhuma câmera configurada</p></div>';
        }
    }
    
    updateCameraStatus(data) {
        const cameraElement = document.querySelector(`[data-camera-id="${data.camera_id}"]`);
        if (!cameraElement) return;
        
        const statusElement = cameraElement.querySelector('.camera-status');
        if (statusElement) {
            if (data.active) {
                statusElement.textContent = '● AO VIVO';
                statusElement.style.color = 'var(--success)';
                cameraElement.style.opacity = '1';
            } else {
                statusElement.textContent = '● OFFLINE';
                statusElement.style.color = 'var(--error)';
                cameraElement.style.opacity = '0.5';
            }
        }
    }
    
    // ===== LIVE =====
    updateLiveEmbed(youtubeUrl) {
        const liveContainer = document.querySelector('.live-container');
        if (!liveContainer || !youtubeUrl) return;
        
        liveContainer.innerHTML = `
            <div class="live-embed">
                <iframe 
                    src="${youtubeUrl}?autoplay=1&mute=0" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
        `;
    }
    
    showLiveEnded() {
        const liveContainer = document.querySelector('.live-container');
        if (!liveContainer) return;
        
        liveContainer.innerHTML = `
            <div class="live-placeholder">
                <div class="placeholder-content">
                    <h3>Live finalizada</h3>
                    <p>Obrigado por participar!</p>
                </div>
            </div>
        `;
    }
    
    // ===== UTILITÁRIOS =====
    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('messageStatus');
        if (!statusElement) return;
        
        statusElement.textContent = message;
        statusElement.className = `message-status ${type}`;
        statusElement.style.display = 'block';
        
        // Ocultar após 5 segundos
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 5000);
    }
    
    loadInitialData() {
        // Carregar enquete ativa
        fetch('/api/polls/active')
            .then(response => response.json())
            .then(data => {
                if (data.id) {
                    this.displayPoll(data);
                }
            })
            .catch(error => console.log('Nenhuma enquete ativa'));
        
        // Carregar screenshots
        this.loadScreenshots();
    }
    
    loadScreenshots() {
        fetch('/api/screenshots?limit=12')
            .then(response => response.json())
            .then(screenshots => {
                const grid = document.getElementById('screenshotsGrid');
                if (!grid || screenshots.length === 0) return;
                
                grid.innerHTML = '';
                
                screenshots.forEach(screenshot => {
                    const item = document.createElement('div');
                    item.className = 'screenshot-item';
                    
                    item.innerHTML = `
                        <div class="screenshot-polaroid">
                            <img src="/static/screenshots/${screenshot.filename}" 
                                 alt="Screenshot" 
                                 class="screenshot-image">
                        </div>
                    `;
                    
                    grid.appendChild(item);
                });
            })
            .catch(error => console.log('Erro ao carregar screenshots:', error));
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    new LiveSystem();
});

