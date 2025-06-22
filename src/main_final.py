"""
Sistema de Live Interativa - MOEDOR AO VIVO
VERSÃO FINAL - Sistema de Duas Lives + Estabilidade + Filas de Eventos
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

class Poll(db.Model):
    __tablename__ = 'polls'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=True)
    option_d = db.Column(db.String(100), nullable=True)
    votes_a = db.Column(db.Integer, default=0)
    votes_b = db.Column(db.Integer, default=0)
    votes_c = db.Column(db.Integer, default=0)
    votes_d = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'options': {
                'a': self.option_a,
                'b': self.option_b,
                'c': self.option_c,
                'd': self.option_d
            },
            'votes': {
                'a': self.votes_a,
                'b': self.votes_b,
                'c': self.votes_c,
                'd': self.votes_d
            },
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Screenshot(db.Model):
    __tablename__ = 'screenshots'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'camera_id': self.camera_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Variáveis globais para serviços
whisper_service = None
event_queue = None
connected_users = set()

def create_app():
    """Factory function para criar a aplicação Flask - VERSÃO FINAL"""
    global whisper_service, event_queue
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configurações otimizadas para produção
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'moedor-ao-vivo-secret-key-2025')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/live_system.db')
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
    os.makedirs('transcriptions', exist_ok=True)
    
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
    
    # Inicializar serviços
    from src.services.whisper_service import init_whisper_service
    from src.services.event_queue import init_event_queue
    
    whisper_service = init_whisper_service(app, socketio)
    event_queue = init_event_queue(socketio)
    
    print("✅ Serviços inicializados: Whisper e Event Queue")
    
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
            title = data.get('title', 'MOEDOR AO VIVO')
            live_oficial_url = data.get('live_oficial_url', '')
            live_mosaico_url = data.get('live_mosaico_url', '')
            
            print(f"📺 Atualizando live: {title}")
            print(f"📺 Live Oficial: {live_oficial_url}")
            print(f"📺 Live Mosaico: {live_mosaico_url}")
            
            # Desativar todas as lives anteriores
            LiveSession.query.update({'active': False})
            
            # Criar nova sessão de live
            live_session = LiveSession(
                title=title,
                live_oficial_url=live_oficial_url,
                live_mosaico_url=live_mosaico_url,
                youtube_url=live_oficial_url,  # Compatibilidade
                active=True
            )
            
            db.session.add(live_session)
            db.session.commit()
            
            print("✅ Live atualizada com sucesso")
            
            # Iniciar Whisper se live oficial estiver configurada
            if live_oficial_url and whisper_service:
                whisper_service.start_transcription(live_oficial_url)
                print("🎤 Whisper iniciado para live oficial")
            
            # Adicionar evento à fila
            if event_queue:
                event_queue.add_event('live_update', live_session.to_dict())
            
            return jsonify({
                'success': True,
                'message': 'Live atualizada com sucesso',
                'live_session': live_session.to_dict()
            })
            
        except Exception as e:
            print(f"❌ Erro ao atualizar live: {e}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/messages/send', methods=['POST'])
    def send_message():
        """Enviar mensagem - COM FILA DE EVENTOS"""
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
            
            print(f"💬 Nova mensagem de {name}: {content}")
            
            # Criar mensagem no banco
            message = Message(
                name=name,
                content=content
            )
            
            db.session.add(message)
            db.session.commit()
            
            print("✅ Mensagem salva no banco de dados")
            
            # Adicionar à fila de eventos
            if event_queue:
                event_queue.add_event('message', message.to_dict())
            
            return jsonify({
                'success': True,
                'message': 'Mensagem enviada com sucesso',
                'data': message.to_dict()
            })
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    @app.route('/api/whisper/generate-song', methods=['POST'])
    def generate_song():
        """Gerar letra da música do dia"""
        try:
            if not whisper_service:
                return jsonify({
                    'success': False,
                    'error': 'Serviço Whisper não disponível'
                }), 500
                
            lyrics_file = whisper_service.generate_song_lyrics()
            
            if lyrics_file:
                return jsonify({
                    'success': True,
                    'message': 'Letra da música gerada com sucesso',
                    'file': lyrics_file
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Não há transcrições suficientes para gerar a música'
                }), 400
                
        except Exception as e:
            print(f"❌ Erro ao gerar música: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/whisper/status')
    def whisper_status():
        """Status do Whisper"""
        try:
            if whisper_service:
                return jsonify({
                    'success': True,
                    'status': whisper_service.get_status()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Serviço não disponível'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/live/status')
    def live_status():
        """Status atual da live"""
        try:
            live_session = LiveSession.query.filter_by(active=True).first()
            
            return jsonify({
                'success': True,
                'live_session': live_session.to_dict() if live_session else None
            })
            
        except Exception as e:
            print(f"❌ Erro ao buscar status da live: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/stats')
    def get_stats():
        """Estatísticas do sistema"""
        try:
            stats = {
                'online_users': len(connected_users),
                'messages_today': Message.query.filter(
                    Message.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
                ).count(),
                'active_polls': Poll.query.filter_by(active=True).count(),
                'screenshots_today': Screenshot.query.filter(
                    Screenshot.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
                ).count(),
                'whisper_status': whisper_service.get_status() if whisper_service else None,
                'queue_status': event_queue.get_status() if event_queue else None
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/health')
    def health_check():
        """Health check para monitoramento"""
        try:
            # Testar conexão com banco
            db.session.execute('SELECT 1')
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'services': {
                    'whisper': whisper_service.is_running if whisper_service else False,
                    'event_queue': event_queue.worker_thread.is_alive() if event_queue and event_queue.worker_thread else False
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
    
    @app.route('/overlay/polls')
    def overlay_polls():
        """Overlay de enquetes"""
        return render_template('overlay/polls.html')
    
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
        print(f"👋 Usuário desconectado: {request.sid} (Total: {len(connected_users)})")
        
        # Emitir estatísticas atualizadas
        socketio.emit('stats_update', {'online_users': len(connected_users)})
    
    @socketio.on('join_room')
    def handle_join_room(data):
        room = data.get('room', 'general')
        join_room(room)
        print(f"🏠 Usuário {request.sid} entrou na sala: {room}")
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        room = data.get('room', 'general')
        leave_room(room)
        print(f"🚪 Usuário {request.sid} saiu da sala: {room}")
    
    # Servir arquivos estáticos
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)
    
    return app, socketio

def setup_signal_handlers(socketio):
    """Configurar handlers para sinais do sistema"""
    def signal_handler(signum, frame):
        print(f"\\n🛑 Recebido sinal {signum}, encerrando servidor...")
        
        # Parar serviços
        if whisper_service:
            whisper_service.stop_transcription()
        if event_queue:
            event_queue.stop()
            
        socketio.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Função principal - VERSÃO FINAL OTIMIZADA"""
    try:
        # Configurações do servidor
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8081))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print("============================================================")
        print("🎬 SISTEMA DE LIVE INTERATIVA - MOEDOR AO VIVO")
        print("============================================================")
        print("🚀 Servidor iniciando...")
        print(f"📡 Host: {host}")
        print(f"🔌 Porta: {port}")
        print(f"🐛 Debug: {debug}")
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("============================================================")
        print(f"🌐 Página principal: http://{host}:{port}")
        print(f"⚙️  Painel admin: http://{host}:{port}/admin")
        print(f"🎬 Overlays: http://{host}:{port}/overlay")
        print(f"❤️  Health check: http://{host}:{port}/api/health")
        print("============================================================")
        
        # Criar aplicação
        app, socketio = create_app()
        
        # Configurar handlers de sinal
        setup_signal_handlers(socketio)
        
        # Iniciar servidor com eventlet para melhor performance
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,  # Evitar problemas em produção
            log_output=True
        )
        
    except Exception as e:
        print(f"❌ Erro crítico ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

