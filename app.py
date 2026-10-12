from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import uuid
app = Flask(__name__)
CORS(app)

corridas=[]
chats={}
usuarios=[] # lista de motoristas/passageiros cadastrados

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo</title><link rel="manifest" href="/manifest.json">
<style>
*{font-family:Arial;box-sizing:border-box}body{margin:0;background:#000;color:#fff}
.header{background:#000;padding:18px;text-align:center;border-bottom:3px solid #00FF88}
.logo{font-size:32px;font-weight:900}.logo span{color:#00FF88}
.card{background:#fff;color:#000;margin:12px;padding:18px;border-radius:18px}
input{width:100%;padding:14px;margin:6px 0;border:2px solid #eee;border-radius:10px;background:#f9f9f9}
.btn{background:#00FF88;color:#000;border:none;padding:15px;border-radius:12px;width:100%;font-weight:900;margin-top:8px}
.btn2{background:#000;color:#00FF88;border:2px solid #00FF88;padding:12px;border-radius:10px;width:100%;font-weight:900;margin-top:6px}
.opt{padding:18px;border:2px solid #eee;border-radius:14px;margin:10px 0;text-align:center;cursor:pointer}
.opt:hover{border-color:#00FF88;background:#f0fff5}
</style>
</head>
<body>
<div class="header"><div class="logo">🏍️ TO<span>INDO</span><br><small style="font-size:11px;color:#888">V8 - Igual ontem, só arrumado pra rodar</small></div></div>

<div id="tela-escolha" class="card">
<h3 style="text-align:center">Bem-vindo ao Toindo</h3>
<div class="opt" onclick="irCad('passageiro')"><b>👤 SOU PASSAGEIRO</b><br><small>Pedir moto</small></div>
<div class="opt" onclick="irCad('motorista')"><b>🏍️ SOU MOTORISTA</b><br><small>Fazer corridas</small></div>
<div style="text-align:center;margin-top:10px"><a href="#" onclick="checkLogin(true)" style="color:#00FF88">Já tenho cadastro - Entrar direto</a></div>
</div>

<div id="tela-cad" class="card" style="display:none">
<h3 id="titCad">Cadastro</h3>
<input id="nome" placeholder="Nome completo">
<input id="cpf" placeholder="CPF">
<input id="tel" placeholder="WhatsApp (65) 9xxxx-xxxx">
<input id="email" placeholder="E-mail">
<input id="endereco" placeholder="Endereço">
<input id="motoInfo" placeholder="Moto - Ex: Titan 160 preta - Placa BRA1234">
<input id="senha" type="password" placeholder="Crie uma senha">
<button class="btn" onclick="salvar()">CRIAR CONTA E SALVAR NO CELULAR</button>
<button class="btn2" onclick="voltar()">VOLTAR</button>
<small style="color:#888">*Uma vez cadastrado, fica salvo. Não pede mais.</small>
</div>

<div id="tela-passageiro" class="card" style="display:none">
<div style="display:flex;justify-content:space-between"><b id="bv"></b><a href="#" onclick="sair()" style="color:red;font-size:12px">Sair</a></div>
<h3>Para onde vamos?</h3>
<button class="btn" style="padding:10px" onclick="gps()">📍 USAR MEU GPS</button>
<small id="gpsSt" style="color:#666"></small>
<input id="origem" placeholder="Origem">
<input id="destino" placeholder="Destino">
<button class="btn" onclick="pedir()">SOLICITAR MOTO</button>
<div id="statusBox" style="display:none;margin-top:10px;padding:12px;background:#f0fff5;border:2px solid #00FF88;border-radius:10px"></div>
</div>

<script>
let tipo='passageiro'; let meuId=null;
function checkLogin(forcar=false){
 const u=localStorage.getItem('toindo_user');
 if(u){
  const user=JSON.parse(u);
  if(user.tipo=='motorista' && user.status!='APROVADO' &&!forcar){ alert('Seu cadastro de motorista está em análise. Aguarde aprovação no painel admin.'); return; }
  if(user.tipo=='motorista'){ window.location.href='/motorista'; return; }
  document.getElementById('tela-escolha').style.display='none';
  document.getElementById('tela-cad').style.display='none';
  document.getElementById('tela-passageiro').style.display='block';
  document.getElementById('bv').innerText='Olá, '+user.nome;
  document.getElementById('origem').value=user.endereco||'';
 } else if(forcar){ alert('Nenhum cadastro salvo nesse celular. Faça o cadastro.'); }
}
checkLogin();
function irCad(t){ tipo=t; document.getElementById('tela-escolha').style.display='none'; document.getElementById('tela-cad').style.display='block'; document.getElementById('titCad').innerText=t=='passageiro'?'Cadastro Passageiro':'Cadastro Motorista'; document.getElementById('motoInfo').style.display=t=='motorista'?'block':'none'; }
function voltar(){ document.getElementById('tela-cad').style.display='none'; document.getElementById('tela-escolha').style.display='block'; }
function sair(){ if(confirm('Tem certeza? Vai ter que cadastrar de novo se desinstalar.')){ localStorage.removeItem('toindo_user'); location.reload(); } }

function salvar(){
 const user={
  id: Date.now().toString(),
  nome: document.getElementById('nome').value,
  cpf: document.getElementById('cpf').value,
  tel: document.getElementById('tel').value,
  email: document.getElementById('email').value,
  endereco: document.getElementById('endereco').value,
  moto: document.getElementById('motoInfo').value,
  senha: document.getElementById('senha').value,
  tipo: tipo,
  status: tipo=='motorista'?'PENDENTE':'APROVADO',
  data: new Date().toLocaleString()
 };
 if(!user.nome||!user.tel){ alert('Preencha nome e zap'); return; }
 localStorage.setItem('toindo_user', JSON.stringify(user));
 fetch('/api/usuarios',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(user)});
 alert(tipo=='motorista'?'Cadastro enviado! Aguarde aprovação no Painel Admin.':'Cadastro salvo! Agora não pede mais.');
 if(tipo=='motorista'){ location.reload(); } else { checkLogin(); }
}
function gps(){
 navigator.geolocation.getCurrentPosition(p=>{
  document.getElementById('origem').value='GPS: '+p.coords.latitude.toFixed(5)+','+p.coords.longitude.toFixed(5);
  document.getElementById('gpsSt').innerText='GPS OK';
 });
}
async function pedir(){
 const u=JSON.parse(localStorage.getItem('toindo_user'));
 const origem=document.getElementById('origem').value; const destino=document.getElementById('destino').value;
 if(!origem||!destino){ alert('Coloque origem e destino'); return; }
 const r=await fetch('/api/solicitar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome:u.nome,tel:u.tel,origem,destino})});
 const d=await r.json(); meuId=d.id;
 const b=document.getElementById('statusBox'); b.style.display='block'; b.innerHTML='🔍 Procurando motorista...'; setInterval(verSt,3000);
}
async function verSt(){
 if(!meuId) return; const r=await fetch('/api/status/'+meuId); const c=await r.json(); if(!c) return;
 if(c.status=='aceita') document.getElementById('statusBox').innerHTML='✅ <b>'+c.nome_moto+'</b> a caminho!';
}
</script>
</body>
</html>
    """

@app.route('/motorista')
def motorista():
    return """<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Motorista</title>
<style>body{background:#000;color:#fff;font-family:Arial;margin:0}.header{background:#00FF88;color:#000;padding:14px;text-align:center;font-weight:900}.card{background:#1a1a1a;margin:10px;padding:12px;border-radius:10px;border-left:4px solid #00FF88}.btn{background:#00FF88;border:none;padding:8px 12px;border-radius:6px;font-weight:900}</style></head>
<body><div class="header">🏍️ PAINEL MOTORISTA</div><div style="padding:10px;text-align:center"><small id="nm"></small> <button class=btn onclick="load()">ATUALIZAR</button> <button class=btn style="background:#333;color:#fff" onclick="localStorage.removeItem('toindo_user');location.href='/'">SAIR</button></div><div id="lista"></div>
<script>
let nome=JSON.parse(localStorage.getItem('toindo_user')||'{}').nome||'Motorista'; document.getElementById('nm').innerText=nome;
async function load(){ const r=await fetch('/api/corridas'); const cs=await r.json(); const d=document.getElementById('lista'); if(cs.length==0){d.innerHTML='<p style=text-align:center>Sem corridas</p>';return;} d.innerHTML=''; cs.reverse().forEach(c=>{d.innerHTML+=`<div class=card><b>${c.nome}</b> - ${c.origem} -> ${c.destino}<br><button class=btn onclick="aceitar('${c.id}')">ACEITAR</button></div>`});}
async function aceitar(id){ await fetch('/api/aceitar/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome_moto:nome})}); load(); }
setInterval(load,4000); load();
</script></body></html>"""

@app.route('/admin')
def admin():
    return """
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Toindo</title>
<style>body{background:#000;color:#fff;font-family:Arial;margin:0;padding:10px}h2{color:#FFD700}.card{background:#1a1a1a;padding:12px;border-radius:10px;margin:10px 0;border-left:4px solid #FFD700}.btn{padding:8px 12px;border:none;border-radius:6px;font-weight:900;margin:3px}.aprov{background:#00FF88}.excl{background:#ff4444;color:#fff}.zap{background:#25D366;color:#fff}</style></head>
<body>
<h2>PAINEL ADMIN - TOINDO</h2>
<div><span id="total"></span> | <button class=btn aprov onclick="aprovarTodos()">Aprovar TODOS</button></div>
<div id="lista"></div>
<script>
async function load(){
 const r=await fetch('/api/usuarios'); const us=await r.json();
 document.getElementById('total').innerText='Total: '+us.length+' | Pendentes: '+us.filter(u=>u.status=='PENDENTE').length;
 const d=document.getElementById('lista'); d.innerHTML='';
 us.reverse().forEach(u=>{
  d.innerHTML+=`<div class=card><b>${u.nome}</b> - ${u.status||'APROVADO'}<br>CPF: ${u.cpf||''}<br>Tel: ${u.tel}<br>Email: ${u.email||''}<br>End: ${u.endereco||''}<br>Moto: ${u.moto||''}<br>ID: ${u.id}<br><br><button class="btn aprov" onclick="aprovar('${u.id}')">APROVAR</button><button class="btn excl" onclick="excluir('${u.id}')">EXCLUIR</button><button class="btn zap" onclick="zap('${u.tel}','${u.nome}')">ENVIAR ZAP APROVADO</button></div>`;
 });
}
async function aprovar(id){ await fetch('/api/aprovar/'+id,{method:'POST'}); load(); }
async function excluir(id){ if(!confirm('Excluir?'))return; await fetch('/api/excluir/'+id,{method:'POST'}); load(); }
async function aprovarTodos(){ await fetch('/api/aprovar_todos',{method:'POST'}); load(); }
function zap(tel,nome){ const msg=encodeURIComponent('Olá '+nome+'! Seu cadastro no TOINDO foi APROVADO! 🏍️ Já pode abrir o app e fazer corridas.'); window.open('https://wa.me/55'+tel.replace(/\\D/g,'')+'?text='+msg,'_blank'); }
setInterval(load,3000); load();
</script>
</body></html>
    """

@app.route('/api/usuarios', methods=['GET','POST'])
def usuarios_api():
    global usuarios
    if request.method=='POST': usuarios.append(request.json); return jsonify({"ok":True})
    return jsonify(usuarios)
@app.route('/api/aprovar/<id>', methods=['POST'])
def aprovar(id):
    for u in usuarios:
        if str(u.get('id'))==str(id): u['status']='APROVADO'
    return jsonify({"ok":True})
@app.route('/api/excluir/<id>', methods=['POST'])
def excluir(id):
    global usuarios
    usuarios=[u for u in usuarios if str(u.get('id'))!=str(id)]
    return jsonify({"ok":True})
@app.route('/api/aprovar_todos', methods=['POST'])
def aprovar_todos():
    for u in usuarios: u['status']='APROVADO'
    return jsonify({"ok":True})
@app.route('/api/solicitar', methods=['POST'])
def solicitar():
    d=request.json; nid=str(uuid.uuid4()); corridas.append({"id":nid,"nome":d.get('nome'),"tel":d.get('tel'),"origem":d.get('origem'),"destino":d.get('destino'),"hora":datetime.now().strftime("%H:%M"),"status":"procurando","nome_moto":""}); chats[nid]=[]; return jsonify({"ok":True,"id":nid})
@app.route('/api/corridas')
def corridas_api(): return jsonify([c for c in corridas if c['status']!='finalizada'])
@app.route('/api/status/<id>')
def status_api(id):
    for c in corridas:
        if c['id']==id: return jsonify(c)
    return jsonify(None)
@app.route('/api/aceitar/<id>', methods=['POST'])
def aceitar_api(id):
    data=request.json or {}
    for c in corridas:
        if c['id']==id: c['status']='aceita'; c['nome_moto']=data.get('nome_moto','Motorista')
    return jsonify({"ok":True})
@app.route('/icon.png')
def icon(): return send_from_directory('.', 'icon.png')
@app.route('/manifest.json')
def manifest(): return jsonify({"name":"Toindo","short_name":"Toindo","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#00FF88","icons":[{"src":"/icon.png","sizes":"512x512","type":"image/png"}]})
if __name__=='__main__': app.run(host='0.0.0.0',port=10000)
