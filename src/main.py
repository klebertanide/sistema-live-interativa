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
            'active': True
        },
        'messages': [],
        'polls': []
    }
    
    @app.route('/')
    def index():
        """Página principal"""
        return '<h1>🎬 SISTEMA LIVE INTERATIVA FUNCIONANDO!</h1><p>Aplicação online no Render!</p>'
    
    @app.route('/health')
    def health_check():
        """Health check para monitoramento"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/admin')
    def admin_dashboard():
        """Dashboard administrativo básico"""
        return jsonify({
            'live_session': app_data['live_session'],
            'total_messages': len(app_data['messages']),
            'total_polls': len(app_data['polls'])
        })
    
    @app.route('/overlay/messages')
    def messages_overlay():
        """Overlay de mensagens para OBS"""
        return jsonify(app_data['messages'][-10:])  # Últimas 10 mensagens
    
    @app.route('/overlay/polls')
    def polls_overlay():
        """Overlay de enquetes para OBS"""
        active_polls = [poll for poll in app_data['polls'] if poll.get('active', False)]
        return jsonify(active_polls)
    
    @app.route('/api/status')
    def api_status():
        """Status da API"""
        return jsonify({
            'api_version': '1.0.0',
            'status': 'online',
            'features': ['messages', 'polls', 'overlays']
        })
    
    return app

def main():
    """Função principal"""
    app = create_app()
    
    # Configurar porta do Render
    port = int(os.environ.get('PORT', 8081))
    
    print(f"🎬 Iniciando Sistema Live Interativa na porta {port}")
    print(f"📺 Acesse: http://localhost:{port}")
    
    # Executar aplicação - CORREÇÃO PARA RENDER
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False  # Adicionar para evitar problemas no Render
    )

if __name__ == '__main__':
    main()

