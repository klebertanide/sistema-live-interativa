# Sistema de Live Interativa - MOEDOR AO VIVO (versão final para Render)

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import signal

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

db = SQLAlchemy()
connected_users = set()

class LiveSession(db.Model):
    __tablename__ = 'live_sessions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='MOEDOR AO VIVO')
    live_oficial_url = db.Column(db.String(500), nullable=True)
    live_mosaico_url = db.Column(db.String(500), nullable=True)
    youtube_url = db.Column(db.String(500), nullable=True)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'live_oficial_url': self.live_oficial_url,
            'live_mosaico_url': self.live_mosaico_url,
            'youtube_url': self.youtube_url,
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

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'moedor-ao-vivo-secret-key-2025')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///live_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'check_same_thread': False}
    }

    db.init_app(app)
    CORS(app, origins="*")

    # Usar threading ao invés de eventlet para compatibilidade com Render
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25
    )

    with app.app_context():
        db.create_all()
        if not LiveSession.query.first():
            db.session.add(LiveSession(active=True))
            db.session.commit()

    @app.route('/')
    def index():
        live = LiveSession.query.filter_by(active=True).first()
        cameras = Camera.query.filter_by(active=True).order_by(Camera.order).all()
        return f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🎬 MOEDOR AO VIVO</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                h1 {{
                    text-align: center;
                    font-size: 3em;
                    margin-bottom: 30px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                }}
                .live-info {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin-bottom: 30px;
                }}
                .status {{
                    display: inline-block;
                    background: #ff4444;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 25px;
                    font-weight: bold;
                    margin-bottom: 15px;
                }}
                .status.live {{
                    background: #44ff44;
                    animation: pulse 2s infinite;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                    100% {{ opacity: 1; }}
                }}
                .features {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }}
                .feature {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                }}
                .feature h3 {{
                    margin-top: 0;
                    font-size: 1.5em;
                }}
                .admin-link {{
                    display: inline-block;
                    background: #ff6b35;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    margin-top: 20px;
                    transition: all 0.3s ease;
                }}
                .admin-link:hover {{
                    background: #e55a2b;
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎬 MOEDOR AO VIVO</h1>
                
                <div class="live-info">
                    <div class="status {'live' if live and live.active else ''}">
                        {'🔴 AO VIVO' if live and live.active else '⚫ OFFLINE'}
                    </div>
                    <h2>{live.title if live else 'Sistema de Live Interativa'}</h2>
                    <p>Sistema profissional de transmissão ao vivo com chat interativo e múltiplas câmeras.</p>
                </div>

                <div class="features">
                    <div class="feature">
                        <h3>📹 Live Oficial</h3>
                        <p>Transmissão principal em alta qualidade</p>
                    </div>
                    <div class="feature">
                        <h3>🎥 Mosaico</h3>
                        <p>Múltiplas câmeras simultâneas</p>
                    </div>
                    <div class="feature">
                        <h3>💬 Chat Interativo</h3>
                        <p>Mensagens em tempo real</p>
                    </div>
                    <div class="feature">
                        <h3>📺 YouTube</h3>
                        <p>Integração com YouTube Live</p>
                    </div>
                    <div class="feature">
                        <h3>🎛️ Painel Admin</h3>
                        <p>Controle total do sistema</p>
                    </div>
                    <div class="feature">
                        <h3>📊 Estatísticas</h3>
                        <p>Usuários online e métricas</p>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="/admin" class="admin-link">🎛️ Acessar Painel Admin</a>
                </div>

                <div style="text-align: center; margin-top: 30px; opacity: 0.7;">
                    <p>Sistema hospedado profissionalmente com infraestrutura escalável</p>
                    <p>Usuários online: <span id="online-count">0</span></p>
                </div>
            </div>

            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script>
                const socket = io();
                
                socket.on('stats_update', function(data) {{
                    document.getElementById('online-count').textContent = data.online_users || 0;
                }});
                
                socket.on('live_updated', function(data) {{
                    location.reload();
                }});
            </script>
        </body>
        </html>
        '''

    @app.route('/admin')
    def admin():
        live = LiveSession.query.filter_by(active=True).first()
        cameras = Camera.query.filter_by(active=True).order_by(Camera.order).all()
        messages = Message.query.order_by(Message.created_at.desc()).limit(10).all()
        return f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🎛️ Admin - MOEDOR AO VIVO</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .panel {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin-bottom: 20px;
                    backdrop-filter: blur(10px);
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                input, textarea {{
                    width: 100%;
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    background: rgba(255, 255, 255, 0.9);
                    color: #333;
                    box-sizing: border-box;
                }}
                button {{
                    background: #3498db;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                }}
                button:hover {{
                    background: #2980b9;
                }}
                .messages {{
                    max-height: 300px;
                    overflow-y: auto;
                    background: rgba(0, 0, 0, 0.3);
                    padding: 15px;
                    border-radius: 10px;
                }}
                .message {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }}
                .stat {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎛️ Painel Admin - MOEDOR AO VIVO</h1>
                    <a href="/" style="color: #3498db;">← Voltar ao Site</a>
                </div>

                <div class="stats">
                    <div class="stat">
                        <h3>👥 Usuários Online</h3>
                        <div id="online-users">0</div>
                    </div>
                    <div class="stat">
                        <h3>💬 Mensagens</h3>
                        <div>{len(messages)}</div>
                    </div>
                    <div class="stat">
                        <h3>📹 Câmeras</h3>
                        <div>{len(cameras)}</div>
                    </div>
                    <div class="stat">
                        <h3>📊 Status</h3>
                        <div>{'🔴 AO VIVO' if live and live.active else '⚫ OFFLINE'}</div>
                    </div>
                </div>

                <div class="panel">
                    <h2>📹 Configurar Live</h2>
                    <form id="live-form">
                        <div class="form-group">
                            <label>Título da Live:</label>
                            <input type="text" id="title" value="{live.title if live else 'MOEDOR AO VIVO'}" required>
                        </div>
                        <div class="form-group">
                            <label>URL Live Oficial:</label>
                            <input type="url" id="live_oficial_url" value="{live.live_oficial_url if live and live.live_oficial_url else ''}" placeholder="https://...">
                        </div>
                        <div class="form-group">
                            <label>URL Live Mosaico:</label>
                            <input type="url" id="live_mosaico_url" value="{live.live_mosaico_url if live and live.live_mosaico_url else ''}" placeholder="https://...">
                        </div>
                        <div class="form-group">
                            <label>URL YouTube:</label>
                            <input type="url" id="youtube_url" value="{live.youtube_url if live and live.youtube_url else ''}" placeholder="https://youtube.com/...">
                        </div>
                        <button type="submit">💾 Salvar Configurações</button>
                    </form>
                </div>

                <div class="panel">
                    <h2>💬 Mensagens Recentes</h2>
                    <div class="messages" id="messages">
                        {''.join([f'<div class="message"><strong>{msg.name}:</strong> {msg.content} <small>({msg.created_at.strftime("%H:%M") if msg.created_at else ""})</small></div>' for msg in messages])}
                    </div>
                </div>

                <div class="panel">
                    <h2>📤 Enviar Mensagem de Teste</h2>
                    <form id="message-form">
                        <div class="form-group">
                            <label>Nome:</label>
                            <input type="text" id="msg-name" value="Admin" required>
                        </div>
                        <div class="form-group">
                            <label>Mensagem:</label>
                            <textarea id="msg-content" rows="3" placeholder="Digite sua mensagem..." required></textarea>
                        </div>
                        <button type="submit">📤 Enviar Mensagem</button>
                    </form>
                </div>
            </div>

            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script>
                const socket = io();
                
                socket.on('stats_update', function(data) {{
                    document.getElementById('online-users').textContent = data.online_users || 0;
                }});
                
                socket.on('new_message', function(data) {{
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message';
                    messageDiv.innerHTML = `<strong>${{data.name}}:</strong> ${{data.content}} <small>(agora)</small>`;
                    messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
                }});

                document.getElementById('live-form').addEventListener('submit', function(e) {{
                    e.preventDefault();
                    const data = {{
                        title: document.getElementById('title').value,
                        live_oficial_url: document.getElementById('live_oficial_url').value,
                        live_mosaico_url: document.getElementById('live_mosaico_url').value,
                        youtube_url: document.getElementById('youtube_url').value
                    }};
                    
                    fetch('/api/live/update', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            alert('✅ Configurações salvas com sucesso!');
                        }} else {{
                            alert('❌ Erro ao salvar configurações');
                        }}
                    }});
                }});

                document.getElementById('message-form').addEventListener('submit', function(e) {{
                    e.preventDefault();
                    const data = {{
                        name: document.getElementById('msg-name').value,
                        content: document.getElementById('msg-content').value
                    }};
                    
                    fetch('/api/messages/send', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            document.getElementById('msg-content').value = '';
                            alert('✅ Mensagem enviada!');
                        }} else {{
                            alert('❌ Erro ao enviar mensagem');
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        '''

    @app.route('/api/live/update', methods=['POST'])
    def update_live():
        try:
            data = request.get_json()
            live = LiveSession.query.filter_by(active=True).first()
            if not live:
                live = LiveSession(active=True)
                db.session.add(live)

            for field in ['title', 'live_oficial_url', 'live_mosaico_url', 'youtube_url']:
                if field in data:
                    setattr(live, field, data[field])

            db.session.commit()
            socketio.emit('live_updated', live.to_dict())
            return jsonify({'success': True, 'live': live.to_dict()})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/messages/send', methods=['POST'])
    def send_message():
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            content = data.get('content', '').strip()

            if not name or len(name) > 50 or not content or len(content) > 250:
                return jsonify({'success': False, 'error': 'Dados inválidos'}), 400

            message = Message(name=name, content=content)
            db.session.add(message)
            db.session.commit()
            socketio.emit('new_message', message.to_dict())
            return jsonify({'success': True, 'message': message.to_dict()})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/messages/recent', methods=['GET'])
    def recent_messages():
        try:
            messages = Message.query.order_by(Message.created_at.desc()).limit(10).all()
            return jsonify({'success': True, 'messages': [m.to_dict() for m in messages]})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/health')
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'users_online': len(connected_users),
                'system': 'MOEDOR AO VIVO'
            })
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @app.route('/overlay')
    def overlay():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Overlay - MOEDOR AO VIVO</title>
            <style>
                body { margin: 0; padding: 20px; background: transparent; color: white; font-family: Arial, sans-serif; }
                .overlay { background: rgba(0,0,0,0.7); padding: 15px; border-radius: 10px; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <div class="overlay">
                <h2>🎬 MOEDOR AO VIVO</h2>
                <p>Overlay para OBS/Streaming</p>
            </div>
        </body>
        </html>
        '''

    @socketio.on('connect')
    def on_connect():
        connected_users.add(request.sid)
        socketio.emit('stats_update', {'online_users': len(connected_users)})

    @socketio.on('disconnect')
    def on_disconnect():
        connected_users.discard(request.sid)
        socketio.emit('stats_update', {'online_users': len(connected_users)})

    return app, socketio

def main():
    print("🎬 MOEDOR AO VIVO - Iniciando servidor...")
    try:
        app, socketio = create_app()
        port = int(os.environ.get('PORT', 5000))
        # Permitir Werkzeug em produção para Render
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

