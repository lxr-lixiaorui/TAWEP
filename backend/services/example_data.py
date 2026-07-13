from datetime import datetime
from uuid import UUID

from backend.schemas import EvaluationJobOut, GrammarItemOut, ReportOut, ScoreComponentsOut


EXAMPLE_SESSION_ID = UUID("00000000-0000-4000-8000-000000000008")

EXAMPLE_ANSWER = (
    "I think small stores are better than super stores, and I agree with Andrew. "
    "First, small stores have more personal service, which is very helpfull. "
    "For example, when my phone broke last year, the guy at the local shop help me fix it in 10 minutes, "
    "and he even teach me how to prevent the problem again. "
    "At super stores, workers don't know you, and they can't give you such good advise. "
    "Also, small stores often have cheaper price for students, and they let you pay in cash or small parts. "
    "Super stores are too big, and it takes too long to find things. "
    "For busy students like me, sometimes we need quick help, not just low prices. "
    "That's why small stores is better for college life."
)

EXAMPLE_REWRITE = (
    "In my opinion, small stores offer more advantages than super stores, and I agree with Andrew. "
    "To begin with, small stores provide personalized service, which is extremely helpful. For instance, "
    "when my phone broke last year, the technician at the local shop helped me fix it in 10 minutes and "
    "even taught me how to prevent similar issues in the future. In contrast, workers at super stores "
    "rarely know their customers and cannot offer such tailored assistance. Moreover, small stores often "
    "have lower prices for students and allow flexible payment options, such as paying in installments or "
    "smaller amounts. Super stores are too large and time-consuming to navigate. For busy students like me, "
    "quick and attentive service matters more than just low prices. Therefore, small stores are better "
    "suited for college life."
)

EXAMPLE_REWRITE_COMPARISON = {
    "sections": [
        {
            "role": "position",
            "original_text": "I think small stores are better than super stores, and I agree with Andrew.",
            "rewritten_text": "In my opinion, small stores offer more advantages than super stores, and I agree with Andrew.",
            "highlights": [
                {
                    "highlight_type": "core_expression",
                    "original_text": "small stores are better than super stores",
                    "rewritten_text": "small stores offer more advantages than super stores",
                }
            ],
        },
        {
            "role": "reasoning",
            "original_text": "First, small stores have more personal service, which is very helpfull.",
            "rewritten_text": "To begin with, small stores provide personalized service, which is extremely helpful.",
            "highlights": [
                {
                    "highlight_type": "logic_connector",
                    "original_text": "First",
                    "rewritten_text": "To begin with",
                },
                {
                    "highlight_type": "core_expression",
                    "original_text": "have more personal service",
                    "rewritten_text": "provide personalized service",
                },
            ],
        },
        {
            "role": "evidence",
            "original_text": "For example, when my phone broke last year, the guy at the local shop help me fix it in 10 minutes, and he even teach me how to prevent the problem again.",
            "rewritten_text": "For instance, when my phone broke last year, the technician at the local shop helped me fix it in 10 minutes and even taught me how to prevent similar issues in the future.",
            "highlights": [],
        },
        {
            "role": "reasoning",
            "original_text": "At super stores, workers don't know you, and they can't give you such good advise. Also, small stores often have cheaper price for students, and they let you pay in cash or small parts. Super stores are too big, and it takes too long to find things.",
            "rewritten_text": "In contrast, workers at super stores rarely know their customers and cannot offer such tailored assistance. Moreover, small stores often have lower prices for students and allow flexible payment options, such as paying in installments or smaller amounts. Super stores are too large and time-consuming to navigate.",
            "highlights": [
                {
                    "highlight_type": "logic_connector",
                    "original_text": "At super stores",
                    "rewritten_text": "In contrast",
                },
                {
                    "highlight_type": "logic_bridge",
                    "original_text": None,
                    "rewritten_text": "such as paying in installments or smaller amounts",
                },
            ],
        },
        {
            "role": "conclusion",
            "original_text": "For busy students like me, sometimes we need quick help, not just low prices. That's why small stores is better for college life.",
            "rewritten_text": "For busy students like me, quick and attentive service matters more than just low prices. Therefore, small stores are better suited for college life.",
            "highlights": [
                {
                    "highlight_type": "logic_connector",
                    "original_text": "That's why",
                    "rewritten_text": "Therefore",
                }
            ],
        },
    ]
}


def build_example_report() -> ReportOut:
    components = ScoreComponentsOut(
        content_relevance=5.0,
        perspective_expansion=3.5,
        linguistic_expression=2.5,
        logical_structure=3.5,
    )
    return ReportOut(
        session_id=EXAMPLE_SESSION_ID,
        total_score=3.7,
        total_score_30=24,
        components=components,
        problems={
            "content_relevance": "The response fully addresses the prompt by comparing small stores and super stores. There is no major relevance problem.",
            "perspective_expansion": "The examples are specific but not developed deeply enough. The service example needs more detail, and the price/payment point is not fully explained.",
            "linguistic_expression": "There are several grammar, spelling, and word-form issues, including helpfull, help, teach, advise, cheaper price, and small parts.",
            "logical_structure": "The overall structure is understandable, but transitions between ideas are limited and some sentence connections feel abrupt.",
        },
        improvements={
            "content_relevance": "Keep the answer directly tied to the question and maintain this level of relevance.",
            "perspective_expansion": "Add more details about how staff understand customer needs, explain the price advantage clearly, and compare the disadvantages of super stores more directly.",
            "linguistic_expression": "Open Grammar Analysis to correct spelling, grammar, and wording issues in the original answer.",
            "logical_structure": "Use transition phrases such as To begin with, Furthermore, and Therefore. Add short concluding sentences after examples and connect them back to the main claim.",
        },
        ai_rewrite=EXAMPLE_REWRITE,
        rewrite_comparison=EXAMPLE_REWRITE_COMPARISON,
        report_html_url=f"/api/v1/sessions/{EXAMPLE_SESSION_ID}/download",
    )


def build_example_grammar() -> list[GrammarItemOut]:
    return [
        GrammarItemOut(
            sentence_index=2,
            original_text="helpfull",
            issue_type="spelling",
            explanation="Spelling error.",
            suggestion="helpful",
        ),
        GrammarItemOut(
            sentence_index=3,
            original_text="help",
            issue_type="grammar",
            explanation="Verb tense error. The sentence describes a past event.",
            suggestion="helped",
        ),
        GrammarItemOut(
            sentence_index=3,
            original_text="teach",
            issue_type="grammar",
            explanation="Verb tense error. The sentence describes a past event.",
            suggestion="taught",
        ),
        GrammarItemOut(
            sentence_index=4,
            original_text="advise",
            issue_type="grammar",
            explanation="Word form error. This sentence needs the noun form.",
            suggestion="advice",
        ),
        GrammarItemOut(
            sentence_index=5,
            original_text="cheaper price",
            issue_type="wording",
            explanation="Awkward comparative expression.",
            suggestion="lower prices",
        ),
        GrammarItemOut(
            sentence_index=5,
            original_text="small parts",
            issue_type="wording",
            explanation="Unclear expression for payment flexibility.",
            suggestion="installments or smaller amounts",
        ),
        GrammarItemOut(
            sentence_index=8,
            original_text="is",
            issue_type="grammar",
            explanation="Subject-verb agreement error. The subject is plural.",
            suggestion="are",
        ),
    ]


def build_example_evaluation_job() -> EvaluationJobOut:
    report = build_example_report()
    components = report.components.model_dump()
    strongest = max(components, key=components.get)
    created_at = datetime(2026, 6, 8, 8, 45, 40)
    return EvaluationJobOut(
        id=EXAMPLE_SESSION_ID,
        session_id=EXAMPLE_SESSION_ID,
        status="completed",
        stage="completed",
        report_locale="en",
        available_sections=[
            "problems",
            "scores",
            "total_score",
            "strongest_part",
            "improvements",
            "ai_rewrite",
            "rewrite_comparison",
            "grammar_analysis",
        ],
        partial_report={
            "problems": report.problems,
            "components": components,
            "total_score": report.total_score,
            "total_score_30": report.total_score_30,
            "strongest_part": strongest,
            "improvements": report.improvements,
            "ai_rewrite": report.ai_rewrite,
            "rewrite_comparison": report.rewrite_comparison,
            "grammar_analysis": [item.model_dump() for item in build_example_grammar()],
        },
        elapsed_seconds=0,
        estimated_min_seconds=120,
        estimated_max_seconds=210,
        attempt=1,
        max_attempts=1,
        created_at=created_at,
        completed_at=created_at,
    )
