"""
AIOrchestrator — Orquestador Híbrido Gemini + Groq
====================================================
Lógica de decisión inteligente:

  ┌─────────────────────────────────────────────────────────────────┐
  │  Texto > 40.000 chars?                                          │
  │    SÍ → Gemini 1.5 Pro (1M tokens, análisis completo)          │
  │          Si Gemini falla → Groq como fallback automático        │
  │    NO → Groq directo (llama-3.3-70b, ultra-rápido)             │
  └─────────────────────────────────────────────────────────────────┘

Beneficios:
  • Documentos grandes → Gemini los lee COMPLETOS (sin truncar)
  • Documentos pequeños → Groq responde en ~3 segundos
  • Si falla el motor principal → cambio automático al de apoyo
"""

import logging
from app.services.gemini_service import gemini_service, GROQ_THRESHOLD_CHARS
from app.services.groq_service import groq_service

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Orquestador que selecciona el motor de IA más adecuado
    según el tamaño del contexto y disponibilidad del servicio.
    """

    async def analyze(self, documents_text: str, force_groq: bool = False) -> dict:
        """
        Punto de entrada único para análisis de documentos.
        Selecciona Gemini o Groq automáticamente.
        """
        text_size = len(documents_text)
        logger.info(f"[ORCHESTRATOR] Contexto: {text_size:,} chars")

        # Si estamos en modo DEMO, forzamos Groq
        if force_groq:
            logger.info("[ORCHESTRATOR] 🟧 MODO DEMO DETECTADO: Forzando motor GROQ")
            return await self._run_groq_with_fallback(documents_text, text_size)

        # ── Decisión de motor normal ──────────────────────────────────────────────────
        if text_size > GROQ_THRESHOLD_CHARS:
            return await self._run_gemini_with_fallback(documents_text, text_size)
        else:
            return await self._run_groq_with_fallback(documents_text, text_size)

    # ── Estrategias ────────────────────────────────────────────────────────────

    async def _run_gemini_with_fallback(self, text: str, size: int) -> dict:
        """Gemini como principal, Groq como fallback."""
        logger.info(
            f"[ORCHESTRATOR] 🟦 Usando GEMINI (contexto grande: {size:,} chars). "
            f"Groq en standby como apoyo."
        )
        try:
            result = await gemini_service.analyze_documents(text)
            result["_engine_used"] = "gemini-2.5-flash"
            result["_engine_reason"] = f"Contexto grande ({size:,} chars > {GROQ_THRESHOLD_CHARS:,} umbral)"
            return result

        except Exception as gemini_error:
            logger.warning(
                f"[ORCHESTRATOR] ⚠️ Gemini falló: {gemini_error}. "
                f"Activando GROQ como apoyo..."
            )
            try:
                # Groq trunca a 80k chars para no exceder su límite
                result = await groq_service.analyze_documents(text)
                result["_engine_used"] = "groq-llama-3.3-70b (fallback)"
                result["_engine_reason"] = f"Gemini falló: {str(gemini_error)[:100]}"
                result["_warning"] = (
                    "Gemini no disponible. Groq procesó con texto truncado a 80k chars. "
                    "Es posible que algunos documentos no hayan sido analizados completamente."
                )
                return result
            except Exception as groq_error:
                logger.error(f"[ORCHESTRATOR] ❌ Ambos motores fallaron.")
                raise Exception(
                    f"Ambos motores de IA fallaron.\n"
                    f"• Gemini: {gemini_error}\n"
                    f"• Groq (fallback): {groq_error}"
                )

    async def _run_groq_with_fallback(self, text: str, size: int) -> dict:
        """Groq como principal (contexto pequeño), Gemini como fallback."""
        logger.info(
            f"[ORCHESTRATOR] 🟧 Usando GROQ directo (contexto pequeño: {size:,} chars). "
            f"Ultra-rápido."
        )
        try:
            result = await groq_service.analyze_documents(text)
            result["_engine_used"] = "groq-llama-3.3-70b"
            result["_engine_reason"] = f"Contexto pequeño ({size:,} chars ≤ {GROQ_THRESHOLD_CHARS:,} umbral)"
            return result

        except Exception as groq_error:
            logger.warning(
                f"[ORCHESTRATOR] ⚠️ Groq falló: {groq_error}. "
                f"Activando GEMINI como apoyo..."
            )
            try:
                result = await gemini_service.analyze_documents(text)
                result["_engine_used"] = "gemini-2.5-flash (fallback)"
                result["_engine_reason"] = f"Groq falló: {str(groq_error)[:100]}"
                return result
            except Exception as gemini_error:
                logger.error(f"[ORCHESTRATOR] ❌ Ambos motores fallaron.")
                raise Exception(
                    f"Ambos motores de IA fallaron.\n"
                    f"• Groq: {groq_error}\n"
                    f"• Gemini (fallback): {gemini_error}"
                )


# Instancia global del orquestador
ai_orchestrator = AIOrchestrator()
