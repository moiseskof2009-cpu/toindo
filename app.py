from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Guarda as corridas na memória
corridas = []

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#000000">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;800&display=swap" rel="stylesheet">
<style>
*{font-family:'Inter',Arial,sans-serif}
body{margin:0;background:#000;color:white;text-align:center}
.header{background:#000;padding:25px 20px;border-bottom:3px solid #00FF88}
.logo{font-size:36px;font-weight:800;letter-spacing:2px}
.logo span{color:#00FF88}
.sub{color:#aaa;font-size:14px;margin-top:5px}
.card{background:white;color:black;margin:20px;padding:22px;border-radius:20px;box-shadow:0 10px 30px rgba(0,255,136,0.2)}
input{width:92%;padding:16px;margin:8px 0;border:2px solid #eee;border-radius:12px;font-size:16px;background:#f9f9f9}
.btn{background:#00FF88;color:black;border:none;padding:17px;border-radius:12px;font-size:17px;width:96%;font-weight:800;margin-top:12px}
.btn2{background:#000;color:#00FF88;border:2px solid #00FF88}
.status{display:none;margin-top:15px;padding:15px;background:#f0fff5;border-radius:12px;border:1px solid #00FF88}
.pulse{width:14px;height:14px;background:#00FF88;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}
@keyframes pulse{0%{transform:scale(0.9);opacity:1}50%{transform:scale(1.3);opacity:0.6}100%{transform:scale(0.9);opacity:1}}
</style>
</head>
<body>
<div class="header">
<div class="logo">TO<span>INDO</span> 🚗</div>
<div class="sub">Várzea Grande • Mais barato que Uber</div>
</div>

<div class="card">
<h3 style="margin:0 0 10px 0">Para onde vamos?</h3>
<input id="nome" placeholder="👤 Seu nome">
<input id="origem" placeholder="📍 De onde você está? Ex: Cohab São Simão">
<input id="destino" placeholder="🏁 Para onde vai? Ex: Centro">
<input id="zap" placeholder="📱 Seu WhatsApp">
<button class="btn" onclick="solicitar()">SOLICITAR CORRIDA AGORA</button>
<div id="status" class="status">
<div><span class="pulse"></span> <b id="stxt">Procurando motoristas perto de você...</b></div>
<p id="sdet" style="font-size:13px;color:#555;margin-top:8px"></p>
</div>
</div>

<div class="card" style="background:#111;color:white;border:1px solid #222">
<h4 style="margin:0">📲 Instalar App</h4>
<p style="font-size:13px;color:#888">Use como App de verdade</p>
<button class="btn btn2" onclick="instalar()">⬇️ INSTALAR TOINDO</button>
<a href="/motorista" style="display:block;margin-top:15px;color:#00FF88;text-decoration:none;font-size:13px">👉 Sou motorista - Ver corridas</a>
</div>

<script>
let deferredPrompt;
window.addEventListener('beforeinstallprompt', e=>{e.preventDefault();deferredPrompt=e;});
function instalar(){if(deferredPrompt)deferredPrompt.prompt();else alert('No topo clique nos 3 pontos ⋮ > Instalar app');}

async function solicitar(){
 const nome=document.getElementById('nome').value;
 const origem=document.getElementById('origem').value;
 const destino=document.getElementById('destino').value;
 const zap=document.getElementById('zap').value;
 if(!origem||!destino||!nome){alert('Preencha nome, origem e destino!');return;}
 document.getElementById('status').style.display='block';
 document.getElementById('stxt').innerText='Enviando solicitação...';
 document.getElementById('sdet').innerText=origem+' → '+destino;
 
 const res = await fetch('/api/solicitar', {
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({nome,origem,destino,zap})
 });
 const data = await res.json();
 if(data.ok){
   document.getElementById('stxt').innerText='✅ Corrida solicitada! Motorista a caminho!';
   document.getElementById('sdet').innerHTML='ID: '+data.id+'<br>Um motorista Toindo vai te chamar no WhatsApp: '+zap;
 }
}
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js');}
</script>
</body>
</html>
    """

@app.route('/motorista')
def motorista():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Motorista Toindo</title>
<meta name="theme-color" content="#000000">
<style>
body{font-family:Arial;margin:0;background:#000;color:white}
.header{background:#00FF88;color:black;padding:18px;text-align:center;font-weight:800;font-size:22px}
.card{background:#1a1a1a;margin:12px;padding:16px;border-radius:14px;border-left:4px solid #00FF88}
.btn{background:#00FF88;border:none;padding:12px 18px;border-radius:10px;font-weight:bold;margin:5px}
small{color:#aaa}
</style>
</head>
<body>
<div class="header">🚗 PAINEL MOTORISTA - TOINDO</div>
<div style="padding:10px;text-align:center"><button class="btn" onclick="load()">🔄 ATUALIZAR CORRIDAS</button>
<a href="/" style="color:#00FF88;font-size:13px">Voltar para App Cliente</a></div>
<div id="lista" style="padding:10px">Carregando...</div>
<script>
async function load(){
 const r = await fetch('/api/corridas');
 const corridas = await r.json();
 const div = document.getElementById('lista');
 if(corridas.length==0){div.innerHTML='<p style="text-align:center;color:#666">Nenhuma corrida no momento. Aguarde...</p>';return;}
 div.innerHTML='';
 corridas.reverse().forEach(c=>{
   div.innerHTML+=`<div class="card">
   <b>👤 ${c.nome}</b> - ${c.zap}<br>
   <small>📍 ${c.origem} → 🏁 ${c.destino}</small><br>
   <small>⏰ ${c.hora} - ID ${c.id.slice(0,6)}</small><br>
   <div style="margin-top:10px">
   <button class="btn" onclick="window.open('https://wa.me/55${c.zap.replace(/[^0-9]/g,'')}?text=Olá ${c.nome}! Aqui é motorista Toindo, vi sua corrida de ${c.origem} para ${c.destino}. Estou a caminho!')">💬 CHAMAR NO ZAP</button>
   <button class="btn" style="background:#333;color:white" onclick="aceitar('${c.id}')">✅ ACEITAR</button>
   </div>
   </div>`;
 });
}
async function aceitar(id){
 await fetch('/api/aceitar/'+id,{method:'POST'});
 alert('Corrida aceita! Chame o cliente no Zap!');
 load();
}
setInterval(load,5000);
load();
</script>
</body>
</html>
    """

@app.route('/api/solicitar', methods=['POST'])
def api_solicitar():
    data = request.json
    nova = {
        "id": str(uuid.uuid4()),
        "nome": data.get('nome','Cliente'),
        "origem": data.get('origem'),
        "destino": data.get('destino'),
        "zap": data.get('zap',''),
        "hora": datetime.now().strftime("%d/%m %H:%M"),
        "status": "pendente"
    }
    corridas.append(nova)
    return jsonify({"ok": True, "id": nova["id"]})

@app.route('/api/corridas')
def api_corridas():
    return jsonify(corridas)

@app.route('/api/aceitar/<id>', methods=['POST'])
def api_aceitar(id):
    global corridas
    corridas = [c for c in corridas if c['id'] != id]
    return jsonify({"ok": True})

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Toindo - Corridas",
        "short_name": "Toindo",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#000000",
        "theme_color": "#000000",
        "icons": [
            {"src": "https://cdn-icons-png.flaticon.com/512/3774/3774.png", "sizes": "512x512", "type": "image/png", "purpose":"any maskable"}
        ]
    })

@app.route('/sw.js')
def sw():
    return "self.addEventListener('install', e=>self.skipWaiting());self.addEventListener('activate', e=>self.clients.claim());", 200, {'Content-Type':'application/javascript'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
