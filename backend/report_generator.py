# backend/report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def estimate_cost(layout_data):
    """Simple mock cost estimation (you can improve formulas)."""
    room_cost = 50  # per m²
    sprinkler_cost = 120  # per unit

    total_room_area = 0
    for room in layout_data.get("rooms", []):
        area = (room["width"] * room["height"]) / 1_000_000  # mm² → m²
        total_room_area += area

    total_sprinklers = len(layout_data.get("sprinklers", []))
    total_cost = (total_room_area * room_cost) + (total_sprinklers * sprinkler_cost)

    return {
        "total_room_area": round(total_room_area, 2),
        "total_sprinklers": total_sprinklers,
        "estimated_cost": round(total_cost, 2),
    }

def generate_report(layout_data, cost_data, output_path="design_report.pdf"):
    """Creates a professional report summarizing design and cost."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("🏗️ Project Design Report", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    # Summary
    story.append(Paragraph("📋 Layout Summary", styles["Heading2"]))
    data = [["Room", "Width (mm)", "Height (mm)", "Area (m²)"]]
    for room in layout_data.get("rooms", []):
        area = (room["width"] * room["height"]) / 1_000_000
        data.append([room["name"], room["width"], room["height"], round(area, 2)])

    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # Sprinkler summary
    story.append(Paragraph("💧 Sprinklers", styles["Heading2"]))
    story.append(Paragraph(f"Total sprinklers: {cost_data['total_sprinklers']}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Cost summary
    story.append(Paragraph("💰 Cost Summary", styles["Heading2"]))
    cost_table = Table([
        ["Total Area (m²)", cost_data["total_room_area"]],
        ["Sprinkler Count", cost_data["total_sprinklers"]],
        ["Estimated Cost (TND)", cost_data["estimated_cost"]],
    ], hAlign="LEFT")
    cost_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story.append(cost_table)

    doc.build(story)
    print(f"✅ Report generated: {output_path}")
