"""
DocumentProcessor — Extractor Premium de Texto Multi-Formato
=============================================================
Mejoras v2:
  - Compresion agresiva de texto: elimina redundancias, paginas vacias, headers repetidos
  - Extraccion por paginas con filtro de calidad (skip paginas vacias/basura)
  - Estadisticas de extraccion por documento
  - Devuelve lista de documentos individuales (para chunking inteligente por doc)
"""

import fitz  # PyMuPDF
from docx import Document
import pandas as pd
import io
from PIL import Image
from typing import Dict, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:

    # ── Limpieza de Texto ───────────────────────────────────────────────────────

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpieza premium: elimina espacios excesivos y caracteres basura."""
        # Normalizar saltos de linea multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Eliminar lineas que son puro ruido (solo simbolos/numeros de pagina)
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Saltar lineas que son solo numeros (numeros de pagina)
            if re.match(r'^\d{1,4}$', stripped):
                continue
            # Saltar lineas muy cortas que son probablemente cabeceras repetidas
            if len(stripped) < 3 and stripped not in ['', '\n']:
                continue
            clean_lines.append(line)
        text = '\n'.join(clean_lines)
        # Eliminar espacios multiples en la misma linea
        text = re.sub(r'[ \t]{2,}', ' ', text)
        return text.strip()

    @staticmethod
    def compress_text(text: str) -> str:
        """
        Compresion inteligente: elimina contenido redundante para maximizar
        la cantidad de informacion util por token enviado a la IA.
        """
        # Eliminar lineas repetidas consecutivas (headers/footers de pagina)
        lines = text.split('\n')
        seen_lines = {}
        compressed = []
        for line in lines:
            key = line.strip().lower()
            if not key:  # Lineas vacias siempre las pasamos (saltos de parrafo)
                compressed.append(line)
                continue
            count = seen_lines.get(key, 0)
            if count < 2:  # Permitir maximo 2 ocurrencias de la misma linea
                compressed.append(line)
                seen_lines[key] = count + 1
        return '\n'.join(compressed)

    # ── Extraccion por Formato ──────────────────────────────────────────────────

    def _extract_pdf(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """Extrae texto de PDF con filtro de calidad por pagina."""
        parts = []
        stats = {"pages_total": 0, "pages_extracted": 0, "pages_skipped": 0}

        with fitz.open(stream=file_content, filetype="pdf") as doc:
            stats["pages_total"] = len(doc)
            for i, page in enumerate(doc):
                page_text = page.get_text("text")  # Modo texto simple (mas limpio)
                cleaned = self.clean_text(page_text)

                # Filtrar paginas con muy poco contenido util (portadas, paginas en blanco)
                words = len(cleaned.split())
                if words < 10:
                    stats["pages_skipped"] += 1
                    continue

                parts.append(f"[PAG.{i+1}] {cleaned}")
                stats["pages_extracted"] += 1

        return '\n'.join(parts), stats

    def _extract_docx(self, file_content: bytes) -> str:
        """Extrae texto de Word con estructura de parrafos."""
        doc = Document(io.BytesIO(file_content))
        parts = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:  # Solo parrafos con contenido real
                # Detectar si es un titulo (estilo Heading)
                if para.style.name.startswith('Heading'):
                    parts.append(f"\n## {text}")
                else:
                    parts.append(text)
        # Tambien extraer tablas de Word
        for table in doc.tables:
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    rows.append(' | '.join(cells))
            if rows:
                parts.append('[TABLA]\n' + '\n'.join(rows))
        return '\n'.join(parts)

    def _extract_excel(self, file_content: bytes, ext: str) -> str:
        """Extrae datos tabulares de Excel/CSV de forma eficiente."""
        try:
            if ext == 'csv':
                df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8', errors='ignore')
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            # Eliminar columnas completamente vacias
            df = df.dropna(axis=1, how='all')
            df = df.fillna('')
            # Limitar filas para no saturar contexto (max 200 filas)
            if len(df) > 200:
                resultado = df.head(200).to_string(index=False)
                return f"[TABLA — mostrando 200 de {len(df)} filas]\n{resultado}"
            return f"[TABLA — {len(df)} filas x {len(df.columns)} cols]\n{df.to_string(index=False)}"
        except Exception as e:
            return f"[Error leyendo tabla: {e}]"

    # ── Metodo Principal ────────────────────────────────────────────────────────

    def extract_text_with_metadata(self, file_content: bytes, filename: str) -> str:
        """
        Extrae texto de mltiples formatos con limpieza y compresion premium.
        Incluye estadisticas de extraccion en el encabezado del documento.
        """
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        header = f"\n{'='*60}\n[[ DOCUMENTO: {filename.upper()} ]]\n{'='*60}\n"

        try:
            if ext == 'pdf':
                raw_text, stats = self._extract_pdf(file_content, filename)
                compressed = self.compress_text(raw_text)
                info = (
                    f"[INFO: {stats['pages_extracted']}/{stats['pages_total']} pags. extraidas"
                    f" | {stats['pages_skipped']} pags. vacias omitidas"
                    f" | {len(compressed):,} chars]\n"
                )
                return header + info + compressed

            elif ext in ['docx', 'doc']:
                raw_text = self._extract_docx(file_content)
                compressed = self.compress_text(self.clean_text(raw_text))
                return header + f"[INFO: {len(compressed):,} chars extraidos de Word]\n" + compressed

            elif ext in ['xlsx', 'xls', 'csv']:
                table_text = self._extract_excel(file_content, ext)
                return header + table_text

            elif ext in ['txt', 'md']:
                raw = file_content.decode('utf-8', errors='ignore')
                compressed = self.compress_text(self.clean_text(raw))
                return header + f"[INFO: {len(compressed):,} chars]\n" + compressed

            elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                img = Image.open(io.BytesIO(file_content))
                return header + f"[IMAGEN] Formato: {img.format}, Tamano: {img.size[0]}x{img.size[1]}px\n"

            else:
                return header + f"[Formato '{ext}' no soportado. Tamano: {len(file_content):,} bytes]\n"

        except Exception as e:
            logger.error(f"[PROCESSOR] Error extrayendo {filename}: {e}")
            return header + f"[ERROR DE EXTRACCION: {str(e)}]\n"

    def extract_documents_individually(self, documents: Dict[str, bytes]) -> List[Dict]:
        """
        Extrae texto de cada documento por separado.
        Retorna una lista de dicts con metadata por documento:
          { name, text, char_count, token_estimate }
        Esto permite al orquestador hacer chunking INTELIGENTE por documento.
        """
        result = []
        for doc_name, content in documents.items():
            text = self.extract_text_with_metadata(content, doc_name)
            char_count = len(text)
            result.append({
                "name": doc_name,
                "text": text,
                "char_count": char_count,
                "token_estimate": char_count // 4,
            })
            logger.info(
                f"[PROCESSOR] '{doc_name}': {char_count:,} chars "
                f"(~{char_count // 4:,} tokens)"
            )
        return result

    @staticmethod
    def validate_integrity(documents: Dict[str, bytes]) -> List[str]:
        """
        Checklist de integridad opcional (no bloqueante).
        """
        required = [
            "PEI", "MANUAL DE CONVIVENCIA", "PMI", "POA",
            "PFI", "SIEE", "LECTURA DE CONTEXTO"
        ]
        present_docs = [name.upper() for name in documents.keys()]
        return [doc for doc in required if doc not in present_docs]

    def prepare_context_for_ai(self, documents: Dict[str, bytes]) -> str:
        """
        Prepara el contexto completo concatenado para la IA.
        Mantiene compatibilidad con el orquestador actual.
        """
        parts = self.extract_documents_individually(documents)
        total_chars = sum(p["char_count"] for p in parts)
        logger.info(
            f"[PROCESSOR] Total contexto: {total_chars:,} chars "
            f"({len(parts)} docs)"
        )
        return "\n\n".join(p["text"] for p in parts)


processor = DocumentProcessor()
