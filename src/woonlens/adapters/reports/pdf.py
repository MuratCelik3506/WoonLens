from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.enums import TA_CENTER  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
from reportlab.lib.styles import (  # type: ignore[import-untyped]
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from woonlens.domain.comparison import ComparedHome, ComparedValue
from woonlens.domain.reporting import ComparisonEvidenceReport

INK = colors.HexColor("#15261F")
GREEN = colors.HexColor("#2F6F52")
MINT = colors.HexColor("#E8F3ED")
SAND = colors.HexColor("#F5F1E8")
LINE = colors.HexColor("#C9D5CF")
MUTED = colors.HexColor("#52665D")


class ReportLabPdfRenderer:
    """Render a transient comparison report as a deterministic PDF."""

    def render(self, report: ComparisonEvidenceReport) -> bytes:
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=landscape(A4),
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="WoonLens comparison evidence report",
            author="WoonLens",
        )
        styles = _styles()
        story = _story(report, styles)
        document.build(
            story,
            onFirstPage=_draw_page,
            onLaterPages=_draw_page,
            canvasmaker=_invariant_canvas,
        )
        return output.getvalue()


def _invariant_canvas(*args: object, **kwargs: object) -> Canvas:
    kwargs["invariant"] = 1
    return Canvas(*args, **kwargs)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "WoonLensTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=INK,
            spaceAfter=5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "WoonLensSubtitle",
            parent=base["Normal"],
            fontSize=9,
            leading=13,
            textColor=MUTED,
            spaceAfter=5 * mm,
        ),
        "heading": ParagraphStyle(
            "WoonLensHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=GREEN,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "WoonLensBody",
            parent=base["BodyText"],
            fontSize=8,
            leading=11,
            textColor=INK,
        ),
        "small": ParagraphStyle(
            "WoonLensSmall",
            parent=base["BodyText"],
            fontSize=7,
            leading=9,
            textColor=INK,
        ),
        "center": ParagraphStyle(
            "WoonLensCenter",
            parent=base["BodyText"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=INK,
        ),
    }


def _story(
    report: ComparisonEvidenceReport,
    styles: dict[str, ParagraphStyle],
) -> list[object]:
    comparison = report.comparison
    story: list[object] = [
        Paragraph("WoonLens comparison evidence", styles["title"]),
        Paragraph(
            "Live official data - generated "
            f"{report.generated_at.isoformat()} - report "
            f"{escape(report.schema_version)} "
            f"- rules {escape(comparison.rules_version)}",
            styles["subtitle"],
        ),
        Paragraph("Compared homes", styles["heading"]),
        _homes_table(comparison.homes, styles),
        Paragraph("Metric comparison", styles["heading"]),
        _metrics_table(report, styles),
        Paragraph("Interpretations", styles["heading"]),
        _insights_table(report, styles),
        Paragraph("Cross-source audits", styles["heading"]),
        _audits_table(report, styles),
        Paragraph("Missing and unavailable data", styles["heading"]),
        *_missing_data(report, styles),
        Paragraph("Sources", styles["heading"]),
        _sources_table(report, styles),
        Paragraph("Limitations", styles["heading"]),
        *_bullets(report.limitations, styles),
        Spacer(1, 3 * mm),
        Paragraph(
            "This PDF was generated for the current request and is not retained "
            "by WoonLens.",
            styles["subtitle"],
        ),
    ]
    return story


def _homes_table(
    homes: tuple[ComparedHome, ...], styles: dict[str, ParagraphStyle]
) -> Table:
    rows: list[list[object]] = [["#", "Address", "Official address UUID"]]
    for index, home in enumerate(homes, start=1):
        if home.overview is None:
            address = f"Unavailable ({home.unavailable_reason})"
        else:
            item = home.overview.address
            number = f"{item.house_number}{item.house_letter or ''}"
            if item.house_number_suffix:
                number = f"{number}-{item.house_number_suffix}"
            address = f"{item.street} {number}, {item.postal_code} {item.city}"
        rows.append(
            [
                str(index),
                Paragraph(escape(address), styles["body"]),
                Paragraph(escape(str(home.address_id)), styles["small"]),
            ]
        )
    return _table(rows, [12 * mm, 120 * mm, 92 * mm])


def _metrics_table(
    report: ComparisonEvidenceReport, styles: dict[str, ParagraphStyle]
) -> Table:
    homes = report.comparison.homes
    width = 227 * mm
    first_width = 52 * mm
    home_width = (width - first_width) / len(homes)
    header: list[object] = ["Metric"]
    header.extend(f"Home {index}" for index in range(1, len(homes) + 1))
    rows: list[list[object]] = [header]
    for metric in report.comparison.metrics:
        definition = (
            f"<b>{escape(metric.metric.label)}</b><br/>"
            f"{escape(metric.metric.scope)} - {escape(metric.metric.unit)}<br/>"
            f"{escape(metric.metric.definition)}"
        )
        row: list[object] = [Paragraph(definition, styles["small"])]
        row.extend(_value_cell(value, styles) for value in metric.values)
        rows.append(row)
    return _table(rows, [first_width] + [home_width] * len(homes), repeat_rows=1)


def _value_cell(value: ComparedValue, styles: dict[str, ParagraphStyle]) -> Paragraph:
    if value.value is None:
        text = (
            "Missing<br/><font color='#52665D'>"
            f"{escape(value.missing_reason or '')}</font>"
        )
    else:
        text = escape(str(value.value))
        if value.is_baseline:
            text += "<br/><font color='#52665D'>baseline</font>"
        elif value.delta_from_baseline is not None:
            text += (
                "<br/><font color='#52665D'>delta "
                f"{value.delta_from_baseline:+g}</font>"
            )
    return Paragraph(text, styles["center"])


def _insights_table(
    report: ComparisonEvidenceReport, styles: dict[str, ParagraphStyle]
) -> Table:
    rows: list[list[object]] = [["Metric", "Classification", "Homes", "Explanation"]]
    for insight in report.comparison.insights:
        homes = ", ".join(
            _home_label(report, address_id) for address_id in insight.address_ids
        )
        rows.append(
            [
                escape(insight.metric_key),
                escape(insight.classification),
                escape(homes or "None"),
                Paragraph(escape(insight.message), styles["small"]),
            ]
        )
    return _table(rows, [42 * mm, 40 * mm, 28 * mm, 117 * mm], repeat_rows=1)


def _audits_table(
    report: ComparisonEvidenceReport, styles: dict[str, ParagraphStyle]
) -> Table:
    rows: list[list[object]] = [
        ["Home", "Classification", "Fields and values", "Explanation"]
    ]
    for audit in report.comparison.audits:
        values = (
            f"{audit.fields[0]}: {audit.values[0]} | "
            f"{audit.fields[1]}: {audit.values[1]}"
        )
        rows.append(
            [
                _home_label(report, audit.address_id),
                escape(audit.classification),
                Paragraph(escape(values), styles["small"]),
                Paragraph(escape(audit.message), styles["small"]),
            ]
        )
    return _table(rows, [20 * mm, 42 * mm, 73 * mm, 92 * mm], repeat_rows=1)


def _missing_data(
    report: ComparisonEvidenceReport, styles: dict[str, ParagraphStyle]
) -> list[object]:
    items: list[str] = []
    for index, home in enumerate(report.comparison.homes, start=1):
        if home.overview is None:
            items.append(f"Home {index}: {home.unavailable_reason}")
        else:
            items.extend(
                f"Home {index} - {item.section}: {item.reason}"
                for item in home.overview.unavailable_sections
            )
    if not items:
        items.append("No unavailable sections were reported for this request.")
    items.extend(notice.message for notice in report.comparison.notices)
    return _bullets(tuple(items), styles)


def _sources_table(
    report: ComparisonEvidenceReport, styles: dict[str, ParagraphStyle]
) -> Table:
    rows: list[list[object]] = [["Provider", "Dataset", "Retrieved", "License / terms"]]
    for source in report.sources:
        rows.append(
            [
                Paragraph(escape(source.provider), styles["small"]),
                Paragraph(escape(source.dataset), styles["small"]),
                Paragraph(escape(source.retrieved_at.isoformat()), styles["small"]),
                Paragraph(escape(source.license_name), styles["small"]),
            ]
        )
    if not report.sources:
        rows.append(["No successful source retrieval", "-", "-", "-"])
    return _table(rows, [45 * mm, 75 * mm, 57 * mm, 50 * mm], repeat_rows=1)


def _bullets(items: tuple[str, ...], styles: dict[str, ParagraphStyle]) -> list[object]:
    return [
        KeepTogether(
            [Paragraph(f"- {escape(item)}", styles["body"]), Spacer(1, 1.5 * mm)]
        )
        for item in items
    ]


def _home_label(report: ComparisonEvidenceReport, address_id: object) -> str:
    for index, home in enumerate(report.comparison.homes, start=1):
        if home.address_id == address_id:
            return f"Home {index}"
    return "Unknown"


def _table(
    rows: list[list[object]],
    widths: list[float],
    *,
    repeat_rows: int = 0,
) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("LEADING", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SAND]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _draw_page(canvas: Canvas, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    width, _ = landscape(A4)
    canvas.setStrokeColor(LINE)
    canvas.line(15 * mm, 11 * mm, width - 15 * mm, 11 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15 * mm, 7 * mm, "WoonLens - live official evidence")
    canvas.drawRightString(width - 15 * mm, 7 * mm, f"Page {document.page}")
    canvas.restoreState()
