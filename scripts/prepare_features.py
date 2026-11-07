import argparse
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"


def load_events(path: str) -> pd.DataFrame:
    """Загружает события пользователей и отмечает покупки."""
    df = pd.read_csv(path)
    df.columns = [c.lower().strip() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
    df["is_purchase_event"] = (
        df["event"].astype(str).str.lower().isin(["purchase", "transaction"])
        | df.get("transactionid", pd.Series([None] * len(df))).notna()
    )
    return df


def load_item_properties(path: str) -> pd.DataFrame:
    """Загружает свойства товаров (только простые поля)."""
    df = pd.read_csv(path, usecols=["itemid", "property", "value"])
    df.columns = [c.lower().strip() for c in df.columns]

    simple_props = df[df["property"].isin(["categoryid", "available"])]
    simple_props = simple_props.sort_values(["itemid", "property"])
    latest = simple_props.groupby(["itemid", "property"], as_index=False).last()

    pivot = latest.pivot_table(
        index="itemid", columns="property", values="value", aggfunc="last"
    )
    pivot = pivot.reset_index()
    pivot.columns.name = None
    return pivot


def compute_item_popularity(events: pd.DataFrame) -> pd.DataFrame:
    """Считает простую популярность товаров."""
    views = (
        events[events["event"].str.lower() == "view"]
        .groupby("itemid")
        .size()
        .rename("views")
    )
    buys = (
        events[events["is_purchase_event"]].groupby("itemid").size().rename("purchases")
    )

    df = pd.concat([views, buys], axis=1).fillna(0)
    df["ctr"] = df["purchases"] / np.maximum(df["views"], 1)
    df = df.reset_index()
    return df


def build_target(
    views: pd.DataFrame, purchases: pd.DataFrame, window_hours=24
) -> pd.DataFrame:
    """Создаёт целевую переменную: купил ли пользователь товар в течение 24 часов после просмотра."""
    window = pd.Timedelta(hours=window_hours)

    purchases = purchases.rename(columns={"timestamp": "purchase_time"})
    df = views.merge(purchases, on=["visitorid", "itemid"], how="left")

    df["target"] = (
        (df["purchase_time"].notna())
        & (df["purchase_time"] > df["timestamp"])
        & (df["purchase_time"] <= df["timestamp"] + window)
    ).astype(int)

    df = df.drop(columns=["purchase_time"])
    return df


def prepare(
    events_path: str,
    item_props_path: str,
    out_item_feats_path: str,
    out_train_path: str,
    window_hours: int = 24,
):
    events = load_events(events_path)

    views = events[events["event"].str.lower() == "view"][
        ["timestamp", "visitorid", "itemid"]
    ].copy()
    purchases = events[events["is_purchase_event"]][
        ["timestamp", "visitorid", "itemid"]
    ].copy()

    views = build_target(views, purchases, window_hours=window_hours)
    pop = compute_item_popularity(events)
    item_props = load_item_properties(item_props_path)

    item_features = pop.merge(item_props, on="itemid", how="left")
    item_features = item_features.fillna(0)
    
    views = views.merge(item_features, on="itemid", how="left")
    views = views.fillna(0)

    views["hour"] = views["timestamp"].dt.hour
    views["weekday"] = views["timestamp"].dt.day_of_week

    for col in item_features.columns:
        if item_features[col].dtype == object:
            item_features[col] = item_features[col].astype(str)
    for col in views.columns:
        if views[col].dtype == object:
            views[col] = views[col].astype(str)

    item_features.to_parquet(out_item_feats_path, index=False)
    views.to_parquet(out_train_path, index=False)
    print(f"Артефакты успешно сохранены в:\n - {out_item_feats_path}\n - {out_train_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default=str(DEFAULT_DATA_DIR / "events.csv"))
    parser.add_argument("--item-props", default=str(DEFAULT_DATA_DIR / "item_properties_part1.csv"))
    parser.add_argument("--out-item-feats", default=str(DEFAULT_DATA_DIR / "item_features.parquet"))
    parser.add_argument("--out-train", default=str(DEFAULT_DATA_DIR / "data_for_training.parquet"))
    parser.add_argument("--window-hours", type=int, default=24)
    args = parser.parse_args()

    prepare(
        args.events,
        args.item_props,
        args.out_item_feats,
        args.out_train,
        args.window_hours,
    )