# util.py

def enough_chars(text: str | None, min_len: int = 10) -> bool:
    return bool(text) and len(text.replace(" ", "")) >= min_len


def make_msg_link(chat_id: int, msg_id: int) -> str:
    cid = str(chat_id)[4:] if str(chat_id).startswith("-100") else chat_id
    return f"https://t.me/c/{cid}/{msg_id}"
