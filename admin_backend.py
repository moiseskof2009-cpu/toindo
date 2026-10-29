import html
import json; import logging
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Response, abort, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash; logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None
try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

DB_PATH = None
DATABASE_URL = None


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, connection, postgres=False):
        self.connection = connection
        self.postgres = postgres
    def execute(self, query, params=()):
        if self.postgres:
            query = query.replace("?", "%s")
        return self.connection.execute(query, params)
    def executescript(self, script):
        if self.postgres:
            for statement in script.split(";"):
                if statement.strip(): self.execute(statement)
        else:
            self.connection.executescript(script)
    def __enter__(self):
        return self
    def __exit__(self, kind, value, traceback):
        if kind is None: self.connection.commit()
        else: self.connection.rollback()
        self.connection.close()

def database():
    if DATABASE_URL:
        if psycopg is None:
            raise RuntimeError("Instale psycopg para usar o banco PostgreSQL.")
        return Database(psycopg.connect(DATABASE_URL, row_factory=dict_row), postgres=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return Database(conn)


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_ok(value):
    return bool(value and secrets.compare_digest(str(value), str(session.get("csrf_token", ""))))


def encryption_ready():
    if os.environ.get("RENDER") and not os.environ.get("TOINDO_DATABASE_URL"):
        return False
    if Fernet is None or not os.environ.get("PII_ENCRYPTION_KEY"):
        return False
    try:
        Fernet(os.environ["PII_ENCRYPTION_KEY"].encode())
        return True
    except Exception:
        return False


def encrypt(value):
    if value in (None, ""):
        return None
    return Fernet(os.environ["PII_ENCRYPTION_KEY"].encode()).encrypt(str(value).encode()).decode()


def decrypt(value):
    if not value:
        return ""
    return Fernet(os.environ["PII_ENCRYPTION_KEY"].encode()).decrypt(value.encode()).decode()


def admin_configured():
    return all(os.environ.get(key) for key in ("ADMIN_USERNAME", "ADMIN_PASSWORD_HASH", "ADMIN_SESSION_SECRET", "TOINDO_DATABASE_URL" if os.environ.get("RENDER") else "ADMIN_USERNAME"))


def admin_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not session.get("admin_user"):
            return redirect(url_for("admin_login", next=request.path))
        return func(*args, **kwargs)
    return wrapped


def add_event(conn, app_id, actor, action, note=""):
    conn.execute("INSERT INTO events VALUES(?,?,?,?,?,?)", (str(uuid.uuid4()), app_id, actor, action, note[:500], now_iso()))


def get_application(app_id):
    with database() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    for field in ("name", "phone", "email", "address", "cpf", "birth", "license", "license_category", "license_expiry", "vehicle"):
        value = data.get(field + "_enc")
        data[field] = json.loads(decrypt(value)) if field == "vehicle" and value else decrypt(value)
    return data


def status_label(status):
    return {"PENDENTE":"Cadastro recebido; aguardando análise", "APROVADO":"Cadastro aprovado", "CORRECAO":"Correção solicitada", "RECUSADO":"Cadastro recusado"}.get(status, "Atualização do cadastro")

def send_whatsapp(applicant, label, detail=""):
    if not applicant.get("whatsapp_opt_in"):
        return "not_opted_in", ""
    token=os.environ.get("WHATSAPP_ACCESS_TOKEN"); phone_id=os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    template=os.environ.get("WHATSAPP_STATUS_TEMPLATE", os.environ.get("WHATSAPP_APPROVED_TEMPLATE"))
    version=os.environ.get("WHATSAPP_API_VERSION"); language=os.environ.get("WHATSAPP_TEMPLATE_LANGUAGE","pt_BR")
    if not all((token,phone_id,template,version)):
        return "not_configured", ""
    number="".join(c for c in applicant["phone"] if c.isdigit())
    if number.startswith("0"): number=number[1:]
    if not number.startswith("55"): number="55"+number
    params=[{"type":"text","text":str(applicant.get("name") or "")[:100]}, {"type":"text","text":str(label)[:100]}, {"type":"text","text":str(detail or "Acompanhe seu cadastro pelo Toindo.")[:500]}]
    payload={"messaging_product":"whatsapp","recipient_type":"individual","to":number,"type":"template","template":{"name":template,"language":{"code":language},"components":[{"type":"body","parameters":params}]}}
    req=Request(f"https://graph.facebook.com/{version}/{phone_id}/messages",data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=15) as response: result=json.loads(response.read().decode())
        return "sent",(result.get("messages") or [{}])[0].get("id","")
    except HTTPError as exc:
        try:
            error_data=json.loads(exc.read().decode())
            api_error=error_data.get("error", {}) if isinstance(error_data, dict) else {}
        except (UnicodeDecodeError, ValueError):
            api_error={}
        logger.warning(
            "WhatsApp Cloud API rejected a message: http_status=%s api_code=%s api_subcode=%s api_type=%s",
            exc.code, api_error.get("code"), api_error.get("error_subcode"), api_error.get("type")
        )
        return "failed", ""
    except (URLError,TimeoutError,ValueError) as exc:
        logger.warning("WhatsApp Cloud API request failed: error_type=%s", type(exc).__name__)
        return "failed", ""
        

def update_whatsapp(app_id):
    applicant=get_application(app_id)
    if not applicant: return "missing"
    label=status_label(applicant["status"])
    status,message_id=send_whatsapp(applicant,label,applicant.get("review_note", ""))
    with database() as conn:
        conn.execute("UPDATE applications SET whatsapp_status=?,whatsapp_message_id=? WHERE id=?",(status,message_id,app_id))
        add_event(conn,app_id,"system","whatsapp_"+status,label)
    return status

def notify_public_submission(app_id):
    base=os.environ.get("ADMIN_INTERNAL_URL","").rstrip("/")
    token=os.environ.get("ADMIN_INTERNAL_TOKEN","")
    if not base or not token: return "not_configured"
    req=Request(base+"/internal/notify/"+app_id,data=b"{}",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=10) as response: return json.loads(response.read().decode()).get("status","failed")
    except (HTTPError,URLError,TimeoutError,ValueError): return "failed"

def login_page(message=""):
    token = html.escape(csrf_token())
    error = f'<p class="notice">{html.escape(message)}</p>' if message else ""
    return Response(f'''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Toindo</title><style>body{{font:16px Arial;background:#f5f5f5}}main{{max-width:440px;margin:50px auto;padding:22px;background:#fff;border-radius:16px}}input{{display:block;width:100%;box-sizing:border-box;padding:12px;margin:8px 0 16px;border:1px solid #ddd;border-radius:8px}}button{{padding:12px 18px;background:#00e676;border:0;border-radius:8px;font-weight:bold}}.notice{{padding:12px;background:#fff3cd}}</style><main><h1>Entrar na administra&ccedil;&atilde;o</h1>{error}<form method="post"><input type="hidden" name="csrf_token" value="{token}"><label>Usu&aacute;rio</label><input name="username" autocomplete="username" required><label>Senha</label><input name="password" type="password" autocomplete="current-password" required><button>ENTRAR</button></form></main></html>''', mimetype="text/html")


def register_admin_routes(app):
    global DB_PATH, DATABASE_URL
    DATABASE_URL = os.environ.get("TOINDO_DATABASE_URL")
    DB_PATH = Path(os.environ.get("TOINDO_DB_PATH", str(Path(app.instance_path) / "toindo.sqlite3")))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = """CREATE TABLE IF NOT EXISTS applications(
    id TEXT PRIMARY KEY,type TEXT NOT NULL,status TEXT NOT NULL,name_enc TEXT NOT NULL,phone_enc TEXT NOT NULL,email_enc TEXT NOT NULL,address_enc TEXT NOT NULL,
    cpf_enc TEXT,birth_enc TEXT,license_enc TEXT,license_category_enc TEXT,license_expiry_enc TEXT,vehicle_enc TEXT,
    whatsapp_opt_in INTEGER NOT NULL DEFAULT 0,whatsapp_opt_in_at TEXT,created_at TEXT NOT NULL,reviewed_at TEXT,review_note TEXT,
    whatsapp_status TEXT NOT NULL DEFAULT 'not_sent',whatsapp_message_id TEXT);
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,application_id TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,note TEXT,created_at TEXT NOT NULL,FOREIGN KEY(application_id) REFERENCES applications(id));"""
    with database() as conn:
        conn.executescript(schema)
    app.secret_key = os.environ.get("ADMIN_SESSION_SECRET") or secrets.token_urlsafe(48)
    app.config.update(MAX_CONTENT_LENGTH=16 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")))

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if not admin_configured():
            return login_page("Configure ADMIN_USERNAME, ADMIN_PASSWORD_HASH e SESSION_SECRET no ambiente."), 503
        if request.method == "POST":
            if not csrf_ok(request.form.get("csrf_token")):
                abort(400)
            username, password = request.form.get("username", ""), request.form.get("password", "")
            if secrets.compare_digest(username, os.environ["ADMIN_USERNAME"]) and check_password_hash(os.environ["ADMIN_PASSWORD_HASH"], password):
                session.clear()
                session["admin_user"] = username
                csrf_token()
                return redirect(url_for("admin_page"))
            return login_page("Usu&aacute;rio ou senha incorretos."), 401
        return login_page()

    @app.route("/admin/logout", methods=["POST"])
    @admin_only
    def admin_logout():
        if not csrf_ok(request.form.get("csrf_token")):
            abort(400)
        session.clear()
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @admin_only
    def admin_page():
        if not encryption_ready():
            return login_page("PII_ENCRYPTION_KEY ainda n&atilde;o foi configurada."), 503
        with database() as conn:
            rows = conn.execute("SELECT * FROM applications WHERE type='motorista' ORDER BY CASE status WHEN 'PENDENTE' THEN 0 ELSE 1 END,created_at DESC").fetchall()
            events = conn.execute("SELECT actor,action,created_at FROM events ORDER BY created_at DESC LIMIT 20").fetchall()
        token = html.escape(csrf_token())
        cards = []
        for raw in rows:
            item = get_application(raw["id"])
            vehicle = item.get("vehicle") or {}
            fields = [("WhatsApp",item["phone"]),("E-mail",item["email"]),("CPF",item["cpf"]),("Nascimento",item["birth"]),("Endere&ccedil;o",item["address"]),("CNH",item["license"]),("Categoria",item["license_category"]),("Validade",item["license_expiry"]),("Moto",vehicle.get("marca_modelo")),("Ano",vehicle.get("ano")),("Placa",vehicle.get("placa")),("Cor",vehicle.get("cor")),("Renavam",vehicle.get("renavam"))]
            details = "".join(f'<div><small>{label}</small><br><b>{html.escape(str(value or "-"))}</b></div>' for label,value in fields)
            status = {"PENDENTE":"Pendente","APROVADO":"Aprovado","CORRECAO":"Corre&ccedil;&atilde;o solicitada","RECUSADO":"Recusado"}.get(item["status"],item["status"])
            wa = {"sent":"WhatsApp enviado","not_opted_in":"Sem consentimento para WhatsApp","not_configured":"WhatsApp n&atilde;o configurado","failed":"Falha no envio","not_sent":"N&atilde;o enviado"}.get(item["whatsapp_status"],item["whatsapp_status"])
            buttons = ""
            if item["status"] == "PENDENTE":
                buttons = f'''<textarea name="note" form="review-{item['id']}" placeholder="Motivo para corre&ccedil;&atilde;o ou recusa"></textarea><form id="review-{item['id']}" method="post" action="/admin/applications/{item['id']}/review"><input type="hidden" name="csrf_token" value="{token}"><button class="btn" name="action" value="approve">APROVAR</button><button class="btn warn" name="action" value="correction">PEDIR CORRE&Ccedil;&Atilde;O</button><button class="btn danger" name="action" value="reject">RECUSAR</button></form>'''
            if item["whatsapp_opt_in"] and item["whatsapp_status"] in ("failed","not_configured","not_sent"):
                buttons += f'<form method="post" action="/admin/applications/{item["id"]}/notify"><input type="hidden" name="csrf_token" value="{token}"><button class="btn alt">REENVIAR WHATSAPP</button></form>'
            cards.append(f'''<article class="card"><div class="head"><h2>{html.escape(item['name'])}</h2><span class="pill">{status}</span><small>Recebido: {html.escape(item['created_at'])}</small><small>{wa} · Consentiu: {'sim' if item['whatsapp_opt_in'] else 'n&atilde;o'}</small></div><div class="grid">{details}</div><p><b>Observa&ccedil;&atilde;o:</b> {html.escape(item['review_note'] or '-')}</p>{buttons}</article>''')
        history = "".join(f'<li>{html.escape(e["created_at"])} — {html.escape(e["actor"])}: {html.escape(e["action"])}</li>' for e in events)
        test_status=request.args.get("whatsapp_test", "")
        test_notice={"sent":"Mensagem de teste enviada.","not_configured":"WhatsApp ainda nao configurado; nenhuma mensagem foi enviada.","failed":"O WhatsApp nao confirmou o envio; tente novamente depois.","not_opted_in":"O teste exige autorizacao explicita."}.get(test_status, "")
        test_banner=f'<p class="note">{html.escape(test_notice)}</p>' if test_notice else ""
        content = f'''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Toindo</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#f5f5f5;color:#171717;font:15px Arial}}main{{max-width:1000px;margin:20px auto;padding:16px}}header,.card{{background:#fff;border-radius:14px;padding:18px;margin:12px 0;box-shadow:0 2px 9px #0001}}header{{background:#080808;color:#fff}}header b{{color:#00e676;font-size:22px}}.head{{display:flex;gap:12px;align-items:center;flex-wrap:wrap}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}}small{{color:#666}}.pill{{padding:6px 10px;border-radius:20px;background:#eee;font-weight:bold}}button{{border:0;border-radius:8px;padding:11px 13px;margin:5px;background:#00e676;font-weight:bold;cursor:pointer}}.warn{{background:#fff0cb}}.danger{{background:#ffe4e4}}.alt{{background:#222;color:white}}textarea{{display:block;width:100%;min-height:62px;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:8px}}.note{{background:#eafff1;padding:12px;border-radius:9px}}</style><main><header><div class="head"><b>TOINDO · Admin</b><span>{html.escape(session['admin_user'])}</span><form method="post" action="/admin/logout"><input type="hidden" name="csrf_token" value="{token}"><button class="alt">SAIR</button></form></div></header><p class="note">Os dados pessoais ficam criptografados no banco. Confira as informa&ccedil;&otilde;es antes de aprovar.</p>{test_banner}<h1>Cadastros de motorista</h1>{''.join(cards) or '<article class="card">Nenhum cadastro recebido.</article>'}<article class="card"><h2>Teste de WhatsApp</h2><p>Informe um n&uacute;mero seu, com DDD. O teste envia uma &uacute;nica mensagem usando o modelo aprovado.</p><form method="post" action="/admin/whatsapp/test"><input type="hidden" name="csrf_token" value="{token}"><input name="phone" placeholder="(65) 99999-9999" required><label><input type="checkbox" name="confirm_test" value="yes" required> Confirmo que o n&uacute;mero &eacute; meu e autorizo esta mensagem de teste.</label><p><button class="btn">ENVIAR MENSAGEM DE TESTE</button></p></form></article><details class="card"><summary>Hist&oacute;rico de decis&otilde;es</summary><ul>{history or '<li>Sem eventos.</li>'}</ul></details></main></html>'''
        return Response(content, mimetype="text/html")

    @app.route("/admin/applications/<app_id>/review", methods=["POST"])
    @admin_only
    def review(app_id):
        if not csrf_ok(request.form.get("csrf_token")):
            abort(400)
        action = request.form.get("action")
        note = request.form.get("note", "").strip()[:500]
        statuses = {"approve":"APROVADO","correction":"CORRECAO","reject":"RECUSADO"}
        if action not in statuses or (action != "approve" and not note):
            abort(400)
        with database() as conn:
            row = conn.execute("SELECT id FROM applications WHERE id=? AND type='motorista'", (app_id,)).fetchone()
            if not row:
                abort(404)
            conn.execute("UPDATE applications SET status=?,reviewed_at=?,review_note=? WHERE id=?", (statuses[action],now_iso(),note,app_id))
            add_event(conn,app_id,session["admin_user"],action,note)
        update_whatsapp(app_id)
        return redirect(url_for("admin_page"))

    @app.route("/admin/applications/<app_id>/notify", methods=["POST"])
    @admin_only
    def retry_whatsapp(app_id):
        if not csrf_ok(request.form.get("csrf_token")):
            abort(400)
        item = get_application(app_id)
        if not item or not item["whatsapp_opt_in"]:
            abort(400)
        update_whatsapp(app_id)
        return redirect(url_for("admin_page"))

    @app.route("/internal/notify/<app_id>", methods=["POST"])
    def internal_notify(app_id):
        expected=os.environ.get("ADMIN_INTERNAL_TOKEN","")
        supplied=request.headers.get("Authorization","").removeprefix("Bearer ")
        if not expected or not secrets.compare_digest(supplied,expected):
            abort(404)
        item=get_application(app_id)
        if not item or item["type"]!="motorista" or item["status"]!="PENDENTE":
            return jsonify({"status":"not_eligible"}),409
        if item["whatsapp_status"]=="sent":
            return jsonify({"status":"already_sent"})
        return jsonify({"status":update_whatsapp(app_id)})

    @app.route("/admin/whatsapp/test", methods=["POST"])
    @admin_only
    def whatsapp_test():
        if not csrf_ok(request.form.get("csrf_token")) or request.form.get("confirm_test")!="yes":
            abort(400)
        phone=request.form.get("phone","").strip()
        digits="".join(ch for ch in phone if ch.isdigit())
        if len(digits) not in (10,11,12,13):
            return redirect(url_for("admin_page"))
        result,_=send_whatsapp({"whatsapp_opt_in":True,"phone":phone,"name":"Teste Toindo"},"Teste da integração","Esta é uma mensagem de teste solicitada pelo administrador.")
        return redirect(url_for("admin_page",whatsapp_test=result))

    @app.route("/api/usuarios", methods=["GET"])
    @admin_only
    def applications_api():
        with database() as conn:
            rows=conn.execute("SELECT id,type,status,created_at,reviewed_at,whatsapp_status FROM applications ORDER BY created_at DESC").fetchall()
        return jsonify([dict(row) for row in rows])

    @app.route("/api/aprovar/<app_id>", methods=["POST"])
    @admin_only
    def approve_api(app_id):
        data=request.get_json(silent=True) or {}
        if not csrf_ok(data.get("_csrf")):
            return jsonify({"error":"CSRF invalido."}),400
        with database() as conn:
            row=conn.execute("SELECT id FROM applications WHERE id=? AND type='motorista'",(app_id,)).fetchone()
            if not row:return jsonify({"error":"Cadastro nao encontrado."}),404
            conn.execute("UPDATE applications SET status='APROVADO',reviewed_at=? WHERE id=?",(now_iso(),app_id))
            add_event(conn,app_id,session["admin_user"],"approve")
        return jsonify({"ok":True,"whatsapp":update_whatsapp(app_id)})

    return csrf_token


def register_public_routes(app):
    global DB_PATH, DATABASE_URL
    DATABASE_URL = os.environ.get("TOINDO_DATABASE_URL")
    DB_PATH = Path(os.environ.get("TOINDO_DB_PATH", str(Path(app.instance_path) / "toindo.sqlite3")))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    app.secret_key = os.environ.get("PUBLIC_SESSION_SECRET") or secrets.token_urlsafe(48)
    app.config.update(MAX_CONTENT_LENGTH=2 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")))
    @app.after_request
    def public_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response
    if not os.environ.get("RENDER"):
        schema = """CREATE TABLE IF NOT EXISTS applications(
        id TEXT PRIMARY KEY,type TEXT NOT NULL,status TEXT NOT NULL,name_enc TEXT NOT NULL,phone_enc TEXT NOT NULL,email_enc TEXT NOT NULL,address_enc TEXT NOT NULL,
        cpf_enc TEXT,birth_enc TEXT,license_enc TEXT,license_category_enc TEXT,license_expiry_enc TEXT,vehicle_enc TEXT,
        whatsapp_opt_in INTEGER NOT NULL DEFAULT 0,whatsapp_opt_in_at TEXT,created_at TEXT NOT NULL,reviewed_at TEXT,review_note TEXT,
        whatsapp_status TEXT NOT NULL DEFAULT 'not_sent',whatsapp_message_id TEXT);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,application_id TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,note TEXT,created_at TEXT NOT NULL,FOREIGN KEY(application_id) REFERENCES applications(id));"""
        with database() as conn:
            conn.executescript(schema)
    @app.route("/api/usuarios", methods=["POST"])
    def submit_application():
        form=request.get_json(silent=True) or {}
        if not csrf_ok(form.get("_csrf")):
            return jsonify({"error":"Sessao expirada. Atualize a pagina."}),400
        if not encryption_ready() or (os.environ.get("RENDER") and not os.environ.get("PUBLIC_SESSION_SECRET")):
            return jsonify({"error":"O armazenamento protegido ainda nao foi configurado."}),503
        try:
            kind=form.get("tipo",""); name=form.get("nome","").strip(); phone=form.get("tel","").strip(); email=form.get("email","").strip(); address=form.get("endereco","").strip()
            digits="".join(ch for ch in phone if ch.isdigit())
            if kind not in ("motorista","passageiro") or len(name)<3 or len(digits) not in (10,11,12,13) or "@" not in email or not address:
                raise ValueError("Confira nome, WhatsApp, e-mail e endereco.")
            app_id=str(uuid.uuid4()); status="APROVADO" if kind=="passageiro" else "PENDENTE"
            if kind=="motorista":
                cpf=form.get("cpf","").strip(); birth=form.get("nascimento",""); license_no=form.get("cnh","").strip(); category=form.get("categoria_cnh",""); expiry=form.get("validade_cnh",""); vehicle=form.get("moto") or {}
                if not all((cpf,birth,license_no,category,expiry,vehicle.get("marca_modelo"),vehicle.get("ano"),vehicle.get("placa"),vehicle.get("cor"))):
                    raise ValueError("Preencha os dados obrigatorios da CNH e da moto.")
                if category not in ("A","AB"):
                    raise ValueError("A categoria da CNH deve ser A ou AB.")
                opt_in=1 if form.get("whatsapp_opt_in") else 0
            else:
                cpf=birth=license_no=category=expiry=None; vehicle=None; opt_in=0
            opt_in_at=now_iso() if opt_in else None
            values=(app_id,kind,status,encrypt(name),encrypt(phone),encrypt(email),encrypt(address),encrypt(cpf),encrypt(birth),encrypt(license_no),encrypt(category),encrypt(expiry),encrypt(json.dumps(vehicle,ensure_ascii=False) if vehicle else None),opt_in,opt_in_at,now_iso())
            with database() as conn:
                conn.execute("INSERT INTO applications(id,type,status,name_enc,phone_enc,email_enc,address_enc,cpf_enc,birth_enc,license_enc,license_category_enc,license_expiry_enc,vehicle_enc,whatsapp_opt_in,whatsapp_opt_in_at,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",values)
                add_event(conn,app_id,"system","submitted")
            if kind == "motorista":
                notify_public_submission(app_id)
            return jsonify({"ok":True,"id":app_id,"status":status}),201
        except ValueError as error:
            return jsonify({"error":str(error)}),400
    return csrf_token
