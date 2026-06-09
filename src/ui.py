import plotly.express as px
import streamlit as st

from src.calculator import get_latest_record, get_recent_records


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


def get_status_color(status: str) -> str:
    colors = {
        "جذاب": "#15803d",
        "عادی": "#1d4ed8",
        "غیرجذاب": "#b91c1c",
    }
    return colors.get(status, "#111827")


def get_status_background(status: str) -> str:
    colors = {
        "جذاب": "#f0fdf4",
        "عادی": "#eff6ff",
        "غیرجذاب": "#fef2f2",
    }
    return colors.get(status, "#ffffff")


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


def render_metric_card(
    label: str,
    value: str,
    color: str = "#111827",
    background: str = "#ffffff",
    small: bool = False,
) -> str:
    value_class = "metric-value metric-value-small" if small else "metric-value"
    return (
        f"""
        <div class="metric-card" style="background: {background};">
            <div class="metric-label">{label}</div>
            <div class="{value_class}" style="color: {color};">{value}</div>
        </div>
        """
    )


def apply_base_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            direction: rtl;
            text-align: right;
            background: #f8fafc;
        }
        [data-testid="stAppViewContainer"] .main .block-container {
            max-width: 1050px;
            margin: 0 auto;
            padding-top: 1.4rem;
            padding-bottom: 1.6rem;
        }
        .stMarkdown, .stDataFrame {
            direction: rtl;
            text-align: right;
        }
        .dashboard-container {
            max-width: 1050px;
            margin: 0 auto;
        }
        .report-header {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            text-align: right;
        }
        .report-header h1 {
            color: #111827;
            font-size: 1.55rem;
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
        .metric-grid {
            display: grid;
            gap: 0.65rem;
            margin-bottom: 0.75rem;
        }
        .metric-grid.primary {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }
        .metric-grid.secondary {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .metric-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            min-height: 92px;
            padding: 0.85rem 0.9rem;
            text-align: right;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.78rem;
            margin-bottom: 0.45rem;
        }
        .metric-value {
            color: #111827;
            font-size: 1.6rem;
            font-weight: 700;
            line-height: 1.35;
        }
        .metric-value-small {
            font-size: 1.35rem;
        }
        .section-title {
            color: #111827;
            font-size: 1rem;
            font-weight: 700;
            margin: 1.15rem 0 0.55rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            background: #ffffff;
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
        @media (max-width: 900px) {
            .metric-grid.primary {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 640px) {
            .metric-grid.primary,
            .metric-grid.secondary {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(latest_date: str) -> None:
    st.markdown(
        f"""
        <div class="dashboard-container">
        <div class="report-header">
            <h1>گزارش روزانه نرخ دلار بانک ملی</h1>
            <p>گزارش ساده وضعیت نرخ بانک ملی نسبت به نرخ بازار آزاد</p>
            <p class="today">امروز: {latest_date}</p>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_chart(chart) -> None:
    chart.update_layout(
        height=300,
        margin=dict(l=16, r=16, t=48, b=28),
        title_x=0.98,
        font=dict(family="Arial", size=12),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    )


def render_dashboard(df, recent_days: int, alert_level: float) -> None:
    latest = get_latest_record(df)
    recent_records = get_recent_records(df, recent_days)
    chart_df = df.copy()
    chart_df["date"] = chart_df["date"].apply(format_jalali_date)
    latest_date = format_jalali_date(latest["date"])

    apply_base_styles()
    render_header(latest_date)

    status = latest["status"]
    st.markdown(
        f"""
        <div class="dashboard-container">
            <div class="metric-grid primary">
                {render_metric_card("نرخ امروز بانک ملی", format_rate(latest["bank_melli_rate"]))}
                {render_metric_card("نرخ امروز بازار آزاد", format_rate(latest["market_rate"]))}
                {render_metric_card("اختلاف امروز", format_percent(latest["difference_percent"]))}
                {render_metric_card("وضعیت امروز", status, get_status_color(status), get_status_background(status))}
            </div>
            <div class="metric-grid secondary">
                {render_metric_card("میانگین اختلاف ۷ رکورد اخیر", format_percent(latest["average_difference"]), small=True)}
                {render_metric_card("سطح هشدار", format_percent(alert_level), small=True)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    display_table = prepare_display_table(recent_records)
    st.markdown('<div class="section-title">۷ رکورد اخیر</div>', unsafe_allow_html=True)
    st.dataframe(style_display_table(display_table), width="stretch", hide_index=True)

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
    with st.container():
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(rates_chart, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

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
    with st.container():
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(difference_chart, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="footer-note">اطلاعات این گزارش صرفاً جهت اطلاع‌رسانی است و مبنای تصمیم‌گیری نمی‌باشد.</div>',
        unsafe_allow_html=True,
    )
