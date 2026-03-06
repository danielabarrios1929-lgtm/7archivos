import sys
import os

# ── Esto es CRÍTICO para Vercel ──
# Agrega 'backend/' al path de Python para que los imports funcionen
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_path)

# Ahora importamos la app FastAPI
from app.main import app  # noqa: E402 F401
