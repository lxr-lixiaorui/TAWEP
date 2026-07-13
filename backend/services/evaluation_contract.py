import json
import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator


CriterionKey = Literal[
    "content_relevance",
    "perspective_expansion",
    "linguistic_expression",
    "logical_structure",
]

CRITERIA: tuple[CriterionKey, ...] = (
    "content_relevance",
    "perspective_expansion",
    "linguistic_expression",
    "logical_structure",
)
SECTION_ORDER = (
    "problems",
    "scores",
    "improvements",
    "ai_rewrite",
    "rewrite_comparison",
)
AI_REWRITE_ADAPTER = TypeAdapter(Annotated[str, Field(min_length=20, max_length=10000)])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProblemDetail(StrictModel):
    explanation: str = Field(min_length=10, max_length=1200)
    evidence_quote: str = Field(min_length=1, max_length=500)


class ProblemsSection(StrictModel):
    content_relevance: ProblemDetail
    perspective_expansion: ProblemDetail
    linguistic_expression: ProblemDetail
    logical_structure: ProblemDetail


class ScoresSection(StrictModel):
    content_relevance: float = Field(ge=0, le=5)
    perspective_expansion: float = Field(ge=0, le=5)
    linguistic_expression: float = Field(ge=0, le=5)
    logical_structure: float = Field(ge=0, le=5)


class ImprovementsSection(StrictModel):
    content_relevance: str = Field(min_length=10, max_length=1200)
    perspective_expansion: str = Field(min_length=10, max_length=1200)
    linguistic_expression: str = Field(min_length=10, max_length=1200)
    logical_structure: str = Field(min_length=10, max_length=1200)


class GrammarIssue(StrictModel):
    sentence_index: int = Field(ge=1)
    occurrence_index: int = Field(default=1, ge=1)
    original_text: str = Field(min_length=1, max_length=160)
    issue_type: Literal["grammar", "spelling", "wording"]
    explanation: str = Field(min_length=3, max_length=1000)
    suggestion: str = Field(min_length=1, max_length=240)

    @field_validator("original_text")
    @classmethod
    def require_minimal_annotation_span(cls, value: str) -> str:
        value = value.strip()
        word_count = len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", value))
        if word_count > 8:
            raise ValueError("original_text must be a minimal word or phrase of at most 8 words")
        if "\n" in value or "\r" in value:
            raise ValueError("original_text must not span multiple lines")
        return value

    @model_validator(mode="after")
    def require_actual_replacement(self) -> "GrammarIssue":
        original = re.sub(r"\s+", " ", self.original_text).strip()
        suggestion = re.sub(r"\s+", " ", self.suggestion).strip()
        if original == suggestion:
            raise ValueError("suggestion must differ from original_text")
        if self.issue_type == "spelling" and len(self.original_text.split()) != 1:
            raise ValueError("spelling annotations must target one misspelled token")
        return self


class RewriteHighlight(StrictModel):
    highlight_type: Literal["logic_connector", "logic_bridge", "removed_content", "core_expression"]
    original_text: str | None = Field(default=None, min_length=1, max_length=600)
    rewritten_text: str | None = Field(default=None, min_length=1, max_length=600)

    @field_validator("original_text", "rewritten_text", mode="before")
    @classmethod
    def normalize_empty_highlight_side(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def require_highlight_sides(self) -> "RewriteHighlight":
        if self.highlight_type == "removed_content":
            if not self.original_text or self.rewritten_text:
                raise ValueError("removed_content requires only original_text")
        elif self.highlight_type in {"logic_connector", "logic_bridge"}:
            if not self.rewritten_text:
                raise ValueError(f"{self.highlight_type} requires rewritten_text")
        elif not self.original_text or not self.rewritten_text:
            raise ValueError("core_expression requires original_text and rewritten_text")
        return self


class RewriteSection(StrictModel):
    role: Literal["position", "reasoning", "evidence", "conclusion"]
    original_text: str = Field(min_length=1, max_length=5000)
    rewritten_text: str = Field(min_length=1, max_length=5000)
    highlights: list[RewriteHighlight] = Field(default_factory=list, max_length=8)


class RewriteComparison(StrictModel):
    sections: list[RewriteSection] = Field(min_length=1, max_length=6)


class EvaluationPayload(StrictModel):
    problems: ProblemsSection
    scores: ScoresSection
    improvements: ImprovementsSection
    ai_rewrite: str = Field(min_length=20, max_length=10000)
    rewrite_comparison: RewriteComparison
    grammar_analysis: list[GrammarIssue] = Field(default_factory=list, max_length=80)


def normalize_locale(locale: str) -> str:
    normalized = locale.strip().replace("_", "-")
    aliases = {"zh": "zh-CN", "en-US": "en", "en-GB": "en"}
    return aliases.get(normalized, normalized)


def locale_name(locale: str) -> str:
    names = {
        "en": "English",
        "zh-CN": "Simplified Chinese",
        "zh-TW": "Traditional Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
    }
    return names.get(normalize_locale(locale), f"the language identified by locale {locale}")


def calculate_total_score(scores: ScoresSection) -> float:
    return round(
        scores.content_relevance * 0.3
        + scores.perspective_expansion * 0.2
        + scores.linguistic_expression * 0.3
        + scores.logical_structure * 0.2,
        1,
    )


def strongest_criterion(scores: ScoresSection) -> CriterionKey:
    values = scores.model_dump()
    return max(CRITERIA, key=lambda key: values[key])


def flatten_problems(problems: ProblemsSection) -> dict[str, str]:
    return {key: getattr(problems, key).explanation for key in CRITERIA}


def problem_evidence(problems: ProblemsSection) -> dict[str, str]:
    return {key: getattr(problems, key).evidence_quote for key in CRITERIA}


def _normalized_text(value: str) -> str:
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", value).strip().casefold()


def validate_rewrite_comparison(
    comparison: RewriteComparison,
    answer_text: str,
    ai_rewrite: str,
) -> None:
    original_sections = " ".join(section.original_text for section in comparison.sections)
    rewritten_sections = " ".join(section.rewritten_text for section in comparison.sections)
    if _normalized_text(original_sections) != _normalized_text(answer_text):
        raise ValueError("Rewrite comparison sections must reproduce the complete original answer")
    if _normalized_text(rewritten_sections) != _normalized_text(ai_rewrite):
        raise ValueError("Rewrite comparison sections must reproduce the complete AI rewrite")

    for section in comparison.sections:
        normalized_original = _normalized_text(section.original_text)
        normalized_rewrite = _normalized_text(section.rewritten_text)
        for highlight in section.highlights:
            if highlight.original_text and _normalized_text(highlight.original_text) not in normalized_original:
                raise ValueError("Rewrite highlight does not occur in its original section")
            if highlight.rewritten_text and _normalized_text(highlight.rewritten_text) not in normalized_rewrite:
                raise ValueError("Rewrite highlight does not occur in its rewritten section")


def validate_evidence(payload: EvaluationPayload, answer_text: str) -> None:
    normalized_answer = _normalized_text(answer_text)
    for key in CRITERIA:
        quote = getattr(payload.problems, key).evidence_quote
        if _normalized_text(quote) not in normalized_answer:
            raise ValueError(f"Evidence for {key} does not occur in the submitted answer")
    for issue in payload.grammar_analysis:
        if _normalized_text(issue.original_text) not in normalized_answer:
            raise ValueError(f"Grammar evidence does not occur in the submitted answer: {issue.original_text!r}")
    validate_rewrite_comparison(payload.rewrite_comparison, answer_text, payload.ai_rewrite)


def validate_section(
    name: str,
    value: Any,
    answer_text: str,
    ai_rewrite: str | None = None,
) -> dict | list | str:
    if name == "problems":
        section = ProblemsSection.model_validate(value)
        normalized_answer = _normalized_text(answer_text)
        for key in CRITERIA:
            quote = getattr(section, key).evidence_quote
            if _normalized_text(quote) not in normalized_answer:
                raise ValueError(f"Evidence for {key} does not occur in the submitted answer")
        return section.model_dump()
    if name == "scores":
        return ScoresSection.model_validate(value).model_dump()
    if name == "improvements":
        return ImprovementsSection.model_validate(value).model_dump()
    if name == "ai_rewrite":
        return AI_REWRITE_ADAPTER.validate_python(value)
    if name == "rewrite_comparison":
        comparison = RewriteComparison.model_validate(value)
        if ai_rewrite is not None:
            validate_rewrite_comparison(comparison, answer_text, ai_rewrite)
        return comparison.model_dump()
    if name == "grammar_analysis":
        issues: list[GrammarIssue] = []
        for item in value:
            try:
                issues.append(GrammarIssue.model_validate(item))
            except ValueError:
                continue
        normalized_answer = _normalized_text(answer_text)
        for issue in issues:
            if _normalized_text(issue.original_text) not in normalized_answer:
                raise ValueError(f"Grammar evidence does not occur in the submitted answer: {issue.original_text!r}")
        return [item.model_dump() for item in issues]
    raise ValueError(f"Unknown evaluation section: {name}")


def sanitize_model_payload(value: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(value)
    grammar_items: list[dict[str, Any]] = []
    for item in sanitized.get("grammar_analysis", []):
        try:
            grammar_items.append(GrammarIssue.model_validate(item).model_dump())
        except ValueError:
            continue
    sanitized["grammar_analysis"] = grammar_items
    return sanitized


def sentence_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for match in re.finditer(r"[^.!?]+(?:[.!?]+[\"']*|$)", text, flags=re.MULTILINE):
        start, end = match.span()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end:
            ranges.append((start, end))
    return ranges


def resolve_grammar_offsets(answer_text: str, issue: GrammarIssue) -> tuple[int | None, int | None]:
    ranges = sentence_ranges(answer_text)
    if issue.sentence_index > len(ranges):
        return None, None
    sentence_start, sentence_end = ranges[issue.sentence_index - 1]
    sentence = answer_text[sentence_start:sentence_end]
    needle = issue.original_text
    matches = [match.start() for match in re.finditer(re.escape(needle), sentence)]
    if not matches:
        matches = [match.start() for match in re.finditer(re.escape(needle), sentence, flags=re.IGNORECASE)]
    if len(matches) == 1:
        start = sentence_start + matches[0]
        return start, start + len(needle)
    if len(matches) < issue.occurrence_index:
        global_matches = [match.start() for match in re.finditer(re.escape(needle), answer_text)]
        if len(global_matches) == 1:
            return global_matches[0], global_matches[0] + len(needle)
        return None, None
    start = sentence_start + matches[issue.occurrence_index - 1]
    return start, start + len(needle)


class OrderedSectionExtractor:
    def __init__(self) -> None:
        self.buffer = ""
        self.search_from = 0
        self.next_index = 0
        self.decoder = json.JSONDecoder()

    def feed(self, content: str) -> list[tuple[str, Any]]:
        self.buffer += content
        completed: list[tuple[str, Any]] = []
        while self.next_index < len(SECTION_ORDER):
            name = SECTION_ORDER[self.next_index]
            marker = json.dumps(name)
            marker_at = self.buffer.find(marker, self.search_from)
            if marker_at < 0:
                break
            colon_at = self.buffer.find(":", marker_at + len(marker))
            if colon_at < 0:
                break
            value_at = colon_at + 1
            while value_at < len(self.buffer) and self.buffer[value_at].isspace():
                value_at += 1
            try:
                value, end_at = self.decoder.raw_decode(self.buffer, value_at)
            except json.JSONDecodeError:
                break
            completed.append((name, value))
            self.search_from = end_at
            self.next_index += 1
        return completed


def parse_final_json(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model response did not contain a JSON object")
    return json.loads(cleaned[start : end + 1])
