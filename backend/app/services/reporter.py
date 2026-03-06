from weasyprint import HTML
import jinja2
from datetime import datetime
import os

TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Helvetica', sans-serif; color: #333; line-height: 1.6; }
        .header { text-align: center; border-bottom: 4px solid #1a365d; padding-bottom: 20px; }
        .title { font-size: 28px; color: #1a365d; margin-bottom: 5px; }
        .subtitle { font-size: 14px; color: #666; }
        .pillar-card { margin-top: 30px; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; }
        .pillar-name { font-size: 20px; color: #2b6cb0; font-weight: bold; }
        .score { float: right; font-size: 24px; color: #2f855a; font-weight: bold; }
        .recommendation-list { background: #f7fafc; padding: 15px; border-left: 4px solid #2b6cb0; }
        .matrix-table { width: 100%; border-collapse: collapse; margin-top: 40px; }
        .matrix-table th { background: #1a365d; color: white; padding: 10px; text-align: left; }
        .matrix-table td { border: 1px solid #cbd5e0; padding: 10px; font-size: 12px; }
        .footer { position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 10px; color: #aaa; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">INFORME DE CALIDAD PTAFI-AI</div>
        <div class="subtitle">AuditorÃ­a Multidocumental Concurrente - {{ institution_name }}</div>
        <div class="subtitle">Tutor: {{ tutor_name }} | Fecha: {{ date }}</div>
    </div>

    <h2>1. Los 5 Pilares de Excelencia</h2>
    {% for pillar in quality_report %}
    <div class="pillar-card">
        <span class="score">{{ pillar.score }}/10</span>
        <div class="pillar-name">{{ pillar.pillar_name }}</div>
        <p>{{ pillar.analysis }}</p>
        <div class="recommendation-list">
            <strong>Recomendaciones EstratÃ©gicas:</strong>
            <ul>
                {% for rec in pillar.recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
        </div>
    </div>
    {% endfor %}

    <div style="page-break-before: always;"></div>

    <h2>2. Matriz Suprema de SistematizaciÃ³n</h2>
    <table class="matrix-table">
        <thead>
            <tr>
                <th>CategorÃ­a</th>
                <th>Hallazgo Principal</th>
                <th>InterpretaciÃ³n PedagÃ³gica</th>
                <th>ImplicaciÃ³n PFI</th>
            </tr>
        </thead>
        <tbody>
            {% for item in matrix %}
            <tr>
                <td><strong>{{ item.category_name }}</strong></td>
                <td>{{ item.hallazgo }}</td>
                <td>{{ item.interpretacion }}</td>
                <td>{{ item.implicacion_pfi }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="footer">
        Generado automÃ¡ticamente por el Motor de Inferencia PTAFI-AI v1.5 - Sistema de Inteligencia Artificial para la Excelencia Educativa.
    </div>
</body>
</html>
"""

class ReporterService:
    @staticmethod
    def generate_pdf(analysis_data: dict) -> bytes:
        """Genera un reporte PDF con diseÃ±o editorial premium."""
        template = jinja2.Template(TEMPLATE_HTML)
        html_content = template.render(
            institution_name=analysis_data['institution_info']['name'],
            tutor_name=analysis_data['institution_info']['tutor'],
            date=datetime.now().strftime("%d/%m/%Y"),
            quality_report=analysis_data['quality_report'],
            matrix=analysis_data['matrix']
        )
        
        # Generar PDF usando WeasyPrint
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

reporter = ReporterService()
