"""Admin routes for configuration management."""

from pathlib import Path

from fastapi import APIRouter, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

router = APIRouter()

# Load HTML templates from static files
ADMIN_HTML: str = (Path(__file__).parent.parent / "static" / "admin.html").read_text(encoding="utf-8")
LOGIN_HTML: str = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>omni-gen 管理登录</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        .login-card {
            background: #1e293b;
            border-radius: 16px;
            padding: 2rem;
            width: 100%;
            max-width: 400px;
            border: 1px solid #334155;
        }
        h1 {
            text-align: center;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .form-group { margin-bottom: 1rem; }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #94a3b8;
        }
        input {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            border: 1px solid #475569;
            background: #0f172a;
            color: #e2e8f0;
            font-size: 1rem;
        }
        input:focus { outline: none; border-color: #667eea; }
        .btn {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transition: all 0.2s;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .error { color: #dc2626; margin-top: 1rem; text-align: center; }
        .back-link {
            display: block;
            text-align: center;
            margin-top: 1rem;
            color: #667eea;
            text-decoration: none;
        }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>🔐 omni-gen 管理登录</h1>
        <div class="form-group">
            <label>密码</label>
            <input type="password" id="password" placeholder="请输入管理密码" onkeypress="handleEnter(event)">
        </div>
        <button class="btn" onclick="login()">登录</button>
        <div id="error" class="error" style="display: none;"></div>
        <a href="/" class="back-link">← 返回首页</a>
    </div>

    <script>
        function handleEnter(e) {
            if (e.key === 'Enter') login();
        }

        async function login() {
            const password = document.getElementById('password').value;
            const error = document.getElementById('error');

            try {
                const response = await fetch('/api/v1/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });

                const data = await response.json();

                if (data.success) {
                    sessionStorage.setItem('admin_token', data.token);
                    window.location.href = '/admin';
                } else {
                    error.textContent = data.error || '登录失败';
                    error.style.display = 'block';
                }
            } catch (err) {
                error.textContent = '登录失败: ' + err.message;
                error.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    """Serve admin login page."""
    return LOGIN_HTML


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Serve admin dashboard page (requires auth)."""
    token = request.cookies.get("admin_token", "")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return LOGIN_HTML

    return ADMIN_HTML


@router.get("/logout")
async def logout():
    """Logout and clear session."""
    response = RedirectResponse(url="/admin/login")
    response.delete_cookie("admin_token")
    return response


# ── API endpoints ──────────────────────────────────────────────

@router.post("/api/v1/admin/login")
async def admin_login(body: dict = Body(...)):
    """Admin login API."""
    import hashlib
    import secrets

    from omni_gen.runtime_config import get_runtime_config

    password = body.get("password")
    if not password:
        return JSONResponse({"success": False, "error": "密码不能为空"}, status_code=400)

    config = get_runtime_config()
    stored_hash = config.get("ADMIN_PASSWORD", "admin123")

    provided_hash = hashlib.sha256(password.encode()).hexdigest()

    if secrets.compare_digest(stored_hash, provided_hash):
        token = hashlib.sha256(f"{password}:{secrets.token_hex(16)}".encode()).hexdigest()
        response = JSONResponse({"success": True, "token": token})
        response.set_cookie(
            key="admin_token",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=3600 * 24,
        )
        return response

    return {"success": False, "error": "密码错误"}


@router.get("/api/v1/admin/config")
async def get_all_config(request: Request):
    """Get all configuration from database."""
    from omni_gen.runtime_config import get_runtime_config

    config = get_runtime_config()
    all_config = config.get_all()

    formatted = {}
    for key, value in all_config.items():
        raw = config.get_raw(key)
        formatted[key] = {
            "value": value,
            "description": raw.get("description") if raw else "",
            "category": raw.get("category") if raw else "",
        }

    return {"config": formatted}


@router.post("/api/v1/admin/config")
async def create_config(body: dict = Body(...)):
    """Create a new config entry."""
    import json

    from omni_gen.runtime_config import get_runtime_config

    key = body.get("key")
    value = body.get("value")
    category = body.get("category")
    description = body.get("description")

    if not key:
        return {"success": False, "error": "配置键名不能为空"}

    try:
        parsed_value = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        parsed_value = value

    config = get_runtime_config()
    config.set(key, parsed_value, description, category)

    return {"success": True}


@router.put("/api/v1/admin/config/{config_key}")
async def update_config(request: Request, config_key: str, body: dict = Body(...)):
    """Update a config value."""
    from omni_gen.runtime_config import get_runtime_config

    config = get_runtime_config()
    raw = config.get_raw(config_key)

    config.set(
        config_key,
        body.get("value"),
        raw.get("description") if raw else None,
        raw.get("category") if raw else None,
    )

    return {"success": True, "message": f"配置 {config_key} 已更新"}


@router.get("/api/v1/admin/defaults")
async def get_defaults():
    """Return .env default values map for all config keys.

    Keys are returned in UPPERCASE to match the config DB naming convention.
    """
    from pathlib import Path

    from omni_gen.config import get_settings

    settings = get_settings()
    defaults = {}
    for key in settings.model_fields:
        val = getattr(settings, key, None)
        if val is None:
            continue
        # Convert key to UPPERCASE to match config DB convention (e.g. admin_password -> ADMIN_PASSWORD)
        db_key = key.upper()
        if isinstance(val, Path):
            defaults[db_key] = str(val)
        else:
            defaults[db_key] = val
    return {"defaults": defaults}


@router.delete("/api/v1/admin/config/{config_key}")
async def delete_config(config_key: str):
    """Delete a config from database."""
    from omni_gen import db
    from omni_gen.runtime_config import get_runtime_config

    db.delete_config(config_key)
    get_runtime_config().reload()

    return {"success": True}