from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

corridas = []
usuarios = []

HTML_HOME = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{font-family:Arial,sans-serif;box-sizing:border-box;margin:0;padding:0}
body{background:#f5f5f5}
.top-yellow{background:#FFEB3B;padding:12px 14px}
.map-box{height:300px;background:#e0e0e0}
#map{height:100%;width:100%}
.card-search{background:#fff;margin:-30px 14px 10px 14px;border-radius:16px;padding:14px;box-shadow:0 4px 12px rgba(0,0,0,0.15);position:relative;z-index:10}
.search-input{width:100%;padding:12px;border:1px solid #e0e0e0;border-radius:10px;background:#f7f7f7;font-size:16px}
.origem-box{display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #f0f0f0}
.origem-dot{width:10px;height:10px;background:#FFC107;border-radius:50%;margin-right:10px}
.dest-dot{width:10px;height:10px;background:#000;margin-right:10px;transform:rotate(45deg)}
.sugestao{padding:10px 4px;border-bottom:1px solid #f0f0f0;cursor:pointer;display:flex;justify-content:space-between}
.btn-moto{background:#00FF88;color:#000;border:none;padding:16px;border-radius:14px;width:100%;font-weight:900;font-size:16px;margin-top:12px}
.header-black{background:#000;color:#fff;padding:12px;text-align:center}
.logo{font-weight:900;font-size:22px}
.tela{display:none}.tela.active{display:block}
.card{background:#fff;margin:10px;border-radius:16px;padding:16px;color:#000}
input{width:100%;padding:13px;margin:6px 0;border:2px solid #eee;border-radius:10px;background:#f9f9f9}
.btn{background:#00FF88;color:#000;border:none;padding:14px;border-radius:10px;width:100%;font-weight:900;margin-top:8px}
.aguardando{background:#FFF3CD;padding:20px;border-radius:14px;border:2px solid #FFC107;text-align:center;margin:20px 10px}
</style>
</head>
<body>
<div id="tela-inicio" class="tela active">
<div class="header-black"><div class="logo">TOINDO</div></div>
<div class="card" style="text-align:center">
<h3>Bem-vindo ao Toindo</h3><br>
<div style="padding:18px;border:2px solid #eee;border-radius:14px;margin:10px 0;cursor:pointer" onclick="irCad('passageiro')"><b>SOU PASSAGEIRO</b></div>
<div style="padding:18px;border:2px solid #eee;border-radius:14px;margin:10px 0;cursor:pointer" onclick="irCad('motorista')"><b>SOU MOTORISTA</b></div>
<a href="#" onclick="checkLogin()">Ja tenho cadastro - Entrar</a>
</div>
</div>
<div id="tela-cad" class="tela">
<div class="header-black"><div class="logo">TOINDO Cadastro</div></div>
<div class="card">
<h3 id="titCad">Cadastro</h3>
<input id="nome" placeholder="Nome completo">
<input id="tel" placeholder="WhatsApp">
<input id="endereco" placeholder="Endereco">
<input id="motoInfo" placeholder="Moto e Placa" style="display:none">
<button class="btn" onclick="salvar()">CRIAR CONTA</button>
<button class="btn" style="background:#000;color:#fff" onclick="showTela('tela-inicio')">VOLTAR</button>
</div>
</div>
<div id="tela-aguardando" class="tela">
<div class="header-black"><div class="logo">TOINDO</div></div>
<div class="aguardando">
<h2>AGUARDANDO APROVACAO</h2><br>
<p>Seu cadastro foi enviado para analise.</p><br>
<b>Em breve voce sera liberado!</b><br><br>
<button class="btn" style="background:#000;color:#fff" onclick="sair()">VOLTAR AO INICIO</button>
</div>
</div>
<div id="tela-app" class="tela">
<div class="top-yellow">
<div style="display:flex;justify-content:space-between"><b>Ola, <span id="nomeUser">Moises</span>!</b><span style="cursor:pointer" onclick="sair()">Sair</span></div>
</div>
<div class="map-box"><div id="map"></div></div>
<div class="card-search">
<div class="origem-box"><div class="origem-dot"></div><input id="origem" class="search-input" style="border:none;padding:6px;background:transparent" placeholder="Origem - pegando GPS..."></div>
<div class="origem-box"><div class="dest-dot"></div><input id="destino" class="search-input" style="border:none;padding:6px;background:transparent" placeholder="Para onde vamos?" oninput="buscar(this.value)"></div>
<div id="listaSugestoes"></div>
<div id="boxValor" style="display:none;margin-top:12px;padding:12px;background:#f0fff5;border:2px solid #00FF88;border-radius:10px">
<b>Destino: <span id="destEscolhido"></span></b><br>
<small>Distancia: <span id="dist">--</span> | Valor: R$ <span id="valor">--</span></small>
<button class="btn-moto" onclick="solicitar()">SOLICITAR MOTO - R$ <span id="valor2">--</span></button>
</div>
<div id="statusBox" style="display:none;margin-top:10px;padding:12px;background:#e8f5e9;border-radius:10px;text-align:center"></div>
</div>
</div>
<script>
let map, markerOrigem, markerDestino, latOrigem, lngOrigem, latDestino, lngDestino;
let meuId=null;
function showTela(id){document.querySelectorAll(".tela").forEach(t=>t.classList.remove("active"));document.getElementById(id).classList.add("active");}
function irCad(t){
 showTela("tela-cad");
 document.getElementById("titCad").innerText=t=="passageiro"?"Cadastro Passageiro":"Cadastro Motorista";
 document.getElementById("tela-cad").dataset.tipo=t;
 document.getElementById("motoInfo").style.display = t=="motorista"? "block" : "none";
}
function checkLogin(){
 const u=localStorage.getItem("toindo_user");
 if(!u){alert("Faca cadastro primeiro");return;}
 const user=JSON.parse(u);
 if(user.tipo=="motorista" && user.status!="APROVADO"){showTela("tela-aguardando");} else {entrarApp(user);}
}
function sair(){localStorage.removeItem("toindo_user");showTela("tela-inicio");}
async function salvar(){
 const tipo=document.getElementById("tela-cad").dataset.tipo;
 const nome=document.getElementById("nome").value.trim();
 const tel=document.getElementById("tel").value.trim();
 const endereco=document.getElementById("endereco").value.trim();
 const moto=document.getElementById("motoInfo").value.trim();
 if(!nome||!tel||!endereco){alert("Preencha Nome, WhatsApp e Endereco");return;}
 if(tipo=="motorista" &&!moto){alert("Motorista precisa informar Moto e Placa");return;}
 const user={id:Date.now().toString(),nome,tel,endereco,moto,tipo,status:tipo=="motorista"?"PENDENTE":"APROVADO"};
 await fetch("/api/usuarios",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(user)});
 localStorage.setItem("toindo_user",JSON.stringify(user));
 if(tipo=="motorista"){showTela("tela-aguardando");} else {entrarApp(user);}
}
function entrarApp(user){
 document.getElementById("nomeUser").innerText=user.nome.split(" ")[0];
 showTela("tela-app");
 setTimeout(initMap,400);
}
function initMap(){
 if(map) {map.invalidateSize(); return;}
 map=L.map("map").setView([-15.6237,-56.1564],15);
 L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
 if(navigator.geolocation){
  navigator.geolocation.getCurrentPosition(async p=>{
   latOrigem=p.coords.latitude; lngOrigem=p.coords.longitude;
   map.setView([latOrigem,lngOrigem],16);
   if(markerOrigem) map.removeLayer(markerOrigem);
   markerOrigem=L.marker([latOrigem,lngOrigem]).addTo(map).bindPopup("Voce esta aqui").openPopup();
   try{
    const r=await fetch("https://nominatim.openstreetmap.org/reverse?lat="+latOrigem+"&lon="+lngOrigem+"&format=json");
    const j=await r.json();
    document.getElementById("origem").value=j.display_name||"GPS: "+latOrigem.toFixed(5)+","+lngOrigem.toFixed(5);
   }catch(e){document.getElementById("origem").value="GPS: "+latOrigem.toFixed(5)+","+lngOrigem.toFixed(5);}
  });
 }
}
async function buscar(q){
 if(q.length<3){document.getElementById("listaSugestoes").innerHTML="";return;}
 try{
  const r=await fetch("https://nominatim.openstreetmap.org/search?q="+encodeURIComponent(q)+"&format=json&limit=6&countrycodes=br");
  const dados=await r.json();
  let html="";
  dados.forEach(item=>{
   const dist=latOrigem? (calcDist(latOrigem,lngOrigem,parseFloat(item.lat),parseFloat(item.lon)).toFixed(1)+"km") : "";
   const nomeSafe=item.display_name.replace(/'/g,"");
   html+="<div class=sugestao onclick=escolherDestino('"+nomeSafe+"',"+item.lat+","+item.lon+")><div><b>"+item.display_name.split(",")[0]+"</b><br><small>"+item.display_name.substring(0,75)+"...</small></div><small>"+dist+"</small></div>";
  });
  document.getElementById("listaSugestoes").innerHTML=html;
 } catch(e){}
}
function escolherDestino(nome,lat,lng){
 latDestino=lat; lngDestino=lng;
 document.getElementById("destino").value=nome;
 document.getElementById("destEscolhido").innerText=nome;
 document.getElementById("listaSugestoes").innerHTML="";
 if(markerDestino) map.removeLayer(markerDestino);
 markerDestino=L.marker([lat,lng]).addTo(map);
 map.fitBounds([[latOrigem,lngOrigem],[lat,lng]],{padding:[30,30]});
 const d=calcDist(latOrigem,lngOrigem,lat,lng);
 document.getElementById("dist").innerText=d.toFixed(1)+" km";
 const valor=(d*2.5+5).toFixed(2);
 document.getElementById("valor").innerText=valor;
 document.getElementById("valor2").innerText=valor;
 document.getElementById("boxValor").style.display="block";
}
function calcDist(la1,lo1,la2,lo2){
 const R=6371; const dLat=(la2-la1)*Math.PI/180; const dLon=(lo2-lo1)*Math.PI/180;
 const a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLon/2)*Math.sin(dLon/2);
 return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}
async function solicitar(){
 const u=JSON.parse(localStorage.getItem("toindo_user"));
 const origem=document.getElementById("origem").value;
 const destino=document.getElementById("destino").value;
 const valor=document.getElementById("valor").innerText;
 const res=await fetch("/api/solicitar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nome:u.nome,tel:u.tel,origem,destino,latOrigem,lngOrigem,latDestino,lngDestino,valor})});
 const d=await res.json(); meuId=d.id;
 document.getElementById("statusBox").style.display="block";
 document.getElementById("statusBox").innerHTML="Procurando motorista...<br><small>"+destino+"</small>";
 document.getElementById("boxValor").style.display="none";
 setInterval(verStatus,3000);
}
async function verStatus(){
 if(!meuId) return; const r=await fetch("/api/status/"+meuId); const c=await r.json(); if(!c) return;
 if(c.status=="aceita") document.getElementById("statusBox").innerHTML="Motorista "+c.nome_moto+" a caminho! Valor: R$ "+c.valor;
}
const saved=localStorage.getItem("toindo_user");
if(saved){
 const user=JSON.parse(saved);
 if(user.tipo=="motorista" && user.status=="PENDENTE"){showTela("tela-aguardando");}
 else if(user.tipo) {entrarApp(user);}
}
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return HTML_HOME

@app.route('/motorista')
def motorista_page():
    return "<h2>Painel Motorista</h2><div id=lista></div><script>async function load(){const r=await fetch('/api/corridas');const cs=await r.json();document.getElementById('lista').innerHTML=cs.map(c=>'<div style=border:1px solid #ccc;padding:8px;margin:5px>'+c.nome+' - '+c.destino+' <button onclick=fetch(\"/api/aceitar/'+c.id+'\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({nome_moto:\"Moto\"})}).then(()=>load())>ACEITAR</button></div>').join('');}setInterval(load,3000);load();</script>"

@app.route('/admin')
def admin_page():
    return "<h2>Admin - Aprovar Motoristas</h2><div id=lista></div><script>async function load(){const r=await fetch('/api/usuarios');const us=await r.json();document.getElementById('lista').innerHTML=us.map(u=>'<div style=border:1px solid #ccc;padding:8px;margin:5px>'+u.nome+' - '+u.status+' - '+u.tipo+' <button onclick=fetch(\"/api/aprovar/'+u.id+'\",{method:\"POST\"}).then(()=>load())>APROVAR</button></div>').join('');}setInterval(load,3000);load();</script>"

@app.route('/api/usuarios', methods=['GET','POST'])
def api_usuarios():
    global usuarios
    if request.method=='POST':
        usuarios.append(request.json)
        return jsonify({"ok":True})
    return jsonify(usuarios)

@app.route('/api/aprovar/<id>', methods=['POST'])
def api_aprovar(id):
    for u in usuarios:
        if str(u.get('id'))==str(id):
            u['status']='APROVADO'
    return jsonify({"ok":True})

@app.route('/api/excluir/<id>', methods=['POST'])
def api_excluir(id):
    global usuarios
    usuarios=[u for u in usuarios if str(u.get('id'))!=str(id)]
    return jsonify({"ok":True})

@app.route('/api/solicitar', methods=['POST'])
def api_solicitar():
    d=request.json
    nid=str(uuid.uuid4())
    corridas.append({"id":nid,"nome":d.get('nome'),"tel":d.get('tel'),"origem":d.get('origem'),"destino":d.get('destino'),"latOrigem":d.get('latOrigem'),"lngOrigem":d.get('lngOrigem'),"latDestino":d.get('latDestino'),"lngDestino":d.get('lngDestino'),"valor":d.get('valor'),"hora":datetime.now().strftime("%H:%M"),"status":"procurando","nome_moto":""})
    return jsonify({"ok":True,"id":nid})

@app.route('/api/corridas')
def api_corridas():
    return jsonify([c for c in corridas if c['status']!='finalizada'])

@app.route('/api/status/<id>')
def api_status(id):
    for c in corridas:
        if c['id']==id:
            return jsonify(c)
    return jsonify(None)

@app.route('/api/aceitar/<id>', methods=['POST'])
def api_aceitar(id):
    data=request.json or {}
    for c in corridas:
        if c['id']==id:
            c['status']='aceita'
            c['nome_moto']=data.get('nome_moto','Motorista')
    return jsonify({"ok":True})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=10000)
