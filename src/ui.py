import plotly.express as px
import streamlit as st

from src.calculator import get_latest_record, get_recent_records


def render_dashboard(df, recent_days: int) -> None:
    latest = get_latest_record(df)
    recent_records = get_recent_records(df, recent_days)

    st.markdown(
        """
        <style>
        body, .stApp {
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
    col1.metric("تاریخ", latest["date"])
    col2.metric("نرخ بانک ملی", f"{latest['bank_melli_rate']:,.0f}")
    col3.metric("نرخ بازار", f"{latest['market_rate']:,.0f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("اختلاف درصدی", f"{latest['difference_percent']:.2f}%")
    col5.metric(
        f"میانگین اختلاف {recent_days} رکورد اخیر",
        f"{latest['average_difference']:.2f}%",
    )
    col6.metric("وضعیت", latest["status"])

    st.subheader(f"{recent_days} رکورد اخیر")
    st.dataframe(recent_records, use_container_width=True)

    st.subheader("نمودار نرخ ها")
    rates_chart = px.line(
        df,
        x="date",
        y=["bank_melli_rate", "market_rate"],
        markers=True,
        labels={
            "date": "تاریخ",
            "value": "نرخ",
            "variable": "نوع نرخ",
        },
    )
    st.plotly_chart(rates_chart, use_container_width=True)

    st.subheader("نمودار اختلاف درصدی")
    difference_chart = px.bar(
        df,
        x="date",
        y="difference_percent",
        labels={
            "date": "تاریخ",
            "difference_percent": "اختلاف درصدی",
        },
    )
    st.plotly_chart(difference_chart, use_container_width=True)
