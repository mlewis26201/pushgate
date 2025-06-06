from fastapi import FastAPI, Request, Depends, Form, HTTPException, status, Query
import re
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
import secrets as pysecrets
from sqlalchemy.orm import Session
from .db import get_db, init_db
from .auth import get_current_admin, get_admin_password
from .pushover import send_pushover_message
from .rate_limit import check_token_rate_limit
from .models import Token, PushoverConfig, Message, AdminSettings
from .crypto import encrypt, decrypt
from datetime import datetime

# Add root_path for proxy path prefix
app = FastAPI(root_path="/pushgate")

app.add_middleware(SessionMiddleware, secret_key="dummy")  # Will be replaced with Docker secret

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
from .crypto import decrypt
# Register the 'decrypt' filter for Jinja2 templates
templates.env.filters["decrypt"] = decrypt

# CSRF token helpers
CSRF_SESSION_KEY = "csrf_token"
def get_csrf_token(request: Request):
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = pysecrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token

def verify_csrf(request: Request, token: str):
    session_token = request.session.get(CSRF_SESSION_KEY)
    if not session_token or session_token != token:
        raise HTTPException(status_code=400, detail="Invalid CSRF token")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    # If not logged in, redirect to login page
    if not request.session.get("admin_authenticated"):
        return RedirectResponse(url="/pushgate/login")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tokens", response_class=HTMLResponse)
def tokens_page(request: Request, db: Session = Depends(get_db), admin=Depends(get_current_admin), msg: str = Query(None)):
    tokens = db.query(Token).all()
    decrypted_tokens = []
    for t in tokens:
        try:
            decrypted = decrypt(t.encrypted_token)
        except Exception:
            decrypted = "<decryption error>"
        decrypted_tokens.append({
            "id": t.id,
            "token": decrypted,
            "created_at": t.created_at,
            "last_used": t.last_used,
            "rate_limit_per_hour": t.rate_limit_per_hour
        })
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse("tokens.html", {"request": request, "tokens": decrypted_tokens, "msg": msg, "csrf_token": csrf_token})

@app.post("/tokens/create")
def create_token(request: Request, db: Session = Depends(get_db), admin=Depends(get_current_admin), rate_limit_per_hour: int = Form(5), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    new_token = pysecrets.token_urlsafe(32)
    encrypted = encrypt(new_token)
    token_obj = Token(encrypted_token=encrypted, created_at=datetime.utcnow(), rate_limit_per_hour=rate_limit_per_hour)
    db.add(token_obj)
    db.commit()
    return RedirectResponse(url="/pushgate/tokens?msg=Token+created", status_code=303)

@app.post("/tokens/rotate")
def rotate_token(request: Request, token_id: int = Form(...), rate_limit_per_hour: int = Form(None), db: Session = Depends(get_db), admin=Depends(get_current_admin), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    token_obj = db.query(Token).filter(Token.id == token_id).first()
    if not token_obj:
        return RedirectResponse(url="/pushgate/tokens?msg=Token+not+found", status_code=303)
    new_token = pysecrets.token_urlsafe(32)
    token_obj.encrypted_token = encrypt(new_token)
    token_obj.created_at = datetime.utcnow()
    if rate_limit_per_hour is not None:
        token_obj.rate_limit_per_hour = rate_limit_per_hour
    db.commit()
    return RedirectResponse(url="/pushgate/tokens?msg=Token+rotated", status_code=303)

@app.post("/tokens/delete")
def delete_token(request: Request, token_id: int = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    token_obj = db.query(Token).filter(Token.id == token_id).first()
    if not token_obj:
        return RedirectResponse(url="/pushgate/tokens?msg=Token+not+found", status_code=303)
    db.delete(token_obj)
    db.commit()
    return RedirectResponse(url="/pushgate/tokens?msg=Token+deleted", status_code=303)

@app.get("/pushover-config", response_class=HTMLResponse)
def pushover_config_page(request: Request, db: Session = Depends(get_db), admin=Depends(get_current_admin), msg: str = Query(None)):
    configs = db.query(PushoverConfig).all()
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse("pushover_config.html", {"request": request, "configs": configs, "msg": msg, "csrf_token": csrf_token})

@app.post("/pushover-config/add")
def add_pushover_config(request: Request, name: str = Form(...), app_token: str = Form(...), user_key: str = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    enc_app_token = encrypt(app_token)
    enc_user_key = encrypt(user_key)
    config = PushoverConfig(name=name, encrypted_app_token=enc_app_token, encrypted_user_key=enc_user_key)
    db.add(config)
    db.commit()
    return RedirectResponse(url="/pushgate/pushover-config?msg=Config+added", status_code=303)

@app.post("/pushover-config/update")
def update_pushover_config(request: Request, config_id: int = Form(...), name: str = Form(...), app_token: str = Form(...), user_key: str = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    config = db.query(PushoverConfig).filter(PushoverConfig.id == config_id).first()
    if not config:
        return RedirectResponse(url="/pushgate/pushover-config?msg=Config+not+found", status_code=303)
    config.name = name
    config.encrypted_app_token = encrypt(app_token)
    config.encrypted_user_key = encrypt(user_key)
    config.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/pushgate/pushover-config?msg=Config+updated", status_code=303)

@app.post("/pushover-config/delete")
def delete_pushover_config(request: Request, config_id: int = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    config = db.query(PushoverConfig).filter(PushoverConfig.id == config_id).first()
    if not config:
        return RedirectResponse(url="/pushgate/pushover-config?msg=Config+not+found", status_code=303)
    db.delete(config)
    db.commit()
    return RedirectResponse(url="/pushgate/pushover-config?msg=Config+deleted", status_code=303)

@app.post("/send")
def send_message(token: str = Form(...), message: str = Form(...), db: Session = Depends(get_db), pushover_config_id: int = Form(None)):
    # Input validation (Pushover rules)
    if not message or len(message.encode('utf-8')) > 1024:
        raise HTTPException(status_code=400, detail="Message is required and must be at most 1024 UTF-8 bytes.")
    if not token or not re.fullmatch(r"[A-Za-z0-9]{30}", token):
        raise HTTPException(status_code=400, detail="Token must be 30 alphanumeric characters.")

    # Validate token
    token_objs = db.query(Token).all()
    valid_token = None
    for t in token_objs:
        try:
            if decrypt(t.encrypted_token) == token:
                valid_token = t
                break
        except Exception:
            continue
    if not valid_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Rate limit check (per-token)
    if not check_token_rate_limit(db, valid_token.id, valid_token.rate_limit_per_hour):
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Max {valid_token.rate_limit_per_hour} messages per hour. Please try again later.")

    # Select pushover config
    config = None
    if pushover_config_id is not None:
        config = db.query(PushoverConfig).filter(PushoverConfig.id == pushover_config_id).first()
        if not config:
            raise HTTPException(status_code=400, detail="Invalid pushover_config_id")
    # Send to Pushover
    status_code, resp_text = send_pushover_message(db, message, config=config)
    # Log message
    from .models import Message
    msg = Message(token_id=valid_token.id, message=message, status=str(status_code), timestamp=datetime.utcnow())
    db.add(msg)
    db.commit()

    if status_code == 200:
        return {"status": "ok", "pushover_response": resp_text}
    else:
        raise HTTPException(status_code=502, detail=f"Pushover error: {resp_text}")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, msg: str = Query(None)):
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "msg": msg, "csrf_token": csrf_token})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form(...), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    admin_password = get_admin_password()
    if password == admin_password:
        request.session["admin_authenticated"] = True
        return RedirectResponse(url="/pushgate/tokens?msg=Login+successful", status_code=303)
    else:
        csrf_token = get_csrf_token(request)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password", "msg": None, "csrf_token": csrf_token})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/pushgate/login?msg=Logged+out", status_code=303)

@app.get("/messages", response_class=HTMLResponse)
def messages_page(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    token_id: int = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Message)
    if token_id:
        query = query.filter(Message.token_id == token_id)
    if status:
        query = query.filter(Message.status == status)
    if search:
        query = query.filter(Message.message.ilike(f"%{search}%"))
    total = query.count()
    messages = (
        query.order_by(Message.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    tokens = db.query(Token).all()
    token_map = {t.id: decrypt(t.encrypted_token) for t in tokens}
    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "messages": messages,
            "token_map": token_map,
            "token_id": token_id,
            "status": status,
            "search": search,
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )

@app.get("/send-message", response_class=HTMLResponse)
def send_message_form(request: Request, db: Session = Depends(get_db), admin=Depends(get_current_admin), msg: str = Query(None), error: str = Query(None)):
    configs = db.query(PushoverConfig).all()
    return templates.TemplateResponse("send_message.html", {"request": request, "msg": msg, "error": error, "configs": configs})

@app.post("/send-message", response_class=HTMLResponse)
def send_message_admin(request: Request, message: str = Form(...), pushover_config_id: int = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    from .models import Token, PushoverConfig, Message
    from .pushover import send_pushover_message
    tokens = db.query(Token).all()
    if not tokens:
        return RedirectResponse(url="/pushgate/send-message?error=No+tokens+available", status_code=303)
    token = decrypt(tokens[0].encrypted_token)
    config = db.query(PushoverConfig).filter(PushoverConfig.id == pushover_config_id).first()
    if not config:
        return RedirectResponse(url="/pushgate/send-message?error=Invalid+Pushover+config", status_code=303)
    try:
        status_code, resp_text = send_pushover_message(db, message, config=config)
        # Log message
        msg = Message(token_id=tokens[0].id, message=message, status=str(status_code), timestamp=datetime.utcnow())
        db.add(msg)
        db.commit()
        if status_code == 200:
            return RedirectResponse(url="/pushgate/send-message?msg=Message+sent", status_code=303)
        else:
            return RedirectResponse(url=f"/pushgate/send-message?error=Pushover+error:+{resp_text}", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/pushgate/send-message?error={e.detail}", status_code=303)

@app.get("/change-password", response_class=HTMLResponse)
def change_password_page(request: Request, admin=Depends(get_current_admin), msg: str = Query(None), error: str = Query(None)):
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse("change_password.html", {"request": request, "msg": msg, "error": error, "csrf_token": csrf_token})

@app.post("/change-password", response_class=HTMLResponse)
def change_password(request: Request, old_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...), csrf_token: str = Form(...)):
    verify_csrf(request, csrf_token)
    admin_password = get_admin_password()
    if old_password != admin_password:
        csrf_token = get_csrf_token(request)
        return templates.TemplateResponse("change_password.html", {"request": request, "msg": None, "error": "Old password is incorrect", "csrf_token": csrf_token})
    if new_password != confirm_password:
        csrf_token = get_csrf_token(request)
        return templates.TemplateResponse("change_password.html", {"request": request, "msg": None, "error": "New passwords do not match", "csrf_token": csrf_token})
    # Update password in DB only
    db = next(get_db())
    from .models import AdminSettings
    from .crypto import encrypt
    from datetime import datetime
    enc_pw = encrypt(new_password)
    admin_settings = db.query(AdminSettings).order_by(AdminSettings.updated_at.desc()).first()
    if admin_settings:
        admin_settings.encrypted_password = enc_pw
        admin_settings.updated_at = datetime.utcnow()
    else:
        admin_settings = AdminSettings(encrypted_password=enc_pw)
        db.add(admin_settings)
    db.commit()
    db.close()
    return RedirectResponse(url="/pushgate/login?msg=Password+changed+successfully", status_code=303)
