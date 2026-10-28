from flask import Flask, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)
corridas = []
usuarios = []

HTML_HOME = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo - Seu transporte em Várzea Grande</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00C853">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f5f5f5}
.header{background:#00C853;color:white;padding:15px;text-align:center;position:sticky;top:0;z-index:10}
.logo{font-size:28px;font-weight:bold}
.container{max-width:480px;margin:0 auto;padding:15px}
.card{background:white;border-radius:16px;padding:20px;margin:10px 0;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.btn{background:#00C853;color:white;border:none;padding:15px 25px;border-radius:12px;width:100%;font-size:16px;font-weight:bold;cursor:pointer;margin:5px 0}
.btn:disabled{background:#ccc}
.btn-outline{background:white;color:#00C853;border:2px solid #00C853}
.input{width:100%;padding:14px;border:1px solid #ddd;border-radius:10px;margin:8px 0;font-size:15px}
.badge{padding:5px 10px;border-radius:20px;font-size:12px;display:inline-block}
.badge-green{background:#e8f5e9;color:#00C853}
.badge-yellow{background:#fff8e1;color:#f57f17}
.tabs{display:flex;gap:10px;margin:15px 0}
.tab{flex:1;padding:12px;text-align:center;background:#eee;border-radius:10px;cursor:pointer}
.tab.active{background:#00C853;color:white}
.hidden{display:none}
.corrida-item{border-left:4px solid #00C853;padding:12px;background:#fafffe;margin:10px 0;border-radius:8px}
</style>
</head>
<body>
<div class="header"><div class="logo">🚗 Toindo</div><small>Várzea Grande - MT</small></div>
<div class="container">

<div id="tela-home" class="card">
<h2>Bem-vindo ao Toindo!</h2>
<p style="margin:10px 0;color:#666">O app de mobilidade de Várzea Grande</p>
<div class="tabs">
<div class="tab active" onclick="mostrar('passageiro')">Passageiro</div>
<div class="tab" onclick="mostrar('motorista')">Motorista</div>
</div>

<div id="passageiro">
<h3>🧍 Sou Passageiro</h3>
<input id="nome" class="input" placeholder="Seu nome completo">
<input id="tel" class="input" placeholder="WhatsApp (ex: 65999999999)">
<input id="origem" class="input" placeholder="De onde? Ex: Centro Várzea Grande">
<input id="destino" class="input" placeholder="Para onde? Ex: Aeroporto Várzea Grande">
<button class="btn" onclick="solicitar()">🚀 Solicitar Corrida Agora</button>
<p id="msg" style="margin-top:10px"></p>
<div id="minhas-corridas"></div>
</div>

<div id="motorista" class="hidden">
<h3>🚙 Sou Motorista</h3>
<input id="nomeM" class="input" placeholder="Seu nome">
<input id="telM" class="input" placeholder="WhatsApp">
<input id="carroM" class="input" placeholder="Carro e placa - Ex: Onix ABC1234">
<button class="btn" onclick="cadastrarMotorista()">✅ Me Cadastrar como Motorista</button>
<p id="msgM" style="margin-top:10px"></p>
<button class="btn btn-outline" onclick="carregarCorridas()">🔄 Ver Corridas Disponíveis</button>
<div id="lista-corridas"></div>
</div>
</div>

<div class="card" style="font-size:13px;color:#888;text-align:center">
📲 Instale no celular: no Chrome clique nos 3 pontinhos > Instalar App<br>
Toindo v2.0 - Feito para Várzea Grande
</div>
</div>

<script>
let meuId = localStorage.getItem('toindo_id') || '';
let meuTipo = localStorage.getItem('toindo_tipo') || '';

function mostrar(t){
 document.getElementById('passageiro').classList.toggle('hidden', t!=='passageiro');
 document.getElementById('motorista').classList.toggle('hidden', t!=='motorista');
 document.querySelectorAll('.tab').forEach((el,i)=>{el.classList.toggle('active',(i==0&&t=='passageiro')||(i==1&&t=='motorista'))});
}
async function cadastrarMotorista(){
 const nome=document.getElementById('nomeM').value;
 const tel=document.getElementById('telM').value;
 const carro=document.getElementById('carroM').value;
 if(!nome||!tel){alert('Preencha nome e telefone');return}
 const r=await fetch('/api/usuarios',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome,tel,tipo:'motorista',carro})});
 const d=await r.json();
 meuId=d.id; localStorage.setItem('toindo_id',meuId); localStorage.setItem('toindo_tipo','motorista');
 document.getElementById('msgM').innerHTML='✅ Cadastrado! Aguarde aprovação. ID: '+d.id;
}
async function solicitar(){
 const nome=document.getElementById('nome').value;
 const tel=document.getElementById('tel').value;
 const origem=document.getElementById('origem').value;
 const destino=document.getElementById('destino').value;
 if(!nome||!tel||!origem||!destino){alert('Preencha tudo!');return}
 if(!meuId){
  const ru=await fetch('/api/usuarios',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome,tel,tipo:'passageiro'})});
  const du=await ru.json(); meuId=du.id; localStorage.setItem('toindo_id',meuId);
 }
 const r=await fetch('/api/solicitar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usuario_id:meuId,origem,destino,nome,tel})});
 const d=await r.json();
 document.getElementById('msg').innerHTML='✅ Corrida solicitada! Código: <b>'+d.id.slice(0,8)+'</b><br>Motoristas de VG vão aceitar.';
 carregarMinhas();
}
async function carregarCorridas(){
 const r=await fetch('/api/corridas'); const lista=await r.json();
 const div=document.getElementById('lista-corridas'); div.innerHTML='<h4>Corridas em aberto ('+lista.length+')</h4>';
 lista.forEach(c=>{
  if(c.status!=='solicitada') return;
  div.innerHTML+=`<div class="corrida-item"><b>${c.origem} → ${c.destino}</b><br><small>${c.nome} - ${c.tel} - ${new Date(c.data).toLocaleTimeString()}</small><br><button class="btn" style="margin-top:8px" onclick="aceitar('${c.id}')">Aceitar Corrida</button></div>`;
 });
}
async function aceitar(id){
 if(!meuId){alert('Se cadastre como motorista primeiro!');return}
 await fetch('/api/aceitar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({corrida_id:id,motorista_id:meuId})});
 alert('Corrida aceita! Entre em contato com o passageiro.'); carregarCorridas();
}
async function carregarMinhas(){
 if(!meuId) return;
 const r=await fetch('/api/minhas/'+meuId); const lista=await r.json();
 const div=document.getElementById('minhas-corridas'); div.innerHTML='<h4 style="margin-top:15px">Minhas corridas</h4>';
 lista.forEach(c=>{div.innerHTML+=`<div class="corrida-item"><b>${c.origem} → ${c.destino}</b> <span class="badge badge-green">${c.status}</span><br><small>${new Date(c.data).toLocaleString()}</small></div>`});
}
carregarMinhas();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_HOME

@app.route('/api/usuarios', methods=['POST'])
def api_usuarios():
    d=request.json
    nid=str(uuid.uuid4())
    usuarios.append({"id":nid,"nome":d.get('nome'),"tel":d.get('tel'),"tipo":d.get('tipo'),"carro":d.get('carro',''),"status":"aprovado" if d.get('tipo')=='passageiro' else "pendente","data":datetime.now().isoformat()})
    return jsonify({"ok":True,"id":nid,"status":"aprovado" if d.get('tipo')=='passageiro' else "pendente"})

@app.route('/api/solicitar', methods=['POST'])
def api_solicitar():
    d=request.json
    nid=str(uuid.uuid4())
    corridas.append({"id":nid,"usuario_id":d.get('usuario_id'),"nome":d.get('nome'),"tel":d.get('tel'),"origem":d.get('origem'),"destino":d.get('destino'),"status":"solicitada","motorista_id":None,"data":datetime.now().isoformat()})
    return jsonify({"ok":True,"id":nid})

@app.route('/api/corridas')
def api_corridas():
    return jsonify(corridas[::-1])

@app.route('/api/minhas/<uid>')
def api_minhas(uid):
    return jsonify([c for c in corridas if c['usuario_id']==uid][::-1])

@app.route('/api/aceitar', methods=['POST'])
def api_aceitar():
    d=request.json
    for c in corridas:
        if c['id']==d.get('corrida_id'):
            c['status']='aceita'
            c['motorista_id']=d.get('motorista_id')
            c['aceita_em']=datetime.now().isoformat()
    return jsonify({"ok":True})

@app.route('/manifest.json')
def manifest():
    return jsonify({"name":"Toindo","short_name":"Toindo","start_url":"/","display":"standalone","background_color":"#00C853","theme_color":"#00C853"})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=10000)
