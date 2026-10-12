from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import uuid
app = Flask(__name__)
CORS(app)
corridas = []
chats = {}
usuarios = []

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo V6</title>
<link rel="manifest" href="/manifest.json">
<style>
*{font-family:Arial,sans-serif;box-sizing:border-box}
body{margin:0;background:#000;color:white}
.header{background:#000;padding:20px;text-align:center;border-bottom:3px solid #00FF88}
.logo{font-size:34px;font-weight:900}.logo span{color:#00FF88}
.card{background:white;color:black;margin:12px;padding:18px;border-radius:18px}
input{width:100%;padding:16px;margin:7px 0;border:2px solid #eee;border-radius:12px;font-size:16px;background:#f9f9f9}
.btn{background:#00FF88;color:black;border:none;padding:16px;border-radius:12px;font-size:17px;width:100%;font-weight:900;margin-top:8px}
.btn2{background:black;color:#00FF88;border:2px solid #00FF88;padding:16px;border-radius:12px;width:100%;font-weight:900;margin-top:8px}
.opt{padding:20px;border:2px solid #eee;border-radius:15px;margin:10px 0;text-align:center;cursor:pointer}
.opt:hover{border-color:#00FF88;background:#f0fff5}
</style>
</head>
<body>
<div class="header"><div class="logo">🏍️ TO<span>INDO</span><br><small style="font-size:12px;color:#888">Moto Taxi VG - V6 Motorista</small></div></div>

<div id="tela-escolha" class="card">
<h2 style="text-align:center">Bem-vindo ao Toindo!</h2>
<p style="text-align:center" style="font-size:12px;color:#888">Escolha como quer entrar</p>
<div class="opt" onclick="irCadastro('passageiro')"><h3>👤 SOU PASSAGEIRO</h3><small>Quero pedir moto</small></div>
<div class="opt" onclick="irCadastro('motorista')"><h3>🏍️ SOU MOTORISTA</h3><small>Quero fazer corridas de moto</small></div>
<p style="text-align:center"><a href="#" onclick="jaTenho()" style="color:#00FF88">Já tenho cadastro</a></p>
</div>

<div id="tela-cadastro" class="card" style="display:none">
<h3 id="tituloCad">Cadastro</h3>
<input id="cad-nome" placeholder="👤 Seu nome completo">
<input id="cad-tel" placeholder="📱 WhatsApp">
<input id="cad-bairro" placeholder="🏠 Seu bairro">
<button class="btn" onclick="salvarCadastro()">CRIAR CONTA</button>
<button class="btn2" onclick="voltar()">VOLTAR</button>
</div>

<div id="tela-passageiro" class="card" style="display:none">
<div style="display:flex;justify-content:space-between"><b id="boasVindas">Olá!</b><a href="#" onclick="sair()" style="font-size:12px;color:red">Sair</a></div>
<h3>Para onde vamos de moto?</h3>
<div style="background:#f0fff5;padding:10px;border-radius:10px;border:1px dashed #00FF88;margin-bottom:8px">
<button class="btn" style="padding:10px;font-size:14px" onclick="pegarGPS()">📍 USAR MINHA LOCALIZAÇÃO ATUAL</button>
<small id="gpsStatus" style="font-size:11px;color:#666">Clique para pegar GPS</small>
</div>
<input id="origem" placeholder="📍 Origem">
<input id="destino" placeholder="🏁 Destino">
<button class="btn" onclick="solicitar()">SOLICITAR MOTO AGORA</button>
<div id="status" style="display:none;margin-top:12px;padding:14px;background:#f0fff5;border-radius:12px;border:2px solid #00FF88"></div>
</div>

<script>
let tipoAtual='passageiro'; let meuId=null;
function checkLogin(){
 const user=localStorage.getItem('toindo_user');
 if(user){
  const u=JSON.parse(user);
  if(u.tipo=='motorista'){ window.location.href='/motorista'; return; }
  document.getElementById('tela-escolha').style.display='none';
  document.getElementById('tela-passageiro').style.display='block';
  document.getElementById('boasVindas').innerText='Olá, '+u.nome+'!';
  document.getElementById('origem').value=u.bairro||'';
 } else { document.getElementById('tela-escolha').style.display='block'; }
}
checkLogin();
function irCadastro(t){ tipoAtual=t; document.getElementById('tela-escolha').style.display='none'; document.getElementById('tela-cadastro').style.display='block'; document.getElementById('tituloCad').innerText=t=='passageiro'?'Cadastro - Passageiro':'Cadastro - Motorista'; }
function voltar(){ document.getElementById('tela-cadastro').style.display='none'; document.getElementById('tela-escolha').style.display='block'; }
function jaTenho(){ const u=localStorage.getItem('toindo_user'); if(!u) alert('Você ainda não tem cadastro!'); else checkLogin(); }
function salvarCadastro(){
 const nome=document.getElementById('cad-nome').value;
 const tel=document.getElementById('cad-tel').value;
 const bairro=document.getElementById('cad-bairro').value;
 if(!nome||!tel){ alert('Preencha nome e tel!'); return; }
 const user={nome,tel,bairro,tipo:tipoAtual};
 localStorage.setItem('toindo_user', JSON.stringify(user));
 fetch('/api/usuarios',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(user)});
 if(tipoAtual=='motorista') window.location.href='/motorista';
 else { document.getElementById('tela-cadastro').style.display='none'; checkLogin(); }
}
function sair(){ localStorage.removeItem('toindo_user'); location.reload(); }
function pegarGPS(){
 const st=document.getElementById('gpsStatus'); st.innerText='Buscando GPS...';
 navigator.geolocation.getCurrentPosition(pos=>{
  const lat=pos.coords.latitude; const lon=pos.coords.longitude;
  document.getElementById('origem').value='Minha localização ('+lat.toFixed(4)+', '+lon.toFixed(4)+')';
  st.innerText='GPS OK';
 }, err=>{ st.innerText='Ative o GPS'; });
}
async function solicitar(){
 const user=JSON.parse(localStorage.getItem('toindo_user'));
 const origem=document.getElementById('origem').value; const destino=document.getElementById('destino').value;
 if(!origem||!destino){ alert('Coloque origem e destino'); return; }
 const r=await fetch('/api/solicitar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome:user.nome, tel:user.tel, origem, destino})});
 const d=await r.json(); meuId=d.id;
 const box=document.getElementById('status'); box.style.display='block';
 box.innerHTML='<b>🔍 Procurando motorista...</b><br><small>Motorista vai ver seu nome: '+user.nome+'</small><div id="chatArea"></div><div style="display:flex;gap:5px;margin-top:8px"><input id="msg" placeholder="Mensagem"><button class=btn style="width:80px;margin:0" onclick="enviar()">ENVIAR</button></div>';
 setInterval(verStatus,3000);
}
async function verStatus(){
 if(!meuId) return; const r=await fetch('/api/status/'+meuId); const c=await r.json(); if(!c) return;
 if(c.status=='aceita') document.getElementById('status').innerHTML='<b style=color:green>✅ '+c.nome_moto+' A CAMINHO!</b><br><small>'+c.origem+' -> '+c.destino+'</small><div id="chatArea"></div><div style="display:flex;gap:5px"><input id="msg"><button class=btn style="width:80px;margin:0" onclick="enviar()">ENVIAR</button></div>';
 loadChat();
}
async function enviar(){
 const t=document.getElementById('msg').value; if(!t) return;
 await fetch('/api/chat/'+meuId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({de:'cliente',texto:t})});
 document.getElementById('msg').value=''; loadChat();
}
async function loadChat(){
 if(!meuId) return; const r=await fetch('/api/chat/'+meuId); const msgs=await r.json();
 let h=''; msgs.forEach(m=>{h+='<div><span style="background:'+(m.de=='cliente'?'#000;color:white':'#00FF88')+';padding:6px 10px;border-radius:10px;margin:3px 0;display:inline-block"><b>'+m.de+':</b> '+m.texto+'</span></div>'});
 const el=document.getElementById('chatArea'); if(el) el.innerHTML=h;
}
</script>
</body>
</html>
    """

@app.route('/motorista')
def motorista():
    return """
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Painel Motorista</title>
<style>body{font-family:Arial;margin:0;background:#000;color:white}.header{background:#00FF88;color:black;padding:16px;text-align:center;font-weight:900}.card{background:#1a1a1a;margin:10px;padding:14px;border-radius:12px;border-left:4px solid #00FF88}.btn{background:#00FF88;border:none;padding:10px 14px;border-radius:8px;font-weight:900;margin:3px}input{width:100%;padding:10px;border-radius:8px;border:none}</style></head>
<body><div class="header">🏍️ PAINEL MOTORISTA - TOINDO V6</div><div style="padding:10px;text-align:center"><small id="motoNome"></small><br><button class=btn onclick="load()">ATUALIZAR</button> <button class=btn style="background:#333;color:white" onclick="sairMoto()">SAIR</button></div><div id="lista"></div>
<script>
let nomeMoto = JSON.parse(localStorage.getItem('toindo_user')||'{}').nome || 'Motorista';
document.getElementById('motoNome').innerText='Logado como Motorista: '+nomeMoto;
function sairMoto(){ localStorage.removeItem('toindo_user'); window.location.href='/'; }
async function load(){
 const r=await fetch('/api/corridas'); const cs=await r.json();
 const div=document.getElementById('lista');
 if(cs.length==0){div.innerHTML='<p style=text-align:center;color:#666>Nenhuma corrida</p>';return;}
 div.innerHTML=''; cs.reverse().forEach(c=>{
  div.innerHTML+=`<div class=card><b>#${c.id.slice(0,5)}</b> - ${c.status.toUpperCase()}<br>👤 Passageiro: ${c.nome}<br>📱 ${c.tel||''}<br>📍 ${c.origem} -> 🏁 ${c.destino}<br><small>⏰ ${c.hora}</small><br><div style=margin-top:8px><button class=btn onclick="aceitar('${c.id}')">ACEITAR</button><button class=btn style=background:white onclick="chegou('${c.id}')">CHEGUEI</button><button class=btn style=background:#333;color:white onclick="finalizar('${c.id}')">FINALIZAR</button></div><div id="chat-${c.id}" style=margin-top:10px;background:#000;padding:8px;border-radius:8px"></div><div style=display:flex;gap:4px><input id="msg-${c.id}" placeholder="Responder passageiro"><button class=btn onclick="enviar('${c.id}')">ENVIAR</button></div></div>`; loadChat(c.id);
 });
}
async function aceitar(id){await fetch('/api/aceitar/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome_moto:nomeMoto})}); load();}
async function chegou(id){await fetch('/api/chegou/'+id,{method:'POST'}); load();}
async function finalizar(id){await fetch('/api/finalizar/'+id,{method:'POST'}); load();}
async function enviar(id){
 const t=document.getElementById('msg-'+id).value; if(!t) return;
 await fetch('/api/chat/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({de:'motorista',texto:t})});
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
    nova={"id":nid,"nome":d.get('nome'),"tel":d.get('tel'),"origem":d.get('origem'),"destino":d.get('destino'),"hora":datetime.now().strftime("%H:%M"),"status":"procurando","nome_moto":""}
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
    data=request.json or {}
    for c in corridas:
        if c['id']==id: c['status']='aceita'; c['nome_moto']=data.get('nome_moto','Motorista')
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
@app.route('/api/usuarios', methods=['POST','GET'])
def users():
    if request.method=='POST': usuarios.append(request.json); return jsonify({"ok":True})
    return jsonify(usuarios)
@app.route('/icon.png')
def icon(): return send_from_directory('.', 'icon.png')
@app.route('/manifest.json')
def manifest():
    return jsonify({"name":"Toindo","short_name":"Toindo","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#00FF88","icons":[{"src":"/icon.png","sizes":"512x512","type":"image/png"}]})
if __name__=='__main__': app.run(host='0.0.0.0',port=10000)
