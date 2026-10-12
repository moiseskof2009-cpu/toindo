from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import uuid
app = Flask(__name__)
CORS(app)

corridas=[]
usuarios=[]

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Toindo - V10 Final</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{font-family:Arial,sans-serif;box-sizing:border-box;margin:0;padding:0}
body{background:#f5f5f5}
.top-yellow{background:#FFEB3B;padding:12px 14px}
.user-row{display:flex;align-items:center;justify-content:space-between}
.map-box{height:300px;background:#e0e0e0;position:relative}
#map{height:100%;width:100%}
.card-search{background:#fff;margin:-30px 14px 10px 14px;border-radius:16px;padding:14px;box-shadow:0 4px 12px rgba(0,0,0,0.15);position:relative;z-index:10}
.search-input{width:100%;padding:14px 12px;border:1px solid #e0e0e0;border-radius:10px;background:#f7f7f7;font-size:16px}
.origem-box{display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0}
.origem-dot{width:10px;height:10px;background:#FFC107;border-radius:50%;margin-right:10px}
.dest-dot{width:10px;height:10px;background:#000;border-radius:0;margin-right:10px;transform:rotate(45deg)}
.sugestao{padding:12px 4px;border-bottom:1px solid #f0f0f0;cursor:pointer;display:flex;justify-content:space-between}
.sugestao:hover{background:#f9f9f9}
.btn-moto{background:#00FF88;color:#000;border:none;padding:16px;border-radius:14px;width:100%;font-weight:900;font-size:16px
