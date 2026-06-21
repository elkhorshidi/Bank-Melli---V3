import base64
import html
from pathlib import Path

import plotly.express as px
import streamlit as st

from src.calculator import get_latest_record, get_recent_records
from src.pdf_exporter import generate_pdf_report
from src.status import get_recommendation_text


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

TABLE_COLUMN_LABELS = {
    "date": "تاریخ",
    "day": "روز",
    "bank_melli_rate": "نرخ بانک ملی",
    "market_rate": "نرخ بازار",
    "difference_percent": "اختلاف درصدی",
    "average_difference": "میانگین اختلاف ۷ رکورد اخیر",
    "status": "وضعیت",
}

TABLE_COLUMN_ORDER = [
    "روز",
    "تاریخ",
    "نرخ بانک ملی",
    "نرخ بازار",
    "اختلاف درصدی",
    "میانگین اختلاف ۷ رکورد اخیر",
    "وضعیت",
]

RATE_SERIES_LABELS = {
    "bank_melli_rate": "نرخ بانک ملی",
    "market_rate": "نرخ بازار آزاد",
}


def format_jalali_date(value) -> str:
    return str(value).replace(" ", "").replace("-", "/")


def format_rate(value) -> str:
    return f"{value:,.0f}"


def format_percent(value) -> str:
    return f"{value:.2f}%"


def format_percent_ltr(value) -> str:
    return f'<span dir="ltr">{format_percent(value)}</span>'


def format_pdf_filename_date(value) -> str:
    return format_jalali_date(value).replace("/", "-")


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_font_base64(font_path: Path) -> str:
    return base64.b64encode(font_path.read_bytes()).decode("utf-8")


def escape_html(value) -> str:
    return html.escape(str(value), quote=True)


def get_status_color(status: str) -> str:
    colors = {
        "بسیار جذاب": "#166534",
        "جذاب": "#15803d",
        "عادی": "#1d4ed8",
        "غیرجذاب": "#b91c1c",
    }
    return colors.get(status, "#111827")


def get_status_background(status: str) -> str:
    colors = {
        "بسیار جذاب": "#dcfce7",
        "جذاب": "#f0fdf4",
        "عادی": "#eff6ff",
        "غیرجذاب": "#fef2f2",
    }
    return colors.get(status, "#ffffff")


def get_status_border_color(status: str) -> str:
    colors = {
        "بسیار جذاب": "#4ade80",
        "جذاب": "#86efac",
        "عادی": "#93c5fd",
        "غیرجذاب": "#fca5a5",
    }
    return colors.get(status, "#e5e7eb")


def get_tone_color(tone: str) -> str:
    colors = {
        "strong_positive": "#166534",
        "positive": "#15803d",
        "neutral": "#1d4ed8",
        "negative": "#b91c1c",
    }
    return colors.get(tone, "#111827")


def get_tone_background(tone: str) -> str:
    colors = {
        "strong_positive": "#dcfce7",
        "positive": "#f0fdf4",
        "neutral": "#eff6ff",
        "negative": "#fef2f2",
    }
    return colors.get(tone, "#ffffff")


def get_tone_border_color(tone: str) -> str:
    colors = {
        "strong_positive": "#4ade80",
        "positive": "#86efac",
        "neutral": "#93c5fd",
        "negative": "#fca5a5",
    }
    return colors.get(tone, "#e5e7eb")


def prepare_display_table(df):
    display_df = df.copy()
    display_df["date"] = display_df["date"].apply(format_jalali_date)
    display_df["day"] = display_df["day"].replace(WEEKDAY_LABELS)
    display_df["bank_melli_rate"] = display_df["bank_melli_rate"].apply(format_rate)
    display_df["market_rate"] = display_df["market_rate"].apply(format_rate)
    display_df["difference_percent"] = display_df["difference_percent"].apply(format_percent)
    display_df["average_difference"] = display_df["average_difference"].apply(format_percent)
    display_df = display_df.rename(columns=TABLE_COLUMN_LABELS)
    return display_df[TABLE_COLUMN_ORDER]


def style_display_table(display_df):
    latest_row_index = display_df.index[-1]
    numeric_columns = [
        "نرخ بانک ملی",
        "نرخ بازار",
        "اختلاف درصدی",
        "میانگین اختلاف ۷ رکورد اخیر",
    ]

    return (
        display_df.style
        .apply(
            lambda row: [
                "background-color: #f8fafc;" if row.name == latest_row_index else ""
                for _ in row
            ],
            axis=1,
        )
        .set_properties(**{"text-align": "right", "font-size": "13px"})
        .set_properties(subset=numeric_columns, **{"text-align": "center"})
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("text-align", "right"),
                        ("font-size", "12px"),
                        ("font-weight", "700"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("padding", "5px 8px"),
                    ],
                },
            ]
        )
    )


def build_recent_records_table_html(display_df) -> str:
    header_cells = "".join(
        f'<th class="{"numeric-column" if column != "روز" and column != "وضعیت" else ""}">{escape_html(column)}</th>'
        for column in TABLE_COLUMN_ORDER
    )
    rows = []

    for index, row in display_df.iterrows():
        row_class = "latest-row" if index == display_df.index[-1] else ""
        cells = []
        for column in TABLE_COLUMN_ORDER:
            value = row[column]
            if column == "وضعیت":
                status_class = {
                    "بسیار جذاب": "status-strong-positive",
                    "جذاب": "status-positive",
                    "عادی": "status-neutral",
                    "غیرجذاب": "status-negative",
                }.get(value, "")
                cells.append(
                    f'<td class="status-cell {status_class}">{escape_html(value)}</td>'
                )
            elif column in [
                "تاریخ",
                "نرخ بانک ملی",
                "نرخ بازار",
                "اختلاف درصدی",
                "میانگین اختلاف ۷ رکورد اخیر",
            ]:
                cells.append(f'<td class="numeric-column">{escape_html(value)}</td>')
            else:
                cells.append(f"<td>{escape_html(value)}</td>")

        rows.append(f'<tr class="{row_class}">{"".join(cells)}</tr>')

    return "".join(
        [
            '<div class="records-table-wrap">',
            '<table class="recent-records-table" dir="rtl">',
            f"<thead><tr>{header_cells}</tr></thead>",
            f"<tbody>{''.join(rows)}</tbody>",
            "</table>",
            "</div>",
        ]
    )


def render_recent_records_html_table(recent_records) -> None:
    display_table = prepare_display_table(recent_records)
    st.markdown(build_recent_records_table_html(display_table), unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value: str,
    color: str = "#111827",
    background: str = "#ffffff",
    small: bool = False,
) -> str:
    value_class = "metric-value metric-value-small" if small else "metric-value"
    return "".join(
        [
            f'<div class="metric-card" style="background: {background};">',
            f'<div class="metric-label">{label}</div>',
            f'<div class="{value_class}" style="color: {color};">{value}</div>',
            "</div>",
        ]
    )


def build_metric_grid(cards: list[str], secondary: bool = False) -> str:
    grid_class = "metric-grid secondary" if secondary else "metric-grid"
    cards_html = "".join(cards)
    return f'<div class="{grid_class}">{cards_html}</div>'


def render_metric_section(latest, alert_level: float) -> None:
    status = latest["status"]
    primary_cards = [
        render_metric_card("نرخ امروز بانک ملی", format_rate(latest["bank_melli_rate"])),
        render_metric_card("نرخ امروز بازار آزاد", format_rate(latest["market_rate"])),
        render_metric_card("اختلاف امروز", format_percent(latest["difference_percent"])),
        render_metric_card(
            "وضعیت امروز",
            status,
            color=get_status_color(status),
            background=get_status_background(status),
        ),
    ]
    secondary_cards = [
        render_metric_card(
            "میانگین اختلاف ۷ رکورد اخیر",
            format_percent(latest["average_difference"]),
            small=True,
        ),
        render_metric_card("سطح هشدار", format_percent(alert_level), small=True),
    ]

    st.markdown(
        build_metric_grid(primary_cards) + build_metric_grid(secondary_cards, secondary=True),
        unsafe_allow_html=True,
    )


def render_records_summary(latest) -> None:
    status = latest["status"]
    cards = [
        render_metric_card(
            "آخرین وضعیت",
            status,
            color=get_status_color(status),
            background=get_status_background(status),
        ),
        render_metric_card("آخرین اختلاف", format_percent(latest["difference_percent"])),
        render_metric_card("آخرین نرخ بانک ملی", format_rate(latest["bank_melli_rate"])),
        render_metric_card("آخرین نرخ بازار آزاد", format_rate(latest["market_rate"])),
    ]
    st.markdown(build_metric_grid(cards), unsafe_allow_html=True)


def render_recommendation_box(recommendation: dict, latest_record) -> None:
    tone = recommendation["tone"]
    detail_items = [
        ("اختلاف امروز", format_percent_ltr(latest_record["difference_percent"])),
        ("میانگین اخیر", format_percent_ltr(latest_record["average_difference"])),
        ("سطح هشدار", format_percent_ltr(recommendation["alert_level"])),
    ]
    details_html = "".join(
        f'<span><strong>{label}:</strong> {value}</span>' for label, value in detail_items
    )
    box_html = "".join(
        [
            f'<div class="recommendation-box" style="background: {get_tone_background(tone)}; border-color: {get_tone_border_color(tone)};">',
            f'<div class="recommendation-title">{recommendation["title"]}</div>',
            f'<div class="recommendation-headline" style="color: {get_tone_color(tone)};">{recommendation["headline"]}</div>',
            f'<div class="recommendation-message">{recommendation["message"]}</div>',
            f'<div class="recommendation-details">{details_html}</div>',
            "</div>",
        ]
    )
    st.markdown(box_html, unsafe_allow_html=True)


def render_pdf_download_button(
    latest,
    recent_records,
    recommendation: dict,
    alert_level: float,
) -> None:
    pdf_bytes = generate_pdf_report(
        latest_record=latest,
        recent_records=recent_records,
        recommendation=recommendation,
        alert_level=alert_level,
    )
    st.download_button(
        label="دانلود گزارش PDF",
        data=pdf_bytes,
        file_name=f"bank_melli_report_{format_pdf_filename_date(latest['date'])}.pdf",
        mime="application/pdf",
    )


def render_footer_note() -> None:
    st.markdown(
        (
            '<div class="footer-note">اطلاعات این گزارش صر'
            'فاً جهت اطلاع‌رسانی است و مبنای تصمیم‌گیری نمی‌باشد.</div>'
        ),
        unsafe_allow_html=True,
    )


def apply_base_styles() -> None:
    project_root = get_project_root()
    regular_font_path = project_root / "assets" / "fonts" / "Vazirmatn-Regular.ttf"
    bold_font_path = project_root / "assets" / "fonts" / "Vazirmatn-Bold.ttf"
    print("Vazirmatn dashboard font injected from:", regular_font_path)

    regular_font = load_font_base64(regular_font_path)
    bold_font = load_font_base64(bold_font_path)
    font_css = f"""
        @font-face {{
            font-family: 'Vazirmatn';
            src: url(data:font/truetype;charset=utf-8;base64,{regular_font}) format('truetype');
            font-weight: 400;
            font-style: normal;
            font-display: swap;
        }}
        @font-face {{
            font-family: 'Vazirmatn';
            src: url(data:font/truetype;charset=utf-8;base64,{bold_font}) format('truetype');
            font-weight: 700;
            font-style: normal;
            font-display: swap;
        }}
    """
    st.markdown(
        """
        <style>
        """
        + font_css
        + """
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMarkdownContainer"],
        [class*="css"],
        button,
        input,
        textarea,
        select,
        div,
        span,
        p,
        table,
        th,
        td {
            font-family: 'Vazirmatn', sans-serif !important;
        }
        .stApp {
            direction: rtl;
            text-align: right;
            background: #f8fafc;
        }
        [data-testid="stAppViewContainer"] .main .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 1050px;
            margin: 0 auto;
            padding-top: 3.2rem;
            padding-bottom: 1.6rem;
        }
        .stMarkdown, .stDataFrame {
            direction: rtl;
            text-align: right;
        }
        .stMarkdown *,
        .stTabs *,
        div[data-testid="stDownloadButton"] *,
        div[data-testid="stPlotlyChart"] * {
            font-family: 'Vazirmatn', sans-serif !important;
        }
        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px 10px 0 0;
            font-size: 0.9rem;
            font-weight: 700;
            height: 2.5rem;
            padding: 0 1rem;
        }
        .stTabs [aria-selected="true"] {
            border-bottom-color: #ffffff;
            color: #111827;
        }
        .dashboard-container {
            max-width: 1050px;
            margin: 0 auto;
        }
        .report-header {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem 1.1rem 0.95rem;
            margin-bottom: 1rem;
            text-align: right;
        }
        .report-header-top {
            align-items: flex-start;
            display: flex;
            gap: 0.75rem;
            justify-content: space-between;
        }
        .report-header h1 {
            color: #111827;
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1.45;
            margin: 0 0 0.15rem;
        }
        .report-header p {
            color: #475569;
            font-size: 0.9rem;
            margin: 0;
        }
        .report-header .today {
            color: #334155;
            font-size: 0.85rem;
            margin-top: 0.3rem;
        }
        .status-pill {
            border: 1px solid #e5e7eb;
            border-radius: 999px;
            flex: 0 0 auto;
            font-size: 0.82rem;
            font-weight: 700;
            line-height: 1;
            padding: 0.45rem 0.75rem;
            white-space: nowrap;
        }
        .metric-grid {
            display: grid;
            gap: 0.7rem;
            margin-bottom: 0.75rem;
            width: 100%;
        }
        .metric-grid {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }
        .metric-grid.secondary {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .metric-card {
            background: #ffffff;
            border: 1px solid #d8dee8;
            border-radius: 10px;
            min-height: 98px;
            padding: 0.9rem 0.95rem;
            text-align: right;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.78rem;
            margin-bottom: 0.55rem;
        }
        .metric-value {
            color: #111827;
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1.35;
        }
        .metric-value-small {
            font-size: 1.25rem;
        }
        .recommendation-box {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            margin: 1rem 0 1.05rem;
            padding: 1.15rem 1.2rem;
            text-align: right;
        }
        .recommendation-title {
            color: #64748b;
            font-size: 0.84rem;
            margin-bottom: 0.35rem;
        }
        .recommendation-headline {
            font-size: 1.85rem;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }
        .recommendation-message {
            color: #334155;
            font-size: 0.9rem;
            line-height: 1.8;
            margin-bottom: 0.65rem;
        }
        .recommendation-details {
            border-top: 1px solid #e5e7eb;
            color: #475569;
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem 1.35rem;
            padding-top: 0.6rem;
            font-size: 0.82rem;
        }
        .section-title {
            color: #111827;
            font-size: 1rem;
            font-weight: 700;
            margin: 1.15rem 0 0.55rem;
        }
        .records-header {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            margin-bottom: 0.9rem;
            padding: 0.9rem 1rem;
            text-align: right;
        }
        .records-header h2 {
            color: #111827;
            font-size: 1.15rem;
            font-weight: 700;
            margin: 0 0 0.2rem;
        }
        .records-header p {
            color: #64748b;
            font-size: 0.86rem;
            margin: 0;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            background: #ffffff;
        }
        .records-table-wrap {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            direction: rtl;
            margin-top: 0.75rem;
            overflow-x: auto;
            width: 100%;
        }
        .recent-records-table {
            border-collapse: collapse;
            direction: rtl;
            font-family: 'Vazirmatn', sans-serif;
            font-size: 0.8rem;
            min-width: 860px;
            table-layout: fixed;
            text-align: right;
            width: 100%;
        }
        .recent-records-table th,
        .recent-records-table td {
            border-bottom: 1px solid #e5e7eb;
            padding: 0.48rem 0.65rem;
            text-align: right;
            vertical-align: middle;
            white-space: nowrap;
        }
        .recent-records-table th {
            background: #f1f5f9;
            color: #334155;
            font-size: 0.76rem;
            font-weight: 700;
        }
        .recent-records-table tbody tr.latest-row {
            background: #f8fafc;
        }
        .recent-records-table tbody tr:last-child td {
            border-bottom: 0;
        }
        .recent-records-table .numeric-column {
            direction: ltr;
            text-align: center;
        }
        .recent-records-table .status-cell {
            font-weight: 700;
            text-align: right;
        }
        .recent-records-table .status-strong-positive {
            color: #166534;
        }
        .recent-records-table .status-positive {
            color: #15803d;
        }
        .recent-records-table .status-neutral {
            color: #1d4ed8;
        }
        .recent-records-table .status-negative {
            color: #b91c1c;
        }
        .chart-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 0.35rem 0.35rem 0;
            margin-bottom: 0.8rem;
        }
        div[data-testid="stPlotlyChart"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 0.35rem;
            margin-bottom: 0.8rem;
        }
        .footer-note {
            color: #94a3b8;
            margin-top: 1.4rem;
            text-align: center;
            font-size: 0.78rem;
        }
        div[data-testid="stElementContainer"]:has(div[data-testid="stDownloadButton"]) {
            left: 24px;
            position: fixed;
            top: 90px;
            width: auto;
            z-index: 999;
        }
        div[data-testid="stDownloadButton"] {
            display: flex;
            direction: rtl;
            justify-content: flex-start;
            margin-bottom: 0.4rem;
            width: auto;
        }
        @media (max-width: 900px) {
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 640px) {
            .report-header-top {
                display: block;
            }
            .status-pill {
                display: inline-block;
                margin-top: 0.7rem;
            }
            .metric-grid,
            .metric-grid.secondary {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(latest_date: str, status: str) -> None:
    st.markdown(
        f"""
        <div class="dashboard-container">
        <div class="report-header">
            <div class="report-header-top">
                <div>
                    <h1>گزارش روزانه نرخ دلار بانک ملی</h1>
                    <p>گزارش ساده وضعیت نرخ بانک ملی نسبت به نرخ بازار آزاد</p>
                    <p class="today">امروز: {latest_date}</p>
                </div>
                <div class="status-pill" style="color: {get_status_color(status)}; background: {get_status_background(status)}; border-color: {get_status_border_color(status)};">{status}</div>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_chart(chart) -> None:
    chart.update_layout(
        height=300,
        margin=dict(l=16, r=16, t=42, b=26),
        title_x=0.98,
        font=dict(family="Vazirmatn", size=12),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    )
    chart.update_xaxes(tickangle=0)


def render_charts_section(chart_df, alert_level: float) -> None:
    st.markdown('<div class="section-title">نمودار نرخ‌ها</div>', unsafe_allow_html=True)
    rates_chart = px.line(
        chart_df,
        x="date",
        y=["bank_melli_rate", "market_rate"],
        markers=True,
        title="روند نرخ بانک ملی و بازار آزاد",
        labels={
            "date": "تاریخ",
            "value": "نرخ",
            "variable": "نوع نرخ",
        },
    )
    rates_chart.for_each_trace(
        lambda trace: trace.update(name=RATE_SERIES_LABELS.get(trace.name, trace.name))
    )
    rates_chart.update_layout(legend_title_text="نوع نرخ")
    style_chart(rates_chart)
    st.plotly_chart(rates_chart, use_container_width=True)

    st.markdown('<div class="section-title">نمودار اختلاف درصدی</div>', unsafe_allow_html=True)
    difference_chart = px.bar(
        chart_df,
        x="date",
        y="difference_percent",
        title="روند اختلاف درصدی",
        labels={
            "date": "تاریخ",
            "difference_percent": "اختلاف درصدی",
        },
    )
    difference_chart.update_traces(name="اختلاف درصدی", showlegend=True)
    difference_chart.add_hline(
        y=alert_level,
        line_dash="dash",
        line_color="red",
        annotation_text="سطح هشدار ۳٪",
        annotation_position="top right",
    )
    style_chart(difference_chart)
    st.plotly_chart(difference_chart, use_container_width=True)


def render_summary_tab(latest, recent_records, chart_df, alert_level: float) -> None:
    latest_date = format_jalali_date(latest["date"])
    render_header(latest_date, latest["status"])
    recommendation = get_recommendation_text(
        latest["status"],
        latest["difference_percent"],
        latest["average_difference"],
        alert_level,
    )
    render_metric_section(latest, alert_level)
    render_recommendation_box(recommendation, latest)
    render_charts_section(chart_df, alert_level)
    render_footer_note()


def render_records_header() -> None:
    st.markdown(
        """
        <div class="records-header">
            <h2>۷ رکورد اخیر</h2>
            <p>مرتب‌شده بر اساس تاریخ گزارش برای مقایسه سریع</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_records_tab(latest, recent_records) -> None:
    render_records_header()
    render_records_summary(latest)
    render_recent_records_html_table(recent_records)
    render_footer_note()


def render_dashboard(df, recent_days: int, alert_level: float) -> None:
    latest = get_latest_record(df)
    recent_records = get_recent_records(df, recent_days)
    chart_df = df.copy()
    chart_df["date"] = chart_df["date"].apply(format_jalali_date)
    recommendation = get_recommendation_text(
        latest["status"],
        latest["difference_percent"],
        latest["average_difference"],
        alert_level,
    )

    apply_base_styles()
    render_pdf_download_button(latest, recent_records, recommendation, alert_level)
    tab_summary, tab_records = st.tabs(["خلاصه گزارش", "۷ رکورد اخیر"])

    with tab_summary:
        render_summary_tab(latest, recent_records, chart_df, alert_level)

    with tab_records:
        render_records_tab(latest, recent_records)
