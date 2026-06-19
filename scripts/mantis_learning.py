"""Learning/research primitives for MANTIS launcher chat."""

from __future__ import annotations

import re
from html.parser import HTMLParser


class WebTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data or "").strip()
        if not text:
            return
        if self._in_title:
            self.title = (self.title + " " + text).strip()
        elif not self._skip_depth:
            self.chunks.append(text)

    def text(self, limit: int = 8000) -> str:
        return re.sub(r"\s+", " ", " ".join(self.chunks)).strip()[:limit]
