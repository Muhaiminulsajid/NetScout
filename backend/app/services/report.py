"""PDF / CSV export of ImageTrace results."""
import csv
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from ..models import ImageSearch

CSV_COLUMNS = ["engine", "page_url", "image_url", "title", "published_at", "similarity"]


def build_csv(search: ImageSearch) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS)
    for m in search.matches:
        writer.writerow([
            m.engine, m.page_url, m.image_url or "", m.title or "",
            m.published_at.isoformat() if m.published_at else "",
            f"{m.similarity:.1f}",
        ])
    return buf.getvalue().encode()


def build_pdf(search: ImageSearch) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="NetScout ImageTrace Report")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("NetScout — ImageTrace Report", styles["Title"]),
        Paragraph(f"File: {search.filename}", styles["Normal"]),
        Paragraph(f"Perceptual hash: {search.phash}", styles["Normal"]),
        Paragraph(f"Generated: {datetime.utcnow().isoformat()}Z", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    if search.exif:
        story.append(Paragraph("EXIF Metadata", styles["Heading2"]))
        exif = search.exif
        rows = [
            ["Camera", exif.get("camera") or "—"],
            ["Captured", exif.get("captured_at") or "—"],
            ["GPS", f'{exif["gps"]["lat"]}, {exif["gps"]["lon"]}' if exif.get("gps") else "—"],
        ]
        t = Table(rows, colWidths=[4 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ]))
        story += [t, Spacer(1, 0.5 * cm)]

    story.append(Paragraph(f"Matches ({len(search.matches)})", styles["Heading2"]))
    header = ["#", "Engine", "Page", "Published", "Similarity"]
    rows = [header]
    for i, m in enumerate(search.matches, 1):
        rows.append([
            str(i), m.engine,
            Paragraph((m.title or m.page_url)[:200], styles["BodyText"]),
            m.published_at.strftime("%Y-%m-%d") if m.published_at else "—",
            f"{m.similarity:.0f}%",
        ])
    table = Table(rows, colWidths=[1 * cm, 2.5 * cm, 8.5 * cm, 2.5 * cm, 2 * cm],
                  repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    doc.build(story)
    return buf.getvalue()
