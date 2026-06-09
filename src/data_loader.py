import pandas as pd


NUMERIC_COLUMNS = ["bank_melli_rate", "market_rate"]
TEXT_COLUMNS = ["date", "day"]
COLUMN_ALIASES = {
    "melli_bank_rate": "bank_melli_rate",
}


def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    df = df.rename(columns=COLUMN_ALIASES)

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=NUMERIC_COLUMNS).reset_index(drop=True)

    for column in TEXT_COLUMNS:
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()

    return df[TEXT_COLUMNS + NUMERIC_COLUMNS]
