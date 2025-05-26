# ai/__init__.py

from .models import zs_pipe, sa_pipe
import asyncio

KEYWORD_TAGS = {
    "баг": "bug", "ошибка": "bug",
    "фича": "feature", "функция": "feature",
    "вопрос": "question", "как ": "question",
    "срочно": "urgent",
    "postgres": "competitor", "postgre": "competitor", "ms sql": "competitor"
}

AI_LABELS = ["bug", "feature", "idea", "praise", "question", "urgent", "competitor"]

KEY_THEME = {
    "не понятно": "вопросы",
    "объясните": "вопросы",
    "есть дока": "вопросы",
    "не работает": "баги",
    "ошибка": "баги",
    "не хватает": "фичи",
    "добавить": "фичи",
    "postgres": "конкуренты",
    "postgre": "конкуренты",
    "ms sql": "конкуренты",
    "oracle": "конкуренты",
}

THEME_THRESHOLD = 0.7


async def keyword_tags(text: str) -> list[str]:
    low = text.lower()
    tags = {tag for kw, tag in KEYWORD_TAGS.items() if kw in low}

    await asyncio.sleep(0)

    return list(tags)


async def theme_tags(text: str) -> list[str]:
    low = (text or "").lower()
    out = {tag for kw, tag in KEY_THEME.items() if kw in low}

    await asyncio.sleep(0)

    return list(out)


async def classify_theme(text: str) -> list[str]:
    if not text:
        return []

    res = zs_pipe(text, list(set(KEY_THEME.values())), multi_label=True)
    labels, scores = res["labels"], res["scores"]
    tags = [lbl for lbl, s in zip(labels, scores) if s >= THEME_THRESHOLD]
    tags.extend(await theme_tags(text))

    return list(set(tags))


async def classify_sentiment(text: str) -> str:
    if not text:
        return "neutral"

    lab = sa_pipe(text)[0]["label"].lower()

    if lab == "positive":
        return "positive"

    if lab == "negative":
        return "negative"

    return "neutral"


async def classify_with_scores(text: str) -> dict:
    if not text:
        return {}

    res = zs_pipe(text, AI_LABELS, multi_label=True)
    label_scores = dict(zip(res["labels"], res["scores"]))

    keywords = await keyword_tags(text)
    for kw in keywords:
        label_scores[kw] = max(label_scores.get(kw, 0.0), 0.9)

    sent = (sa_pipe(text)[0]["label"]).lower()
    label_scores["positive" if sent == "positive" else "negative"] = 0.99

    return label_scores
