"""
Test rápido: verifica que el procesador puede leer los 7 archivos
"""
import sys
import os

# Agregar la ruta del backend al path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, '.env'))

from app.services.processor import processor

carpeta = os.path.join(os.path.dirname(__file__), '7 archivos')
print(f"\n🔍 Leyendo archivos desde: {carpeta}\n")
print("=" * 60)

documentos = {}
for nombre in sorted(os.listdir(carpeta)):
    ruta = os.path.join(carpeta, nombre)
    if os.path.isfile(ruta):
        with open(ruta, 'rb') as f:
            documentos[nombre] = f.read()
        print(f"✅ Cargado: {nombre} ({len(documentos[nombre]):,} bytes)")

print(f"\n📊 Total: {len(documentos)} archivos\n")
print("=" * 60)
print("\n🤖 Extrayendo texto con el procesador...\n")

for nombre, contenido in documentos.items():
    texto = processor.extract_text_with_metadata(contenido, nombre)
    print(f"\n{'─'*55}")
    print(f"📄 {nombre}")
    print(f"   → {len(texto):,} chars extraídos")
    # Mostrar primeros 200 chars del contenido
    preview = texto.replace('\n', ' ')[:200]
    print(f"   Preview: {preview}...")

print(f"\n{'='*60}")
print("✅ ¡Procesador funcionando correctamente!")
print(f"   Todos los {len(documentos)} archivos fueron procesados.")
print()
