from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import io

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TitlePrimary',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor("#1e3a8a"),  # Blue 900
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=16,
            spaceBefore=20,
            spaceAfter=15,
            textColor=colors.HexColor("#2563eb"),  # Blue 600
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='HallazgoTitle',
            fontSize=12,
            spaceBefore=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#4b5563")  # Gray 600
        ))
        self.styles.add(ParagraphStyle(
            name='EvidenceStyle',
            fontSize=10,
            leftIndent=20,
            firstLineIndent=0,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor("#6b7280")  # Gray 500
        ))

    def generate_pdf(self, data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []

        # --- Portada ---
        elements.append(Paragraph("INFORME DE AUDITORÍA PEDAGÓGICA", self.styles['TitlePrimary']))
        elements.append(Paragraph(f"Institución: {data['institution_info']['name']}", self.styles['Heading2']))
        elements.append(Paragraph(f"Tutor Responsable: {data['institution_info']['tutor']}", self.styles['Normal']))
        elements.append(Spacer(1, 40))

        # --- 1. Matriz de Hallazgos ---
        elements.append(Paragraph("1. MATRIZ DE SISTEMATIZACIÓN DE HALLAZGOS", self.styles['SectionHeader']))
        
        for item in data.get('matrix', []):
            elements.append(Paragraph(f"Categoría: {item['category_name']}", self.styles['HallazgoTitle']))
            elements.append(Paragraph(f"<b>Hallazgo:</b> {item['hallazgo']}", self.styles['Normal']))
            
            evid = item.get('evidencia', {})
            elements.append(Paragraph(f"<b>Evidencia:</b> \"{evid.get('text', 'N/A')}\" (Doc: {evid.get('document_name', 'N/A')})", self.styles['EvidenceStyle']))
            
            elements.append(Paragraph(f"<b>Interpretación Pedagógica:</b> {item['interpretacion']}", self.styles['Normal']))
            elements.append(Paragraph(f"<b>Implicación para el PFI:</b> {item['implicacion_pfi']}", self.styles['Normal']))
            elements.append(Spacer(1, 15))

        elements.append(PageBreak())

        # --- 2. Reporte de Calidad (Pilares) ---
        elements.append(Paragraph("2. REPORTE DE CALIDAD (PILARES ESTRATÉGICOS)", self.styles['SectionHeader']))
        
        for p in data.get('quality_report', []):
            elements.append(Paragraph(f"{p['pillar_name']} - Puntaje: {p['score']}/10", self.styles['HallazgoTitle']))
            elements.append(Paragraph(f"<b>Análisis:</b> {p['analysis']}", self.styles['Normal']))
            
            recs = p.get('recommendations', [])
            if recs:
                elements.append(Paragraph("<b>Recomendaciones:</b>", self.styles['Normal']))
                for r in recs:
                    elements.append(Paragraph(f"• {r}", self.styles['Normal']))
            elements.append(Spacer(1, 15))

        doc.build(elements)
        pdf_value = buffer.getvalue()
        buffer.close()
        return pdf_value

pdf_reporter = ReportGenerator()
