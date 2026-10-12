from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'toindo_segredo_2024'

# === AQUI VOCÊ TROCA SUA SENHA DE ADMIN - SÓ VOCÊ VAI SABER ===
SENHA_ADMIN_SECRETA = "toindo2024"  # <-- TROCA AQUI: ex: "MinhaSenhaForte123"

motoristas = []
next_id = 1

HOME_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TOINDO</title>
<style>body{font-family:Arial;background:#111;color:white;text-align:center;padding:20px}
.btn{display:block;background:#FFD700;color:black;padding:18px;margin:15px;border-radius:12px;font-weight:bold;text-decoration:none}</style>
</head><body>
<h1 style="color:#FFD700;font-size:40px">TOINDO</h1>
<p>Mototaxi - Varzea Grande e Cuiaba</p>
<a class="btn" href="/cadastro">FAZER CADASTRO</a>
<a class="btn" href="/entrar">ENTRAR</a>
<br><br><a class="btn" style="background:#333;color:#FFD700;border:1px solid #FFD700" href="/admin">PAINEL ADMIN</a>
<p style="font-size:12px;color:#888">Total: {{total}} | Pendentes: {{pendentes}}</p>
</body></html>
"""

CADASTRO_ESCOLHA = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;text-align:center;padding:20px}
.btn{display:block;background:#FFD700;color:black;padding:18px;margin:15px;border-radius:12px;font-weight:bold;text-decoration:none}</style>
</head><body><h2>Cadastro</h2>
<a class="btn" href="/cadastro-motorista">CADASTRO MOTORISTA</a>
<a class="btn" style="background:#555;color:white" href="/">VOLTAR</a>
</body></html>
"""

CADASTRO_MOTORISTA = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;padding:20px}
input{width:100%;padding:14px;margin:8px 0;border-radius:8px;border:none;font-size:16px}
.btn{background:#FFD700;color:black;padding:16px;border:none;width:100%;border-radius:12px;font-weight:bold;font-size:18px;margin-top:10px}
label{color:#FFD700;font-size:14px;margin-top:10px;display:block;text-align:left}</style>
</head><body>
<h2 style="text-align:center;color:#FFD700">Cadastro Motorista</h2>
<form method="POST">
<label>Nome completo</label><input name="nome" required>
<label>WhatsApp (com DDD)</label><input name="whatsapp" required placeholder="65999999999">
<label>CPF</label><input name="cpf" required>
<label>Numero da CNH</label><input name="cnh" required>
<label>Placa da moto</label><input name="placa" required>
<label>Modelo / Cor da moto</label><input name="modelo" required>
<label>Bairro</label><input name="bairro" required placeholder="Ex: Cristo Rei, Centro, Tijucal">
<label>Municipio</label><input name="municipio" required placeholder="Ex: Varzea Grande ou Cuiaba">
<label>Crie uma senha</label><input name="senha" type="password" required>
<button class="btn">ENVIAR PARA ANALISE</button>
</form><br><a href="/" style="color:white;text-align:center;display:block">VOLTAR</a>
</body></html>
"""

AGUARDE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;text-align:center;padding:30px}
.box{background:#222;padding:20px;border-radius:12px;border:1px solid #FFD700}
.btn{display:block;background:#FFD700;color:black;padding:16px;margin:15px;border-radius:12px;font-weight:bold;text-decoration:none}</style>
</head><body><div class="box"><h2 style="color:#FFD700">Obrigado, {{nome}}!</h2><p>Cadastro enviado para analise.</p></div>
<a class="btn" href="/">VOLTAR AO INICIO</a></body></html>
"""

ENTRAR_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;padding:20px}
input{width:100%;padding:14px;margin:8px 0;border-radius:8px;border:none;font-size:16px}
.btn{background:#FFD700;color:black;padding:16px;border:none;width:100%;border-radius:12px;font-weight:bold;font-size:18px;margin-top:10px}</style>
</head><body><h2 style="text-align:center;color:#FFD700">ENTRAR</h2>
{% if erro %}<p style="color:red;text-align:center">{{erro}}</p>{% endif %}
<form method="POST"><input name="whatsapp" required placeholder="Seu WhatsApp">
<input name="senha" type="password" required placeholder="Sua senha">
<button class="btn">ENTRAR</button></form>
<br><a href="/" style="color:white;text-align:center;display:block">VOLTAR</a></body></html>
"""

PLANOS_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;text-align:center;padding:20px}
.card{background:#222;padding:20px;margin:15px 0;border-radius:12px;border:2px solid #FFD700}
.btn{background:#FFD700;color:black;padding:14px;border:none;width:100%;border-radius:10px;font-weight:bold;font-size:16px}</style>
</head><body>
<h2 style="color:#FFD700">Bem-vindo, {{nome}}!</h2><p>APROVADO!</p>
<div class="card"><h3>MENSAL</h3><h1>R$ 15 / mes</h1><button class="btn">ASSINAR R$15</button></div>
<div class="card"><h3>POR CORRIDA</h3><h1>R$ 2 por corrida</h1><button class="btn">USAR POR CORRIDA</button></div>
<br><a href="/sair" style="display:block;background:#ff4444;color:white;padding:16px;border-radius:12px;text-decoration:none;font-weight:bold">SAIR</a>
</body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;padding:15px}
.card{background:#222;padding:15px;margin:10px 0;border-radius:10px;border-left:5px solid orange}
.btn{padding:10px 15px;border:none;border-radius:8px;font-weight:bold;text-decoration:none;display:inline-block;margin:5px}
.aprovar{background:#00c853;color:white}.reprovar{background:#ff4444;color:white}.zap{background:#25D366;color:white}</style>
</head><body>
<h2 style="color:#FFD700">PAINEL ADMIN - TOINDO</h2>
<p>Total: {{motoristas|length}} | Pendentes: {{pendentes}}</p>
<a href="/" style="color:#FFD700">Voltar</a> | <a href="/sair" style="color:#aaa">Sair do Admin</a> | <a href="/admin/limpar" style="color:#ff4444" onclick="return confirm('APAGAR TUDO?')">APAGAR TODOS</a><hr>
{% for m in motoristas %}
<div class="card" style="border-left-color: {{'green' if m.status=='APROVADO' else 'orange'}}">
<b>{{m.nome}}</b> - <span style="color:{{'lightgreen' if m.status=='APROVADO' else 'orange'}}">{{m.status}}</span><br>
Whatsapp: {{m.whatsapp}}<br>CPF: {{m.cpf}}<br>CNH: {{m.cnh}}<br>Placa: {{m.placa}}<br>Modelo: {{m.modelo}}<br>Bairro: {{m.bairro}}<br>Municipio: {{m.municipio}}<br>Senha: {{m.senha}}<br>ID: {{m.id}}<br>
{% if m.status!= 'APROVADO' %}
<a class="btn aprovar" href="/admin/aprovar/{{m.id}}">APROVAR</a>
{% else %}
<a class="btn zap" target="_blank" href="https://wa.me/55{{m.whatsapp}}?text=Ol%C3%A1%20{{m.nome}}%21%20Seu%20cadastro%20no%20T%C3%94INDO%20foi%20APROVADO%21%20%F0%9F%8E%89%20Agora%20pode%20entrar%20no%20app.">📱 CONFIRMAR NO WHATSAPP</a>
{% endif %}
<a class="btn reprovar" href="/admin/reprovar/{{m.id}}">EXCLUIR</a>
</div>
{% else %}<p>Nenhum cadastro.</p>{% endfor %}
</body></html>
"""

ADMIN_LOGIN = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#111;color:white;text-align:center;padding:30px}
input{padding:12px;width:80%;border-radius:8px;border:none;margin:10px}
.btn{background:#FFD700;padding:12px 20px;border:none;border-radius:8px;font-weight:bold}</style>
</head><body><h3>Admin Toindo</h3><form method="POST"><input name="senha_admin" type="password" placeholder="Digite sua senha admin"><br><button class="btn">ENTRAR</button></form></body></html>
"""

@app.route('/')
def home():
    pend = len([m for m in motoristas if m['status']!='APROVADO'])
    return render_template_string(HOME_HTML, total=len(motoristas), pendentes=pend)

@app.route('/cadastro')
def cadastro():
    return render_template_string(CADASTRO_ESCOLHA)

@app.route('/cadastro-motorista', methods=['GET','POST'])
def cadastro_motorista():
    global next_id
    if request.method=='POST':
        novo={'id':next_id,'nome':request.form['nome'],'whatsapp':request.form['whatsapp'],'cpf':request.form['cpf'],'cnh':request.form['cnh'],'placa':request.form['placa'],'modelo':request.form['modelo'],'bairro':request.form['bairro'],'municipio':request.form['municipio'],'senha':request.form['senha'],'status':'PENDENTE'}
        motoristas.append(novo)
        next_id+=1
        return render_template_string(AGUARDE, nome=novo['nome'])
    return render_template_string(CADASTRO_MOTORISTA)

@app.route('/entrar', methods=['GET','POST'])
def entrar():
    if request.method=='POST':
        whatsapp=request.form['whatsapp']
        senha=request.form['senha']
        for m in motoristas:
            if m['whatsapp']==whatsapp and m['senha']==senha:
                if m['status']!='APROVADO':
                    return render_template_string(ENTRAR_HTML, erro=f"Cadastro {m['status']}. Aguarde liberacao.")
                session['motorista_id']=m['id']
                session['motorista_nome']=m['nome']
                return redirect(url_for('planos'))
        return render_template_string(ENTRAR_HTML, erro="WhatsApp ou senha errados!")
    return render_template_string(ENTRAR_HTML, erro=None)

@app.route('/planos')
def planos():
    if 'motorista_id' not in session:
        return redirect(url_for('entrar'))
    return render_template_string(PLANOS_HTML, nome=session.get('motorista_nome'))

@app.route('/sair')
def sair():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=='POST':
        if request.form.get('senha_admin')==SENHA_ADMIN_SECRETA:
            session['admin']=True
            return redirect(url_for('admin'))
        else:
            return "Senha errada! <a href='/admin'>Voltar</a>"
    if not session.get('admin'):
        return render_template_string(ADMIN_LOGIN)
    pend = len([m for m in motoristas if m['status']!='APROVADO'])
    return render_template_string(ADMIN_HTML, motoristas=list(reversed(motoristas)), pendentes=pend)

@app.route('/admin/aprovar/<int:id>')
def aprovar(id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    for m in motoristas:
        if m['id']==id:
            m['status']='APROVADO'
    return redirect(url_for('admin'))

@app.route('/admin/reprovar/<int:id>')
def reprovar(id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    global motoristas
    motoristas=[m for m in motoristas if m['id']!=id]
    return redirect(url_for('admin'))

@app.route('/admin/limpar')
def limpar():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    global motoristas, next_id
    motoristas=[]
    next_id=1
    return redirect(url_for('admin'))

if __name__=='__main__':
    app.run(debug=True)