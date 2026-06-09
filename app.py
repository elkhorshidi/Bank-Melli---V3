import streamlit as st

import config
from src.calculator import add_calculations
from src.data_loader import load_data
from src.status import add_status_column
from src.ui import render_dashboard


def main() -> None:
    st.set_page_config(
        page_title="گزارش روزانه نرخ دلار بانک ملی",
        layout="wide",
    )

    df = load_data(config.GOOGLE_SHEET_CSV_URL)
    df = add_calculations(df, config.ALERT_LEVEL, config.RECENT_DAYS)
    df = add_status_column(df, config.ALERT_LEVEL, config.RECENT_DAYS)

    render_dashboard(df, config.RECENT_DAYS, config.ALERT_LEVEL)


if __name__ == "__main__":
    main()
