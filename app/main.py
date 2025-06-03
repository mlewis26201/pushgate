from fastapi import FastAPI, Request, Depends, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
import secrets
from sqlalchemy.orm import Session
from .db import get_db, init_db
from .auth import get_current_admin, get_admin_password
from .pushover import send_pushover_message
from .rate_limit import check_token_rate_limit
from .models import Token, PushoverConfig, Message
from .crypto import encrypt, decrypt
from datetime import datetime

# Add root_path for proxy path prefix
app = FastAPI(root_path="/pushgate")

app.add_middleware(SessionMiddleware, secret_key="dummy")  # Will be replaced with Docker secret

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    init_db()

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
    return templates.TemplateResponse("tokens.html", {"request": request, "tokens": decrypted_tokens, "msg": msg})

@app.post("/tokens/create")
def create_token(request: Request, db: Session = Depends(get_db), admin=Depends(get_current_admin), rate_limit_per_hour: int = Form(5)):
    new_token = secrets.token_urlsafe(32)
    encrypted = encrypt(new_token)
    token_obj = Token(encrypted_token=encrypted, created_at=datetime.utcnow(), rate_limit_per_hour=rate_limit_per_hour)
    db.add(token_obj)
    db.commit()
    return RedirectResponse(url="/pushgate/tokens?msg=Token+created", status_code=303)

@app.post("/tokens/rotate")
def rotate_token(request: Request, token_id: int = Form(...), rate_limit_per_hour: int = Form(None), db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    token_obj = db.query(Token).filter(Token.id == token_id).first()
    if not token_obj:
        return RedirectResponse(url="/pushgate/tokens?msg=Token+not+found", status_code=303)
    new_token = secrets.token_urlsafe(32)
    token_obj.encrypted_token = encrypt(new_token)
    token_obj.created_at = datetime.utcnow()
    if rate_limit_per_hour is not None:
        token_obj.rate_limit_per_hour = rate_limit_per_hour
    db.commit()
    return RedirectResponse(url="/pushgate/tokens?msg=Token+rotated", status_code=303)

@app.post("/tokens/delete")
def delete_token(request: Request, token_id: int = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    token_obj = db.query(Token).filter(Token.id == token_id).first()
    if not token_obj:
        return RedirectResponse(url="/pushgate/tokens?msg=Token+not+found", status_code=303)
    db.delete(token_obj)
    db.commit()
    return RedirectResponse(url="/pushgate/tokens?msg=Token+deleted", status_code=303)

@app.get("/pushover-config", response_class=HTMLResponse)
def pushover_config_page(request: Request, db: Session = Depends(get_db), admin=Depends(get_current_admin), msg: str = Query(None)):
    config = db.query(PushoverConfig).first()
    app_token = user_key = ""
    if config:
        try:
            app_token = decrypt(config.encrypted_app_token)
            user_key = decrypt(config.encrypted_user_key)
        except Exception:
            app_token = user_key = "<decryption error>"
    return templates.TemplateResponse("pushover_config.html", {"request": request, "app_token": app_token, "user_key": user_key, "msg": msg})

@app.post("/pushover-config/update")
def update_pushover_config(request: Request, app_token: str = Form(...), user_key: str = Form(...), db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    config = db.query(PushoverConfig).first()
    enc_app_token = encrypt(app_token)
    enc_user_key = encrypt(user_key)
    if config:
        config.encrypted_app_token = enc_app_token
        config.encrypted_user_key = enc_user_key
        config.updated_at = datetime.utcnow()
    else:
        config = PushoverConfig(encrypted_app_token=enc_app_token, encrypted_user_key=enc_user_key)
        db.add(config)
    db.commit()
    return RedirectResponse(url="/pushgate/pushover-config?msg=Config+updated", status_code=303)

@app.post("/send")
def send_message(token: str = Form(...), message: str = Form(...), db: Session = Depends(get_db)):
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

    # Send to Pushover
    status_code, resp_text = send_pushover_message(db, message)
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
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "msg": msg})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form(...)):
    admin_password = get_admin_password()
    if password == admin_password:
        request.session["admin_authenticated"] = True
        return RedirectResponse(url="/pushgate/tokens?msg=Login+successful", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password", "msg": None})

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
