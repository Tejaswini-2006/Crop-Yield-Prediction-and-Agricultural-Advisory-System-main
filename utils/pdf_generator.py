import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    """
    Generates official, beautifully styled PDF reports for agricultural predictions and advisories.
    """
    @staticmethod
    def generate_report(report_type, title, input_data, result_data, farmer_name="Valued Farmer"):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.HexColor('#2d5016'),
            spaceAfter=4
        )
        
        subheader_style = ParagraphStyle(
            'SubHeaderStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=11,
            textColor=colors.HexColor('#4a7c59'),
            spaceAfter=15
        )

        section_title = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=colors.HexColor('#1b4332'),
            spaceBefore=12,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2b2b2b')
        )

        story = []

        # Document Header
        story.append(Paragraph("🌾 AgriPredict Smart Farming Advisory", header_style))
        story.append(Paragraph(f"Official Analytical Report | Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", subheader_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2d5016'), spaceAfter=15))

        # Metadata Table
        meta_data = [
            [Paragraph("<b>Farmer Name:</b>", body_style), Paragraph(str(farmer_name), body_style)],
            [Paragraph("<b>Report Type:</b>", body_style), Paragraph(str(title), body_style)],
            [Paragraph("<b>Status:</b>", body_style), Paragraph("<font color='#2d5016'><b>Verified AI Analysis</b></font>", body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[130, 400])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f9f4')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0e1d4'))
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # Input Parameters Section
        story.append(Paragraph("Input Environmental & Farm Parameters", section_title))
        input_rows = [[Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Input Value</b>", body_style)]]
        
        for k, v in input_data.items():
            param_name = str(k).replace('_', ' ').title()
            input_rows.append([Paragraph(param_name, body_style), Paragraph(str(v), body_style)])
            
        input_table = Table(input_rows, colWidths=[230, 300])
        input_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#2d5016')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc'))
        ]))
        story.append(input_table)
        story.append(Spacer(1, 15))

        # Results & Recommendation Section
        story.append(Paragraph("Analytical Findings & Recommendations", section_title))
        
        result_rows = [[Paragraph("<b>Metric / Indicator</b>", body_style), Paragraph("<b>Details & Recommendations</b>", body_style)]]
        
        if isinstance(result_data, dict):
            for k, v in result_data.items():
                metric_name = str(k).replace('_', ' ').title()
                val_str = str(v)
                if isinstance(v, dict) or isinstance(v, list):
                    val_str = str(v)
                result_rows.append([Paragraph(metric_name, body_style), Paragraph(val_str, body_style)])
        else:
            result_rows.append([Paragraph("Prediction Output", body_style), Paragraph(str(result_data), body_style)])

        result_table = Table(result_rows, colWidths=[180, 350])
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#40916c')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b7e4c7'))
        ]))
        story.append(result_table)
        story.append(Spacer(1, 20))

        # Footer Notice
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=10))
        story.append(Paragraph("<i>Disclaimer: This report is generated using AI/ML algorithms and agricultural rule frameworks. Results should be combined with local agronomic practices.</i>", ParagraphStyle('Disclaimer', parent=styles['Italic'], fontSize=8, textColor=colors.gray)))

        doc.build(story)
        buffer.seek(0)
        return buffer
