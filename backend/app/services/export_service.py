"""
Data export service — spec 2.3, supports JSON, CSV, Markdown, PDF.
"""
import json
import csv
import io
from typing import List, Dict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def to_json(rows: List[Dict]) -> str:
    return json.dumps(rows, indent=2, default=str)


def to_csv(rows: List[Dict]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def to_xml(rows: List[Dict], root_tag: str = "records", row_tag: str = "record") -> str:
    def escape(val):
        return (
            str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    lines = [f"<{root_tag}>"]
    for row in rows:
        lines.append(f"  <{row_tag}>")
        for k, v in row.items():
            lines.append(f"    <{k}>{escape(v)}</{k}>")
        lines.append(f"  </{row_tag}>")
    lines.append(f"</{root_tag}>")
    return "\n".join(lines)


def to_markdown(rows: List[Dict]) -> str:
    if not rows:
        return "_No data._"
    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |",
              "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines)


def to_pdf_bytes(rows: List[Dict], title: str = "Weather Query Export") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    if rows:
        headers = list(rows[0].keys())
        data = [headers] + [[str(row.get(h, "")) for h in headers] for row in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No data available.", styles["Normal"]))

    doc.build(elements)
    return buf.getvalue()
