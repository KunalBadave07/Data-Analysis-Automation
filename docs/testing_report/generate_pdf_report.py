from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle


ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = ROOT / "testing_report" / "FINAL_TEST_REPORT.md"
SYSTEM_CASES_MD = ROOT / "testing_report" / "SYSTEM_TEST_CASES.md"
OUTPUT_PDF = ROOT / "testing_report" / "FINAL_TEST_REPORT.pdf"


def _inline_markdown_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def _parse_markdown_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if all(set(part) <= {"-", " "} for part in parts):
            continue
        rows.append(parts)
    return rows


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#153B50"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#58707f"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#153B50"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#274c5e"),
            spaceBefore=6,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=14,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=14,
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=3,
        )
    )
    return styles


def _build_cover(story, styles):
    story.append(Spacer(1, 1.1 * inch))
    story.append(Paragraph("Retail Sales Analytics Pipeline", styles["ReportTitle"]))
    story.append(Paragraph("Quality Assurance Test Report", styles["ReportTitle"]))
    story.append(
        Paragraph(
            f"Prepared from executed automated validation on {datetime.now().strftime('%d %B %Y')}",
            styles["Meta"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "This PDF is generated from the real executed test evidence, coverage output, and structured QA findings contained in the repository artifacts.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 0.35 * inch))
    story.append(
        Paragraph(
            "<b>Evidence Sources</b><br/>"
            "test_logs/pytest_run.log<br/>"
            "test_logs/junit.xml<br/>"
            "coverage_report/coverage.xml<br/>"
            "testing_report/FINAL_TEST_REPORT.md<br/>"
            "testing_report/SYSTEM_TEST_CASES.md",
            styles["Body"],
        )
    )
    story.append(PageBreak())


def _append_markdown_document(story, styles, path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    paragraph_buffer: list[str] = []
    index = 0

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            story.append(Paragraph(_inline_markdown_to_html(" ".join(paragraph_buffer).strip()), styles["Body"]))
            paragraph_buffer = []

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            story.append(Spacer(1, 0.08 * inch))
            index += 1
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].rstrip())
                index += 1
            rows = _parse_markdown_table(table_lines)
            if rows:
                header = [Paragraph(_inline_markdown_to_html(cell), styles["Body"]) for cell in rows[0]]
                body = [
                    [Paragraph(_inline_markdown_to_html(cell), styles["Body"]) for cell in row]
                    for row in rows[1:]
                ]
                table = LongTable([header] + body, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#153B50")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#97A6B0")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F5F8FA")]),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 0.14 * inch))
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(_inline_markdown_to_html(stripped[4:]), styles["SubHeading"]))
            index += 1
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(_inline_markdown_to_html(stripped[3:]), styles["SectionHeading"]))
            index += 1
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(_inline_markdown_to_html(stripped[2:]), styles["ReportTitle"]))
            index += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            story.append(Paragraph(_inline_markdown_to_html(stripped), styles["ReportBullet"]))
            index += 1
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph("&bull; " + _inline_markdown_to_html(stripped[2:]), styles["ReportBullet"]))
            index += 1
            continue

        paragraph_buffer.append(stripped)
        index += 1

    flush_paragraph()


def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#58707f"))
    canvas.drawRightString(A4[0] - 40, 20, f"Page {page_num}")


def main():
    styles = _build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=34,
        title="Retail Sales Analytics Pipeline - QA Validation Report",
        author="OpenAI Codex",
    )

    story = []
    _build_cover(story, styles)
    _append_markdown_document(story, styles, REPORT_MD)
    story.append(PageBreak())
    story.append(Paragraph("System Test Cases", styles["SectionHeading"]))
    _append_markdown_document(story, styles, SYSTEM_CASES_MD)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF generated at: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
