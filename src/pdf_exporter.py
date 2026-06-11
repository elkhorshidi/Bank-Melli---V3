from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_NAME = "Vazirmatn"
BOLD_FONT_NAME = "Vazirmatn-Bold"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = PROJECT_ROOT / "assets" / "fonts"
VAZIRMATN_REGULAR = FONT_DIR / "Vazirmatn-Regular.ttf"
VAZIRMATN_BOLD = FONT_DIR / "Vazirmatn-Bold.ttf"

WEEKDAY_LABELS = {
    "Sunday": "یکشنبه",
    "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه",
    "Thursday": "پنجشنبه",
    "Friday": "جمعه",
    "Saturday": "شنبه",
}

FOOTER_NOTE = (
    "اطلاعات این گزارش صر"
    "فاً جهت اطلاع‌رسانی است و مبنای تصمیم‌گیری نمی‌باشد."
)

STATUS_COLORS = {
    "جذاب": {
        "text": "#15803d",
        "background": "#f0fdf4",
        "border": "#86efac",
    },
    "عادی": {
        "text": "#1d4ed8",
        "background": "#eff6ff",
        "border": "#93c5fd",
    },
    "غیرجذاب": {
        "text": "#b91c1c",
        "background": "#fef2f2",
        "border": "#fca5a5",
    },
}

PDF_RECOMMENDATION_MESSAGES = {
    "جذاب": "امروز زمان مناسبی برای فروش ارز به بانک ملی است؛ اختلاف نرخ بانک ملی با بازار آزاد در سطح پایینی قرار دارد.",
    "عادی": "امروز شرایط فروش ارز به بانک ملی در محدوده عادی قرار دارد؛ اختلاف نرخ با بازار آزاد قابل‌قبول است، اما مزیت خیلی بالایی مشاهده نمی‌شود.",
    "غیرجذاب": "امروز زمان خیلی مناسبی برای فروش ارز به بانک ملی نیست؛ اختلاف نرخ بانک ملی با بازار آزاد در سطح بالایی قرار دارد.",
}

TONE_COLORS = {
    "positive": STATUS_COLORS["جذاب"],
    "neutral": STATUS_COLORS["عادی"],
    "negative": STATUS_COLORS["غیرجذاب"],
}


def clean_persian_text(text) -> str:
    if text is None:
        return ""

    replacements = {
        "مرتب" + "شده": "مرتب‌شده",
        "مرتب شده": "مرتب‌شده",
        "قابل" + "قبول": "قابل‌قبول",
        "قابل قبول": "قابل‌قبول",
        "نمی" + "شود": "نمی‌شود",
        "نمی شود": "نمی‌شود",
        "پایین" + "تر": "پایین‌تر",
        "پایین تر": "پایین‌تر",
        "نسب" + "تا": "نسبتاً",
        "می" + "شود": "می‌شود",
        "می شود": "می‌شود",
        "شاخص" + "های": "شاخص‌های",
        "شاخص های": "شاخص‌های",
        "صر" + "فا": "صر" + "فاً",
        "اطلاع" + "رسانی": "اطلاع‌رسانی",
        "اطلاع رسانی": "اطلاع‌رسانی",
        "تصمیم" + "گیری": "تصمیم‌گیری",
        "تصمیم گیری": "تصمیم‌گیری",
        "نمی" + "باشد": "نمی‌باشد",
        "نمی باشد": "نمی‌باشد",
        "سه" + "شنبه": "سه‌شنبه",
        "سه شنبه": "سه‌شنبه",
        "چهارشنبه": "چهارشنبه",
        "یکشنبه": "یکشنبه",
        "دوشنبه": "دوشنبه",
        "پنجشنبه": "پنجشنبه",
    }
    text = str(text)
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    return text


def fa(text) -> str:
    """
    Prepare Persian/Arabic text for ReportLab rendering:
    - clean Persian text before shaping
    - reshape Persian/Arabic characters
    - apply bidi display ordering
    - return the shaped text
    """
    text = clean_persian_text(text)
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)


def register_pdf_fonts() -> tuple[str, str]:
    # Vazirmatn is bundled to ensure stable Persian rendering on Streamlit Cloud.
    if not VAZIRMATN_REGULAR.exists():
        raise FileNotFoundError(f"Missing font: {VAZIRMATN_REGULAR}")
    if not VAZIRMATN_BOLD.exists():
        raise FileNotFoundError(f"Missing font: {VAZIRMATN_BOLD}")

    pdfmetrics.registerFont(TTFont(FONT_NAME, str(VAZIRMATN_REGULAR)))
    pdfmetrics.registerFont(TTFont(BOLD_FONT_NAME, str(VAZIRMATN_BOLD)))

    return FONT_NAME, BOLD_FONT_NAME


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


def _fa_paragraph(text, style: ParagraphStyle) -> Paragraph:
    return _paragraph(fa(clean_persian_text(text)), style)


def _mixed_value(label: str, value: str) -> str:
    return f"{fa(clean_persian_text(label))} {value}"


def _build_styles(font_name: str, bold_font_name: str) -> dict:
    styles = {
        "title": ParagraphStyle(
            "PersianTitle",
            fontName=bold_font_name,
            fontSize=20,
            leading=30,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#111827"),
            rightIndent=0,
        ),
        "subtitle": ParagraphStyle(
            "PersianSubtitle",
            fontName=font_name,
            fontSize=10.5,
            leading=18,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#475569"),
            rightIndent=0,
        ),
        "section": ParagraphStyle(
            "PersianSection",
            fontName=bold_font_name,
            fontSize=13,
            leading=21,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#111827"),
            rightIndent=0,
        ),
        "body": ParagraphStyle(
            "PersianBody",
            fontName=font_name,
            fontSize=10,
            leading=17,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#334155"),
            rightIndent=0,
            wordWrap="RTL",
        ),
        "recommendation_message": ParagraphStyle(
            "PersianRecommendationMessage",
            fontName=font_name,
            fontSize=8,
            leading=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#334155"),
            rightIndent=0,
            wordWrap="RTL",
        ),
        "small": ParagraphStyle(
            "PersianSmall",
            fontName=font_name,
            fontSize=8.5,
            leading=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#64748b"),
            rightIndent=0,
            wordWrap="RTL",
        ),
        "metric_label": ParagraphStyle(
            "PersianMetricLabel",
            fontName=font_name,
            fontSize=8.6,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#64748b"),
            rightIndent=0,
        ),
        "metric_value": ParagraphStyle(
            "PersianMetricValue",
            fontName=bold_font_name,
            fontSize=11.5,
            leading=16,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#111827"),
            rightIndent=0,
        ),
        "headline": ParagraphStyle(
            "PersianHeadline",
            fontName=bold_font_name,
            fontSize=22,
            leading=30,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#111827"),
            rightIndent=0,
        ),
        "footer": ParagraphStyle(
            "PersianFooter",
            fontName=font_name,
            fontSize=8,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#94a3b8"),
        ),
    }
    for status, palette in STATUS_COLORS.items():
        styles[f"status_{status}"] = ParagraphStyle(
            f"PersianStatus{status}",
            parent=styles["metric_value"],
            textColor=colors.HexColor(palette["text"]),
        )
    return styles


def _palette_for_status(status: str) -> dict:
    return STATUS_COLORS.get(status, STATUS_COLORS["عادی"])


def _palette_for_tone(tone: str) -> dict:
    return TONE_COLORS.get(tone, TONE_COLORS["neutral"])


def _value_paragraph(value, styles: dict) -> Paragraph:
    if value in STATUS_COLORS:
        return _fa_paragraph(value, styles[f"status_{value}"])
    return _paragraph(value, styles["metric_value"])


def _status_badge(status: str, styles: dict, font_regular: str, font_bold: str) -> Table:
    palette = _palette_for_status(status)
    table = Table(
        [[_fa_paragraph(status, styles[f"status_{status}"])]],
        colWidths=[28 * mm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_bold),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(palette["background"])),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(palette["border"])),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _report_header(
    latest_record,
    styles: dict,
    font_regular: str,
    font_bold: str,
) -> Table:
    title_stack = [
        _fa_paragraph("گزارش روزانه نرخ دلار بانک ملی", styles["title"]),
        _fa_paragraph("وضعیت نرخ بانک ملی نسبت به نرخ بازار آزاد", styles["subtitle"]),
        _paragraph(_mixed_value("امروز:", _format_jalali_date(latest_record["date"])), styles["subtitle"]),
    ]
    table = Table(
        [[_status_badge(latest_record["status"], styles, font_regular, font_bold), title_stack]],
        colWidths=[36 * mm, 132 * mm],
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_regular),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _section_title(title: str, styles: dict) -> Paragraph:
    return _fa_paragraph(title, styles["section"])


def _metric_card(label: str, value: str, styles: dict, font_regular: str, font_bold: str) -> Table:
    table = Table(
        [[_value_paragraph(value, styles), _fa_paragraph(label, styles["metric_label"])]],
        colWidths=[35 * mm, 48 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_regular),
                ("FONTNAME", (0, 0), (0, 0), font_bold),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _metric_grid(
    metrics: list[tuple[str, str]],
    styles: dict,
    font_regular: str,
    font_bold: str,
) -> Table:
    rows = []
    for index in range(0, len(metrics), 2):
        right_metric = metrics[index]
        left_metric = metrics[index + 1] if index + 1 < len(metrics) else ("", "")
        rows.append(
            [
                _metric_card(left_metric[0], left_metric[1], styles, font_regular, font_bold),
                _metric_card(right_metric[0], right_metric[1], styles, font_regular, font_bold),
            ]
        )

    table = Table(rows, colWidths=[85 * mm, 85 * mm], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _recommendation_box(
    latest_record,
    recommendation,
    styles: dict,
    font_regular: str,
    font_bold: str,
) -> Table:
    palette = _palette_for_tone(recommendation.get("tone", "neutral"))
    message = PDF_RECOMMENDATION_MESSAGES.get(
        recommendation["headline"],
        clean_persian_text(recommendation["message"]),
    )
    details = [
        ("اختلاف امروز:", _format_percent(latest_record["difference_percent"])),
        ("میانگین اخیر:", _format_percent(latest_record["average_difference"])),
        ("سطح هشدار:", _format_percent(recommendation["alert_level"])),
    ]
    detail_table = Table(
        [
            [_paragraph(value, styles["small"]), _fa_paragraph(label, styles["small"])]
            for label, value in details
        ],
        colWidths=[28 * mm, 136 * mm],
        hAlign="RIGHT",
    )
    detail_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_regular),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    headline_style = ParagraphStyle(
        "RecommendationHeadline",
        parent=styles["headline"],
        textColor=colors.HexColor(palette["text"]),
    )
    rows = [
        [_fa_paragraph(recommendation["title"], styles["small"])],
        [_fa_paragraph(recommendation["headline"], headline_style)],
        [_fa_paragraph(message, styles["recommendation_message"])],
        [detail_table],
    ]
    table = Table(rows, colWidths=[168 * mm], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_regular),
                ("FONTNAME", (0, 1), (0, 1), font_bold),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(palette["border"])),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(palette["background"])),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEABOVE", (0, 3), (-1, 3), 0.5, colors.HexColor(palette["border"])),
            ]
        )
    )
    return table


def _footer(styles: dict) -> Paragraph:
    return _fa_paragraph(FOOTER_NOTE, styles["footer"])


def _bar_color(value: float) -> colors.Color:
    if value < 2.5:
        return colors.HexColor("#22c55e")
    if value <= 4.0:
        return colors.HexColor("#3b82f6")
    return colors.HexColor("#ef4444")


def draw_difference_bar_chart(
    c,
    recent_records,
    x,
    y,
    width,
    height,
    font_regular,
    font_bold,
):
    print("Drawing difference chart with records:", len(recent_records))
    values = [float(value) for value in recent_records["difference_percent"].tolist()]
    dates = [_format_jalali_date(value) for value in recent_records["date"].tolist()]
    if not values:
        return

    warning_level = 3.0
    y_max = max(max(values), warning_level) + 0.7
    plot_x = x + 9 * mm
    plot_y = y + 12 * mm
    plot_width = width - 18 * mm
    plot_height = height - 26 * mm

    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(0.7)
    c.rect(x, y, width, height, stroke=1, fill=1)

    c.setFont(font_bold, 9)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawRightString(x + width - 7 * mm, y + height - 7 * mm, fa("روند اختلاف درصدی ۷ رکورد اخیر"))

    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(0.5)
    c.line(plot_x, plot_y, plot_x + plot_width, plot_y)

    warning_y = plot_y + (warning_level / y_max) * plot_height

    bar_slot = plot_width / len(values)
    bar_width = min(9 * mm, bar_slot * 0.52)
    for index, (date, value) in enumerate(zip(dates, values)):
        center_x = plot_x + bar_slot * index + bar_slot / 2
        bar_height = max(1.2, (value / y_max) * plot_height)
        bar_x = center_x - bar_width / 2
        color = _bar_color(value)

        c.setFillColor(color)
        c.setStrokeColor(color)
        c.rect(bar_x, plot_y, bar_width, bar_height, stroke=0, fill=1)

        c.setFont(font_regular, 6.2)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawCentredString(center_x, plot_y + bar_height + 3, _format_percent(value))
        c.drawCentredString(center_x, y + 4.2 * mm, date)

    c.setStrokeColor(colors.HexColor("#dc2626"))
    c.setDash(3, 2)
    c.line(plot_x, warning_y, plot_x + plot_width, warning_y)
    c.setDash()
    c.setFont(font_regular, 6.5)
    c.setFillColor(colors.HexColor("#dc2626"))
    c.drawRightString(plot_x + plot_width - 5 * mm, warning_y + 4, fa("سطح ۳٪"))
    c.drawString(plot_x, warning_y + 4, "3.00%")

    c.setFont(font_regular, 6.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawRightString(plot_x + plot_width, plot_y - 3.5 * mm, fa("تاریخ"))
    c.restoreState()


class DifferenceBarChart(Flowable):
    def __init__(self, recent_records, width, height, font_regular, font_bold):
        super().__init__()
        self.recent_records = recent_records
        self.width = width
        self.height = height
        self.font_regular = font_regular
        self.font_bold = font_bold

    def draw(self):
        draw_difference_bar_chart(
            self.canv,
            self.recent_records,
            0,
            0,
            self.width,
            self.height,
            self.font_regular,
            self.font_bold,
        )


def _recent_records_table(
    recent_records,
    styles: dict,
    font_regular: str,
    font_bold: str,
) -> Table:
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
        status = record["status"]
        rows.append(
            [
                _fa_paragraph(WEEKDAY_LABELS.get(record["day"], record["day"]), styles["body"]),
                _paragraph(_format_jalali_date(record["date"]), styles["body"]),
                _paragraph(_format_rate(record["bank_melli_rate"]), styles["body"]),
                _paragraph(_format_rate(record["market_rate"]), styles["body"]),
                _paragraph(_format_percent(record["difference_percent"]), styles["body"]),
                _fa_paragraph(status, styles[f"status_{status}"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[25 * mm, 30 * mm, 31 * mm, 31 * mm, 28 * mm, 24 * mm],
        repeatRows=1,
        hAlign="CENTER",
    )
    latest_row = len(rows) - 1
    table_styles = [
        ("FONTNAME", (0, 0), (-1, -1), font_regular),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (0, latest_row), (-1, latest_row), colors.HexColor("#f8fafc")),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (1, 1), (4, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    table.setStyle(
        TableStyle(table_styles)
    )
    return table


def generate_pdf_font_smoke_test() -> bytes:
    font_regular, font_bold = register_pdf_fonts()
    print("Using PDF fonts:", VAZIRMATN_REGULAR, VAZIRMATN_BOLD)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont(font_bold, 18)
    c.drawRightString(width - 18 * mm, height - 30 * mm, fa("گزارش روزانه نرخ دلار بانک ملی"))

    c.setFont(font_regular, 12)
    c.drawRightString(width - 18 * mm, height - 45 * mm, "172,500")
    c.drawRightString(width - 18 * mm, height - 55 * mm, "3.66%")

    c.showPage()
    c.save()
    return buffer.getvalue()


def generate_pdf_report(
    latest_record,
    recent_records,
    recommendation,
    alert_level,
) -> bytes:
    font_name, bold_font_name = register_pdf_fonts()
    print("PDF title raw:", clean_persian_text("شاخص" + "های کلیدی"))
    print(
        "PDF footer raw:",
        clean_persian_text(
            "اطلاعات این گزارش صر"
            "فا جهت اطلاع"
            "رسانی است و مبنای تصمیم"
            "گیری نمی"
            "باشد."
        ),
    )
    print("PDF recommendation raw:", clean_persian_text(recommendation.get("message", "")))
    styles = _build_styles(font_name, bold_font_name)
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

    key_metrics = [
        ("نرخ امروز بانک ملی", _format_rate(latest_record["bank_melli_rate"])),
        ("نرخ امروز بازار آزاد", _format_rate(latest_record["market_rate"])),
        ("اختلاف امروز", _format_percent(latest_record["difference_percent"])),
        ("وضعیت امروز", latest_record["status"]),
        ("میانگین اختلاف ۷ رکورد اخیر", _format_percent(latest_record["average_difference"])),
        ("سطح هشدار", _format_percent(alert_level)),
    ]
    latest_metrics = [
        ("آخرین وضعیت", latest_record["status"]),
        ("آخرین اختلاف", _format_percent(latest_record["difference_percent"])),
        ("آخرین نرخ بانک ملی", _format_rate(latest_record["bank_melli_rate"])),
        ("آخرین نرخ بازار آزاد", _format_rate(latest_record["market_rate"])),
    ]

    page_width, _ = A4
    chart_x = 72
    chart_y = 110
    chart_width = page_width - 144
    chart_height = 150

    def draw_first_page_chart(c, _document):
        draw_difference_bar_chart(
            c,
            recent_records,
            chart_x,
            chart_y,
            chart_width,
            chart_height,
            font_name,
            bold_font_name,
        )
        c.saveState()
        c.setFont(font_name, 8)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawCentredString(page_width / 2, 78, fa(FOOTER_NOTE))
        c.restoreState()

    story = [
        _report_header(latest_record, styles, font_name, bold_font_name),
        Spacer(1, 8 * mm),
        _section_title("شاخص‌های کلیدی", styles),
        Spacer(1, 2 * mm),
        _metric_grid(key_metrics, styles, font_name, bold_font_name),
        Spacer(1, 8 * mm),
        _recommendation_box(latest_record, recommendation, styles, font_name, bold_font_name),
        Spacer(1, 64 * mm),
        PageBreak(),
        _fa_paragraph("۷ رکورد اخیر", styles["title"]),
        _fa_paragraph("مرتب‌شده بر اساس تاریخ گزارش برای مقایسه سریع", styles["subtitle"]),
        Spacer(1, 8 * mm),
        _section_title("خلاصه آخرین وضعیت", styles),
        Spacer(1, 2 * mm),
        _metric_grid(latest_metrics, styles, font_name, bold_font_name),
        Spacer(1, 8 * mm),
        _recent_records_table(recent_records, styles, font_name, bold_font_name),
        Spacer(1, 12 * mm),
        _footer(styles),
    ]

    document.build(story, onFirstPage=draw_first_page_chart)
    return buffer.getvalue()
