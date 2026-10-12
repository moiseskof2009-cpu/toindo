from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo - Solicite sua corrida</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00C851">
<style>
body{font-family:Arial,sans-serif;margin:0;background:#f5f5f5;text-align:center}
.header{background:#00C851;color:white;padding:20px}
.logo{font-size:32px;font-weight:bold}
.card{background:white;margin:20px;padding:20px;border-radius:15px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.btn{background:#00C851;color:white;border:none;padding:15px 30px;border-radius:10px;font-size:18px;width:90%;margin:10px;font-weight:bold}
.btn:active{transform:scale(0.98)}
input{width:90%;padding:15px;margin:10px;border:1px solid #ddd;border-radius:10px;font-size:16px}
.install{background:#FFD600;color:black}
</style>
</head>
<body>
<div class="header">
<div class="logo">🚗 TOINDO</div>
<p>Solicite sua corrida - Várzea Grande</p>
</div>

<div class="card">
<h3>Para onde vamos?</h3>
<input id="origem" placeholder="📍 De onde você está?">
<input id="destino" placeholder="🏁 Para onde vai?">
<button class="btn" onclick="solicitar()">SOLICITAR CORRIDA AGORA</button>
<p id="msg"></p>
</div>

<div class="card">
<h3>📲 Instalar App no Celular</h3>
<p>Clique no botão abaixo e depois em "Instalar"</p>
<button class="btn install" onclick="instalar()">⬇️ BAIXAR APP TOINDO</button>
<p style="font-size:12px;color:#666;margin-top:10px">No iPhone: clique no botão compartilhar [↑] e em "Adicionar à Tela de Início"</p>
</div>

<div class="card" style="font-size:12px;color:#666">
<p>✅ Motoristas da sua região<br>✅ Preço justo, sem taxa abusiva<br>✅ Pague só quando entrar no carro</p>
</div>

<script>
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
});

function instalar(){
  if(deferredPrompt){
    deferredPrompt.prompt();
  } else {
    alert('Para instalar: No Chrome clique nos 3 pontinhos ⋮ > Instalar app ou Adicionar à tela inicial');
  }
}

function solicitar(){
  const o = document.getElementById('origem').value;
  const d = document.getElementById('destino').value;
  if(!o || !d){ alert('Preencha origem e destino!'); return; }
  document.getElementById('msg').innerHTML = '✅ Corrida solicitada!<br>Procurando motoristas perto de '+o+'...<br><br>Em breve um motorista Toindo vai te chamar no WhatsApp!';
}

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
</script>
</body>
</html>
    """

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Toindo - Solicite sua corrida",
        "short_name": "Toindo",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#00C851",
        "theme_color": "#00C851",
        "icons": [
            {"src": "https://cdn-icons-png.flaticon.com/512/3774/3774092.png", "sizes": "512x512", "type": "image/png"}
        ]
    })

@app.route('/sw.js')
def sw():
    return """
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
""", 200, {'Content-Type': 'application/javascript'}

@app.route('/api/status')
def status():
    return jsonify({"status": "online", "app": "Toindo", "cidade": "Várzea Grande"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
