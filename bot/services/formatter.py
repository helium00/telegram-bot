import html


MAX_MESSAGE_LENGTH = 4096


def escape_html(text: str) -> str:
    return html.escape(text)


def truncate(text: str, max_length: int = MAX_MESSAGE_LENGTH, suffix: str = "…") -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def bold(text: str) -> str:
    return f"<b>{escape_html(text)}</b>"


def italic(text: str) -> str:
    return f"<i>{escape_html(text)}</i>"


def code(text: str) -> str:
    return f"<code>{escape_html(text)}</code>"
