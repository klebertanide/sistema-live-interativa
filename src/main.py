from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
<title>Sistema Live Interativa</title>
<meta charset="UTF-8">
<style>
body {
font-family: Arial, sans-serif;
text-align: center;
padding: 50px;
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
margin: 0;
}
.container {
max-width: 600px;
margin: 0 auto;
background: rgba(255,255,255,0.1);
padding: 40px;
border-radius: 20px;
backdrop-filter: blur(10px);
}
h1 {
color: #fff;
font-size: 2.5em;
margin-bottom: 20px;
}
p {
color: #f0f0f0;
font-size: 1.2em;
margin: 15px 0;
}
.status {
background: #4CAF50;
padding: 10px 20px;
border-radius: 25px;
display: inline-block;
margin: 20px 0;
}
</style>
</head>
<body>
<div class="container">
<h1>🎬 SISTEMA LIVE INTERATIVA</h1>
<p>Aplicação funcionando perfeitamente no Render!</p>
<div class="status">✅ Status: Online</div>
<p>Deploy realizado com sucesso via GitHub + Render</p>
</div>
</body>
</html>
'''

if __name__ == '__main__':
     port = int(os.environ.get('PORT', 5000))
     app.run(host='0.0.0.0', port=port, debug=False)
