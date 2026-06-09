import pandas as pd

from src.calculator import get_recent_records


def determine_status(
    difference_percent: float,
    average_difference: float,
    alert_level: float,
) -> str:
    if difference_percent < alert_level:
        return "جذاب"
    if difference_percent <= average_difference:
        return "عادی"
    return "غیرجذاب"


def add_status_column(
    df: pd.DataFrame,
    alert_level: float,
    recent_days: int,
) -> pd.DataFrame:
    df = df.copy()

    average_difference = get_recent_records(df, recent_days)["difference_percent"].mean()
    df["status"] = df["difference_percent"].apply(
        lambda difference: determine_status(
            difference,
            average_difference,
            alert_level,
        )
    )

    return df
