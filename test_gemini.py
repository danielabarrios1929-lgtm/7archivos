"""
Test rapido de la API de Gemini
Verifica: conexion, autenticacion, y que responde JSON correctamente.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join("backend", ".env"))

import google.generativeai as genai
import json

API_KEY = os.environ.get("GOOGLE_API_KEY", "")
TEST_MODEL = "gemini-2.5-flash"

print("\n" + "="*55)
print("  TEST DE CONEXION — GEMINI API")
print("="*55)

# ── 1. Verificar que la key existe ─────────────────────────
if not API_KEY or API_KEY == "your_google_key_here":
    print("❌ GOOGLE_API_KEY no configurada en .env")
    sys.exit(1)
print(f"✅ API Key encontrada: {API_KEY[:10]}...{API_KEY[-4:]}")

# ── 2. Configurar Gemini ────────────────────────────────────
genai.configure(api_key=API_KEY)
print(f"✅ Cliente Gemini configurado")

# ── 3. Listar modelos disponibles ───────────────────────────
print(f"\n📋 Modelos disponibles (con generateContent):")
try:
    available = [
        m.name for m in genai.list_models()
        if 'generateContent' in m.supported_generation_methods
    ]
    for m in available:
        marker = " ◄ MODELO ACTIVO" if TEST_MODEL in m else ""
        print(f"   • {m}{marker}")

    if not any(TEST_MODEL in m for m in available):
        print(f"\n⚠️  '{TEST_MODEL}' NO esta en la lista. Modelos compatibles:")
        # Intentar con gemini-2.0-flash como alternativa
        fallback = next((m for m in available if 'flash' in m), None)
        if fallback:
            TEST_MODEL = fallback.replace("models/", "")
            print(f"   → Usando alternativa: {TEST_MODEL}")
        else:
            print("❌ No se encontro modelo compatible.")
            sys.exit(1)
except Exception as e:
    print(f"⚠️  No se pudo listar modelos: {e}")

# ── 4. Test de llamada simple ───────────────────────────────
print(f"\n🔥 Enviando llamada de prueba a '{TEST_MODEL}'...")

SIMPLE_PROMPT = """Responde SOLO con este JSON exacto (sin cambios, sin markdown):
{"status": "ok", "message": "Gemini respondio correctamente", "model": "gemini"}"""

try:
    model = genai.GenerativeModel(
        model_name=TEST_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=0.0,
            max_output_tokens=100,
        ),
    )
    response = model.generate_content(SIMPLE_PROMPT)
    raw = response.text.strip()
    print(f"   Respuesta raw: {raw[:200]}")

    # Intentar parsear JSON
    if raw.startswith("```"):
        import re
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        if m:
            raw = m.group(1).strip()

    parsed = json.loads(raw)
    print(f"\n✅ JSON parseado correctamente:")
    print(f"   status  : {parsed.get('status')}")
    print(f"   message : {parsed.get('message')}")
    print(f"\n{'='*55}")
    print(f"  ✅ GEMINI FUNCIONA CORRECTAMENTE")
    print(f"  Modelo : {TEST_MODEL}")
    print(f"  La API responde y parsea JSON sin errores.")
    print(f"{'='*55}\n")

except json.JSONDecodeError as e:
    print(f"\n⚠️  Gemini respondio pero el JSON tiene formato invalido: {e}")
    print(f"   Texto recibido: {raw[:300]}")
    print(f"\n   CONCLUSION: La API FUNCIONA pero hay que ajustar el parseo.")

except Exception as e:
    err = str(e)
    print(f"\n❌ Error en la llamada a Gemini: {err}")

    if "429" in err or "quota" in err.lower():
        print("   CAUSA: Rate limit / Cuota excedida.")
        print("   SOLUCION: Espera unos minutos o usa otra API key.")
    elif "403" in err or "permission" in err.lower():
        print("   CAUSA: API key no autorizada para este modelo.")
        print("   SOLUCION: Ve a https://aistudio.google.com y verifica que tu key tiene acceso.")
    elif "404" in err:
        print("   CAUSA: Modelo no encontrado.")
        print("   SOLUCION: Revisa los modelos disponibles en la lista de arriba.")
    else:
        print("   Revisa tu conexion a internet y el estado de la API en https://status.cloud.google.com")
