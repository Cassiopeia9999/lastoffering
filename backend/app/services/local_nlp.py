from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence

try:
    import jieba  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    jieba = None


STOPWORDS = {
    "我",
    "我的",
    "一个",
    "一只",
    "一把",
    "一台",
    "一副",
    "一张",
    "那个",
    "这个",
    "可能",
    "应该",
    "就是",
    "然后",
    "一下",
    "最近",
    "今天",
    "昨天",
    "前天",
    "上午",
    "下午",
    "晚上",
    "中午",
    "附近",
    "里面",
    "外面",
    "那里",
    "这里",
    "东西",
    "物品",
    "时候",
    "可以",
    "帮我",
}

FEATURE_PATTERNS = [
    r"(?:有|带|挂着|挂了)([^，。；,;\n]{1,12}(?:挂件|贴纸|壳|钥匙扣|吊坠|绳子|保护套|卡套))",
    r"((?:透明|磨砂|金属|塑料|皮质|布艺|纯色|条纹|格子)[^，。；,;\n]{0,8}(?:外壳|保护壳|壳|背带|挂绳|卡套|书套))",
    r"((?:有点|明显|轻微)?[^，。；,;\n]{0,8}(?:划痕|磨损|裂痕|污渍|掉漆|磕碰|折痕))",
    r"((?:双肩|单肩|斜挎|长柄|短柄|折叠|金属边框|圆框|方框)[^，。；,;\n]{0,10})",
]

TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9\+\-]{2,}")


@dataclass
class BM25Document:
    raw_text: str
    tokens: list[str]


def _fallback_tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def tokenize_text(text: str | None) -> list[str]:
    raw_text = (text or "").strip()
    if not raw_text:
        return []

    if jieba is not None:
        try:
            tokens = [token.strip() for token in jieba.lcut(raw_text) if token.strip()]
        except Exception:
            tokens = _fallback_tokenize(raw_text)
    else:
        tokens = _fallback_tokenize(raw_text)

    compact: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        normalized = token.strip().lower()
        if (
            not normalized
            or normalized in STOPWORDS
            or len(normalized) == 1
            or normalized in seen
        ):
            continue
        seen.add(normalized)
        compact.append(token.strip())
    return compact


def extract_feature_phrases(text: str | None) -> list[str]:
    raw_text = (text or "").strip()
    if not raw_text:
        return []

    matches: list[str] = []
    for pattern in FEATURE_PATTERNS:
        for match in re.finditer(pattern, raw_text, flags=re.IGNORECASE):
            phrase = next((group for group in match.groups() if group), "").strip(" ，。；,;")
            if phrase and phrase not in matches:
                matches.append(phrase)

    # Fallback: preserve short characteristic fragments around separators.
    if not matches:
        for segment in re.split(r"[，。；,;\n]", raw_text):
            segment = segment.strip()
            if 2 <= len(segment) <= 16 and any(
                keyword in segment for keyword in ["划痕", "贴纸", "挂件", "挂绳", "钥匙扣", "保护壳", "卡套", "磨损", "裂痕"]
            ):
                matches.append(segment)

    return matches[:4]


def build_bm25_documents(texts: Sequence[str | None]) -> list[BM25Document]:
    return [BM25Document(raw_text=(text or ""), tokens=tokenize_text(text)) for text in texts]


def bm25_score(query_tokens: Sequence[str], documents: Sequence[BM25Document], index: int, k1: float = 1.5, b: float = 0.75) -> float:
    if not query_tokens or not documents:
        return 0.0

    total_len = sum(len(doc.tokens) for doc in documents) or 1
    avgdl = total_len / len(documents)
    current_tokens = documents[index].tokens
    if not current_tokens:
        return 0.0

    score = 0.0
    current_counter = Counter(token.lower() for token in current_tokens)
    for token in query_tokens:
        normalized = token.lower()
        freq = current_counter.get(normalized, 0)
        if not freq:
            continue
        doc_freq = sum(1 for doc in documents if normalized in {item.lower() for item in doc.tokens})
        idf = math.log(1 + (len(documents) - doc_freq + 0.5) / (doc_freq + 0.5))
        denom = freq + k1 * (1 - b + b * len(current_tokens) / (avgdl or 1))
        score += idf * (freq * (k1 + 1)) / (denom or 1)
    return round(score, 4)


def normalize_bm25_scores(scores: Iterable[float]) -> list[float]:
    values = list(scores)
    if not values:
        return []
    max_score = max(values)
    if max_score <= 0:
        return [0.0 for _ in values]
    return [round(value / max_score, 4) for value in values]
