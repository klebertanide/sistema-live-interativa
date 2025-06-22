/**
 * JavaScript do Painel Administrativo - Big Brother Moído
 * VERSÃO CORRIGIDA - Funcionalidade do botão INICIAR LIVE
 */

class AdminPanel {
    constructor() {
        this.socket = null;
        this.startTime = Date.now();
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.initEventListeners();
        this.startSystemMonitoring();
        console.log('🎛️ Painel Admin inicializado');
    }
    
    // ===== WEBSOCKET =====
    initSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔌 Admin conectado ao servidor');
                this.updateWebSocketStatus('Conectado');
                this.showStatus('Conectado ao servidor', 'success');
            });
            
            this.socket.on('disconnect', () => {
                console.log('❌ Admin desconectado do servidor');
                this.updateWebSocketStatus('Desconectado');
                this.showStatus('Conexão perdida. Tentando reconectar...', 'error');
            });
            
            // Eventos de usuários
            this.socket.on('user_count_update', (data) => {
                this.updateOnlineCount(data.count);
            });
            
            // Eventos de mensagens
            this.socket.on('new_message', (data) => {
                this.addNewMessage(data);
            });
            
        } catch (error) {
            console.log('⚠️ WebSocket não disponível, usando apenas HTTP');
            this.updateWebSocketStatus('HTTP Only');
        }
    }
    
    // ===== EVENT LISTENERS =====
    initEventListeners() {
        console.log('🎯 Configurando event listeners...');
        
        // Controles de live - CORRIGIDO
        const startLiveBtn = document.getElementById('startLiveBtn');
        const endLiveBtn = document.getElementById('endLiveBtn');
        const updateUrlBtn = document.getElementById('updateUrlBtn');
        
        if (startLiveBtn) {
            console.log('✅ Botão INICIAR LIVE encontrado');
            startLiveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🚀 Botão INICIAR LIVE clicado');
                this.startLive();
            });
        } else {
            console.log('❌ Botão INICIAR LIVE não encontrado');
        }
        
        if (endLiveBtn) {
            console.log('✅ Botão FINALIZAR LIVE encontrado');
            endLiveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.endLive();
            });
        }
        
        if (updateUrlBtn) {
            console.log('✅ Botão ATUALIZAR URL encontrado');
            updateUrlBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.updateLiveUrl();
            });
        }
        
        // Controles de câmera
        const addCameraBtn = document.getElementById('addCameraBtn');
        if (addCameraBtn) {
            console.log('✅ Botão ADICIONAR CÂMERA encontrado');
            addCameraBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addCamera();
            });
        }
        
        // Botões de câmera (delegação de eventos)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-camera-btn')) {
                e.preventDefault();
                this.toggleCamera(e.target.dataset.cameraId);
            } else if (e.target.classList.contains('remove-camera-btn')) {
                e.preventDefault();
                this.removeCamera(e.target.dataset.cameraId);
            }
        });
        
        // Controles do Whisper
        const generateLyricsBtn = document.getElementById('generateLyricsBtn');
        if (generateLyricsBtn) {
            generateLyricsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.generateLyrics();
            });
        }
        
        const copyLyricsBtn = document.getElementById('copyLyricsBtn');
        if (copyLyricsBtn) {
            copyLyricsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.copyLyrics();
            });
        }
        
        console.log('✅ Event listeners configurados');
    }
    
    // ===== CONTROLES DE LIVE - CORRIGIDO =====
    startLive() {
        console.log('🎬 Iniciando live...');
        
        const title = document.getElementById('liveTitle').value.trim();
        const youtubeUrl = document.getElementById('youtubeUrl').value.trim();
        
        console.log('📝 Dados:', { title, youtubeUrl });
        
        // Validações
        if (!title) {
            this.showStatus('Título da live é obrigatório', 'error');
            return;
        }
        
        if (!youtubeUrl) {
            this.showStatus('URL do YouTube é obrigatória', 'error');
            return;
        }
        
        // Validar URL do YouTube
        if (!this.isValidYouTubeUrl(youtubeUrl)) {
            this.showStatus('URL do YouTube inválida. Use o formato embed: https://www.youtube.com/embed/VIDEO_ID', 'error');
            return;
        }
        
        // Desabilitar botão durante o processo
        const btn = document.getElementById('startLiveBtn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Iniciando...';
        }
        
        // Fazer requisição para a API correta
        fetch('/api/live/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                youtube_url: youtubeUrl
            })
        })
        .then(response => {
            console.log('📡 Resposta recebida:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📊 Dados da resposta:', data);
            
            if (data.success) {
                this.showStatus('Live iniciada com sucesso!', 'success');
                this.updateLiveStatus('AO VIVO');
                
                // Recarregar página após 2 segundos
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showStatus(data.error || 'Erro ao iniciar live', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro na requisição:', error);
            this.showStatus('Erro de conexão com o servidor', 'error');
        })
        .finally(() => {
            // Reabilitar botão
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Iniciar Live';
            }
        });
    }
    
    endLive() {
        if (!confirm('Tem certeza que deseja finalizar a live?')) {
            return;
        }
        
        console.log('🛑 Finalizando live...');
        
        const btn = document.getElementById('endLiveBtn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Finalizando...';
        }
        
        fetch('/api/live/end', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showStatus('Live finalizada com sucesso!', 'success');
                this.updateLiveStatus('OFFLINE');
                
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showStatus(data.error || 'Erro ao finalizar live', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro:', error);
            this.showStatus('Erro de conexão', 'error');
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Finalizar Live';
            }
        });
    }
    
    updateLiveUrl() {
        const youtubeUrl = document.getElementById('youtubeUrl').value.trim();
        const title = document.getElementById('liveTitle').value.trim() || 'Big Brother Moído';
        
        if (!youtubeUrl) {
            this.showStatus('URL do YouTube é obrigatória', 'error');
            return;
        }
        
        if (!this.isValidYouTubeUrl(youtubeUrl)) {
            this.showStatus('URL do YouTube inválida', 'error');
            return;
        }
        
        console.log('🔄 Atualizando URL da live...');
        
        fetch('/api/live/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                youtube_url: youtubeUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showStatus('URL da live atualizada!', 'success');
            } else {
                this.showStatus(data.error || 'Erro ao atualizar URL', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro:', error);
            this.showStatus('Erro de conexão', 'error');
        });
    }
    
    // ===== CONTROLES DE CÂMERA =====
    addCamera() {
        const url = document.getElementById('cameraUrl').value.trim();
        
        if (!url) {
            this.showStatus('URL da câmera é obrigatória', 'error');
            return;
        }
        
        console.log('📹 Adicionando câmera:', { url });
        
        fetch('/api/cameras', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showStatus('Câmera adicionada com sucesso!', 'success');
                
                // Limpar formulário
                document.getElementById('cameraUrl').value = '';
                
                // Recarregar página
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showStatus(data.error || 'Erro ao adicionar câmera', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro ao adicionar câmera:', error);
            this.showStatus('Erro de conexão', 'error');
        });
    }
    
    removeCamera(cameraId) {
        if (!confirm('Tem certeza que deseja ocultar esta câmera?')) {
            return;
        }
        
        console.log('📹 Ocultando câmera:', cameraId);
        
        fetch(`/api/cameras/${cameraId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showStatus('Câmera ocultada com sucesso!', 'success');
                
                // Recarregar página
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showStatus(data.error || 'Erro ao ocultar câmera', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro ao ocultar câmera:', error);
            this.showStatus('Erro de conexão', 'error');
        });
    }
    
    toggleCamera(cameraId) {
        console.log('🔄 Alternando status da câmera:', cameraId);
        
        fetch(`/api/cameras/${cameraId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showStatus('Status da câmera atualizado', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showStatus('Erro ao atualizar câmera', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro:', error);
            this.showStatus('Erro de conexão', 'error');
        });
    }
    
    removeCamera(cameraId) {
        if (!confirm('Tem certeza que deseja remover esta câmera?')) {
            return;
        }
        
        console.log('🗑️ Removendo câmera:', cameraId);
        
        fetch(`/api/cameras/${cameraId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showStatus('Câmera removida com sucesso!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showStatus('Erro ao remover câmera', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro:', error);
            this.showStatus('Erro de conexão', 'error');
        });
    }
    
    // ===== CONTROLES DO WHISPER =====
    generateLyrics() {
        const btn = document.getElementById('generateLyricsBtn');
        const originalText = btn.textContent;
        
        btn.disabled = true;
        btn.textContent = 'Gerando...';
        
        fetch('/api/whisper/generate-lyrics', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showLyrics(data.lyrics);
                this.showStatus('Letra gerada com sucesso!', 'success');
            } else {
                this.showStatus(data.error || 'Erro ao gerar letra', 'error');
            }
        })
        .catch(error => {
            console.error('❌ Erro:', error);
            this.showStatus('Erro de conexão', 'error');
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = originalText;
        });
    }
    
    showLyrics(lyrics) {
        const lyricsOutput = document.getElementById('lyricsOutput');
        const lyricsContent = document.getElementById('lyricsContent');
        
        if (lyricsOutput && lyricsContent) {
            lyricsContent.textContent = lyrics;
            lyricsOutput.style.display = 'block';
            lyricsOutput.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    copyLyrics() {
        const lyricsContent = document.getElementById('lyricsContent');
        if (lyricsContent) {
            navigator.clipboard.writeText(lyricsContent.textContent)
                .then(() => {
                    this.showStatus('Letra copiada para a área de transferência!', 'success');
                })
                .catch(() => {
                    this.showStatus('Erro ao copiar letra', 'error');
                });
        }
    }
    
    // ===== ATUALIZAÇÕES DE UI =====
    updateOnlineCount(count) {
        const element = document.getElementById('onlineCount');
        if (element) {
            element.textContent = count;
        }
    }
    
    updateLiveStatus(status) {
        const element = document.getElementById('liveStatus');
        if (element) {
            element.textContent = status;
            element.className = status === 'AO VIVO' ? 'stat-value status-live' : 'stat-value status-offline';
        }
    }
    
    updateWebSocketStatus(status) {
        const element = document.getElementById('websocketStatus');
        if (element) {
            element.textContent = status;
        }
    }
    
    addNewMessage(messageData) {
        const messagesList = document.getElementById('recentMessages');
        if (!messagesList) return;
        
        // Remover mensagem "nenhuma mensagem"
        const noMessages = messagesList.querySelector('.no-messages');
        if (noMessages) {
            noMessages.remove();
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message-item';
        
        const timestamp = new Date(messageData.timestamp);
        const timeString = timestamp.toLocaleTimeString('pt-BR');
        
        messageElement.innerHTML = `
            <div class="message-header">
                <strong>${messageData.name}</strong>
                <span class="message-time">${timeString}</span>
            </div>
            <div class="message-content">${messageData.content}</div>
        `;
        
        // Adicionar no topo da lista
        messagesList.insertBefore(messageElement, messagesList.firstChild);
        
        // Limitar a 20 mensagens
        const messages = messagesList.querySelectorAll('.message-item');
        if (messages.length > 20) {
            messages[messages.length - 1].remove();
        }
    }
    
    // ===== MONITORAMENTO DO SISTEMA =====
    startSystemMonitoring() {
        // Atualizar uptime a cada segundo
        setInterval(() => {
            this.updateUptime();
        }, 1000);
        
        // Verificar status do sistema a cada 30 segundos
        setInterval(() => {
            this.checkSystemStatus();
        }, 30000);
    }
    
    updateUptime() {
        const uptimeElement = document.getElementById('systemUptime');
        if (uptimeElement) {
            const uptime = Date.now() - this.startTime;
            const hours = Math.floor(uptime / (1000 * 60 * 60));
            const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((uptime % (1000 * 60)) / 1000);
            
            uptimeElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    checkSystemStatus() {
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    // Sistema funcionando normalmente
                }
            })
            .catch(error => {
                console.log('⚠️ Erro ao verificar status:', error);
            });
    }
    
    // ===== UTILITÁRIOS =====
    isValidYouTubeUrl(url) {
        // Aceitar tanto URLs embed quanto URLs normais
        const embedRegex = /^https:\/\/(www\.)?youtube\.com\/embed\/[a-zA-Z0-9_-]+/;
        const watchRegex = /^https:\/\/(www\.)?youtube\.com\/watch\?v=[a-zA-Z0-9_-]+/;
        const liveRegex = /^https:\/\/(www\.)?youtube\.com\/live\/[a-zA-Z0-9_-]+/;
        
        return embedRegex.test(url) || watchRegex.test(url) || liveRegex.test(url);
    }
    
    showStatus(message, type = 'info') {
        console.log(`📢 Status [${type}]:`, message);
        
        const statusElement = document.getElementById('adminStatus');
        if (!statusElement) {
            // Criar elemento de status se não existir
            const statusDiv = document.createElement('div');
            statusDiv.id = 'adminStatus';
            statusDiv.className = 'admin-status';
            document.body.appendChild(statusDiv);
        }
        
        const status = document.getElementById('adminStatus');
        status.textContent = message;
        status.className = `admin-status ${type}`;
        status.style.display = 'block';
        
        // Ocultar após 5 segundos
        setTimeout(() => {
            status.style.display = 'none';
        }, 5000);
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando Painel Admin...');
    new AdminPanel();
});

// Debug: Verificar se elementos existem
window.addEventListener('load', () => {
    console.log('🔍 Verificando elementos da página...');
    
    const elements = [
        'startLiveBtn',
        'endLiveBtn', 
        'updateUrlBtn',
        'liveTitle',
        'youtubeUrl',
        'addCameraBtn',
        'cameraUrl',
        'cameraName'
    ];
    
    elements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`${element ? '✅' : '❌'} ${id}:`, element);
    });
});

