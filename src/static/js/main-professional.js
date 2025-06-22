/**
 * JavaScript Principal - MOEDOR AO VIVO
 * Comunicação em tempo real com WebSocket
 */

class MoedorAoVivo {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentLive = null;
        this.cameras = [];
        this.messages = [];
        
        this.init();
    }
    
    init() {
        console.log('🎬 Inicializando MOEDOR AO VIVO...');
        
        // Conectar WebSocket
        this.connectWebSocket();
        
        // Configurar formulário de mensagem
        this.setupMessageForm();
        
        // Carregar dados iniciais
        this.loadInitialData();
        
        // Configurar atualizações automáticas
        this.setupAutoUpdates();
        
        console.log('✅ MOEDOR AO VIVO inicializado com sucesso');
    }
    
    connectWebSocket() {
        try {
            console.log('🔌 Conectando WebSocket...');
            
            // Conectar ao Socket.IO
            this.socket = io();
            
            // Eventos de conexão
            this.socket.on('connect', () => {
                console.log('✅ WebSocket conectado');
                this.isConnected = true;
                this.updateConnectionStatus('Conectado');
            });
            
            this.socket.on('disconnect', () => {
                console.log('❌ WebSocket desconectado');
                this.isConnected = false;
                this.updateConnectionStatus('Desconectado');
            });
            
            // Eventos de live
            this.socket.on('live_updated', (data) => {
                console.log('📺 Live atualizada via WebSocket:', data);
                this.updateLiveDisplay(data);
            });
            
            this.socket.on('live_ended', () => {
                console.log('🔴 Live finalizada via WebSocket');
                this.clearLiveDisplay();
            });
            
            // Eventos de mensagens
            this.socket.on('new_message', (data) => {
                console.log('💬 Nova mensagem via WebSocket:', data);
                this.addMessageToList(data);
            });
            
            // Eventos de câmeras
            this.socket.on('cameras_updated', (data) => {
                console.log('📹 Câmeras atualizadas via WebSocket:', data);
                this.updateCamerasDisplay(data.cameras);
            });
            
        } catch (error) {
            console.error('❌ Erro ao conectar WebSocket:', error);
            this.updateConnectionStatus('Erro de conexão');
        }
    }
    
    async loadInitialData() {
        console.log('📊 Carregando dados iniciais...');
        
        try {
            // Carregar status da live
            await this.loadLiveStatus();
            
            // Carregar câmeras
            await this.loadCameras();
            
            // Carregar mensagens
            await this.loadMessages();
            
            console.log('✅ Dados iniciais carregados');
            
        } catch (error) {
            console.error('❌ Erro ao carregar dados iniciais:', error);
        }
    }
    
    async loadLiveStatus() {
        try {
            const response = await fetch('/api/live/status');
            const data = await response.json();
            
            if (data.success && data.live_session) {
                console.log('📺 Live ativa encontrada:', data.live_session);
                this.updateLiveDisplay(data.live_session);
            } else {
                console.log('📺 Nenhuma live ativa');
                this.clearLiveDisplay();
            }
            
        } catch (error) {
            console.error('❌ Erro ao carregar status da live:', error);
        }
    }
    
    async loadCameras() {
        try {
            const response = await fetch('/api/cameras');
            const data = await response.json();
            
            if (data.success) {
                console.log('📹 Câmeras carregadas:', data.cameras);
                this.updateCamerasDisplay(data.cameras);
            }
            
        } catch (error) {
            console.error('❌ Erro ao carregar câmeras:', error);
        }
    }
    
    async loadMessages() {
        try {
            const response = await fetch('/api/messages');
            const data = await response.json();
            
            if (data.success) {
                console.log('💬 Mensagens carregadas:', data.messages);
                this.updateMessagesDisplay(data.messages);
            }
            
        } catch (error) {
            console.error('❌ Erro ao carregar mensagens:', error);
        }
    }
    
    updateLiveDisplay(liveData) {
        console.log('🎬 Atualizando display da live:', liveData);
        
        // Atualizar título
        const titleElement = document.getElementById('liveTitle');
        if (titleElement) {
            titleElement.textContent = liveData.title || 'MOEDOR AO VIVO';
        }
        
        // Atualizar status
        const statusElement = document.getElementById('liveStatus');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="status-dot status-online"></div>
                <span>AO VIVO</span>
            `;
        }
        
        // Atualizar player
        const containerElement = document.getElementById('liveContainer');
        if (containerElement && liveData.youtube_url) {
            // Extrair ID do YouTube
            const videoId = this.extractYouTubeId(liveData.youtube_url);
            
            if (videoId) {
                containerElement.innerHTML = `
                    <div class="live-player-active">
                        <iframe 
                            src="https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1" 
                            frameborder="0" 
                            allowfullscreen
                            allow="autoplay; encrypted-media"
                            class="youtube-iframe">
                        </iframe>
                    </div>
                `;
            } else {
                // URL personalizada
                containerElement.innerHTML = `
                    <div class="live-player-active">
                        <iframe 
                            src="${liveData.youtube_url}" 
                            frameborder="0" 
                            allowfullscreen
                            class="youtube-iframe">
                        </iframe>
                    </div>
                `;
            }
        }
        
        this.currentLive = liveData;
    }
    
    clearLiveDisplay() {
        console.log('🔴 Limpando display da live');
        
        // Atualizar status
        const statusElement = document.getElementById('liveStatus');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="status-dot"></div>
                <span>OFFLINE</span>
            `;
        }
        
        // Limpar player
        const containerElement = document.getElementById('liveContainer');
        if (containerElement) {
            containerElement.innerHTML = `
                <div class="live-placeholder">
                    <div class="placeholder-icon">📺</div>
                    <div class="placeholder-text">LIVE EM BREVE...</div>
                    <div class="placeholder-subtitle">Aguarde o início da transmissão</div>
                </div>
            `;
        }
        
        this.currentLive = null;
    }
    
    updateCamerasDisplay(cameras) {
        console.log('📹 Atualizando display das câmeras:', cameras);
        
        const gridElement = document.getElementById('camerasGrid');
        if (!gridElement) return;
        
        if (!cameras || cameras.length === 0) {
            gridElement.innerHTML = `
                <div class="no-cameras">
                    <div class="no-cameras-icon">📹</div>
                    <p>Nenhuma câmera configurada</p>
                </div>
            `;
            return;
        }
        
        gridElement.innerHTML = cameras.map(camera => `
            <div class="camera-item">
                <div class="rtsp-player" id="player-${camera.id}">
                    <iframe 
                        class="rtsp-iframe"
                        src="http://localhost:8081/stream/${camera.id}"
                        frameborder="0"
                        allowfullscreen
                        loading="lazy"
                    ></iframe>
                </div>
            </div>
        `).join('');
        
        this.cameras = cameras;
    }
    
    getRTSPProxyUrl(rtspUrl) {
        // Converter RTSP para URL de proxy HLS
        // Por enquanto, usar URL de teste
        return `data:video/mp4;base64,`;
    }
    
    initializePlayer(cameraId, rtspUrl) {
        console.log(`🎬 Inicializando player para câmera ${cameraId}`);
        
        const video = document.querySelector(`#player-${cameraId} video`);
        if (!video) return;
        
        // Tentar usar WebRTC ou HLS.js para RTSP
        if (this.canPlayHLS()) {
            this.setupHLSPlayer(video, rtspUrl);
        } else {
            this.setupWebRTCPlayer(video, rtspUrl);
        }
    }
    
    canPlayHLS() {
        const video = document.createElement('video');
        return video.canPlayType('application/vnd.apple.mpegurl') !== '';
    }
    
    setupHLSPlayer(video, rtspUrl) {
        // Implementar HLS.js para reprodução
        console.log('🎥 Configurando player HLS para:', rtspUrl);
        
        // Por enquanto, mostrar placeholder
        video.poster = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMjIyIi8+PHRleHQgeD0iNTAlIiB5PSI0MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzM0OThkYiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfk7kgQ8OibWVyYSBBdGl2YTwvdGV4dD48dGV4dCB4PSI1MCUiIHk9IjYwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Q2xpcXVlIHBhcmEgcmVwcm9kdXppcjwvdGV4dD48L3N2Zz4=";
    }
    
    setupWebRTCPlayer(video, rtspUrl) {
        // Implementar WebRTC para reprodução
        console.log('🌐 Configurando player WebRTC para:', rtspUrl);
        
        // Por enquanto, mostrar placeholder
        video.poster = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMjIyIi8+PHRleHQgeD0iNTAlIiB5PSI0MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzM0OThkYiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfk7kgQ8OibWVyYSBBdGl2YTwvdGV4dD48dGV4dCB4PSI1MCUiIHk9IjYwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Q2xpcXVlIHBhcmEgcmVwcm9kdXppcjwvdGV4dD48L3N2Zz4=";
    }
    
    playCamera(cameraId, rtspUrl) {
        console.log(`▶️ Reproduzindo câmera ${cameraId}:`, rtspUrl);
        
        const video = document.querySelector(`#player-${cameraId} video`);
        const overlay = document.querySelector(`#player-${cameraId} .player-overlay`);
        
        if (video && overlay) {
            overlay.style.display = 'none';
            
            // Tentar reproduzir
            video.play().catch(error => {
                console.error('❌ Erro ao reproduzir:', error);
                overlay.style.display = 'flex';
                
                // Mostrar opção de abrir no VLC
                overlay.innerHTML = `
                    <div class="error-message">
                        <p>⚠️ Não foi possível reproduzir</p>
                        <a href="${rtspUrl}" class="vlc-link">📺 Abrir no VLC</a>
                    </div>
                `;
            });
        }
    }
    
    updateMessagesDisplay(messages) {
        console.log('💬 Atualizando display das mensagens:', messages);
        
        const listElement = document.getElementById('messagesList');
        if (!listElement) return;
        
        if (!messages || messages.length === 0) {
            listElement.innerHTML = `
                <div class="no-messages">
                    <p>Nenhuma mensagem ainda</p>
                    <small>Seja o primeiro a enviar uma mensagem!</small>
                </div>
            `;
            return;
        }
        
        listElement.innerHTML = messages.map(message => `
            <div class="message-item">
                <div class="message-header">
                    <span class="message-author">${message.name}</span>
                    <span class="message-time">${this.formatTime(message.created_at)}</span>
                </div>
                <div class="message-content">${message.content}</div>
            </div>
        `).join('');
        
        this.messages = messages;
    }
    
    addMessageToList(message) {
        console.log('💬 Adicionando nova mensagem:', message);
        
        const listElement = document.getElementById('messagesList');
        if (!listElement) return;
        
        // Remover placeholder se existir
        const noMessages = listElement.querySelector('.no-messages');
        if (noMessages) {
            noMessages.remove();
        }
        
        // Adicionar nova mensagem no topo
        const messageElement = document.createElement('div');
        messageElement.className = 'message-item message-new';
        messageElement.innerHTML = `
            <div class="message-header">
                <span class="message-author">${message.name}</span>
                <span class="message-time">agora</span>
            </div>
            <div class="message-content">${message.content}</div>
        `;
        
        listElement.insertBefore(messageElement, listElement.firstChild);
        
        // Remover animação após um tempo
        setTimeout(() => {
            messageElement.classList.remove('message-new');
        }, 2000);
        
        // Manter apenas as últimas 20 mensagens
        const messages = listElement.querySelectorAll('.message-item');
        if (messages.length > 20) {
            messages[messages.length - 1].remove();
        }
    }
    
    setupMessageForm() {
        const form = document.getElementById('messageForm');
        const nameInput = document.getElementById('userName');
        const messageInput = document.getElementById('userMessage');
        const submitButton = document.getElementById('submitMessage');
        const charCounter = document.getElementById('charCounter');
        
        if (!form || !nameInput || !messageInput || !submitButton) {
            console.warn('⚠️ Elementos do formulário não encontrados');
            return;
        }
        
        // Contador de caracteres
        messageInput.addEventListener('input', () => {
            const remaining = 250 - messageInput.value.length;
            charCounter.textContent = `${remaining} caracteres restantes`;
            charCounter.style.color = remaining < 20 ? '#e74c3c' : '#7f8c8d';
        });
        
        // Envio do formulário
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = nameInput.value.trim();
            const content = messageInput.value.trim();
            
            if (!name || !content) {
                alert('Por favor, preencha seu nome e mensagem');
                return;
            }
            
            try {
                submitButton.disabled = true;
                submitButton.textContent = 'Enviando...';
                
                const response = await fetch('/api/messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        content: content
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    console.log('✅ Mensagem enviada com sucesso');
                    messageInput.value = '';
                    charCounter.textContent = '250 caracteres restantes';
                    charCounter.style.color = '#7f8c8d';
                } else {
                    console.error('❌ Erro ao enviar mensagem:', data.error);
                    alert('Erro ao enviar mensagem: ' + data.error);
                }
                
            } catch (error) {
                console.error('❌ Erro ao enviar mensagem:', error);
                alert('Erro ao enviar mensagem');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = 'Enviar Mensagem';
            }
        });
    }
    
    setupAutoUpdates() {
        // Atualizar dados a cada 30 segundos como backup
        setInterval(() => {
            if (!this.isConnected) {
                console.log('🔄 WebSocket desconectado, atualizando via API...');
                this.loadInitialData();
            }
        }, 30000);
    }
    
    updateConnectionStatus(status) {
        const statusElements = document.querySelectorAll('.connection-status');
        statusElements.forEach(element => {
            element.textContent = status;
            element.className = `connection-status ${status.toLowerCase().replace(' ', '-')}`;
        });
    }
    
    extractYouTubeId(url) {
        const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'agora';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`;
        
        return date.toLocaleDateString('pt-BR');
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.moedorAoVivo = new MoedorAoVivo();
});

// Exportar para uso global
window.MoedorAoVivo = MoedorAoVivo;

