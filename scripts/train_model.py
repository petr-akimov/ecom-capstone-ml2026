import pandas as pd
import pickle
from pathlib import Path
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import average_precision_score, roc_auc_score

def main():
    BASE_DIR = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "data" / "data_for_training.parquet"
    
    print("Загрузка подготовленных данных...")
    if not data_path.exists():
        raise FileNotFoundError(f"Файл {data_path} не найден! Сначала запустите prepare_features.py")
    
    df = pd.read_parquet(data_path)

    feature_cols = [
        "views",
        "purchases",
        "ctr",
        "hour",
        "weekday",
        "categoryid",
        "available",
    ]
    
    X = df[feature_cols].astype(float)
    y = df["target"]

    print(f"Размер датасета для обучения: {X.shape}")
    print(f"Доля положительного класса: {y.mean():.4f}")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    train_pool = Pool(X_train, y_train)
    val_pool = Pool(X_val, y_val)

    print("Инициализация и обучение модели CatBoost...")
    model = CatBoostClassifier(
        iterations=500,
        depth=6,
        learning_rate=0.1,
        loss_function="Logloss",
        eval_metric="PRAUC",
        random_seed=42,
        early_stopping_rounds=50,
        verbose=100
    )

    model.fit(train_pool, eval_set=val_pool)

    val_preds = model.predict_proba(X_val)[:, 1]
    pr_auc = average_precision_score(y_val, val_preds)
    roc_auc = roc_auc_score(y_val, val_preds)

    print(f"\n--- Результаты валидации ---")
    print(f"Validation PR-AUC: {pr_auc:.4f}")
    print(f"Validation ROC-AUC: {roc_auc:.4f}")

    model_path = BASE_DIR / "ranker.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Модель успешно сохранена в {model_path}")

if __name__ == "__main__":
    main()