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


def render_metric_card(label: str, value: str, color: str = "#111827", small: bool = False) -> None:
    value_class = "metric-value small" if small else "metric-value"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="{value_class}" style="color: {color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
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
            max-width: 1200px;
            margin: 0 auto;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stMarkdown, .stDataFrame {
            direction: rtl;
            text-align: right;
        }
        .dashboard-header {
            margin-bottom: 1.5rem;
        }
        .dashboard-title {
            color: #111827;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.5;
            margin: 0 0 0.25rem;
        }
        .dashboard-subtitle {
            color: #475569;
            font-size: 1rem;
            margin: 0 0 0.5rem;
        }
        .dashboard-date {
            color: #334155;
            font-size: 0.95rem;
            margin: 0;
        }
        .metric-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            min-height: 112px;
            text-align: right;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 0.6rem;
        }
        .metric-value {
            color: #111827;
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.4;
        }
        .metric-value.small {
            font-size: 1.35rem;
        }
        .section-title {
            color: #111827;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 1.75rem 0 0.75rem;
        }
        .footer-note {
            color: #64748b;
            border-top: 1px solid #e2e8f0;
            margin-top: 2rem;
            padding-top: 1rem;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(latest_date: str) -> None:
    st.markdown(
        f"""
        <div class="dashboard-header">
            <h1 class="dashboard-title">گزارش روزانه نرخ دلار بانک ملی</h1>
            <p class="dashboard-subtitle">گزارش ساده وضعیت نرخ بانک ملی نسبت به نرخ بازار آزاد</p>
            <p class="dashboard-date">امروز: {latest_date}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_chart(chart) -> None:
    chart.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=60, b=35),
        title_x=0.98,
        font=dict(family="Arial", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )


def render_dashboard(df, recent_days: int, alert_level: float) -> None:
    latest = get_latest_record(df)
    recent_records = get_recent_records(df, recent_days)
    chart_df = df.copy()
    chart_df["date"] = chart_df["date"].apply(format_jalali_date)
    latest_date = format_jalali_date(latest["date"])

    apply_base_styles()
    render_header(latest_date)

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_metric_card("نرخ امروز بانک ملی", format_rate(latest["bank_melli_rate"]))
    with summary_cols[1]:
        render_metric_card("نرخ امروز بازار آزاد", format_rate(latest["market_rate"]))
    with summary_cols[2]:
        render_metric_card("اختلاف امروز", format_percent(latest["difference_percent"]))
    with summary_cols[3]:
        render_metric_card(
            "وضعیت امروز",
            latest["status"],
            color=get_status_color(latest["status"]),
        )

    detail_cols = st.columns(2)
    with detail_cols[0]:
        render_metric_card(
            "میانگین اختلاف ۷ رکورد اخیر",
            format_percent(latest["average_difference"]),
            small=True,
        )
    with detail_cols[1]:
        render_metric_card("سطح هشدار", format_percent(alert_level), small=True)

    st.markdown(f'<div class="section-title">{recent_days} رکورد اخیر</div>', unsafe_allow_html=True)
    st.dataframe(prepare_display_table(recent_records), width="stretch", hide_index=True)

    st.markdown('<div class="section-title">نمودارها</div>', unsafe_allow_html=True)
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
    st.plotly_chart(rates_chart, width="stretch")

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
    st.plotly_chart(difference_chart, width="stretch")

    st.markdown(
        '<div class="footer-note">اطلاعات این گزارش صرفاً جهت اطلاع‌رسانی است و مبنای تصمیم‌گیری نمی‌باشد.</div>',
        unsafe_allow_html=True,
    )
