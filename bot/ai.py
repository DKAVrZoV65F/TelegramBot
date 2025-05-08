# ai.py
import asyncio
from collections import defaultdict

# ---------- Уровень 0: правила / словарь ----------
KEYWORD_TAGS = {
    "оплата":  "finance",
    "прайс":   "finance",
    "срочно":  "urgent",
    "баг":     "bug",
    "ошибка":  "bug",
    "фича":    "feature",
}


async def keyword_tagger(text: str | None) -> list[str]:
    if not text:
        return []
    low = text.lower()
    tags = {tag for kw, tag in KEYWORD_TAGS.items() if kw in low}
    await asyncio.sleep(0)  # имитация async-IO
    return list(tags)


# ---------- Уровень 1: Unsupervised ----------
"""
После накопления n-сот сообщений мы можем
1. строить sentence-эмбеддинги (Sentence-BERT, ruBERT, universal-sentence-encoder);
2. кластеризовать (K-means, DBSCAN) → кластеры = кандидаты в теги;
3. вручную подписать кластеры (30-60 мин работы куратора);
4. сохранить mapping «кластер → тег» и использовать.
"""

# ---------- Уровень 2: Supervised ----------
"""
Когда ручных меток накопится ~500-1000,
обучаем классификатор (sklearn / XGBoost / fine-tune BERT/ruBERT).
Обучение — offline-скрипт в /scripts/train.py, модель кладём в data/model.onnx.
В проде загружаем модель и получаем predict → tags.
"""