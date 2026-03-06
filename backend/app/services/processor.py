import fitz  # PyMuPDF
from docx import Document
import pandas as pd
import io
from PIL import Image
from typing import Dict, List
import re


class DocumentProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        """Limpieza premium de texto: elimina espacios excesivos y caracteres no deseados."""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_text_with_metadata(self, file_content: bytes, filename: str) -> str:
        """Extrae texto de múltiples formatos con marcadores para la IA."""
        structured_text = f"[[ DOCUMENTO: {filename} ]]\n"
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        try:
            if ext == 'pdf':
                with fitz.open(stream=file_content, filetype="pdf") as doc:
                    for i, page in enumerate(doc):
                        page_text = page.get_text()
                        structured_text += f"[PÁGINA {i+1}]\n{page_text}\n"
            
            elif ext in ['docx', 'doc']:
                doc = Document(io.BytesIO(file_content))
                for i, para in enumerate(doc.paragraphs):
                    structured_text += f"[PÁRR {i+1}]\n{para.text}\n"
            
            elif ext in ['xlsx', 'xls', 'csv']:
                if ext == 'csv':
                    df = pd.read_csv(io.BytesIO(file_content))
                else:
                    df = pd.read_excel(io.BytesIO(file_content))
                structured_text += f"[DATOS TABULARES]\n{df.to_string(index=False, max_rows=100)}\n"
            
            elif ext in ['txt', 'md']:
                text_content = file_content.decode('utf-8', errors='ignore')
                structured_text += text_content
            
            elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                # Sin OCR pesado, solo metadatos básicos
                img = Image.open(io.BytesIO(file_content))
                structured_text += f"[IMAGEN] Formato: {img.format}, Tamaño: {img.size}. (Contenido visual no extraído sin OCR).\n"
            
            else:
                structured_text += f"Formato no soportado directamente. Tamaño: {len(file_content)} bytes.\n"
                
            return structured_text
        except Exception as e:
            return f"Error extrayendo {filename}: {str(e)}"

    @staticmethod
    def validate_integrity(documents: Dict[str, bytes]) -> List[str]:
        """
        Checklist de integridad opcional (ahora más flexible).
        Retorna los que faltan pero no bloquearemos el proceso si el usuario quiere.
        """
        required = [
            "PEI", "MANUAL DE CONVIVENCIA", "PMI", "POA",
            "PFI", "SIEE", "LECTURA DE CONTEXTO"
        ]

        present_docs = [name.upper() for name in documents.keys()]
        missing = [doc for doc in required if doc not in present_docs]
        return missing

    def prepare_context_for_ai(self, documents: Dict[str, bytes]) -> str:
        """
        Prepara el 'Golden Context' para la IA.
        Concatena todos los documentos con delimitadores claros.
        """
        context_parts = []
        for doc_name, content in documents.items():
            text = self.extract_text_with_metadata(content, doc_name)
            context_parts.append(text)

        return "\n\n".join(context_parts)


processor = DocumentProcessor()
