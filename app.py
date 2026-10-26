from flask import Flask, jsonify, request


from datetime import datetime

import uuid



app = Flask(__name__)




corridas = []

usuarios = []



HTML_HOME = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="csrf-token" content="__CSRF_TOKEN__">
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

.auth-shell{max-width:480px;margin:0 auto;min-height:100vh;background:#fff}.auth-hero{background:#080808;color:#fff;padding:30px 22px 26px;border-radius:0 0 26px 26px}.auth-hero .logo{font-size:28px;letter-spacing:1px;color:#00e676}.auth-hero p{color:#ddd;margin-top:12px;line-height:1.5}.auth-content{padding:20px 18px 30px}.eyebrow{color:#666;font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin:7px 0}.auth-title{font-size:24px;margin:6px 0 8px}.auth-copy{color:#666;line-height:1.45;margin-bottom:18px;font-size:14px}.auth-choice{display:block;width:100%;text-align:left;padding:17px;margin:10px 0;border:1px solid #e7e7e7;border-radius:14px;background:#fff;cursor:pointer}.auth-choice b{display:block;font-size:16px;margin-bottom:5px}.auth-choice small{color:#666;line-height:1.4}.btn-primary{background:#00e676;color:#07120b;border:none;padding:15px;border-radius:12px;width:100%;font-weight:900;font-size:15px;margin-top:9px;cursor:pointer}.btn-secondary{background:#fff;color:#111;border:1px solid #ddd;padding:14px;border-radius:12px;width:100%;font-weight:800;margin-top:9px;cursor:pointer}.field-label{display:block;font-size:13px;font-weight:700;margin:12px 0 4px}.field-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.step-dots{display:flex;gap:6px;margin:14px 0 18px}.step-dots span{height:4px;flex:1;border-radius:9px;background:#e8e8e8}.step-dots span.on{background:#00c853}.form-note{font-size:12px;color:#666;line-height:1.45;margin:13px 0}.pill{display:inline-block;background:#eafff1;color:#087a37;padding:6px 10px;border-radius:20px;font-weight:800;font-size:12px}@media(max-width:380px){.field-row{grid-template-columns:1fr}}
</style>
</head>
<body>
<div id="tela-inicio" class="tela active"><div class="auth-shell"><div class="auth-hero"><div class="logo">TOINDO</div><p>Sua cidade em movimento.<br>Peça uma moto ou venha pilotar com a gente.</p></div><div class="auth-content"><div class="eyebrow">Bem-vindo</div><h1 class="auth-title">Como você quer continuar?</h1><p class="auth-copy">Entre na sua conta ou crie seu cadastro para começar.</p><button class="btn-primary" onclick="showTela('tela-entrar')">ENTRAR</button><button class="btn-secondary" onclick="showTela('tela-tipo')">CADASTRAR</button></div></div></div>
<div id="tela-entrar" class="tela"><div class="auth-shell"><div class="auth-hero"><div class="logo">TOINDO</div><p>Acesse sua conta para continuar.</p></div><div class="auth-content"><div class="eyebrow">Acessar</div><h1 class="auth-title">Entrar</h1><p class="auth-copy">Informe o WhatsApp usado no seu cadastro.</p><label class="field-label" for="loginTel">WhatsApp</label><input id="loginTel" type="tel" placeholder="(65) 99999-9999"><button class="btn-primary" onclick="checkLogin(true)">CONTINUAR</button><p class="form-note">Ainda não tem cadastro? <a href="#" onclick="showTela('tela-tipo');return false">Cadastre-se</a></p><button class="btn-secondary" onclick="showTela('tela-inicio')">VOLTAR</button></div></div></div>
<div id="tela-tipo" class="tela"><div class="auth-shell"><div class="auth-hero"><div class="logo">TOINDO</div><p>Um cadastro simples, do seu jeito.</p></div><div class="auth-content"><div class="eyebrow">Criar cadastro</div><h1 class="auth-title">Escolha como vai usar</h1><p class="auth-copy">Selecione seu perfil para ver os dados necessários.</p><button class="auth-choice" onclick="irCad('passageiro')"><b>Sou passageiro</b><small>Quero solicitar corridas de moto.</small></button><button class="auth-choice" onclick="irCad('motorista')"><b>Quero ser motorista</b><small>Quero pilotar e receber chamadas. Cadastro exclusivo para moto.</small></button><button class="btn-secondary" onclick="showTela('tela-inicio')">VOLTAR</button></div></div></div>
<div id="tela-cad" class="tela"><div class="auth-shell"><div class="auth-hero"><div class="logo">TOINDO</div><p id="cadSubtitulo">Seu cadastro começa aqui.</p></div><div class="auth-content"><div class="eyebrow" id="cadEtapa">Seus dados</div><h1 class="auth-title" id="titCad">Cadastro</h1><div class="step-dots"><span id="dot1" class="on"></span><span id="dot2"></span></div><div id="cadDadosPessoais"><label class="field-label" for="nome">Nome completo</label><input id="nome" placeholder="Como aparece no seu documento"><div class="field-row"><div><label class="field-label" for="tel">WhatsApp</label><input id="tel" type="tel" placeholder="(65) 99999-9999"></div><div><label class="field-label" for="email">E-mail</label><input id="email" type="email" placeholder="voce@email.com"></div></div><div id="camposMotorista" style="display:none"><label class="field-label" for="cpf">CPF</label><input id="cpf" inputmode="numeric" placeholder="000.000.000-00"><div class="field-row"><div><label class="field-label" for="nascimento">Nascimento</label><input id="nascimento" type="date"></div><div><label class="field-label" for="endereco">Endereço</label><input id="endereco" placeholder="Rua e número"></div></div><p class="form-note"><span class="pill">Cadastro exclusivo para moto</span></p></div><div id="camposPassageiro"><label class="field-label" for="cidade">Cidade</label><input id="cidade" placeholder="Cuiabá ou Várzea Grande"></div><button class="btn-primary" onclick="avancarCadastro()">CONTINUAR</button></div><div id="cadDadosVeiculo" style="display:none"><label class="field-label" for="cnh">Número de registro da CNH</label><input id="cnh" inputmode="numeric" placeholder="Digite o número da CNH"><div class="field-row"><div><label class="field-label" for="categoriaCnh">Categoria da CNH</label><select id="categoriaCnh" style="width:100%;padding:13px;border:2px solid #eee;border-radius:10px;background:#f9f9f9;margin:6px 0"><option value="">Selecione</option><option>A</option><option>AB</option></select></div><div><label class="field-label" for="validadeCnh">Validade da CNH</label><input id="validadeCnh" type="date"></div></div><div class="field-row"><div><label class="field-label" for="motoMarca">Marca e modelo</label><input id="motoMarca" placeholder="Ex.: Honda CG 160"></div><div><label class="field-label" for="motoAno">Ano</label><input id="motoAno" inputmode="numeric" placeholder="2022"></div></div><div class="field-row"><div><label class="field-label" for="motoPlaca">Placa</label><input id="motoPlaca" placeholder="ABC1D23"></div><div><label class="field-label" for="motoCor">Cor</label><input id="motoCor" placeholder="Preta"></div></div><label class="field-label" for="motoRenavam">Renavam (opcional)</label><input id="motoRenavam" inputmode="numeric" placeholder="Número do Renavam"><label style="display:flex;gap:8px;align-items:flex-start;margin:14px 0;font-size:13px"><input id="whatsappOptIn" type="checkbox" style="width:auto;margin:2px 0 0">Aceito receber atualiza&ccedil;&otilde;es do meu cadastro pelo WhatsApp do Toindo.</label><p class="form-note">A equipe vai revisar as informa&ccedil;&otilde;es e pode pedir documentos por um canal seguro. A mensagem de aprova&ccedil;&atilde;o s&oacute; ser&aacute; enviada se voc&ecirc; autorizar o contato pelo WhatsApp.</p><button class="btn-primary" onclick="salvar()">ENVIAR CADASTRO</button><button class="btn-secondary" onclick="voltarEtapaCadastro()">VOLTAR</button></div><button id="btnVoltarTipo" class="btn-secondary" onclick="showTela('tela-tipo')">VOLTAR</button></div></div></div>
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
function irCad(t){showTela("tela-cad");document.getElementById("titCad").innerText=t=="passageiro"?"Cadastro de passageiro":"Cadastro de motorista";document.getElementById("cadSubtitulo").innerText=t=="passageiro"?"Peça sua primeira corrida de moto.":"Só para quem vai pilotar uma moto.";document.getElementById("tela-cad").dataset.tipo=t;document.getElementById("camposMotorista").style.display=t=="motorista"?"block":"none";document.getElementById("camposPassageiro").style.display=t=="motorista"?"none":"block";document.getElementById("cadDadosPessoais").style.display="block";document.getElementById("cadDadosVeiculo").style.display="none";document.getElementById("btnVoltarTipo").style.display="block";document.getElementById("cadEtapa").innerText=t=="motorista"?"Etapa 1 de 2":"Seus dados";document.getElementById("dot2").classList.remove("on");document.getElementById("dot1").classList.add("on");}
function avancarCadastro(){const tipo=document.getElementById("tela-cad").dataset.tipo;const nome=document.getElementById("nome").value.trim(),tel=document.getElementById("tel").value.trim(),email=document.getElementById("email").value.trim();if(!nome||!tel||!email){alert("Preencha nome completo, WhatsApp e e-mail.");return;}if(tipo=="motorista"){if(!document.getElementById("cpf").value.trim()||!document.getElementById("nascimento").value||!document.getElementById("endereco").value.trim()){alert("Preencha CPF, data de nascimento e endereço.");return;}document.getElementById("cadDadosPessoais").style.display="none";document.getElementById("cadDadosVeiculo").style.display="block";document.getElementById("btnVoltarTipo").style.display="none";document.getElementById("cadEtapa").innerText="Etapa 2 de 2";document.getElementById("dot2").classList.add("on");}else salvar();}
function voltarEtapaCadastro(){document.getElementById("cadDadosPessoais").style.display="block";document.getElementById("cadDadosVeiculo").style.display="none";document.getElementById("btnVoltarTipo").style.display="block";document.getElementById("cadEtapa").innerText="Etapa 1 de 2";document.getElementById("dot2").classList.remove("on");}
function checkLogin(){alert("O acesso estará disponível quando a autenticação segura estiver configurada.");}
async function salvar(){
 const tipo=document.getElementById("tela-cad").dataset.tipo, nome=document.getElementById("nome").value.trim(), tel=document.getElementById("tel").value.trim(), email=document.getElementById("email").value.trim();
 const payload={_csrf:document.querySelector('meta[name="csrf-token"]').content,tipo,nome,tel,email};
 if(tipo==="motorista"){
  payload.endereco=document.getElementById("endereco").value.trim();payload.cpf=document.getElementById("cpf").value.trim();payload.nascimento=document.getElementById("nascimento").value;payload.cnh=document.getElementById("cnh").value.trim();payload.categoria_cnh=document.getElementById("categoriaCnh").value;payload.validade_cnh=document.getElementById("validadeCnh").value;payload.moto={marca_modelo:document.getElementById("motoMarca").value.trim(),ano:document.getElementById("motoAno").value.trim(),placa:document.getElementById("motoPlaca").value.trim().toUpperCase(),cor:document.getElementById("motoCor").value.trim(),renavam:document.getElementById("motoRenavam").value.trim()};payload.whatsapp_opt_in=document.getElementById("whatsappOptIn").checked;
 }else payload.endereco=document.getElementById("cidade").value.trim();
 if(!nome||!tel||!email||!payload.endereco){alert("Preencha os campos obrigatorios.");return;}
 if(tipo==="motorista"&&(!payload.cpf||!payload.nascimento||!payload.cnh||!payload.categoria_cnh||!payload.validade_cnh||!payload.moto.marca_modelo||!payload.moto.ano||!payload.moto.placa||!payload.moto.cor)){alert("Preencha os dados obrigatorios do motorista e da moto.");return;}
 try{const response=await fetch("/api/usuarios",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const result=await response.json();if(!response.ok)throw new Error(result.error||"Nao foi possivel enviar o cadastro.");if(tipo==="motorista"){document.querySelector("#tela-aguardando p").innerText="Recebemos seu cadastro. A equipe do Toindo vai revisar as informacoes e avisar sobre a decisao.";showTela("tela-aguardando");}else{localStorage.setItem("toindo_user",JSON.stringify({id:result.id,nome,tel,tipo,status:result.status}));entrarApp({nome});}}catch(error){alert(error.message||"Nao foi possivel enviar o cadastro.");}
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
</script>
</body>
</html>
'''



@app.route('/')

def home():

    return HTML_HOME.replace("__CSRF_TOKEN__", csrf_token())



@app.route('/motorista')

def motorista_page():

    return "<h2>Painel Motorista</h2><div id=lista></div><script>async function load(){const r=await fetch('/api/corridas');const cs=await r.json();document.getElementById('lista').innerHTML=cs.map(c=>'<div style=border:1px solid #ccc;padding:8px;margin:5px>'+c.nome+' - '+c.destino+' <button onclick=fetch(\"/api/aceitar/'+c.id+'\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({nome_moto:\"Moto\"})}).then(()=>load())>ACEITAR</button></div>').join('');}setInterval(load,3000);load();</script>"



from admin_backend import register_public_routes, csrf_token
register_public_routes(app)


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
