import pandas as pd


def determine_status(
    difference_percent: float,
) -> str:
    if difference_percent < 2.5:
        return "جذاب"
    if difference_percent <= 4.0:
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
            "message": "امروز زمان مناسبی برای فروش ارز به بانک ملی است؛ اختلاف نرخ بانک ملی با بازار آزاد در سطح پایینی قرار دارد.",
            "tone": "positive",
            "alert_level": alert_level,
        }

    if status == "عادی":
        return {
            "title": title,
            "headline": "عادی",
            "message": "امروز شرایط فروش ارز به بانک ملی در محدوده عادی قرار دارد؛ اختلاف نرخ با بازار آزاد قابل‌قبول است، اما مزیت خیلی بالایی مشاهده نمی‌شود.",
            "tone": "neutral",
            "alert_level": alert_level,
        }

    return {
        "title": title,
        "headline": "غیرجذاب",
        "message": "امروز زمان خیلی مناسبی برای فروش ارز به بانک ملی نیست؛ اختلاف نرخ بانک ملی با بازار آزاد در سطح بالایی قرار دارد.",
        "tone": "negative",
        "alert_level": alert_level,
    }


def add_status_column(
    df: pd.DataFrame,
    alert_level: float,
    recent_days: int,
) -> pd.DataFrame:
    df = df.copy()

    df["status"] = df["difference_percent"].apply(determine_status)

    return df
