import pandas as pd


def add_calculations(
    df: pd.DataFrame,
    alert_level: float,
    recent_days: int,
) -> pd.DataFrame:
    df = df.copy()

    df["difference_percent"] = (
        (df["market_rate"] - df["bank_melli_rate"]) / df["market_rate"]
    ) * 100

    average_difference = get_recent_records(df, recent_days)["difference_percent"].mean()
    df["average_difference"] = average_difference

    return df


def get_latest_record(df: pd.DataFrame) -> pd.Series:
    return df.iloc[-1]


def get_recent_records(df: pd.DataFrame, recent_days: int) -> pd.DataFrame:
    return df.tail(recent_days)
