import logging
from fastapi import FastAPI, HTTPException
from scripts.loaded_models import ranker, item_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"

app = FastAPI(
    title="Retail Recommendation API",
    version=APP_VERSION,
    description="API для выдачи рекомендаций и вероятностей покупки.",
)


@app.get("/health", tags=["system"])
def health_check():
    """Проверка состояния сервиса и доступности моделей."""
    ok = {
        "ranker_loaded": ranker is not None,
        "items_in_feature_store": len(item_features),
    }
    logger.info(f"Health check: {ok}")
    return {"status": "ok", "details": ok}


@app.get("/version", tags=["system"])
def version():
    """Возвращает текущую версию сервиса."""
    return {"version": APP_VERSION, "service": "retail_recsys"}


@app.get("/", tags=["system"])
def root():
    return {"message": "Retail recommender API running", "version": APP_VERSION}


@app.get("/predict_purchase")
def predict_purchase(itemid: int = 98113, hour: int = 12, weekday: int = 3) -> dict:
    """Предсказываем вероятность покупки товара."""
    row = item_features[item_features["itemid"] == itemid].copy()
    if row.empty:
        raise HTTPException(status_code=404, detail="Item not found in feature store")

    row["hour"] = hour
    row["weekday"] = weekday
    
    feature_cols = ["views", "purchases", "ctr", "hour", "weekday", "categoryid", "available"]
    
    # Заполняем пропуски, если какие-то фичи отсутствуют у конкретного товара
    for col in feature_cols:
        if col not in row.columns:
            row[col] = 0.0

    x = row[feature_cols].astype(float)
    prob = float(ranker.predict_proba(x)[0][1])
    
    return {
        "itemid": itemid,
        "purchase_probability": round(prob, 4),
        "recommendation": "High likelihood" if prob > 0.5 else "Standard"
    }


@app.get("/metrics", tags=["system"])
def metrics():
    """Эндпоинт для сбора метрик (Prometheus)."""
    # Заглушка под будущую интеграцию с Prometheus
    return {"metrics_status": "enabled"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=32000, workers=1)