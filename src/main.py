import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema Live Interativa</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            h1 {
                font-size: 3em;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }
            p {
                font-size: 1.2em;
                margin-bottom: 30px;
                opacity: 0.9;
            }
            .status {
                background: rgba(0, 255, 0, 0.2);
                padding: 15px;
                border-radius: 10px;
                border: 2px solid rgba(0, 255, 0, 0.5);
                margin-top: 20px;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .feature {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Sistema Live Interativa</h1>
            <p>Seu sistema está funcionando perfeitamente!</p>
            
            <div class="status">
                <h3>✅ Status: ONLINE</h3>
                <p>Deploy realizado com sucesso via GitHub + Render</p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h4>🔧 GitHub</h4>
                    <p>Repositório configurado</p>
                </div>
                <div class="feature">
                    <h4>☁️ Render</h4>
                    <p>Deploy automático ativo</p>
                </div>
                <div class="feature">
                    <h4>🌐 Online</h4>
                    <p>Acessível globalmente</p>
                </div>
                <div class="feature">
                    <h4>⚡ Flask</h4>
                    <p>Framework Python</p>
                </div>
            </div>
            
            <p style="margin-top: 30px; font-size: 0.9em; opacity: 0.7;">
                Hospedado profissionalmente com infraestrutura escalável
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/status')
def status():
    return {
        'status': 'online',
        'message': 'Sistema funcionando perfeitamente!',
        'framework': 'Flask',
        'hosting': 'Render',
        'repository': 'GitHub'
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

