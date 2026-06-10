from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_NAME = "BankMelliPersian"
FALLBACK_FONT_NAME = "Helvetica"

PERSIAN_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Tahoma.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/GeezaPro.ttc",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

WEEKDAY_LABELS = {
    "Sunday": "یکشنبه",
    "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه",
    "Thursday": "پنجشنبه",
    "Friday": "جمعه",
    "Saturday": "شنبه",
}


def fa(text: str) -> str:
    """
    Prepare Persian/Arabic text for ReportLab rendering:
    - convert input to string
    - reshape Persian/Arabic characters
    - apply bidi display ordering
    - return the shaped text
    """
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)


def register_pdf_font() -> str:
    for font_path in PERSIAN_FONT_CANDIDATES:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
                return FONT_NAME
            except Exception:
                continue

    # TODO: Add a project-approved Persian font file later for stable deployment.
    # Helvetica is a safe PDF fallback, but Persian glyph support will be limited.
    return FALLBACK_FONT_NAME


def _format_jalali_date(value) -> str:
    return str(value).replace(" ", "").replace("-", "/")


def _format_filename_date(value) -> str:
    return _format_jalali_date(value).replace("/", "-")


def _format_rate(value) -> str:
    return f"{value:,.0f}"


def _format_percent(value) -> str:
    return f"{value:.2f}%"


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text), style)


def _fa_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return _paragraph(fa(text), style)


def _mixed_value(label: str, value: str) -> str:
    return f"{fa(label)} {value}"


def _build_styles(font_name: str) -> dict:
    base_styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PersianTitle",
            parent=base_styles["Title"],
            fontName=font_name,
            fontSize=18,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "PersianSubtitle",
            parent=base_styles["Normal"],
            fontName=font_name,
            fontSize=11,
            leading=18,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#475569"),
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "PersianSection",
            parent=base_styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=21,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "PersianBody",
            parent=base_styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=17,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#334155"),
        ),
        "headline": ParagraphStyle(
            "PersianHeadline",
            parent=base_styles["Heading1"],
            fontName=font_name,
            fontSize=17,
            leading=25,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        ),
    }


def _metric_table(metrics: list[tuple[str, str]], styles: dict) -> Table:
    rows = [
        [_fa_paragraph(label, styles["body"]), _paragraph(value, styles["body"])]
        for label, value in metrics
    ]
    table = Table(rows, colWidths=[82 * mm, 58 * mm], hAlign="RIGHT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _recent_records_table(recent_records, styles: dict) -> Table:
    headers = [
        "روز",
        "تاریخ",
        "نرخ بانک ملی",
        "نرخ بازار",
        "اختلاف درصدی",
        "وضعیت",
    ]
    rows = [[_fa_paragraph(header, styles["body"]) for header in headers]]

    for _, record in recent_records.iterrows():
        rows.append(
            [
                _fa_paragraph(WEEKDAY_LABELS.get(record["day"], record["day"]), styles["body"]),
                _paragraph(_format_jalali_date(record["date"]), styles["body"]),
                _paragraph(_format_rate(record["bank_melli_rate"]), styles["body"]),
                _paragraph(_format_rate(record["market_rate"]), styles["body"]),
                _paragraph(_format_percent(record["difference_percent"]), styles["body"]),
                _fa_paragraph(record["status"], styles["body"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[25 * mm, 30 * mm, 31 * mm, 31 * mm, 28 * mm, 24 * mm],
        repeatRows=1,
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def generate_pdf_report(
    latest_record,
    recent_records,
    recommendation,
    alert_level,
) -> bytes:
    font_name = register_pdf_font()
    styles = _build_styles(font_name)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Bank Melli Report {_format_filename_date(latest_record['date'])}",
    )

    story = [
        _fa_paragraph("گزارش روزانه نرخ دلار بانک ملی", styles["title"]),
        _paragraph(_mixed_value("امروز:", _format_jalali_date(latest_record["date"])), styles["subtitle"]),
        Spacer(1, 5 * mm),
        _fa_paragraph("شاخص‌های کلیدی", styles["section"]),
        _metric_table(
            [
                ("نرخ امروز بانک ملی", _format_rate(latest_record["bank_melli_rate"])),
                ("نرخ امروز بازار آزاد", _format_rate(latest_record["market_rate"])),
                ("اختلاف امروز", _format_percent(latest_record["difference_percent"])),
                ("وضعیت امروز", fa(latest_record["status"])),
                ("میانگین اختلاف ۷ رکورد اخیر", _format_percent(latest_record["average_difference"])),
                ("سطح هشدار", _format_percent(alert_level)),
            ],
            styles,
        ),
        Spacer(1, 7 * mm),
        _fa_paragraph(recommendation["title"], styles["section"]),
        _fa_paragraph(recommendation["headline"], styles["headline"]),
        _fa_paragraph(recommendation["message"], styles["body"]),
        Spacer(1, 4 * mm),
        _metric_table(
            [
                ("اختلاف امروز", _format_percent(latest_record["difference_percent"])),
                ("میانگین اخیر", _format_percent(latest_record["average_difference"])),
                ("سطح هشدار", _format_percent(alert_level)),
            ],
            styles,
        ),
        PageBreak(),
        _fa_paragraph("۷ رکورد اخیر", styles["title"]),
        _fa_paragraph("مرتب‌شده بر اساس تاریخ گزارش برای مقایسه سریع", styles["subtitle"]),
        Spacer(1, 5 * mm),
        _fa_paragraph("خلاصه آخرین وضعیت", styles["section"]),
        _metric_table(
            [
                ("آخرین وضعیت", fa(latest_record["status"])),
                ("آخرین اختلاف", _format_percent(latest_record["difference_percent"])),
                ("آخرین نرخ بانک ملی", _format_rate(latest_record["bank_melli_rate"])),
                ("آخرین نرخ بازار آزاد", _format_rate(latest_record["market_rate"])),
            ],
            styles,
        ),
        Spacer(1, 7 * mm),
        _recent_records_table(recent_records, styles),
    ]

    document.build(story)
    return buffer.getvalue()
