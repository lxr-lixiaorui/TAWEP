from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from backend.api.deps import require_admin
from backend.core.config import get_settings
from backend.db.session import get_db
from backend.models import (
    AdminAuditLog,
    AnswerSession,
    AuthSession,
    CreditLedger,
    CreditWallet,
    EmailOutbox,
    EvaluationReport,
    InboxMessage,
    Question,
    QuestionMessage,
    QuestionSource,
    ReportFeedback,
    ReviewStatus,
    Topic,
    UploadedQuestionReview,
    User,
    UserRole,
    UserStatus,
)
from backend.schemas import (
    APIMessage,
    AdminAccountAction,
    AdminAccountDelete,
    AdminAccountOut,
    AdminCreditAdjustment,
    AdminMessageCreate,
    AdminQuestionCreate,
    AdminQuestionOut,
    AdminQuestionReviewOut,
    AdminQuestionUpdate,
    AdminReportFeedbackOut,
    AdminReviewDecision,
    AdminUserCreate,
    QuestionCreate,
    QuestionMessageOut,
)
from backend.services.authentication import hash_password, normalize_email, now_utc
from backend.services.practice import ensure_user_wallet
from backend.services.questions import apply_question_messages, next_question_number, resolve_topic


router = APIRouter(dependencies=[Depends(require_admin)])
settings = get_settings()


def _audit(
    admin: User,
    action: str,
    target_id: UUID,
    payload: dict | None = None,
    *,
    target_type: str = "user",
) -> AdminAuditLog:
    return AdminAuditLog(
        admin_id=admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload or {},
    )


async def _target_user(db: AsyncSession, user_id: UUID, *, lock: bool = False) -> User:
    statement = select(User).where(User.id == user_id)
    if lock:
        statement = statement.with_for_update()
    user = await db.scalar(statement)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _protect_admin_change(db: AsyncSession, admin: User, target: User) -> None:
    if target.id == admin.id:
        raise HTTPException(status_code=409, detail="You cannot disable or delete your own administrator account")
    if target.role == UserRole.admin and target.status == UserStatus.active:
        active_admins = await db.scalar(
            select(func.count()).select_from(User).where(User.role == UserRole.admin, User.status == UserStatus.active)
        )
        if int(active_admins or 0) <= 1:
            raise HTTPException(status_code=409, detail="The last active administrator cannot be removed")


def _question_statement():
    return select(Question).options(joinedload(Question.topic), selectinload(Question.messages))


async def _question_by_id(db: AsyncSession, question_id: UUID, *, lock: bool = False) -> Question:
    if lock:
        locked_id = await db.scalar(select(Question.id).where(Question.id == question_id).with_for_update())
        if locked_id is None:
            raise HTTPException(status_code=404, detail="Question not found")
    statement = _question_statement().where(Question.id == question_id)
    question = await db.scalar(statement)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


def _admin_question_out(
    question: Question,
    creator: User | None,
    session_count: int = 0,
) -> AdminQuestionOut:
    return AdminQuestionOut(
        id=question.id,
        question_no=question.question_no,
        source=question.source.value,
        status=question.status.value,
        topic=question.topic.name_en,
        topic_key=question.topic.key,
        exam_type=question.exam_type,
        difficulty=question.difficulty,
        summary=question.summary,
        avg_score=float(question.avg_score) if question.avg_score is not None else None,
        word_count=question.word_count,
        creator_id=question.creator_user_id,
        creator_alias=creator.alias if creator else None,
        creator_email=creator.email if creator else None,
        session_count=session_count,
        messages=[
            QuestionMessageOut(
                speaker_role=message.speaker_role,
                speaker_name=message.speaker_name,
                content=message.content,
                sort_order=message.sort_order,
            )
            for message in sorted(question.messages, key=lambda item: item.sort_order)
        ],
        created_at=question.created_at,
    )


async def _question_context(
    db: AsyncSession,
    questions: list[Question],
) -> tuple[dict[UUID, User], dict[UUID, int]]:
    creator_ids = {question.creator_user_id for question in questions if question.creator_user_id}
    creators = {}
    if creator_ids:
        creator_rows = (await db.scalars(select(User).where(User.id.in_(creator_ids)))).all()
        creators = {user.id: user for user in creator_rows}
    counts = {}
    if questions:
        count_rows = (
            await db.execute(
                select(AnswerSession.question_id, func.count(AnswerSession.id))
                .where(AnswerSession.question_id.in_([question.id for question in questions]))
                .group_by(AnswerSession.question_id)
            )
        ).all()
        counts = {question_id: int(count) for question_id, count in count_rows}
    return creators, counts


def _question_payload_from_admin(payload: AdminQuestionCreate) -> QuestionCreate:
    return QuestionCreate(
        topic=payload.topic,
        exam_type=payload.exam_type,
        difficulty=payload.difficulty,
        student_a_name=payload.student_a_name,
        student_a_content=payload.student_a_content,
        student_b_name=payload.student_b_name,
        student_b_content=payload.student_b_content,
        professor_name=payload.professor_name,
        professor_content=payload.professor_content,
    )


def _question_notice(question: Question, decision: ReviewStatus, comment: str | None) -> tuple[str, str]:
    decision_text = decision.value
    title = f"Your uploaded question was {decision_text}"
    body = f"Question #{question.question_no}, {question.summary}, was {decision_text}."
    if comment:
        body += f" Reviewer note: {comment.strip()}"
    return title, body


@router.get("/accounts", response_model=list[AdminAccountOut])
async def accounts(db: AsyncSession = Depends(get_db)) -> list[AdminAccountOut]:
    rows = (
        await db.execute(
            select(User, CreditWallet.balance)
            .outerjoin(CreditWallet, CreditWallet.user_id == User.id)
            .order_by(User.created_at.desc())
        )
    ).all()
    return [
        AdminAccountOut(
            id=user.id,
            email=user.email,
            alias=user.alias,
            role=user.role.value,
            status=user.status.value,
            credit=int(balance or 0),
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
        )
        for user, balance in rows
    ]


@router.post("/accounts", response_model=AdminAccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AdminUserCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAccountOut:
    email = normalize_email(str(payload.email))
    encoded_password = hash_password(payload.password)
    async with db.begin():
        if await db.scalar(select(User.id).where(User.email == email)) is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        user = User(
            email=email,
            password_hash=encoded_password,
            alias=payload.alias.strip(),
            role=UserRole(payload.role),
            status=UserStatus.active,
            preferred_locale=payload.preferred_locale,
            theme="light",
            email_verified_at=now_utc(),
        )
        db.add(user)
        await db.flush()
        wallet = CreditWallet(
            user_id=user.id,
            balance=settings.initial_credit,
            weekly_limit=settings.weekly_credit_limit,
            weekly_used=0,
            weekly_window_start=now_utc(),
            total_planned_credit=settings.initial_credit,
        )
        db.add(wallet)
        db.add(
            InboxMessage(
                user_id=user.id,
                title="Account created by an administrator",
                body="Your TAWEP account is active. Change the temporary password using password reset after email delivery is configured.",
                type="system",
            )
        )
        db.add(_audit(admin, "account.create", user.id, {"email": email, "role": payload.role}))
        await db.flush()
        return AdminAccountOut(
            id=user.id,
            email=user.email,
            alias=user.alias,
            role=user.role.value,
            status=user.status.value,
            credit=wallet.balance,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
        )


@router.delete("/accounts/{user_id}", response_model=APIMessage)
async def delete_account(
    user_id: UUID,
    payload: AdminAccountDelete,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        target = await _target_user(db, user_id, lock=True)
        await _protect_admin_change(db, admin, target)
        if normalize_email(str(payload.confirm_email)) != normalize_email(target.email):
            raise HTTPException(status_code=422, detail="Confirmation email does not match the target account")
        target_email = target.email
        db.add(_audit(admin, "account.delete", target.id, {"email": target_email, "role": target.role.value}))
        await db.execute(delete(EmailOutbox).where(EmailOutbox.user_id == target.id))
        await db.execute(delete(User).where(User.id == target.id))
    return APIMessage(message=f"Account {target_email} was permanently deleted")


@router.patch("/accounts/{user_id}/ban", response_model=APIMessage)
async def ban_account(
    user_id: UUID,
    payload: AdminAccountAction,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        target = await _target_user(db, user_id, lock=True)
        await _protect_admin_change(db, admin, target)
        target.status = UserStatus.banned
        target.token_version += 1
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == target.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now_utc())
        )
        db.add(_audit(admin, "account.ban", target.id, {"comment": payload.comment}))
    return APIMessage(message=f"Account {target.email} was banned")


@router.patch("/accounts/{user_id}/unban", response_model=APIMessage)
async def unban_account(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        target = await _target_user(db, user_id, lock=True)
        target.status = UserStatus.active if target.email_verified_at else UserStatus.pending
        db.add(_audit(admin, "account.unban", target.id))
    return APIMessage(message=f"Account {target.email} was restored")


@router.post("/accounts/{user_id}/messages", response_model=APIMessage)
async def send_account_message(
    user_id: UUID,
    payload: AdminMessageCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        target = await _target_user(db, user_id)
        db.add(InboxMessage(user_id=target.id, title=payload.title, body=payload.body, type="admin"))
        db.add(_audit(admin, "account.message", target.id, {"title": payload.title}))
    return APIMessage(message=f"Message sent to {target.email}")


@router.post("/accounts/{user_id}/credits", response_model=APIMessage)
async def adjust_account_credits(
    user_id: UUID,
    payload: AdminCreditAdjustment,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        target = await _target_user(db, user_id)
        await ensure_user_wallet(db, target.id)
        wallet = await db.get(CreditWallet, target.id, with_for_update=True)
        if wallet is None:
            raise HTTPException(status_code=500, detail="Credit wallet is missing")
        if wallet.balance + payload.delta < 0:
            raise HTTPException(status_code=409, detail="Credit balance cannot become negative")
        wallet.balance += payload.delta
        db.add(
            CreditLedger(
                user_id=target.id,
                delta=payload.delta,
                reason=payload.reason,
                admin_id=admin.id,
            )
        )
        db.add(_audit(admin, "account.credit", target.id, {"delta": payload.delta, "reason": payload.reason}))
    return APIMessage(message=f"Account balance is now {wallet.balance}")


@router.post("/login", response_model=APIMessage)
async def admin_login() -> APIMessage:
    return APIMessage(message="Use the normal authentication endpoint with an administrator account")


@router.get("/feedback", response_model=list[AdminReportFeedbackOut])
async def report_feedback(
    feedback_type: str | None = Query(default=None, pattern="^(too_high|too_low|other)$"),
    db: AsyncSession = Depends(get_db),
) -> list[AdminReportFeedbackOut]:
    statement = (
        select(ReportFeedback, User, AnswerSession, Question, EvaluationReport)
        .join(User, User.id == ReportFeedback.user_id)
        .join(EvaluationReport, EvaluationReport.id == ReportFeedback.report_id)
        .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
        .join(Question, Question.id == AnswerSession.question_id)
        .order_by(ReportFeedback.created_at.desc())
    )
    if feedback_type:
        statement = statement.where(ReportFeedback.feedback_type == feedback_type)
    rows = (await db.execute(statement)).all()
    return [
        AdminReportFeedbackOut(
            id=feedback.id,
            session_id=answer_session.id,
            question_no=question.question_no,
            user_id=user.id,
            user_alias=user.alias,
            user_email=user.email,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            consent_to_share=feedback.consent_to_share,
            answer_snapshot=feedback.answer_snapshot,
            report_snapshot=feedback.report_snapshot,
            total_score=float(evaluation_report.total_score),
            created_at=feedback.created_at,
        )
        for feedback, user, answer_session, question, evaluation_report in rows
    ]


@router.get("/questions", response_model=list[AdminQuestionOut])
async def manage_questions(
    source: str | None = Query(default=None, pattern="^(official|user)$"),
    question_status: str | None = Query(default=None, alias="status", pattern="^(pending|accepted|rejected)$"),
    topic: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AdminQuestionOut]:
    statement = _question_statement().order_by(Question.question_no.desc())
    if source:
        statement = statement.where(Question.source == QuestionSource(source))
    if question_status:
        statement = statement.where(Question.status == ReviewStatus(question_status))
    if topic:
        statement = statement.join(Topic).where(Topic.name_en == topic)
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(Question.summary.ilike(term))
    questions = list((await db.scalars(statement)).all())
    creators, counts = await _question_context(db, questions)
    return [
        _admin_question_out(question, creators.get(question.creator_user_id), counts.get(question.id, 0))
        for question in questions
    ]


@router.post("/questions", response_model=AdminQuestionOut, status_code=status.HTTP_201_CREATED)
async def create_official_question(
    payload: AdminQuestionCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionOut:
    async with db.begin():
        topic = await resolve_topic(db, payload.topic)
        if topic is None:
            raise HTTPException(status_code=422, detail="Unknown topic")
        question = Question(
            question_no=await next_question_number(db),
            source=QuestionSource.official,
            topic_id=topic.id,
            exam_type=payload.exam_type,
            difficulty=payload.difficulty,
            summary=payload.summary.strip(),
            status=ReviewStatus(payload.status),
            messages=[],
        )
        apply_question_messages(question, _question_payload_from_admin(payload))
        db.add(question)
        await db.flush()
        db.add(
            _audit(
                admin,
                "question.create",
                question.id,
                {"question_no": question.question_no, "source": "official"},
                target_type="question",
            )
        )
    question = await _question_by_id(db, question.id)
    return _admin_question_out(question, None)


@router.patch("/questions/{question_id}", response_model=AdminQuestionOut)
async def update_question(
    question_id: UUID,
    payload: AdminQuestionUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminQuestionOut:
    async with db.begin():
        question = await _question_by_id(db, question_id, lock=True)
        old_status = question.status
        if payload.topic is not None:
            topic = await resolve_topic(db, payload.topic)
            if topic is None:
                raise HTTPException(status_code=422, detail="Unknown topic")
            question.topic_id = topic.id
            question.topic = topic
        for field in ("exam_type", "difficulty", "summary"):
            value = getattr(payload, field)
            if value is not None:
                setattr(question, field, value.strip() if isinstance(value, str) else value)
        message_values = {
            "professor": (payload.professor_name, payload.professor_content),
            "student_a": (payload.student_a_name, payload.student_a_content),
            "student_b": (payload.student_b_name, payload.student_b_content),
        }
        by_role = {message.speaker_role: message for message in question.messages}
        for role, (name, content) in message_values.items():
            message = by_role.get(role)
            if message is None:
                raise HTTPException(status_code=409, detail=f"Question is missing the {role} message")
            if name is not None:
                message.speaker_name = name.strip()
            if content is not None:
                message.content = content.strip()
        question.word_count = sum(len(message.content.split()) for message in question.messages)
        if payload.status is not None:
            if old_status != ReviewStatus.pending and payload.status == ReviewStatus.pending.value:
                raise HTTPException(status_code=409, detail="A completed review cannot be moved back to pending")
            question.status = ReviewStatus(payload.status)
        if question.source == QuestionSource.user and question.status != old_status:
            if question.status == ReviewStatus.rejected and not (payload.review_comment or "").strip():
                raise HTTPException(status_code=422, detail="A rejection reason is required")
            review = await db.scalar(
                select(UploadedQuestionReview)
                .where(UploadedQuestionReview.question_id == question.id)
                .with_for_update()
            )
            if review is None:
                review = UploadedQuestionReview(question_id=question.id)
                db.add(review)
            review.status = question.status
            review.reviewer_id = admin.id
            review.comment = payload.review_comment
            review.reviewed_at = now_utc()
            if question.creator_user_id:
                title, body = _question_notice(question, question.status, payload.review_comment)
                db.add(InboxMessage(user_id=question.creator_user_id, title=title, body=body, type="moderation"))
        db.add(
            _audit(
                admin,
                "question.update",
                question.id,
                {"question_no": question.question_no, "status": question.status.value},
                target_type="question",
            )
        )
    question = await _question_by_id(db, question.id)
    creator = await db.get(User, question.creator_user_id) if question.creator_user_id else None
    session_count = int(
        await db.scalar(select(func.count(AnswerSession.id)).where(AnswerSession.question_id == question.id)) or 0
    )
    return _admin_question_out(question, creator, session_count)


@router.delete("/questions/{question_id}", response_model=APIMessage)
async def delete_question(
    question_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        question = await _question_by_id(db, question_id, lock=True)
        session_count = int(
            await db.scalar(select(func.count(AnswerSession.id)).where(AnswerSession.question_id == question.id)) or 0
        )
        if session_count:
            raise HTTPException(
                status_code=409,
                detail="This question has answer sessions and cannot be deleted. Set its status to rejected instead.",
            )
        question_no = question.question_no
        db.add(
            _audit(
                admin,
                "question.delete",
                question.id,
                {"question_no": question_no, "source": question.source.value},
                target_type="question",
            )
        )
        await db.execute(delete(UploadedQuestionReview).where(UploadedQuestionReview.question_id == question.id))
        await db.execute(delete(QuestionMessage).where(QuestionMessage.question_id == question.id))
        await db.execute(delete(Question).where(Question.id == question.id))
    return APIMessage(message=f"Question #{question_no} was permanently deleted")


@router.get("/review-questions", response_model=list[AdminQuestionReviewOut])
async def review_questions(
    review_status: str | None = Query(default="pending", alias="status", pattern="^(pending|accepted|rejected)$"),
    db: AsyncSession = Depends(get_db),
) -> list[AdminQuestionReviewOut]:
    statement = (
        select(UploadedQuestionReview)
        .join(Question, Question.id == UploadedQuestionReview.question_id)
        .order_by(Question.created_at.desc())
    )
    if review_status:
        statement = statement.where(UploadedQuestionReview.status == ReviewStatus(review_status))
    reviews = list((await db.scalars(statement)).all())
    question_ids = [review.question_id for review in reviews]
    questions = []
    if question_ids:
        questions = list((await db.scalars(_question_statement().where(Question.id.in_(question_ids)))).all())
    questions_by_id = {question.id: question for question in questions}
    creators, counts = await _question_context(db, questions)
    reviewer_ids = {review.reviewer_id for review in reviews if review.reviewer_id}
    reviewers = {}
    if reviewer_ids:
        reviewer_rows = (await db.scalars(select(User).where(User.id.in_(reviewer_ids)))).all()
        reviewers = {user.id: user for user in reviewer_rows}
    return [
        AdminQuestionReviewOut(
            review_id=review.id,
            question=_admin_question_out(
                questions_by_id[review.question_id],
                creators.get(questions_by_id[review.question_id].creator_user_id),
                counts.get(review.question_id, 0),
            ),
            reviewer_id=review.reviewer_id,
            reviewer_alias=reviewers.get(review.reviewer_id).alias if review.reviewer_id in reviewers else None,
            status=review.status.value,
            comment=review.comment,
            reviewed_at=review.reviewed_at,
        )
        for review in reviews
        if review.question_id in questions_by_id
    ]


async def _decide_question(
    question_id: UUID,
    payload: AdminReviewDecision,
    decision: ReviewStatus,
    admin: User,
    db: AsyncSession,
) -> APIMessage:
    comment = payload.comment.strip() if payload.comment else None
    if decision == ReviewStatus.rejected and not comment:
        raise HTTPException(status_code=422, detail="A rejection reason is required")
    async with db.begin():
        question = await _question_by_id(db, question_id, lock=True)
        if question.source != QuestionSource.user:
            raise HTTPException(status_code=409, detail="Only user-created questions use the review workflow")
        review = await db.scalar(
            select(UploadedQuestionReview)
            .where(UploadedQuestionReview.question_id == question.id)
            .with_for_update()
        )
        if review is None:
            raise HTTPException(status_code=409, detail="Question has no review record")
        if review.status != ReviewStatus.pending:
            raise HTTPException(status_code=409, detail=f"Question has already been {review.status.value}")
        question.status = decision
        review.status = decision
        review.reviewer_id = admin.id
        review.comment = comment
        review.reviewed_at = now_utc()
        if question.creator_user_id:
            title, body = _question_notice(question, decision, comment)
            db.add(InboxMessage(user_id=question.creator_user_id, title=title, body=body, type="moderation"))
        db.add(
            _audit(
                admin,
                f"question.{decision.value}",
                question.id,
                {"question_no": question.question_no, "comment": comment},
                target_type="question",
            )
        )
    return APIMessage(message=f"Question #{question.question_no} was {decision.value}")


@router.post("/review-questions/{question_id}/accept", response_model=APIMessage)
async def accept_question(
    question_id: UUID,
    payload: AdminReviewDecision,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    return await _decide_question(question_id, payload, ReviewStatus.accepted, admin, db)


@router.post("/review-questions/{question_id}/reject", response_model=APIMessage)
async def reject_question(
    question_id: UUID,
    payload: AdminReviewDecision,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    return await _decide_question(question_id, payload, ReviewStatus.rejected, admin, db)
