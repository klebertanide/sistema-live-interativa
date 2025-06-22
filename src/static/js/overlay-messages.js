/**
 * JavaScript do Overlay de Mensagens FINAL - MOEDOR AO VIVO
 * Mostra mensagens REAIS do sistema, não aleatórias
 */

class MessageOverlay {
    constructor() {
        this.socket = null;
        this.messageQueue = [];
        this.isDisplaying = false;
        this.displayDuration = 8000; // 8 segundos
        this.fadeDuration = 500; // 0.5 segundos
        this.messageCount = 0;
        this.displayedMessages = new Set(); // Controle de mensagens já exibidas
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.startMessageProcessor();
        this.pollForRealMessages(); // Buscar mensagens reais do sistema
    }
    
    // ===== WEBSOCKET PARA MENSAGENS REAIS =====
    initSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 5000,
                forceNew: true
            });
            
            this.socket.on('connect', () => {
                console.log('🔌 Overlay de mensagens conectado');
                this.socket.emit('join_room', 'overlay_messages');
            });
            
            this.socket.on('disconnect', () => {
                console.log('❌ Overlay de mensagens desconectado');
            });
            
            // Escutar mensagens REAIS do sistema
            this.socket.on('new_message', (messageData) => {
                console.log('📨 Nova mensagem REAL recebida:', messageData);
                this.addRealMessageToQueue(messageData);
            });
            
            // Escutar mensagens do chat principal
            this.socket.on('message', (messageData) => {
                console.log('💬 Mensagem do chat principal:', messageData);
                this.addRealMessageToQueue(messageData);
            });
            
            // Escutar mensagens enviadas via formulário
            this.socket.on('user_message', (messageData) => {
                console.log('👤 Mensagem de usuário:', messageData);
                this.addRealMessageToQueue(messageData);
            });
            
        } catch (error) {
            console.error('❌ Erro ao conectar WebSocket:', error);
        }
    }
    
    // ===== BUSCAR MENSAGENS REAIS DO BANCO =====
    pollForRealMessages() {
        // Buscar mensagens reais a cada 2 segundos
        setInterval(() => {
            this.fetchRealMessages();
        }, 2000);
        
        // Busca inicial
        this.fetchRealMessages();
    }
    
    async fetchRealMessages() {
        try {
            const response = await fetch('/api/messages/recent?limit=5');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.messages) {
                    data.messages.forEach(message => {
                        // Verificar se já foi exibida
                        if (!this.displayedMessages.has(message.id)) {
                            this.addRealMessageToQueue(message);
                            this.displayedMessages.add(message.id);
                        }
                    });
                }
            }
        } catch (error) {
            console.log('⚠️ Erro ao buscar mensagens reais:', error.message);
        }
    }
    
    // ===== PROCESSAMENTO DE MENSAGENS REAIS =====
    addRealMessageToQueue(messageData) {
        // Validar dados da mensagem
        if (!messageData || (!messageData.name && !messageData.author) || !messageData.content) {
            console.warn('⚠️ Mensagem inválida ignorada:', messageData);
            return;
        }
        
        // Normalizar dados da mensagem
        const normalizedMessage = {
            id: messageData.id || Date.now() + Math.random(),
            name: messageData.name || messageData.author || 'Usuário',
            content: messageData.content || messageData.message || '',
            timestamp: messageData.timestamp || messageData.created_at || new Date().toISOString(),
            type: 'real'
        };
        
        // Verificar se já foi exibida
        if (this.displayedMessages.has(normalizedMessage.id)) {
            return;
        }
        
        this.messageQueue.push(normalizedMessage);
        this.displayedMessages.add(normalizedMessage.id);
        
        console.log('📨 Mensagem REAL adicionada à fila:', normalizedMessage.name, '- Total na fila:', this.messageQueue.length);
    }
    
    startMessageProcessor() {
        setInterval(() => {
            if (!this.isDisplaying && this.messageQueue.length > 0) {
                const message = this.messageQueue.shift();
                this.displayMessage(message);
            }
        }, 100); // Verificar a cada 100ms
    }
    
    displayMessage(messageData) {
        if (this.isDisplaying) return;
        
        this.isDisplaying = true;
        this.messageCount++;
        
        const container = document.getElementById('messageContainer');
        const messageElement = this.createMessageElement(messageData);
        
        // Limpar mensagens antigas se houver muitas
        const existingMessages = container.querySelectorAll('.message-overlay');
        if (existingMessages.length > 0) {
            existingMessages.forEach(msg => {
                if (msg.parentNode) {
                    msg.parentNode.removeChild(msg);
                }
            });
        }
        
        // Adicionar ao container
        container.appendChild(messageElement);
        
        // Animar entrada
        setTimeout(() => {
            messageElement.classList.add('show');
        }, 50);
        
        // Programar saída
        setTimeout(() => {
            this.hideMessage(messageElement);
        }, this.displayDuration);
        
        console.log('📺 Exibindo mensagem REAL #' + this.messageCount + ':', messageData.name);
    }
    
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-overlay';
        
        // Determinar tipo de mensagem
        const messageType = this.getMessageType(messageData);
        if (messageType) {
            messageDiv.classList.add(messageType);
        }
        
        // Formatar timestamp
        const timestamp = new Date(messageData.timestamp || Date.now());
        const timeString = timestamp.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Truncar mensagem se muito longa
        let content = messageData.content;
        if (content.length > 120) {
            content = content.substring(0, 120) + '...';
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-author">${this.escapeHtml(messageData.name)}</span>
                <span class="message-time">${timeString}</span>
            </div>
            <div class="message-content">${this.escapeHtml(content)}</div>
            <div class="message-progress"></div>
        `;
        
        return messageDiv;
    }
    
    getMessageType(messageData) {
        const content = messageData.content.toLowerCase();
        const name = messageData.name.toLowerCase();
        
        // Mensagens VIP
        if (name.includes('admin') || name.includes('mod') || content.includes('!')) {
            return 'vip';
        }
        
        // Mensagens destacadas
        const highlightKeywords = ['incrível', 'demais', 'top', 'show', 'perfeito', 'nossa', 'épico'];
        if (highlightKeywords.some(keyword => content.includes(keyword))) {
            return 'highlight';
        }
        
        return 'normal';
    }
    
    hideMessage(messageElement) {
        messageElement.classList.add('hide');
        
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
            this.isDisplaying = false;
        }, this.fadeDuration);
    }
    
    // ===== UTILITÁRIOS =====
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ===== MÉTODOS PÚBLICOS PARA TESTE =====
    testMessage() {
        const testMessage = {
            id: Date.now(),
            name: 'Usuário Teste',
            content: 'Esta é uma mensagem de teste para o overlay!',
            timestamp: new Date().toISOString(),
            type: 'test'
        };
        
        this.addRealMessageToQueue(testMessage);
        console.log('🧪 Mensagem de teste adicionada');
    }
    
    clearQueue() {
        this.messageQueue = [];
        this.displayedMessages.clear();
        console.log('🧹 Fila de mensagens limpa');
    }
    
    getStatus() {
        return {
            connected: this.socket ? this.socket.connected : false,
            queueLength: this.messageQueue.length,
            isDisplaying: this.isDisplaying,
            messageCount: this.messageCount,
            displayedCount: this.displayedMessages.size
        };
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.messageOverlay = new MessageOverlay();
    
    // Expor métodos para teste no console
    window.testMessage = () => window.messageOverlay.testMessage();
    window.clearQueue = () => window.messageOverlay.clearQueue();
    window.getStatus = () => window.messageOverlay.getStatus();
    
    console.log('📺 Overlay de mensagens REAL iniciado');
    console.log('💡 Use testMessage() no console para testar');
    console.log('📊 Use getStatus() para ver status');
    
    // Mostrar status a cada 30 segundos
    setInterval(() => {
        const status = window.messageOverlay.getStatus();
        console.log('📊 Status do overlay:', status);
    }, 30000);
});

