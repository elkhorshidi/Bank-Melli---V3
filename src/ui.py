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


def prepare_display_table(df):
    display_df = df.copy()
    display_df["date"] = display_df["date"].apply(format_jalali_date)
    display_df["day"] = display_df["day"].replace(WEEKDAY_LABELS)
    display_df["bank_melli_rate"] = display_df["bank_melli_rate"].apply(format_rate)
    display_df["market_rate"] = display_df["market_rate"].apply(format_rate)
    display_df["difference_percent"] = display_df["difference_percent"].apply(format_percent)
    display_df["average_difference"] = display_df["average_difference"].apply(format_percent)
    return display_df.rename(columns=TABLE_COLUMN_LABELS)


def render_dashboard(df, recent_days: int, alert_level: float) -> None:
    latest = get_latest_record(df)
    recent_records = get_recent_records(df, recent_days)
    chart_df = df.copy()
    chart_df["date"] = chart_df["date"].apply(format_jalali_date)

    st.markdown(
        """
        <style>
        .stApp {
            direction: rtl;
            text-align: right;
        }
        .stMarkdown, .stMetric, .stDataFrame {
            direction: rtl;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("گزارش روزانه نرخ دلار بانک ملی")

    st.subheader("آخرین وضعیت")
    col1, col2, col3 = st.columns(3)
    col1.metric("تاریخ", format_jalali_date(latest["date"]))
    col2.metric("نرخ بانک ملی", format_rate(latest["bank_melli_rate"]))
    col3.metric("نرخ بازار آزاد", format_rate(latest["market_rate"]))

    col4, col5, col6 = st.columns(3)
    col4.metric("اختلاف امروز", format_percent(latest["difference_percent"]))
    col5.metric(
        "میانگین اختلاف ۷ رکورد اخیر",
        format_percent(latest["average_difference"]),
    )
    col6.metric("وضعیت", latest["status"])

    st.subheader(f"{recent_days} رکورد اخیر")
    st.dataframe(prepare_display_table(recent_records), width="stretch")

    st.subheader("روند نرخ بانک ملی و بازار آزاد")
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
    st.plotly_chart(rates_chart, width="stretch")

    st.subheader("روند اختلاف درصدی")
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
    st.plotly_chart(difference_chart, width="stretch")
