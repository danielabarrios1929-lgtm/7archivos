"""
╔══════════════════════════════════════════════════════════════════════╗
║   AUTO-CARGADOR DE 7 ARCHIVOS → PTAFI-AI                           ║
║   Carga automáticamente todos los documentos de la carpeta          ║
║   "7 archivos" y los envía al motor de análisis IA                  ║
╚══════════════════════════════════════════════════════════════════════╝

USO:
  python auto_cargar_7archivos.py
  python auto_cargar_7archivos.py --institucion "Mi Colegio" --tutor "Juan"
  python auto_cargar_7archivos.py --carpeta "otra_carpeta"
"""

import os
import sys
import argparse
import requests
import json
import time
from pathlib import Path

# ── Colores para consola ──────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
VERDE  = "\033[92m"
ROJO   = "\033[91m"
AZUL   = "\033[94m"
AMARILLO = "\033[93m"
CYAN   = "\033[96m"

def color(texto, c): return f"{c}{texto}{RESET}"

# ── Extensiones soportadas ────────────────────────────────────────────
EXTENSIONES_SOPORTADAS = {
    # Documentos de texto
    '.pdf', '.docx', '.doc', '.txt', '.md',
    # Hojas de cálculo
    '.xlsx', '.xls', '.csv',
    # Imágenes (ahora con OCR/Visión IA)
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif',
    # Presentaciones
    '.pptx', '.ppt',
}

def banner():
    print(color("""
╔══════════════════════════════════════════════════════════════════════╗
║                    PTAFI-AI AUTO-CARGADOR v2.0                      ║
║         Carga inteligente de documentos para auditoría IA           ║
╚══════════════════════════════════════════════════════════════════════╝
""", CYAN + BOLD))

def encontrar_archivos(carpeta: Path) -> list:
    """Busca todos los archivos soportados en la carpeta."""
    archivos = []
    for archivo in sorted(carpeta.iterdir()):
        if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES_SOPORTADAS:
            archivos.append(archivo)
    return archivos

def mostrar_archivos(archivos: list):
    """Muestra la lista de archivos encontrados."""
    print(color(f"\n📁 Archivos encontrados ({len(archivos)}):", BOLD))
    print("─" * 60)
    for i, archivo in enumerate(archivos, 1):
        size_kb = archivo.stat().st_size / 1024
        ext = archivo.suffix.upper()
        # Icono según tipo
        iconos = {
            '.pdf': '📄', '.docx': '📝', '.doc': '📝', '.txt': '📋', '.md': '📋',
            '.xlsx': '📊', '.xls': '📊', '.csv': '📊',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.webp': '🖼️',
            '.bmp': '🖼️', '.tiff': '🖼️', '.gif': '🖼️',
            '.pptx': '📑', '.ppt': '📑',
        }
        icono = iconos.get(archivo.suffix.lower(), '📎')
        print(f"  {i}. {icono} {color(archivo.name, AZUL)} "
              f"{color(f'[{ext}]', AMARILLO)} "
              f"{color(f'({size_kb:.1f} KB)', CYAN)}")
    print("─" * 60)

def enviar_al_backend(
    archivos: list,
    institucion: str,
    tutor: str,
    url_backend: str
) -> dict:
    """Envía los archivos al backend PTAFI-AI para análisis."""
    
    print(color(f"\n🚀 Enviando {len(archivos)} archivos al motor de IA...", BOLD))
    print(color(f"   URL Backend: {url_backend}", CYAN))
    print(color(f"   Institución: {institucion}", CYAN))
    print(color(f"   Tutor: {tutor}", CYAN))
    print()
    
    # Preparar archivos para multipart/form-data
    files_payload = []
    for archivo in archivos:
        content = archivo.read_bytes()
        # Detectar MIME type
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': 'text/csv',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.gif': 'image/gif',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
        }
        mime = mime_types.get(archivo.suffix.lower(), 'application/octet-stream')
        files_payload.append(('files', (archivo.name, content, mime)))
        print(f"  ✅ Preparado: {color(archivo.name, AZUL)} ({len(content):,} bytes)")
    
    print(color("\n⏳ Procesando con IA... (puede tardar 30-120 segundos para documentos grandes)", AMARILLO))
    
    # Animación de espera
    inicio = time.time()
    
    try:
        response = requests.post(
            f"{url_backend}/api/v1/analysis/process",
            files=files_payload,
            data={
                'institution_name': institucion,
                'tutor_name': tutor
            },
            timeout=300  # 5 minutos máximo
        )
        
        duracion = time.time() - inicio
        print(color(f"\n✅ Respuesta recibida en {duracion:.1f}s", VERDE + BOLD))
        
        if response.status_code == 200:
            return response.json()
        else:
            print(color(f"\n❌ Error del servidor: {response.status_code}", ROJO))
            print(color(f"   {response.text[:500]}", ROJO))
            return None
            
    except requests.exceptions.ConnectionError:
        print(color(f"\n❌ No se pudo conectar al backend en {url_backend}", ROJO))
        print(color("   Asegúrate de que el servidor esté corriendo.", AMARILLO))
        print(color("   Ejecuta: cd backend && uvicorn app.main:app --reload", AMARILLO))
        return None
    except requests.exceptions.Timeout:
        print(color("\n⚠️  Timeout: El análisis tomó demasiado tiempo.", AMARILLO))
        print(color("   El servidor sigue procesando, pero la conexión se cerró.", AMARILLO))
        return None
    except Exception as e:
        print(color(f"\n❌ Error inesperado: {e}", ROJO))
        return None

def mostrar_resultados(resultado: dict):
    """Muestra los resultados del análisis de forma legible."""
    if not resultado:
        return
    
    print(color("\n" + "═" * 70, CYAN))
    print(color("  RESULTADOS DEL ANÁLISIS PEDAGÓGICO", CYAN + BOLD))
    print(color("═" * 70, CYAN))
    
    # Info institución
    inst = resultado.get('institution_info', {})
    print(f"\n  🏫 Institución: {color(inst.get('name', 'N/A'), BOLD)}")
    print(f"  👤 Tutor: {color(inst.get('tutor', 'N/A'), BOLD)}")
    
    # Motor IA usado
    engine = resultado.get('ai_engine', {})
    print(f"  🤖 Motor IA: {color(engine.get('used', 'N/A'), VERDE)}")
    if engine.get('warning'):
        print(color(f"  ⚠️  {engine['warning']}", AMARILLO))
    
    # Integridad
    integridad = resultado.get('integrity_check', {})
    missing = integridad.get('missing', [])
    if missing:
        print(color(f"\n  ⚠️  Documentos faltantes: {', '.join(missing)}", AMARILLO))
    else:
        print(color("\n  ✅ Todos los documentos presentes", VERDE))
    
    # Matriz de análisis
    matrix = resultado.get('matrix', [])
    if matrix:
        print(color(f"\n  📊 MATRIZ DE ANÁLISIS ({len(matrix)} categorías):", BOLD))
        print("  " + "─" * 65)
        for item in matrix:
            cat = item.get('category_name', 'N/A')
            hallazgo = item.get('hallazgo', 'N/A')
            print(f"\n  {color('▶ ' + cat, AZUL + BOLD)}")
            # Truncar hallazgo largo
            if len(hallazgo) > 200:
                hallazgo = hallazgo[:200] + "..."
            print(f"    {hallazgo}")
    
    # Reporte de calidad
    quality = resultado.get('quality_report', [])
    if quality:
        print(color(f"\n  🎯 REPORTE DE CALIDAD ({len(quality)} pilares):", BOLD))
        print("  " + "─" * 65)
        for pilar in quality:
            nombre = pilar.get('pillar_name', 'N/A')
            score = pilar.get('score', 0)
            # Barra de progreso
            barra = "█" * score + "░" * (10 - score)
            color_score = VERDE if score >= 7 else (AMARILLO if score >= 5 else ROJO)
            print(f"\n  {color('◆ ' + nombre, BOLD)}")
            print(f"    Score: {color(f'[{barra}] {score}/10', color_score)}")
            analisis = pilar.get('analysis', '')[:150]
            if analisis:
                print(f"    {analisis}...")
    
    # PDF generado
    pdf_b64 = resultado.get('pdf_base64')
    if pdf_b64:
        print(color("\n  📄 PDF generado correctamente (base64 disponible)", VERDE))
    
    print(color("\n" + "═" * 70 + "\n", CYAN))

def guardar_resultado(resultado: dict, output_path: Path):
    """Guarda el resultado JSON en un archivo."""
    try:
        # Guardar sin el PDF (muy grande)
        resultado_limpio = {k: v for k, v in resultado.items() if k != 'pdf_base64'}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resultado_limpio, f, ensure_ascii=False, indent=2)
        print(color(f"  💾 Resultado guardado en: {output_path}", VERDE))
    except Exception as e:
        print(color(f"  ⚠️  No se pudo guardar: {e}", AMARILLO))

def main():
    banner()
    
    # ── Argumentos de línea de comandos ─────────────────────────────
    parser = argparse.ArgumentParser(
        description="Auto-cargador de 7 archivos para PTAFI-AI"
    )
    parser.add_argument(
        '--carpeta',
        default='7 archivos',
        help='Carpeta con los documentos (default: "7 archivos")'
    )
    parser.add_argument(
        '--institucion',
        default='Institución Educativa Guaimaral',
        help='Nombre de la institución'
    )
    parser.add_argument(
        '--tutor',
        default='Tutor PTAFI',
        help='Nombre del tutor/auditor'
    )
    parser.add_argument(
        '--backend',
        default='http://localhost:8000',
        help='URL del backend (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--output',
        default='resultado_analisis.json',
        help='Archivo de salida JSON (default: resultado_analisis.json)'
    )
    parser.add_argument(
        '--solo-listar',
        action='store_true',
        help='Solo listar archivos sin enviar al backend'
    )
    
    args = parser.parse_args()
    
    # ── Encontrar carpeta ─────────────────────────────────────────────
    script_dir = Path(__file__).parent
    carpeta = script_dir / args.carpeta
    
    if not carpeta.exists():
        print(color(f"❌ Carpeta no encontrada: {carpeta}", ROJO))
        print(color(f"   Carpetas disponibles:", AMARILLO))
        for item in script_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                print(color(f"     - {item.name}", AMARILLO))
        sys.exit(1)
    
    # ── Buscar archivos ──────────────────────────────────────────────
    archivos = encontrar_archivos(carpeta)
    
    if not archivos:
        print(color(f"❌ No se encontraron archivos soportados en: {carpeta}", ROJO))
        print(color(f"   Extensiones soportadas: {', '.join(sorted(EXTENSIONES_SOPORTADAS))}", AMARILLO))
        sys.exit(1)
    
    mostrar_archivos(archivos)
    
    if args.solo_listar:
        print(color("\n✅ Fin (modo solo-listar). Para procesar, quita --solo-listar\n", VERDE))
        return
    
    # ── Confirmar envío ──────────────────────────────────────────────
    print(color(f"\n📡 Este script enviará los {len(archivos)} archivos a:", BOLD))
    print(color(f"   {args.backend}", AZUL))
    print(color(f"   Institución: {args.institucion}", AZUL))
    print(color(f"   Tutor:       {args.tutor}", AZUL))
    
    try:
        respuesta = input(color("\n¿Continuar? [S/n]: ", BOLD)).strip().lower()
        if respuesta in ['n', 'no']:
            print(color("\n❌ Cancelado por el usuario.\n", AMARILLO))
            return
    except KeyboardInterrupt:
        print(color("\n\n❌ Cancelado.\n", AMARILLO))
        return
    
    # ── Enviar al backend ────────────────────────────────────────────
    resultado = enviar_al_backend(
        archivos=archivos,
        institucion=args.institucion,
        tutor=args.tutor,
        url_backend=args.backend
    )
    
    if resultado:
        # Mostrar resumen
        mostrar_resultados(resultado)
        
        # Guardar JSON
        output_path = script_dir / args.output
        guardar_resultado(resultado, output_path)
        
        print(color("✅ ¡Análisis completado exitosamente!\n", VERDE + BOLD))
    else:
        print(color("\n❌ El análisis no se completó. Revisa que el backend esté corriendo.\n", ROJO))
        sys.exit(1)


if __name__ == "__main__":
    main()
