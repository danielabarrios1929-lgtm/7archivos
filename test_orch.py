import asyncio
import os
import sys

# Agrega backend al sys paths para poder importar
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.services.ai_orchestrator import ai_orchestrator
from app.services.gemini_service import GROQ_THRESHOLD_CHARS

async def run_tests():
    print("Testing Orchestrator...")
    
    # Text large enough to trigger Gemini
    large_text = "Esto es un documento de prueba. " * (GROQ_THRESHOLD_CHARS // 30 + 1)
    print(f"Text size: {len(large_text)} chars")
    
    # 1. Test NORMAL (Debería usar Gemini)
    print("\n--- TEST 1: Análisis Normal (Gemini) ---")
    try:
        res1 = await ai_orchestrator.analyze(large_text, force_groq=False)
        print(f"Motor usado: {res1.get('_engine_used')}")
        print(f"Razón: {res1.get('_engine_reason')}")
    except Exception as e:
        print(f"Error test 1: {e}")

    # 2. Test DEMO (Debería usar Groq)
    print("\n--- TEST 2: Análisis Demo (Forzar Groq) ---")
    try:
        res2 = await ai_orchestrator.analyze(large_text, force_groq=True)
        print(f"Motor usado: {res2.get('_engine_used')}")
        print(f"Razón: {res2.get('_engine_reason')}")
    except Exception as e:
        print(f"Error test 2: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join("backend", ".env"))
    asyncio.run(run_tests())
