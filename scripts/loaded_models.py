import pickle
import pandas as pd
from pathlib import Path

# Относительные пути с учетом структуры проекта (из scripts/ на уровень выше в data/ и корневую директорию)
BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "ranker.pkl", "rb") as f:
    ranker = pickle.load(f)

item_features = pd.read_parquet(BASE_DIR / "data" / "item_features.parquet")