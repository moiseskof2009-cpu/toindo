from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

corridas = []
chats = {}

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo - Moto Taxi VG</title>
<link rel="manifest" href="/manifest.json">
<style>
*{font-family:Arial,sans-serif;box-sizing:border-box}
body{margin:0;background:#000;color:white}
.header{background:#000;padding:22px;text-align:center;border-bottom:3px solid #00FF88}
.logo{font-size:36px;font-weight:900;letter-spacing:1px}.logo span{color:#00FF88}
.card{background:white;color:black;margin:14px;padding:18px;border-radius:18px}
input{width:100%;padding:16px;margin:7px 0;border:2px solid #eee;border-radius:12px;font-size:16px;background:#f9f9f9}
.btn{background:#00FF88;color:black;border:none;padding:16px;border-radius:12px;font-size:17px;width:100%;font-weight:900;margin-top:10px}
.status{display:none;margin-top:12px;padding:14px;background:#f0fff5;border-radius:12px;border:2px solid #00FF88}
.dot{width:10px;height:10px;background:#00FF88;border-radius:50%;display:inline-block;animation:blink 1s infinite}
@keyframes blink{50%{opacity:0.2}}
</style>
</head>
<body>
<div class="header"><div class="logo">🏍️ TO<span>INDO</span><br><small style="font-size:13px;color:#888;font-weight:400">Moto Taxi - Varzea Grande - V4</small></div></div>
<div class="card">
<h3 style="margin:0 0 10px 0">Para onde vamos de moto?</h3>
<input id="nome" placeholder="👤 Seu nome">
<input id="origem" placeholder="📍 Origem - Ex: Sao Simao">
<input id="destino" placeholder="🏁 Destino - Ex: Aeroporto">
<button class="btn" onclick="solicitar()">SOLICITAR MOTO AGORA</button>
<div id="status" class="status"></div>
</div>
<div class="card" style="background:#111;color:white;border:1px solid #222;text-align:center">
<a href="/motorista" style="color:#00FF88;text-decoration:none;font-weight:bold">👉 ENTRAR COMO MOTOTAXISTA</a><br><small style="color:#666">Chat anonimo - sem WhatsApp</small>
</div>
<script>
let meuId=null;
async function solicitar(){
 const nome=document.getElementById('nome').value;
 const origem=document.getElementById('origem').value;
 const destino=document.getElementById('destino').value;
 if(!nome||!origem||!destino){alert('Preencha tudo!');return;}
 const r=await fetch('/api/solicitar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome,origem,destino})});
 const d=await r.json(); meuId=d.id;
 const box=document.getElementById('status'); box.style.display='block';
 box.innerHTML='<span class=dot></span> <b>Procurando mototaxista...</b><br><small>ID: #'+d.id.slice(0,5)+'</small><div id="chatArea" style="margin-top:10px"></div><div style="display:flex;gap:5px;margin-top:8px"><input id="msg" placeholder="Mensagem" style="margin:0"><button class=btn style="width:80px;margin:0" onclick="enviar()">ENVIAR</button></div>';
 setInterval(verStatus,3000);
}
async function verStatus(){
 if(!meuId) return;
 const r=await fetch('/api/status/'+meuId); const c=await r.json(); if(!c) return;
 loadChat();
 if(c.status=='aceita') document.getElementById('status').innerHTML='<span class=dot></span> <b style=color:green>✅ MOTOTAXISTA A CAMINHO!</b><br><small>'+c.origem+' -> '+c.destino+'</small><div id="chatArea" style="margin-top:10px"></div><div style="display:flex;gap:5px;margin-top:8px"><input id="msg" placeholder="Fala com o moto" style="margin:0"><button class=btn style="width:80px;margin:0" onclick="enviar()">ENVIAR</button></div>';
 if(c.status=='chegou') document.getElementById('status').innerHTML='<b style=color:green>🏍️ MOTO CHEGOU!</b><div id="chatArea" style="margin-top:10px"></div><div style="display:flex;gap:5px;margin-top:8px"><input id="msg" placeholder="Mensagem" style="margin:0"><button class=btn style="width:80px;margin:0" onclick="enviar()">ENVIAR</button></div>';
}
async function enviar(){
 const texto=document.getElementById('msg').value; if(!texto) return;
 await fetch('/api/chat/'+meuId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({de:'cliente',texto})});
 document.getElementById('msg').value=''; loadChat();
}
async function loadChat(){
 if(!meuId) return;
 const r=await fetch('/api/chat/'+meuId); const msgs=await r.json();
 let h=''; msgs.forEach(m=>{h+='<div><span style="background:'+(m.de=='cliente'?'#000;color:white':'#00FF88;color:black')+';padding:6px 10px;border-radius:10px;margin:3px 0;display:inline-block"><b>'+m.de+':</b> '+m.texto+'</span></div>'});
 const el=document.getElementById('chatArea'); if(el) el.innerHTML=h;
}
setInterval(loadChat,2000);
</script>
</body>
</html>
    """

@app.route('/motorista')
def motorista():
    return """
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Moto Toindo</title>
<style>body{font-family:Arial;margin:0;background:#000;color:white}.header{background:#00FF88;color:black;padding:16px;text-align:center;font-weight:900}.card{background:#1a1a1a;margin:10px;padding:14px;border-radius:12px;border-left:4px solid #00FF88}.btn{background:#00FF88;border:none;padding:10px 14px;border-radius:8px;font-weight:900;margin:3px}input{width:100%;padding:10px;border-radius:8px;border:none;margin-top:6px}</style></head>
<body><div class="header">🏍️ PAINEL MOTO - TOINDO V4</div><div style="text-align:center;padding:10px"><button class=btn onclick="load()">🔄 ATUALIZAR</button></div><div id="lista"></div>
<script>
async function load(){
 const r=await fetch('/api/corridas'); const cs=await r.json();
 const div=document.getElementById('lista');
 if(cs.length==0){div.innerHTML='<p style=text-align:center;color:#666>Nenhuma corrida</p>';return;}
 div.innerHTML=''; cs.reverse().forEach(c=>{
  div.innerHTML+=`<div class=card><b>#${c.id.slice(0,5)}</b> - ${c.status.toUpperCase()}<br>👤 ${c.nome}<br>📍 ${c.origem} -> 🏁 ${c.destino}<br><small>⏰ ${c.hora}</small><br><div style=margin-top:8px><button class=btn onclick="aceitar('${c.id}')">✅ ACEITAR</button><button class=btn style=background:white onclick="chegou('${c.id}')">📍 CHEGUEI</button><button class=btn style=background:#333;color:white onclick="finalizar('${c.id}')">🏁 FINALIZAR</button></div><div id="chat-${c.id}" style=margin-top:10px;background:#000;padding:8px;border-radius:8px"></div><div style=display:flex;gap:4px><input id="msg-${c.id}" placeholder="Responder"><button class=btn onclick="enviar('${c.id}')">ENVIAR</button></div></div>`; loadChat(c.id);
 });
}
async function aceitar(id){await fetch('/api/aceitar/'+id,{method:'POST'}); load();}
async function chegou(id){await fetch('/api/chegou/'+id,{method:'POST'}); load();}
async function finalizar(id){await fetch('/api/finalizar/'+id,{method:'POST'}); load();}
async function enviar(id){
 const t=document.getElementById('msg-'+id).value; if(!t) return;
 await fetch('/api/chat/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({de:'mototaxista',texto:t})});
 document.getElementById('msg-'+id).value=''; loadChat(id);
}
async function loadChat(id){
 const r=await fetch('/api/chat/'+id); const msgs=await r.json();
 let h=''; msgs.forEach(m=>{h+=`<div style="font-size:13px;margin:3px 0"><b>${m.de}:</b> ${m.texto}</div>`});
 const el=document.getElementById('chat-'+id); if(el) el.innerHTML=h;
}
setInterval(load,4000); load();
</script></body></html>
    """

@app.route('/api/solicitar', methods=['POST'])
def solicitar_api():
    d=request.json
    nid=str(uuid.uuid4())
    nova={"id":nid,"nome":d.get('nome'),"origem":d.get('origem'),"destino":d.get('destino'),"hora":datetime.now().strftime("%H:%M"),"status":"procurando"}
    corridas.append(nova); chats[nid]=[]
    return jsonify({"ok":True,"id":nid})

@app.route('/api/corridas')
def list_corridas(): return jsonify([c for c in corridas if c['status']!='finalizada'])

@app.route('/api/status/<id>')
def status_corrida(id):
    for c in corridas:
        if c['id']==id: return jsonify(c)
    return jsonify(None)

@app.route('/api/aceitar/<id>', methods=['POST'])
def aceitar(id):
    for c in corridas:
        if c['id']==id: c['status']='aceita'
    return jsonify({"ok":True})

@app.route('/api/chegou/<id>', methods=['POST'])
def chegou(id):
    for c in corridas:
        if c['id']==id: c['status']='chegou'
    return jsonify({"ok":True})

@app.route('/api/finalizar/<id>', methods=['POST'])
def finalizar(id):
    for c in corridas:
        if c['id']==id: c['status']='finalizada'
    return jsonify({"ok":True})

@app.route('/api/chat/<id>', methods=['GET','POST'])
def chat(id):
    if request.method=='POST':
        data=request.json
        if id not in chats: chats[id]=[]
        chats[id].append({"de":data.get('de'),"texto":data.get('texto')})
        return jsonify({"ok":True})
    else:
        return jsonify(chats.get(id,[]))

@app.route('/icon.png')
def icon(): return send_from_directory('.', 'icon.png')

@app.route('/manifest.json')
def manifest():
    return jsonify({"name":"Toindo Moto Taxi","short_name":"Toindo","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#00FF88","icons":[{"src":"/icon.png","sizes":"512x512","type":"image/png"}]})

if __name__=='__main__': app.run(host='0.0.0.0',port=10000)
