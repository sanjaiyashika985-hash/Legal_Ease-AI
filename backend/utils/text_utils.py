from html import escape


def text_to_html(text: str) -> str:
    paragraphs = [part for part in text.split("\n\n") if part.strip()]
    return "\n".join(
        f"<p>{'<br>'.join(escape(line) for line in paragraph.splitlines())}</p>"
        for paragraph in paragraphs
    )