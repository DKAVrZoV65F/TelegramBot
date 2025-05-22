# ai.py
import asyncio
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
from .config import settings

KEYWORD_TAGS = { "оплата":"finance", "прайс":"finance",
                 "срочно":"urgent",  "баг":"bug",
                 "ошибка":"bug",     "фича":"feature" }

# Расширенные метки для классификации
AI_LABELS = [
    "bug", "feature", "idea", "praise", "question", "urgent",
    "positive", "negative", "proposal", "competitor", "flood"
]

async def keyword_tagger(text: str) -> list[str]:
    if not text:
        return []
    low = text.lower()
    tags = {tag for kw, tag in KEYWORD_TAGS.items() if kw in low}
    await asyncio.sleep(0)
    return list(tags)

cache = str(settings.HF_CACHE_DIR)

tokenizer_zs = AutoTokenizer.from_pretrained(
    "facebook/bart-large-mnli",
    cache_dir=cache,
    local_files_only=False
)
model_zs = AutoModelForSequenceClassification.from_pretrained(
    "facebook/bart-large-mnli",
    cache_dir=cache,
    local_files_only=False
)
_zs_classifier = pipeline(
    "zero-shot-classification",
    model=model_zs,
    tokenizer=tokenizer_zs,
    device=0
)

tokenizer_sa = AutoTokenizer.from_pretrained(
    "distilbert-base-uncased-finetuned-sst-2-english",
    cache_dir=cache,
    local_files_only=False
)
model_sa = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased-finetuned-sst-2-english",
    cache_dir=cache,
    local_files_only=False
)
_sentiment = pipeline(
    "sentiment-analysis",
    model=model_sa,
    tokenizer=tokenizer_sa,
    device=0
)

async def ai_tagger(text: str) -> list[str]:
    if not text:
        return []
    res = _zs_classifier(text, ["bug","feature","idea","praise","question","urgent"], multi_label=True)
    return [lbl for lbl, score in zip(res["labels"], res["scores"]) if score > 0.4]

async def ai_sentiment(text: str) -> str:
    if not text:
        return "neutral"
    res = _sentiment(text)[0]
    return res["label"].lower()

# Новая функция классификации сообщения
async def classify_message(text: str) -> list:
    if not text:
        return []

    # Используем существующий pipeline для классификации
    res = _zs_classifier(text, AI_LABELS, multi_label=True)
    tags = [lbl for lbl, score in zip(res["labels"], res["scores"]) if score > 0.4]

    # Определение тональности
    sentiment_res = _sentiment(text)[0]
    sentiment_label = sentiment_res["label"].lower()
    if sentiment_label == "positive":
        tags.append("praise")
    elif sentiment_label == "negative":
        tags.append("negative")

    # Обнаружение продуктов и конкурентов по ключевым словам
    lower_text = text.lower()

    # Продукты
    if "firebird" in lower_text:
        tags.append("firebird")
    if "reddatabase" in lower_text:
        tags.append("reddatabase")
    if "ib expert" in lower_text:
        tags.append("red-expert")
    # Конкуренты
    if "postgre" in lower_text:
        tags.append("competitor")
    if "ib expert" in lower_text:
        tags.append("competitor")
    # Флуд
    if " самолет" in lower_text or "флуд" in lower_text:
        tags.append("flood")

    return list(set(tags))
