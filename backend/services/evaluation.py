from uuid import UUID

from backend.schemas import GrammarItemOut, ReportOut, ScoreComponentsOut


def score_to_30(score_five: float) -> int:
    return round(score_five * 5 + 5)


def build_debug_report(session_id: UUID, answer_text: str) -> ReportOut:
    components = ScoreComponentsOut(
        content_relevance=4.0,
        perspective_expansion=3.8,
        linguistic_expression=3.5,
        logical_structure=3.8,
    )
    score_five = round(
        components.content_relevance * 0.3
        + components.perspective_expansion * 0.2
        + components.linguistic_expression * 0.3
        + components.logical_structure * 0.2,
        1,
    )
    return ReportOut(
        session_id=session_id,
        total_score=score_five,
        total_score_30=score_to_30(score_five),
        components=components,
        problems={
            "content_relevance": "The response addresses the prompt but needs a sharper position.",
            "perspective_expansion": "Examples should explain why the chosen view matters.",
            "linguistic_expression": "Some word choices are repetitive or too informal.",
            "logical_structure": "Transitions can better connect the two main points.",
        },
        improvements={
            "content_relevance": "State your position in the first sentence and return to it in the conclusion.",
            "perspective_expansion": "Use one concrete academic or social example to deepen the argument.",
            "linguistic_expression": "Replace repeated basic verbs with precise academic verbs.",
            "logical_structure": "Use a clear concession or contrast before the second reason.",
        },
        ai_rewrite=(
            "I believe this proposal is generally beneficial because it can improve access while encouraging "
            "students to think more independently. A well-designed policy would not only support immediate "
            "learning needs but also help learners develop habits that remain useful in academic settings."
        ),
        report_html_url=f"/api/v1/sessions/{session_id}/download",
    )


def build_debug_grammar(answer_text: str) -> list[GrammarItemOut]:
    first_sentence = answer_text.strip().split(".")[0] or "No answer text was submitted"
    return [
        GrammarItemOut(
            sentence_index=1,
            original_text=first_sentence,
            issue_type="wording",
            explanation="The opening sentence can be more precise and academic.",
            suggestion="Use a direct claim with a clear reason.",
        )
    ]
