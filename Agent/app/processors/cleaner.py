"""Text cleaning utilities for ingestion pipeline.
导入流水线的文本清洗工具。
"""

from __future__ import annotations

import re


_MULTI_BLANK_LINES_RE = re.compile(r"\n{3,}")
_MULTI_SPACES_RE = re.compile(r"[ \t]{2,}")
_CONTROL_CHARS_RE = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")


def clean_text(text: str) -> str:
    """Normalize noisy text from heterogeneous sources.
    标准化来自不同来源的噪声文本。
    """

    if not text:
        return ""

    normalized = str(text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00a0", " ")
    normalized = normalized.replace("\u200b", "")
    normalized = _CONTROL_CHARS_RE.sub("", normalized)

    lines = []
    for raw_line in normalized.split("\n"):
        line = _MULTI_SPACES_RE.sub(" ", raw_line).strip()
        lines.append(line)
    normalized = "\n".join(lines)
    normalized = _MULTI_BLANK_LINES_RE.sub("\n\n", normalized)
    return normalized.strip()
