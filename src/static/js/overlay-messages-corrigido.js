/**
 * JavaScript do Overlay de Mensagens CORRIGIDO - MOEDOR AO VIVO
 * Para uso no OBS Studio - VERSÃO FUNCIONAL
 */

class MessageOverlay {
    constructor() {
        this.socket = null;
        this.messageQueue = [];
        this.isDisplaying = false;
        this.displayDuration = 8000; // 8 segundos
        this.fadeDuration = 500; // 0.5 segundos
        this.messageCount = 0;
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.startMessageProcessor();
        this.startDemoMessages(); // DEMO para mostrar funcionamento
    }
    
    // ===== WEBSOCKET CORRIGIDO =====
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
            
            // Escutar novas mensagens - CORRIGIDO
            this.socket.on('new_message', (messageData) => {
                console.log('📨 Nova mensagem recebida:', messageData);
                this.addMessageToQueue(messageData);
            });
            
            // Escutar mensagens do chat
            this.socket.on('message', (messageData) => {
                console.log('💬 Mensagem do chat:', messageData);
                this.addMessageToQueue(messageData);
            });
            
            // Escutar broadcast de mensagens
            this.socket.on('broadcast_message', (messageData) => {
                console.log('📢 Broadcast recebido:', messageData);
                this.addMessageToQueue(messageData);
            });
            
        } catch (error) {
            console.error('❌ Erro ao conectar WebSocket:', error);
            this.fallbackToPolling();
        }
        
        // Polling como backup
        this.pollForMessages();
    }
    
    // ===== DEMO MESSAGES PARA TESTE =====
    startDemoMessages() {
        const demoMessages = [
            { name: "João Silva", content: "Que programa incrível! Estou adorando!" },
            { name: "Maria Santos", content: "NOSSA! Que situação louca essa!" },
            { name: "Pedro Costa", content: "Concordo totalmente com isso aí!" },
            { name: "Ana Oliveira", content: "Não acredito que isso aconteceu!" },
            { name: "Carlos Lima", content: "Muito bom esse programa, parabéns!" },
            { name: "Fernanda", content: "Que momento épico, galera!" },
            { name: "Roberto", content: "Isso é muito polêmico mesmo!" },
            { name: "Juliana", content: "Estou rindo muito aqui! 😂" },
            { name: "Marcos", content: "Que história maluca essa!" },
            { name: "Patrícia", content: "Vocês concordam com isso?" }
        ];
        
        // Adicionar mensagem demo a cada 15-30 segundos
        setInterval(() => {
            if (this.messageQueue.length < 3) { // Não sobrecarregar
                const randomMessage = demoMessages[Math.floor(Math.random() * demoMessages.length)];
                const demoMessage = {
                    id: Date.now() + Math.random(),
                    name: randomMessage.name,
                    content: randomMessage.content,
                    timestamp: new Date().toISOString(),
                    type: 'demo'
                };
                
                this.addMessageToQueue(demoMessage);
                console.log('🎭 Mensagem demo adicionada:', demoMessage.name);
            }
        }, Math.random() * 15000 + 15000); // 15-30 segundos
    }
    
    // ===== PROCESSAMENTO DE MENSAGENS CORRIGIDO =====
    addMessageToQueue(messageData) {
        // Validar dados da mensagem
        if (!messageData || !messageData.name || !messageData.content) {
            console.warn('⚠️ Mensagem inválida ignorada:', messageData);
            return;
        }
        
        // Adicionar ID se não existir
        if (!messageData.id) {
            messageData.id = Date.now() + Math.random();
        }
        
        // Adicionar timestamp se não existir
        if (!messageData.timestamp) {
            messageData.timestamp = new Date().toISOString();
        }
        
        this.messageQueue.push(messageData);
        console.log('📨 Nova mensagem na fila:', messageData.name, '- Total na fila:', this.messageQueue.length);
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
        
        console.log('📺 Exibindo mensagem #' + this.messageCount + ':', messageData.name);
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
        
        // Mensagens demo
        if (messageData.type === 'demo') {
            return 'demo';
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
    
    // ===== POLLING CORRIGIDO =====
    pollForMessages() {
        setInterval(() => {
            fetch('/api/messages/recent')
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('Erro na API');
                })
                .then(data => {
                    if (data.messages && data.messages.length > 0) {
                        data.messages.forEach(message => {
                            // Verificar se já foi exibida
                            if (!this.isMessageDisplayed(message.id)) {
                                this.addMessageToQueue(message);
                                this.markMessageAsDisplayed(message.id);
                            }
                        });
                    }
                })
                .catch(error => {
                    // Silencioso - normal quando não há API
                });
        }, 3000); // A cada 3 segundos
    }
    
    fallbackToPolling() {
        console.log('🔄 Usando polling como fallback');
        
        setInterval(() => {
            fetch('/overlay/api/next-message')
                .then(response => response.json())
                .then(data => {
                    if (data.has_message) {
                        this.addMessageToQueue(data.message);
                    }
                })
                .catch(error => {
                    // Silencioso
                });
        }, 2000);
    }
    
    // ===== CONTROLE DE MENSAGENS EXIBIDAS =====
    isMessageDisplayed(messageId) {
        const displayed = localStorage.getItem('displayed_messages');
        if (!displayed) return false;
        
        const displayedList = JSON.parse(displayed);
        return displayedList.includes(messageId);
    }
    
    markMessageAsDisplayed(messageId) {
        let displayed = localStorage.getItem('displayed_messages');
        let displayedList = displayed ? JSON.parse(displayed) : [];
        
        displayedList.push(messageId);
        
        // Manter apenas os últimos 100
        if (displayedList.length > 100) {
            displayedList = displayedList.slice(-100);
        }
        
        localStorage.setItem('displayed_messages', JSON.stringify(displayedList));
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
        
        this.addMessageToQueue(testMessage);
        console.log('🧪 Mensagem de teste adicionada');
    }
    
    clearQueue() {
        this.messageQueue = [];
        console.log('🧹 Fila de mensagens limpa');
    }
    
    getStatus() {
        return {
            connected: this.socket ? this.socket.connected : false,
            queueLength: this.messageQueue.length,
            isDisplaying: this.isDisplaying,
            messageCount: this.messageCount
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
    
    console.log('📺 Overlay de mensagens CORRIGIDO iniciado');
    console.log('💡 Use testMessage() no console para testar');
    console.log('📊 Use getStatus() para ver status');
    
    // Mostrar status a cada 30 segundos
    setInterval(() => {
        const status = window.messageOverlay.getStatus();
        console.log('📊 Status do overlay:', status);
    }, 30000);
});

