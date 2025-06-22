# Sistema de Live Interativa - MOEDOR AO VIVO (versão simplificada)

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import eventlet
import signal

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Carregar variáveis de ambiente
load_dotenv()

# Logging
logging.basicConfig(
level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
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
    app = Flask(__name__, template_folder='templates', static_folder='static')

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

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
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
        return render_template('index.html', live_session=live, cameras=cameras)

    @app.route('/admin')
    def admin():
        live = LiveSession.query.filter_by(active=True).first()
        cameras = Camera.query.filter_by(active=True).order_by(Camera.order).all()
        messages = Message.query.order_by(Message.created_at.desc()).limit(10).all()
        return render_template('admin/dashboard.html', live_session=live, cameras=cameras, messages=messages)

    @app.route('/api/live/update', methods=['POST'])
    def update_live():
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

    @app.route('/api/messages/send', methods=['POST'])
    def send_message():
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

    @app.route('/api/messages/recent', methods=['GET'])
    def recent_messages():
        messages = Message.query.order_by(Message.created_at.desc()).limit(10).all()
        return jsonify({'success': True, 'messages': [m.to_dict() for m in messages]})

    @app.route('/api/health')
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'users_online': len(connected_users)
            })
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @app.route('/overlay')
    def overlay():
        return render_template('overlay/index.html')

    @app.route('/overlay/messages')
    def overlay_messages():
        return render_template('overlay/messages.html')

    @socketio.on('connect')
    def on_connect():
        connected_users.add(request.sid)
        socketio.emit('stats_update', {'online_users': len(connected_users)})

    @socketio.on('disconnect')
    def on_disconnect():
        connected_users.discard(request.sid)
        socketio.emit('stats_update', {'online_users': len(connected_users)})

    return app, socketio

def setup_signal_handlers(socketio):
    def handle_exit(signum, frame):
        print("Encerrando servidor...")
        socketio.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

def main():
    print("🎬 MOEDOR AO VIVO")
    try:
        app, socketio = create_app()
        setup_signal_handlers(socketio)
        socketio.run(app, host='0.0.0.0', port=8081, debug=False)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
