"""
Sistema de Live Interativa - MOEDOR AO VIVO
VERSÃO LIMPA - Apenas Sistema de Duas Lives
"""

import os
import sys
import logging
from datetime import datetime
import threading
import time
import signal
import atexit

# Configurar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, send_from_directory, request, jsonify, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import eventlet

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Inicializar extensões globalmente
db = SQLAlchemy()

# Definir modelos globalmente - SISTEMA DE DUAS LIVES
class LiveSession(db.Model):
    __tablename__ = 'live_sessions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='MOEDOR AO VIVO')
    live_oficial_url = db.Column(db.String(500), nullable=True)  # Live Oficial
    live_mosaico_url = db.Column(db.String(500), nullable=True)  # Live Mosaico
    youtube_url = db.Column(db.String(500), nullable=True)  # Compatibilidade
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'live_oficial_url': self.live_oficial_url,
            'live_mosaico_url': self.live_mosaico_url,
            'youtube_url': self.youtube_url,  # Compatibilidade
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    displayed = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'displayed': self.displayed
        }

class Camera(db.Model):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=1)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'order': self.order,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Screenshot(db.Model):
    __tablename__ = 'screenshots'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    emotion = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'emotion': self.emotion,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Variáveis globais para serviços
event_queue = None
screenshot_service = None
connected_users = set()

def create_app():
    """Factory function para criar a aplicação Flask - VERSÃO LIMPA"""
    global event_queue, screenshot_service
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configurações otimizadas para produção
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'moedor-ao-vivo-secret-key-2025')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///live_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'check_same_thread': False}
    }
    
    # Inicializar extensões
    db.init_app(app)
    CORS(app, origins="*")
    
    # SocketIO otimizado para produção
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='eventlet',
        ping_timeout=60,
        ping_interval=25,
        max_http_buffer_size=1000000
    )
    
    # Criar diretórios necessários
    os.makedirs('instance', exist_ok=True)
    os.makedirs('static/screenshots', exist_ok=True)
    os.makedirs('static/polaroids', exist_ok=True)
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        print("✅ Banco de dados inicializado com sucesso")
        
        # Garantir que existe uma sessão de live padrão
        live_session = LiveSession.query.first()
        if not live_session:
            live_session = LiveSession(
                title="MOEDOR AO VIVO",
                live_oficial_url="",
                live_mosaico_url="",
                youtube_url="",
                active=False
            )
            db.session.add(live_session)
            db.session.commit()
            print("✅ Sessão de live padrão criada")
    
    # Inicializar serviços básicos
    from services.event_queue import init_event_queue
    from services.youtube_screenshot_service import init_youtube_screenshot_service, get_youtube_screenshot_service
    
    event_queue = init_event_queue(socketio)
    screenshot_service = init_youtube_screenshot_service(app, db, socketio)
    
    print("✅ Serviços inicializados: Event Queue e Screenshots")
    
    # Auto-iniciar serviços
    if screenshot_service:
        screenshot_service.start()
        print("📸 Serviço de screenshots das lives do YouTube iniciado")
    
    # Rotas principais
    @app.route('/')
    def index():
        """Página principal - SISTEMA DE DUAS LIVES"""
        try:
            live_session = LiveSession.query.filter_by(active=True).first()
            cameras = Camera.query.filter_by(active=True).order_by(Camera.order).all()
            
            print(f"🏠 Renderizando página principal - Live: {live_session is not None}, Câmeras: {len(cameras)}")
            
            return render_template('index.html', 
                                 live_session=live_session,
                                 cameras=cameras)
        except Exception as e:
            print(f"❌ Erro na página principal: {e}")
            return render_template('index.html', live_session=None, cameras=[])
    
    @app.route('/admin')
    def admin_dashboard():
        """Painel administrativo - SISTEMA DE DUAS LIVES"""
        try:
            live_session = LiveSession.query.filter_by(active=True).first()
            cameras = Camera.query.filter_by(active=True).order_by(Camera.order).all()
            messages = Message.query.order_by(Message.created_at.desc()).limit(10).all()
            
            print(f"📊 Renderizando dashboard admin - Live: {live_session is not None}, Câmeras: {len(cameras)}, Mensagens: {len(messages)}")
            
            return render_template('admin/dashboard.html',
                                 live_session=live_session,
                                 cameras=cameras,
                                 messages=messages)
        except Exception as e:
            print(f"❌ Erro no dashboard admin: {e}")
            import traceback
            traceback.print_exc()
            return render_template('admin/dashboard.html',
                                 live_session=None,
                                 cameras=[],
                                 messages=[])
    
    # APIs REST - SISTEMA DE DUAS LIVES
    @app.route('/api/live/update', methods=['POST'])
    def update_live():
        """Atualizar configurações da live - SISTEMA DE DUAS LIVES"""
        try:
            data = request.get_json()
            
            # Buscar sessão ativa ou criar nova
            live_session = LiveSession.query.filter_by(active=True).first()
            if not live_session:
                live_session = LiveSession(active=True)
                db.session.add(live_session)
            
            # Atualizar campos
            if 'title' in data:
                live_session.title = data['title']
            if 'live_oficial_url' in data:
                live_session.live_oficial_url = data['live_oficial_url']
            if 'live_mosaico_url' in data:
                live_session.live_mosaico_url = data['live_mosaico_url']
            if 'youtube_url' in data:  # Compatibilidade
                live_session.youtube_url = data['youtube_url']
            
            db.session.commit()
            
            print(f"🔄 Live atualizada: {live_session.title}")
            
            # Emitir via WebSocket
            if socketio:
                socketio.emit('live_updated', live_session.to_dict())
            
            # Adicionar à fila de eventos
            if event_queue:
                event_queue.add_event('live_updated', live_session.to_dict())
            
            return jsonify({
                'success': True,
                'message': 'Live atualizada com sucesso',
                'live': live_session.to_dict()
            })
            
        except Exception as e:
            print(f"❌ Erro ao atualizar live: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/messages/send', methods=['POST'])
    def send_message():
        """Enviar mensagem"""
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            content = data.get('content', '').strip()
            
            # Validações
            if not name or len(name) > 50:
                return jsonify({
                    'success': False,
                    'error': 'Nome inválido (máximo 50 caracteres)'
                }), 400
            
            if not content or len(content) > 250:
                return jsonify({
                    'success': False,
                    'error': 'Mensagem inválida (máximo 250 caracteres)'
                }), 400
            
            # Criar mensagem
            message = Message(name=name, content=content)
            db.session.add(message)
            db.session.commit()
            
            print(f"💬 Nova mensagem de {name}: {content}")
            
            # Emitir via WebSocket
            if socketio:
                socketio.emit('new_message', message.to_dict())
            
            # Adicionar à fila de eventos
            if event_queue:
                event_queue.add_event('message_sent', message.to_dict())
            
            return jsonify({
                'success': True,
                'message': 'Mensagem enviada com sucesso',
                'data': message.to_dict()
            })
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/messages/recent', methods=['GET'])
    def get_recent_messages():
        """Buscar mensagens recentes"""
        try:
            limit = request.args.get('limit', 10, type=int)
            limit = min(limit, 50)  # Máximo 50 mensagens
            
            # Buscar mensagens mais recentes
            messages = Message.query.order_by(Message.created_at.desc()).limit(limit).all()
            
            # Converter para dict
            messages_data = [message.to_dict() for message in messages]
            
            return jsonify({
                'success': True,
                'messages': messages_data,
                'count': len(messages_data)
            })
            
        except Exception as e:
            print(f"❌ Erro ao buscar mensagens recentes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/health')
    def health_check():
        """Health check para monitoramento"""
        try:
            # Testar conexão com banco
            db.session.execute(db.text('SELECT 1'))
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'services': {
                    'event_queue': event_queue.worker_thread.is_alive() if event_queue and event_queue.worker_thread else False,
                    'screenshot_service': screenshot_service.is_running if screenshot_service else False
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    # Overlays para OBS
    @app.route('/overlay')
    def overlay_index():
        """Página de overlays"""
        return render_template('overlay/index.html')
    
    @app.route('/overlay/messages')
    def overlay_messages():
        """Overlay de mensagens"""
        return render_template('overlay/messages.html')
    
    # WebSocket Events - OTIMIZADOS COM SALAS
    @socketio.on('connect')
    def handle_connect():
        global connected_users
        connected_users.add(request.sid)
        print(f"👤 Usuário conectado: {request.sid} (Total: {len(connected_users)})")
        emit('connected', {'status': 'success'})
        
        # Emitir estatísticas atualizadas
        socketio.emit('stats_update', {'online_users': len(connected_users)})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        global connected_users
        connected_users.discard(request.sid)
        print(f"👤 Usuário desconectado: {request.sid} (Total: {len(connected_users)})")
        
        # Emitir estatísticas atualizadas
        socketio.emit('stats_update', {'online_users': len(connected_users)})
    
    @socketio.on('join_room')
    def handle_join_room(data):
        room = data.get('room', 'general')
        join_room(room)
        print(f"👤 Usuário {request.sid} entrou na sala: {room}")
        emit('joined_room', {'room': room})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        room = data.get('room', 'general')
        leave_room(room)
        print(f"👤 Usuário {request.sid} saiu da sala: {room}")
        emit('left_room', {'room': room})
    
    return app, socketio

def setup_signal_handlers(socketio):
    """Configurar handlers para sinais do sistema"""
    def signal_handler(signum, frame):
        print(f"\\n🛑 Recebido sinal {signum}, encerrando servidor...")
        
        # Parar serviços
        if event_queue:
            event_queue.stop()
        if screenshot_service:
            screenshot_service.stop()
        
        # Encerrar SocketIO
        socketio.stop()
        
        print("✅ Servidor encerrado com sucesso")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Função principal"""
    print("=" * 60)
    print("🎬 SISTEMA DE LIVE INTERATIVA - MOEDOR AO VIVO")
    print("=" * 60)
    print("🚀 Servidor iniciando...")
    print(f"📡 Host: 0.0.0.0")
    print(f"🔌 Porta: 8081")
    print(f"🐛 Debug: False")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    print("🌐 Página principal: http://0.0.0.0:8081")
    print("⚙️  Painel admin: http://0.0.0.0:8081/admin")
    print("🎬 Overlays: http://0.0.0.0:8081/overlay")
    print("❤️  Health check: http://0.0.0.0:8081/api/health")
    print("=" * 60)
    
    try:
        app, socketio = create_app()
        
        # Configurar handlers de sinal
        setup_signal_handlers(socketio)
        
        # Iniciar servidor
        socketio.run(
            app,
            host='0.0.0.0',
            port=8081,
            debug=False,
            use_reloader=False,
            log_output=False
        )
        
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

