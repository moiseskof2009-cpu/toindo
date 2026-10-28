from flask import Flask, jsonify, request
from datetime import datetime
import uuid, urllib.parse

app = Flask(__name__)

# BANCO TEMPORÁRIO (depois trocamos por banco de verdade)
cadastros_motorista = []

# SEU HTML DO APP PRINCIPAL (PASSAGEIRO) - MANTIDO IGUAL VOCÊ JÁ TEM
HTML_HOME = """
<!DOCTYPE html>
<html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Toindo</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}body{background:#f7f7f7}.header{background:#0e0e0e;color:white;padding:25px;border-radius:0 0 20px 20px}.header h1{color:#00FF66}.container{max-width:480px;margin:0 auto;padding:15px}.card{background:white;padding:20px;border-radius:16px;margin-top:15px}.btn{background:#00FF66;padding:15px;border-radius:12px;width:100%;border:none;font-weight:900;cursor:pointer;margin-top:10px}.input{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;margin:6px 0}</style>
</head><body><div class="container"><div class="header"><h1>TOINDO</h1><p>Sua cidade em movimento.</p></div>
<div class="card"><h3>Solicitar Moto</h3><input id="o" class="input" placeholder="De onde?"><input id="d" class="input" placeholder="Para onde?"><button class="btn" onclick="alert('Corrida solicitada! (teste)')">SOLICITAR</button><br><br><a href='/admin'>Ir para Painel Admin</a></div></div></body></html>
"""

# HTML DO ADMIN IGUAL SUA FOTO
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin - Toindo</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f5f5f5;padding:20px}
.top{color:#666;font-size:13px;margin-bottom:15px}
h1{font-size:28px;margin-bottom:15px}
.card{background:white;border-radius:16px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:20px}
.badge{background:#eee;padding:5px 12px;border-radius:20px;font-size:13px;font-weight:700;margin-left:10px}
.badge.pendente{background:#fff0c0}
.nome{font-size:20px;font-weight:900}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:15px 0}
.grid div small{color:#666;font-size:11px;display:block}
.grid div b{font-size:14px;word-break:break-all}
textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;margin:10px 0;min-height:70px}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
.btn{border:none;padding:12px 18px;border-radius:8px;font-weight:800;cursor:pointer;font-size:13px}
.aprovar{background:#00E676;color:#000}
.correcao{background:#FFF3CD;color:#111;border:1px solid #ffeaa7}
.recusar{background:#F8D7DA;color:#111;border:1px solid #f5c6cb}
.reenviar{background:#111;color:white}
</style>
</head>
<body>
<div class="top">Os dados pessoais ficam criptografados no banco. Confira as informações antes de aprovar.</div>
<h1>Cadastros de motorista</h1>
<div id="lista"></div>

<script>
async function carregar(){
  const r = await fetch('/api/admin/listar');
  const dados = await r.json();
  const div = document.getElementById('lista');
  if(dados.length==0){div.innerHTML='<p>Nenhum cadastro pendente</p>';return}
  div.innerHTML='';
  dados.forEach(c=>{
    div.innerHTML+=`
    <div class="card">
      <div class="nome">${c.nome} <span class="badge pendente">${c.status}</span> <small style="color:#666;font-weight:400">Recebido: ${c.data} - Falha no envio · Consentiu: ${c.consentiu||'sim'}</small></div>
      <div class="grid">
        <div><small>WhatsApp</small><b>${c.whatsapp}</b></div>
        <div><small>E-mail</small><b>${c.email}</b></div>
        <div><small>CPF</small><b>${c.cpf}</b></div>
        <div><small>Nascimento</small><b>${c.nascimento}</b></div>
        <div><small>Endereço</small><b>${c.endereco}</b></div>
        <div><small>CNH</small><b>${c.cnh}</b></div>
        <div><small>Categoria</small><b>${c.categoria}</b></div>
        <div><small>Validade</small><b>${c.validade}</b></div>
        <div><small>Moto</small><b>${c.moto}</b></div>
        <div><small>Ano</small><b>${c.ano}</b></div>
        <div><small>Placa</small><b>${c.placa}</b></div>
        <div><small>Cor</small><b>${c.cor}</b></div>
        <div><small>Renavam</small><b>${c.renavam}</b></div>
      </div>
      <div><small>Observação:</small> <b>${c.observacao||'-'}</b></div>
      <textarea id="motivo-${c.id}" placeholder="Motivo para correção ou recusa"></textarea>
      <div class="btns">
        <button class="btn aprovar" onclick="acao('${c.id}','aprovar')">APROVAR</button>
        <button class="btn correcao" onclick="acao('${c.id}','correcao')">PEDIR CORREÇÃO</button>
        <button class="btn recusar" onclick="acao('${c.id}','recusar')">RECUSAR</button>
        <button class="btn reenviar" onclick="acao('${c.id}','reenviar')">REENVIAR WHATSAPP</button>
      </div>
    </div>`;
  });
}

async function acao(id, tipo){
  const motivo = document.getElementById('motivo-'+id).value;
  if((tipo=='correcao' || tipo=='recusar') && !motivo){alert('Digite o motivo!');return}
  const r = await fetch('/api/admin/'+tipo, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id, motivo})});
  const res = await r.json();
  if(res.ok){
    // ABRE O WHATSAPP AUTOMATICO
    if(res.whatsapp_url){
      window.open(res.whatsapp_url, '_blank');
    }
    alert(res.mensagem);
    carregar();
  } else {
    alert('Erro: '+res.erro);
  }
}

carregar();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_HOME

@app.route('/admin')
def admin():
    return HTML_ADMIN

# API PARA O APP SALVAR CADASTRO (você já tem isso no seu app principal)
@app.route('/api/cadastrar-motorista', methods=['POST'])
def cadastrar():
    d = request.json
    novo = {
        "id": str(uuid.uuid4())[:8],
        "nome": d.get('nome','moises jose da costa'),
        "whatsapp": d.get('whatsapp','65996726172'),
        "email": d.get('email','moiseskof2009@gmail.com'),
        "cpf": d.get('cpf','06026942130'),
        "nascimento": d.get('nascimento','1997-03-17'),
        "endereco": d.get('endereco','rua sorriso 12'),
        "cnh": d.get('cnh','1231014500321'),
        "categoria": d.get('categoria','AB'),
        "validade": d.get('validade','2035-01-01'),
        "moto": d.get('moto','honda cg fan 160'),
        "ano": d.get('ano','2024'),
        "placa": d.get('placa','AAA1234'),
        "cor": d.get('cor','preta'),
        "renavam": d.get('renavam','00000000000'),
        "observacao": d.get('observacao','-'),
        "status": "Pendente",
        "data": datetime.now().isoformat(),
        "consentiu": "sim"
    }
    cadastros_motorista.append(novo)
    return jsonify({"ok":True})

# ADMIN APIS
@app.route('/api/admin/listar')
def listar():
    # se tiver vazio, cria um de teste igual sua foto
    if len(cadastros_motorista)==0:
        cadastros_motorista.append({
            "id":"teste123","nome":"moises jose da costa","whatsapp":"65996726172","email":"moiseskof2009@gmail.com",
            "cpf":"06026942130","nascimento":"1997-03-17","endereco":"rua sorriso 12","cnh":"1231014500321",
            "categoria":"AB","validade":"2035-01-01","moto":"honda cg fan 160","ano":"2024","placa":"AAA1234",
            "cor":"preta","renavam":"00000000000","observacao":"-","status":"Pendente",
            "data":"2026-10-28T21:42:21+00:00","consentiu":"sim"
        })
    return jsonify(cadastros_motorista[::-1])

def make_whatsapp_link(tel, texto):
    tel_limpo = ''.join(filter(str.isdigit, tel))
    if not tel_limpo.startswith('55'):
        tel_limpo = '55'+tel_limpo
    return f"https://wa.me/{tel_limpo}?text={urllib.parse.quote(texto)}"

@app.route('/api/admin/aprovar', methods=['POST'])
def aprovar():
    d=request.json
    for c in cadastros_motorista:
        if c['id']==d['id']:
            c['status']='Aprovado'
            msg = f"Olá {c['nome']}! 🏍️✅ Seu cadastro no TOINDO foi APROVADO! Você já pode receber corridas em Várzea Grande. Baixe o app e fique online. Qualquer dúvida chama aqui. Equipe Toindo."
            url = make_whatsapp_link(c['whatsapp'], msg)
            return jsonify({"ok":True, "mensagem":"Aprovado! Abrindo WhatsApp...", "whatsapp_url":url})
    return jsonify({"ok":False, "erro":"não encontrado"})

@app.route('/api/admin/correcao', methods=['POST'])
def correcao():
    d=request.json
    for c in cadastros_motorista:
        if c['id']==d['id']:
            c['status']='Correção'
            msg = f"Olá {c['nome']}! ⚠️ Seu cadastro no TOINDO precisa de correção: {d['motivo']}. Por favor, corrija e reenvie no app. Equipe Toindo."
            url = make_whatsapp_link(c['whatsapp'], msg)
            return jsonify({"ok":True, "mensagem":"Pedido de correção enviado! Abrindo WhatsApp...", "whatsapp_url":url})
    return jsonify({"ok":False, "erro":"não encontrado"})

@app.route('/api/admin/recusar', methods=['POST'])
def recusar():
    d=request.json
    for c in cadastros_motorista:
        if c['id']==d['id']:
            c['status']='Recusado'
            msg = f"Olá {c['nome']}! Seu cadastro no TOINDO foi RECUSADO. Motivo: {d['motivo']}. Se achar que foi um engano, fale com a gente. Equipe Toindo."
            url = make_whatsapp_link(c['whatsapp'], msg)
            return jsonify({"ok":True, "mensagem":"Recusado! Abrindo WhatsApp...", "whatsapp_url":url})
    return jsonify({"ok":False, "erro":"não encontrado"})

@app.route('/api/admin/reenviar', methods=['POST'])
def reenviar():
    d=request.json
    for c in cadastros_motorista:
        if c['id']==d['id']:
            msg = f"Olá {c['nome']}! Aqui é da equipe TOINDO. Seu cadastro está em análise. Em breve retornamos. Qualquer dúvida: {d.get('motivo','')}"
            url = make_whatsapp_link(c['whatsapp'], msg)
            return jsonify({"ok":True, "mensagem":"Reenviando WhatsApp...", "whatsapp_url":url})
    return jsonify({"ok":False})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=10000)
