# ai/models.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from config import settings

cache = str(settings.HF_CACHE)

_tok_zs = AutoTokenizer.from_pretrained("facebook/bart-large-mnli", cache_dir=cache)
_mod_zs = AutoModelForSequenceClassification.from_pretrained("facebook/bart-large-mnli", cache_dir=cache)
zs_pipe = pipeline("zero-shot-classification", model=_mod_zs, tokenizer=_tok_zs)

_tok_sa = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", cache_dir=cache)
_mod_sa = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", cache_dir=cache)
sa_pipe = pipeline("sentiment-analysis", model=_mod_sa, tokenizer=_tok_sa)
