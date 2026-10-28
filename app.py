from flask import Flask, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)
corridas = []
usuarios = []

HTML_HOME = """ [ ... todo o HTML grande ... ] """

@app.route('/')
def home():
    return HTML_HOME

@app.route('/api/usuarios', methods=['POST'])
def api_usuarios():
    d=request.json
    nid=str(uuid.uuid4())
    usuarios.append({"id":nid,"nome":d.get('nome'),"tel":d.get('tel'),"tipo":d.get('tipo'),"status":"aprovado" if d.get('tipo')=='passageiro' else 'pendente'})
    return jsonify({"ok":True,"id":nid,"status":"aprovado" if d.get('tipo')=='passageiro' else 'pendente'})

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
