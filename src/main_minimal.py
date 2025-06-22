#!/usr/bin/env python3
"""
Sistema de Live Interativa - Big Brother Moído
VERSÃO MÍNIMA FUNCIONAL - Sem SQLAlchemy para evitar erros
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify

def create_app():
    """Factory function para criar a aplicação Flask"""
    
    # Definir caminhos corretos para templates e static
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # Criar app Flask com caminhos corretos
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configurações básicas
    app.config['SECRET_KEY'] = 'big-brother-moido-secret-key-2024'
    
    # Dados em memória (temporário)
    app_data = {
        'live_session': {
            'title': 'Big Brother Moído',
            'youtube_url': '',
            'active': False
        },
        'cameras': [],
        'messages': [],
        'polls': [],
        'online_users': 0
    }
    
    @app.route('/')
    def index():
        """Página principal para os usuários"""
        try:
            print("📺 Renderizando página principal")
            return render_template('index.html', 
                                 live_session=app_data['live_session'],
                                 cameras=app_data['cameras'])
        except Exception as e:
            print(f"❌ Erro na página principal: {e}")
            return f"<h1>Big Brother Moído</h1><p>Sistema em manutenção</p><p>Erro: {e}</p>"
    
    @app.route('/health')
    def health_check():
        """Endpoint para verificar se o sistema está funcionando"""
        return {
            'status': 'ok', 
            'message': 'Sistema funcionando normalmente',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @app.route('/admin')
    def admin_dashboard():
        """Painel administrativo principal"""
        try:
            print("⚙️ Renderizando painel admin")
            return render_template('admin/dashboard.html',
                                 live_session=app_data['live_session'],
                                 cameras=app_data['cameras'],
                                 recent_messages=app_data['messages'][-10:],
                                 active_polls=app_data['polls'],
                                 online_users=app_data['online_users'])
        except Exception as e:
            print(f"❌ Erro no dashboard admin: {e}")
            return f"<h1>Painel Admin</h1><p>Sistema em manutenção</p><p>Erro: {e}</p>"
    
    @app.route('/overlay/messages')
    def messages_overlay():
        """Overlay para exibição de mensagens"""
        try:
            print("🎬 Renderizando overlay de mensagens")
            return render_template('overlay/messages.html')
        except Exception as e:
            print(f"❌ Erro no overlay de mensagens: {e}")
            return f"<h1>Overlay Mensagens</h1><p>Sistema em manutenção</p><p>Erro: {e}</p>"
    
    @app.route('/overlay/polls')
    def polls_overlay():
        """Overlay para exibição de enquetes"""
        try:
            print("🎬 Renderizando overlay de enquetes")
            return render_template('overlay/polls.html')
        except Exception as e:
            print(f"❌ Erro no overlay de enquetes: {e}")
            return f"<h1>Overlay Enquetes</h1><p>Sistema em manutenção</p><p>Erro: {e}</p>"
    
    @app.route('/api/status')
    def api_status():
        """Status da API"""
        return jsonify({
            'status': 'ok',
            'live_active': app_data['live_session']['active'],
            'cameras_count': len(app_data['cameras']),
            'messages_count': len(app_data['messages']),
            'online_users': app_data['online_users']
        })
    
    return app

def main():
    """Função principal para executar a aplicação"""
    try:
        app = create_app()
        
        host = '0.0.0.0'
        port = 8081
        debug = False
        
        print("=" * 60)
        print("🎬 SISTEMA DE LIVE INTERATIVA - BIG BROTHER MOÍDO")
        print("=" * 60)
        print(f"🚀 Servidor iniciando...")
        print(f"📡 Host: {host}")
        print(f"🔌 Porta: {port}")
        print(f"🐛 Debug: {debug}")
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        print(f"🌐 Página principal: http://{host}:{port}")
        print(f"⚙️  Painel admin: http://{host}:{port}/admin")
        print(f"🎬 Overlays: http://{host}:{port}/overlay")
        print("=" * 60)
        
        app.run(
            host=host,
            port=port,
            debug=debug
        )
        
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

