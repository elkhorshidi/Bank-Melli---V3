import pandas as pd

from src.calculator import get_recent_records


def determine_status(
    difference_percent: float,
    average_difference: float,
    alert_level: float,
) -> str:
    if difference_percent <= average_difference:
        return "جذاب"
    if difference_percent <= average_difference + 0.25:
        return "عادی"
    return "غیرجذاب"


def get_recommendation_text(
    status: str,
    difference_percent: float,
    average_difference: float,
    alert_level: float,
) -> dict:
    title = "پیشنهاد امروز برای فروش ارز به بانک ملی"

    if status == "جذاب":
        return {
            "title": title,
            "headline": "جذاب",
            "message": "اختلاف امروز پایین‌تر یا نزدیک به میانگین اخیر است؛ بنابراین فروش ارز به بانک ملی از نظر نرخ، نسبتاً جذاب ارزیابی می‌شود.",
            "tone": "positive",
            "alert_level": alert_level,
        }

    if status == "عادی":
        return {
            "title": title,
            "headline": "عادی",
            "message": "اختلاف امروز در محدوده قابل‌قبول قرار دارد، اما مزیت نرخ بانک ملی نسبت به روزهای بهتر اخیر چندان برجسته نیست.",
            "tone": "neutral",
            "alert_level": alert_level,
        }

    return {
        "title": title,
        "headline": "غیرجذاب",
        "message": "امروز زمان مناسبی برای فروش ارز به بانک ملی نیست؛ اختلاف نرخ بانک ملی با بازار آزاد بالاتر از میانگین اخیر قرار دارد.",
        "tone": "negative",
        "alert_level": alert_level,
    }


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
