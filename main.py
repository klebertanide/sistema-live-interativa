import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>🎬 SISTEMA LIVE INTERATIVA FUNCIONANDO!</h1><p>Aplicação online no Render!</p>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port)
