from copy import deepcopy


LEGAL_UPDATED_AT = "2026-07-16"
TERMS_VERSION = "2026-07-16"
PRIVACY_VERSION = "2026-07-15"
CROSS_BORDER_VERSION = "2026-07-15"
MODEL_IMPROVEMENT_VERSION = "2026-07-15"
THIRD_PARTY_AI_VERSION = "2026-07-15"
QUESTION_RIGHTS_VERSION = "2026-07-16"
CREDIT_EXPLANATION_VERSION = "2026-07-17"


def _document(title: str, summary: str, version: str, sections: list[dict]) -> dict:
    return {
        "title": title,
        "summary": summary,
        "version": version,
        "updated_at": LEGAL_UPDATED_AT,
        "sections": sections,
    }


DOCUMENTS: dict[str, dict[str, dict]] = {
    "terms": {
        "en": _document(
            "TAWEP (TOEFL Academic Discussion Evaluation Project) User Service Agreement",
            "The rules governing accounts, writing evaluation, AI-generated content, and acceptable use.",
            TERMS_VERSION,
            [
                {"heading": "1. Operator and agreement", "paragraphs": ["TAWEP (TOEFL Academic Discussion Evaluation Project) is operated by the owner of tawep.org (the Operator). Account and privacy requests may be sent to authissue@tawep.org; product feedback and complaints may be sent to feedback@tawep.org. By registering, you enter into this agreement with the Operator."]},
                {"heading": "2. Service", "paragraphs": ["TAWEP provides writing prompts, practice sessions, AI-estimated scores, grammar analysis, reports, and AI rewrites. Features may change as the project develops. Credits are service-use units, have no cash value, and are not transferable or redeemable. New accounts currently receive 45 credits without a weekly usage limit. An uploaded question that passes administrator review currently earns its contributor a one-time reward of 60 credits."]},
                {"heading": "3. Accounts", "bullets": ["Provide a reachable email address and accurate registration information.", "Protect passwords, verification codes, and API keys; do not share or resell accounts.", "We may restrict automated registrations, attacks, abuse, attempts to bypass limits, or other unlawful activity."]},
                {"heading": "4. Minors", "paragraphs": ["A person under 14 may not register independently. Until TAWEP provides a verified guardian-consent flow, registration by users under 14 is not available. Users aged 14 to 17 should use TAWEP only after a guardian has reviewed and agreed to these terms. Minors must not submit identity documents, exact addresses, school-class details, biometric data, or other unnecessary sensitive information."]},
                {"heading": "5. AI service statement", "bullets": ["Scores and comments are AI estimates for practice only, not official test results or professional advice.", "AI output can omit errors, misjudge language, change meaning, or vary between runs; review it before use.", "AI-generated or materially AI-rewritten content may carry required labels and must not be misrepresented as wholly independent work.", "Do not use TAWEP for examination cheating, academic misconduct, fraud, impersonation, or infringement."]},
                {"heading": "6. User content", "paragraphs": ["You retain rights you lawfully hold in your writing. You grant TAWEP a non-exclusive, purpose-limited permission to store, process, display to you, back up, and generate requested reports. Public question submissions require a separate rights confirmation. TAWEP will not use your writing for model improvement unless you separately opt in.", "You are responsible for the source, authorization, and legality of questions you submit. If TAWEP receives a rights complaint or identifies a material compliance risk, it may temporarily archive the question and stop displaying or using it while sending notice to your registered email. You have 7 calendar days from that notice to respond with an explanation or evidence of rights. If you do not respond in time, the question will remain archived; TAWEP may act sooner where law, a valid notice, examination security, or an urgent risk requires it."]},
                {"heading": "7. Third-party services", "paragraphs": ["Platform-funded evaluation currently uses DeepSeek. If you configure another OpenAI-compatible endpoint, you must review that provider's terms and privacy rules. TAWEP does not accept third-party terms on your behalf. Personal APIs still consume TAWEP credits because reports, answer pages, storage, moderation, and server resources remain part of the service."]},
                {"heading": "8. Intellectual property and independence", "paragraphs": ["TAWEP code is governed by the repository license; that license does not automatically cover trademarks, user content, question data, or third-party materials. TOEFL is a registered trademark of ETS. TAWEP is an independent project and is not affiliated with, sponsored, endorsed, or approved by ETS."]},
                {"heading": "9. Availability and liability", "paragraphs": ["We use reasonable measures to operate the service but do not promise uninterrupted or error-free availability. Nothing in this agreement excludes liability that cannot lawfully be excluded. Users remain responsible for reviewing outputs and protecting their credentials."]},
                {"heading": "10. Changes and disputes", "paragraphs": ["Material changes will be notified prominently. Continued silence will not replace a new consent where law requires one. This agreement is governed by the laws of Mainland China, and disputes should first be resolved through good-faith consultation before submission to a court with lawful jurisdiction."]},
            ],
        ),
        "zh": _document(
            "TAWEP（TOEFL Academic Discussion Evaluation Project）用户服务协议",
            "适用于账户、写作评估、人工智能生成内容及用户行为的服务规则。",
            TERMS_VERSION,
            [
                {"heading": "一、运营主体与协议成立", "paragraphs": ["TAWEP（TOEFL Academic Discussion Evaluation Project）由 tawep.org 网站所有者（以下简称“运营方”）运营。账户及隐私事项请联系 authissue@tawep.org，产品反馈及投诉请联系 feedback@tawep.org。用户完成注册即与运营方订立本协议。"]},
                {"heading": "二、服务内容", "paragraphs": ["TAWEP 提供写作题目、练习会话、AI 预估评分、语法分析、报告和 AI Rewrite 等功能。功能可能随开发进度调整。Credits 仅为服务使用额度，不具有现金价值，不可兑换、出售或转让。新账户当前获得 45 credits，不设每周使用上限；用户上传的题目通过管理员审核后，贡献者当前可获得一次性 60 credits 奖励。"]},
                {"heading": "三、账户规则", "bullets": ["使用可以正常接收邮件的地址注册，并提供真实、合法的信息。", "妥善保管密码、验证码及 API Key，不得共享、出租或转售账户。", "运营方可以限制批量注册、攻击、滥用、绕过额度限制或其他违法行为。"]},
                {"heading": "四、未成年人流程", "paragraphs": ["不满十四周岁的用户不得独立注册。在 TAWEP 建立可核验的监护人同意流程前，暂不向不满十四周岁的用户开放注册。已满十四周岁但未满十八周岁的用户，应当由监护人阅读并同意本协议后使用。未成年人不得提交身份证件、精确住址、学校班级、生物识别信息或其他非必要敏感信息。"]},
                {"heading": "五、人工智能服务声明", "bullets": ["分数和评价是用于练习的 AI 预估结果，不是正式考试成绩或专业意见。", "AI 可能遗漏错误、误判语言、改变原意或在不同调用中给出不同结果，使用前应自行复核。", "AI 生成或实质性改写内容将按适用规则进行标识，用户不得将其虚假陈述为完全独立创作。", "不得将 TAWEP 用于考试作弊、学术不端、欺诈、冒用身份或侵权。"]},
                {"heading": "六、用户内容", "paragraphs": ["用户保留其依法享有的文章权利，并授予 TAWEP 为提供存储、处理、向用户展示、备份和生成报告所必需的非独占、限目的许可。公开上传题目需要单独确认权利。除非用户另行主动同意，TAWEP 不会使用其文章改进评分模型。", "用户应对其上传题目的来源、授权情况及合法性负责。TAWEP 收到权利投诉或发现重大合规风险时，可以先将相关题目临时归档，停止展示和使用，并向用户注册邮箱发送通知。用户应在通知发出之日起 7 个自然日内回复说明或提交权利证明；逾期未回复的，相关题目将继续保持归档状态。法律、有效权利通知、考试安全或紧急风险要求更快处理的，TAWEP 可以立即采取必要措施。"]},
                {"heading": "七、第三方模型", "paragraphs": ["平台承担模型费用时当前使用 DeepSeek。用户设置其他 OpenAI-compatible endpoint 时，应自行阅读该提供商的条款和隐私规则，TAWEP 不代替用户接受第三方协议。个人 API 仍会消耗 TAWEP credits，因为报告、答题页面、数据存储、审核及服务器资源仍由平台提供。"]},
                {"heading": "八、知识产权及独立关系", "paragraphs": ["TAWEP 程序代码适用代码仓库载明的许可证；该许可证不当然适用于商标、用户内容、题库数据或第三方材料。TOEFL 是 ETS 的注册商标。TAWEP 是独立项目，与 ETS 不存在隶属、赞助、认可或授权关系。"]},
                {"heading": "九、服务可用性与责任", "paragraphs": ["运营方将采取合理措施维护服务，但不承诺服务永不中断或完全无误。本协议不排除法律规定不得排除的责任。用户应自行复核 AI 输出并保护账户凭证。"]},
                {"heading": "十、协议更新与争议", "paragraphs": ["重大变更将以显著方式通知；依法需要重新同意时，不以用户沉默替代。协议适用中国大陆法律，争议应先友好协商，协商不成时提交依法有管辖权的人民法院处理。"]},
            ],
        ),
    },
    "privacy": {
        "en": _document(
            "TAWEP (TOEFL Academic Discussion Evaluation Project) Privacy Policy",
            "How account, writing, report, security, and AI-processing data is handled.",
            PRIVACY_VERSION,
            [
                {"heading": "1. Controller and contact", "paragraphs": ["The owner of tawep.org determines TAWEP's personal-information processing. Contact authissue@tawep.org for access, correction, deletion, withdrawal, or account requests; use feedback@tawep.org for report feedback."]},
                {"heading": "2. Information processed", "bullets": ["Account data: email, alias, password hash, locale, theme, verification and login times.", "Practice data: selected question, answer text, timing, report, grammar annotations, score, and feedback.", "Security data: IP address, user agent, authentication sessions, audit records, and error logs.", "Personal API data: provider label, endpoint, model, encrypted API key, and key hint."]},
                {"heading": "3. Purposes", "paragraphs": ["We process data to create and secure accounts, deliver practice and reports, enforce credits, provide support, prevent abuse, meet legal obligations, and improve models only where separate optional consent has been given."]},
                {"heading": "4. AI providers", "paragraphs": ["For platform evaluation, the prompt, discussion, answer, and requested report language are provided to DeepSeek. For a personal API, those fields are provided to the provider and endpoint selected by you. Avoid including personal or sensitive information in writing submissions."]},
                {"heading": "5. Location and cross-border processing", "paragraphs": ["TAWEP's application and database servers are located in Hong Kong. Data submitted from Mainland China is therefore stored and processed outside Mainland China. A separate cross-border notice and consent is presented during registration."]},
                {"heading": "6. Retention and security", "paragraphs": ["Account and practice data is retained while the account remains active or as needed to provide requested history. Authentication sessions expire according to their configured lifetime. On valid deletion requests, data is deleted or anonymized unless law, security, accounting, dispute resolution, or abuse prevention requires limited retention. Passwords are hashed; personal API keys are encrypted at rest and are never returned in full by the API."]},
                {"heading": "7. Sharing and publication", "paragraphs": ["We do not publicly display private writing by default. We disclose data to model providers only to perform requested processing, to infrastructure providers as operationally necessary, or where law requires. Public question submissions are displayed only after the user's separate confirmation and administrator review."]},
                {"heading": "8. Your rights", "paragraphs": ["Subject to applicable law, you may request access, copy, correction, deletion, consent withdrawal, explanation, or account closure through authissue@tawep.org. Withdrawal does not affect processing already lawfully completed."]},
                {"heading": "9. Minors and updates", "paragraphs": ["TAWEP does not accept independent registration by children under 14 without a verified guardian flow. Material policy updates will be prominently notified and renewed consent will be obtained where required."]},
            ],
        ),
        "zh": _document(
            "TAWEP（TOEFL Academic Discussion Evaluation Project）隐私政策",
            "说明账户、文章、报告、安全日志及 AI 处理信息的处理方式。",
            PRIVACY_VERSION,
            [
                {"heading": "一、处理者与联系方式", "paragraphs": ["tawep.org 网站所有者决定 TAWEP 的个人信息处理活动。查询、复制、更正、删除、撤回同意或注销账户请联系 authissue@tawep.org；报告反馈请联系 feedback@tawep.org。"]},
                {"heading": "二、处理的信息", "bullets": ["账户信息：邮箱、昵称、密码哈希、语言、主题、验证及登录时间。", "练习信息：所选题目、文章、计时、报告、语法标注、评分和反馈。", "安全信息：IP 地址、User-Agent、登录会话、审计记录和错误日志。", "个人 API 信息：提供商名称、endpoint、模型、加密后的 API Key 及末位提示。"]},
                {"heading": "三、处理目的", "paragraphs": ["我们为创建并保护账户、提供练习和报告、执行 credits 规则、支持用户、防止滥用、履行法定义务而处理信息；仅在用户另行自愿同意后，才使用相关数据改进评分模型。"]},
                {"heading": "四、AI 服务商", "paragraphs": ["使用平台评分时，题目、讨论内容、用户文章及报告语言会提供给 DeepSeek。使用个人 API 时，上述信息会提供给用户选择的服务商和 endpoint。请勿在文章中填写个人或敏感信息。"]},
                {"heading": "五、存储地点与跨境处理", "paragraphs": ["TAWEP 应用及数据库服务器位于香港。来自中国大陆的数据因此会在中国大陆境外存储和处理。注册时将另行展示跨境处理告知并取得单独同意。"]},
                {"heading": "六、保存与安全", "paragraphs": ["账户及练习数据在账户有效期间或提供历史记录所需期限内保存；登录会话按配置期限失效。收到有效删除请求后，除法律、安全、审计、争议处理或防止滥用所需的有限保留外，数据将被删除或匿名化。密码使用哈希保存；个人 API Key 加密存储，接口不会返回完整明文。"]},
                {"heading": "七、共享与公开", "paragraphs": ["平台默认不公开用户文章。仅为完成用户请求向模型服务商提供必要数据，或在运营基础设施和法律要求的必要范围内提供数据。公开题目仅在用户单独确认并经管理员审核后展示。"]},
                {"heading": "八、用户权利", "paragraphs": ["在适用法律范围内，用户可以通过 authissue@tawep.org 请求查询、复制、更正、删除、撤回同意、获取解释或注销账户。撤回同意不影响此前已合法完成的处理。"]},
                {"heading": "九、未成年人及更新", "paragraphs": ["在建立可核验的监护人流程前，TAWEP 不接受不满十四周岁用户独立注册。重大政策更新将显著通知，并在法律要求时重新取得同意。"]},
            ],
        ),
    },
    "cross-border": {
        "en": _document("Cross-border Processing Notice", "Separate notice for storage and processing on TAWEP servers in Hong Kong.", CROSS_BORDER_VERSION, [{"heading": "Storage in Hong Kong", "paragraphs": ["You separately agree that the account, practice, report, consent, and security information described in the Privacy Policy may be transmitted to and stored on TAWEP servers in Hong Kong for account operation, writing evaluation, report history, security, and support. The recipient is the owner of tawep.org and may be contacted at authissue@tawep.org. You may withdraw consent or request deletion, but doing so may make the hosted service unavailable."]}]),
        "zh": _document("个人信息跨境处理告知书", "针对 TAWEP 香港服务器存储与处理的单独告知。", CROSS_BORDER_VERSION, [{"heading": "在香港存储与处理", "paragraphs": ["您单独同意将《隐私政策》所述账户、练习、报告、同意记录及安全信息传输至 TAWEP 位于香港的服务器并进行存储和处理，用于账户运行、写作评估、报告历史、安全保障和用户支持。境外接收方为 tawep.org 网站所有者，联系方式为 authissue@tawep.org。您可以撤回同意或请求删除，但撤回后可能无法继续使用托管服务。"]}]),
    },
    "third-party-ai": {
        "en": _document("Third-party AI Processing Consent", "Applies when you configure a personal OpenAI-compatible API.", THIRD_PARTY_AI_VERSION, [{"heading": "Data sent to your provider", "paragraphs": ["When personal API mode is enabled, TAWEP sends the selected question, discussion posts, your complete answer, report language, and evaluation instructions to the provider and endpoint displayed in Settings. The provider handles that data under its own terms and privacy rules. You are responsible for the endpoint and account, and should not include personal or sensitive information. TAWEP encrypts the key at rest and does not return it in full."]}]),
        "zh": _document("第三方 AI 处理同意书", "适用于用户配置个人 OpenAI-compatible API 的场景。", THIRD_PARTY_AI_VERSION, [{"heading": "向用户选择的服务商提供信息", "paragraphs": ["启用个人 API 后，TAWEP 会把所选题目、讨论内容、完整文章、报告语言和评分指令提供给 Settings 页面显示的服务商和 endpoint。第三方按照其自身条款和隐私规则处理数据，用户应对 endpoint 和账户合法性负责，并避免提交个人或敏感信息。TAWEP 对 API Key 进行加密存储，且不会通过接口返回完整明文。"]}]),
    },
    "question-publication": {
        "en": _document("Question Submission and Publication Statement", "Rights confirmation required before a community question is reviewed.", QUESTION_RIGHTS_VERSION, [{"heading": "Your confirmation", "paragraphs": ["You confirm that the submitted prompt and student perspectives are original or lawfully licensed, and authorize TAWEP to review, format, store, and publicly display them after approval. You are responsible for the source and must not submit official, leaked, copied, or restricted material in violation of ETS or any other institution's terms, copyright, trademark, confidentiality, or test-security rules. A source note or paraphrase does not itself create permission."]}, {"heading": "Rights complaints and archiving", "paragraphs": ["If TAWEP receives a rights complaint or identifies a material compliance risk, it may temporarily archive the question and stop displaying or using it while notifying you at your registered email. You have 7 calendar days from the notice to provide an explanation or evidence of rights. Without a timely response, the question will remain archived. TAWEP may take immediate or earlier action where required by law, a valid rights notice, examination security, or an urgent risk."]}]),
        "zh": _document("题目上传与公开声明", "社区题目进入审核前必须确认的权利声明。", QUESTION_RIGHTS_VERSION, [{"heading": "用户确认", "paragraphs": ["您确认上传的教授题干和学生观点为原创内容或已取得合法授权，并授权 TAWEP 在审核通过后进行格式整理、存储和公开展示。您应对题目来源负责，不得提交违反 ETS 或其他机构条款、著作权、商标权、保密义务或考试安全规则的官方、泄露、复制或受限制材料。标注“来源于网络”或进行改写本身不代表已经取得许可。"]}, {"heading": "权利投诉与归档处理", "paragraphs": ["TAWEP 收到权利投诉或发现重大合规风险时，可以先将相关题目临时归档，停止展示和使用，并向您的注册邮箱发送通知。您应在通知发出之日起 7 个自然日内回复说明或提交权利证明；逾期未回复的，相关题目将继续保持归档状态。法律、有效权利通知、考试安全或紧急风险要求更快处理的，TAWEP 可以立即采取必要措施。"]}]),
    },
    "model-improvement": {
        "en": _document("Optional Model Improvement Consent", "Optional use of de-identified writing and reports to improve evaluation quality.", MODEL_IMPROVEMENT_VERSION, [{"heading": "Optional processing", "paragraphs": ["If enabled, TAWEP may use de-identified copies of your writing, reports, grammar annotations, and feedback to evaluate and improve scoring quality. This is optional, is not required for registration, and can be withdrawn in Settings. TAWEP will remove direct account identifiers before this use and will not publicly publish your original writing through this consent."]}]),
        "zh": _document("模型改进可选同意书", "可选允许平台使用去标识化文章和报告改进评分质量。", MODEL_IMPROVEMENT_VERSION, [{"heading": "可选处理", "paragraphs": ["启用后，TAWEP 可以使用文章、报告、语法标注和反馈的去标识化副本评估并改进评分质量。本项完全自愿，不是注册条件，并可在 Settings 中撤回。平台将在该用途前移除直接账户标识，且不会依据本同意公开发布用户原文。"]}]),
    },
    "credit-explanation": {
        "en": _document("Credit Explanation", "How evaluation credits, contribution rewards, and personal APIs work.", CREDIT_EXPLANATION_VERSION, [{"heading": "Current rules", "bullets": ["A complete evaluation normally costs 3 credits.", "If an account has a planned exam date and that exam is 0–7 days away, including exam day, each evaluation costs 2 credits.", "New accounts receive 45 credits. Credits no longer have a weekly usage limit.", "When a user-created question passes administrator review, its contributor receives 60 credits. Each accepted question can be rewarded only once.", "A personal API does not remove the credit cost. TAWEP still provides the answer interface, report pipeline, storage, security controls, and server processing.", "If the remaining balance cannot cover an evaluation, TAWEP does not create a normal scored practice session.", "Credit history in Settings records grants, evaluation charges, refunds, and contribution rewards."]}]),
        "zh": _document("Credits 说明", "说明评分额度、贡献奖励及个人 API 的使用规则。", CREDIT_EXPLANATION_VERSION, [{"heading": "当前规则", "bullets": ["一次完整评估通常消耗 3 credits。", "账户填写计划考试日期后，距离考试还有 0–7 天时（含考试当天），每次评估只消耗 2 credits。", "新账户获得 45 credits；credits 不再设置每周使用上限。", "用户上传的题目通过管理员审核后，贡献者获得 60 credits；每道通过审核的题目只奖励一次。", "个人 API 不免除 credits 消耗；答题页面、报告流程、存储、安全控制和服务器处理仍由 TAWEP 提供。", "剩余余额不足以支付一次评估时，TAWEP 不会创建正常评分练习会话。", "设置页的 credit 记录会展示发放、评分消耗、失败退款和题目贡献奖励。"]}]),
    },
}


def normalize_legal_locale(locale: str) -> str:
    return "zh" if locale.lower().startswith("zh") else "en"


def get_document(slug: str, locale: str) -> dict | None:
    localized = DOCUMENTS.get(slug, {}).get(normalize_legal_locale(locale))
    if localized is None:
        return None
    result = deepcopy(localized)
    result["slug"] = slug
    return result


def list_documents(locale: str, *, cross_border_visible: bool = True) -> list[dict]:
    return [
        {key: value for key, value in get_document(slug, locale).items() if key in {"slug", "title", "summary", "version"}}
        for slug in DOCUMENTS
        if slug != "cross-border" or cross_border_visible
    ]


def require_version(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise ValueError(f"The {label} version is no longer current. Review the latest document and try again.")
