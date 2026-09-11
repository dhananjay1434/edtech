from __future__ import annotations
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether,
)


def safe(value) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def build_report(data: dict, regular_font: Path, bold_font: Path) -> bytes:
    if not regular_font.is_file() or not bold_font.is_file():
        raise ValueError("Approved report fonts are missing")
    pdfmetrics.registerFont(TTFont("CDEBody", str(regular_font)))
    pdfmetrics.registerFont(TTFont("CDEBold", str(bold_font)))
    pdfmetrics.registerFontFamily("CDEBody", normal="CDEBody", bold="CDEBold",
                                  italic="CDEBody", boldItalic="CDEBold")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("CDEText", fontName="CDEBody", fontSize=10,
                              leading=15, spaceAfter=7, splitLongWords=True))
    styles.add(ParagraphStyle("CDETitle", fontName="CDEBold", fontSize=23,
                              leading=28, spaceAfter=14))
    styles.add(ParagraphStyle("CDEHeading", fontName="CDEBold", fontSize=13,
                              leading=18, spaceBefore=12, spaceAfter=7,
                              keepWithNext=True, alignment=TA_LEFT))
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
        topMargin=18*mm, bottomMargin=20*mm, title="Personalized practice",
        author="Cognitive Diagnostic Engine", pageCompression=1,
    )
    story = []
    def paragraph(text, style="CDEText"):
        return Paragraph(safe(text), styles[style])
    story.append(paragraph("Your next steps", "CDETitle"))
    story.append(paragraph(data["student_display_name"]))
    story.append(paragraph(data["exam_title"]))
    story.append(paragraph(f"Score: {data['score']} / {data['maximum_score']}  ·  {data['percentage']}%"))
    story.append(paragraph(f"Report revision: {data['report_revision']}"))
    story.append(paragraph("Focused practice based on the answers and working available for review."))
    for gap in data["gaps"]:
        story.append(paragraph(gap["heading"], "CDEHeading"))
        story.append(paragraph(gap["summary"]))
        story.append(paragraph(gap["next_step"]))
    if data.get("unfilled_gaps"):
        story.append(paragraph("Practice awaiting educator selection", "CDEHeading"))
        for gap in data["unfilled_gaps"]:
            story.append(paragraph(gap))
    if data["questions"]:
        story.append(PageBreak())
        story.append(paragraph("Targeted practice", "CDETitle"))
        for number, question in enumerate(data["questions"], 1):
            # Do not wrap long questions in KeepTogether: allow safe page splitting.
            story.append(paragraph(f"Practice {number} · {question['topic_label']}", "CDEHeading"))
            story.append(paragraph(question["stem"]))
            for option, text in sorted(question["options"].items()):
                story.append(paragraph(f"{option}. {text}"))
            story.append(Spacer(1, 16*mm))
        story.append(PageBreak())
        story.append(paragraph("Check your reasoning", "CDETitle"))
        for number, question in enumerate(data["questions"], 1):
            story.append(paragraph(f"Practice {number} · Answer {question['correct_option']}", "CDEHeading"))
            story.append(paragraph(question["explanation"]))
    else:
        story.append(paragraph("No practice questions were assigned in this report."))
    report_id = str(data["report_id"])
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("CDEBody", 8)
        canvas.setFillColor(colors.HexColor("#52616B"))
        canvas.drawString(18*mm, 11*mm, f"Private student report · {report_id[:12]}")
        canvas.drawRightString(A4[0]-18*mm, 11*mm, f"Page {doc.page}")
        canvas.restoreState()
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
