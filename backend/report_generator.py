# backend/report_generator.py
"""
Generates:
- Technical report (PDF) summarizing layout, counts, basic notes
- Financial report (PDF) with a simple cost estimate
Uses reportlab.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
import uuid

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../backend_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def estimate_cost(layout: dict) -> dict:
    # Basic cost formula — adjust to your price list
    sprinkler_unit_cost = 120.0  # currency unit per sprinkler
    area_unit_cost = 10.0       # per m2
    total_area_mm2 = 0
    for r in layout.get("rooms", []):
        w = float(r.get("width", 0))
        h = float(r.get("height", 0))
        area_m2 = (w * h) / 1_000_000.0
        total_area_mm2 += area_m2

    total_sprinklers = len(layout.get("sprinklers", []))
    cost = total_sprinklers * sprinkler_unit_cost + total_area_mm2 * area_unit_cost
    return {"total_area_m2": round(total_area_mm2,2), "total_sprinklers": total_sprinklers, "estimated_cost": round(cost,2)}

def generate_technical_report(layout: dict, filename: str = None) -> str:
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    fname = filename or f"technical_report_{now}_{uid}.pdf"
    path = os.path.join(OUTPUT_DIR, fname)

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("FireAI — Technical Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1,12))

    # Summary table
    data = [["Room", "Width (mm)", "Height (mm)", "Area (m²)"]]
    for r in layout.get("rooms", []):
        w = float(r.get("width",0)); h = float(r.get("height",0))
        area = (w * h) / 1_000_000.0
        data.append([r.get("name",""), str(w), str(h), f"{area:.2f}"])

    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(Paragraph("Layout Summary", styles["Heading2"]))
    story.append(t)
    story.append(Spacer(1,12))

    story.append(Paragraph("Sprinkler Positions", styles["Heading2"]))
    for idx, s in enumerate(layout.get("sprinklers", []), start=1):
        story.append(Paragraph(f"{idx}. x: {s.get('x')} mm, y: {s.get('y')} mm", styles["Normal"]))

    doc.build(story)
    return path

def generate_financial_report(layout: dict, filename: str = None) -> str:
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    fname = filename or f"financial_report_{now}_{uid}.pdf"
    path = os.path.join(OUTPUT_DIR, fname)

    cost = estimate_cost(layout)
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FireAI — Financial Estimate", styles["Title"]))
    story.append(Spacer(1,12))
    story.append(Paragraph(f"Total area (m²): {cost['total_area_m2']}", styles["Normal"]))
    story.append(Paragraph(f"Total sprinklers: {cost['total_sprinklers']}", styles["Normal"]))
    story.append(Spacer(1,12))
    story.append(Paragraph(f"Estimated cost: {cost['estimated_cost']} (currency)", styles["Heading2"]))

    doc.build(story)
    return path
