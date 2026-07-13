import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    rewrite: {
      tab: 'AI Rewrite',
      entryTitle: 'See how the response was rebuilt',
      entryBody: 'Compare the rewrite with your original response by logical role and review only the changes that matter.',
      open: 'Open AI Rewrite',
      stage: 'Aligning the rewrite with your argument',
      title: 'AI Rewrite Comparison',
      subtitle: 'The two versions are aligned by their role in the argument. Fluorescent highlights show only meaningful structural and expressive changes.',
      aiVersion: 'AI Rewrite',
      originalVersion: 'Your Original',
      legendTitle: 'Highlight key',
      roles: {
        position: 'Position',
        reasoning: 'Reasoning',
        evidence: 'Evidence / Example',
        conclusion: 'Conclusion'
      },
      legend: {
        logicConnector: 'Logical connection',
        logicBridge: 'Added reasoning',
        removedContent: 'Removed content',
        coreExpression: 'Core expression'
      }
    },
    nav: {
      bank: 'Question Bank',
      example: 'Example Report',
      login: 'Login',
      dashboard: 'Dashboard',
      settings: 'Settings',
      inbox: 'Inbox'
    },
    actions: {
      start: 'Start Practice',
      upload: 'Upload your own',
      submit: 'Submit',
      save: 'Save'
    },
    report: {
      tabs: { answer: 'Answer Page', report: 'Report', grammar: 'Grammar Analysis', download: 'Download' },
      evaluating: 'Evaluating your response',
      ready: 'Report is ready',
      failed: 'Evaluation could not be completed',
      refunded: 'Your credits have been refunded. Start a new practice session to try again.',
      typical: 'Usually ready in 2–3 minutes',
      elapsed: 'elapsed',
      waiting: 'Waiting',
      evaluationReport: 'Evaluation Report',
      focusOn: 'Focus on {criterion}',
      focusThesis: 'This is the clearest place to improve your next answer. Fix this first, then review the full score breakdown below.',
      startHere: 'Start here',
      doNext: 'Do this next',
      question: 'Question {number}',
      totalScore: 'Total Score',
      converted: '{score} / 30 converted',
      strongestArea: 'Strongest Area',
      languageFlags: 'Language Flags',
      flagSummary: '{grammar} grammar · {spelling} spelling',
      breakdown: 'Breakdown',
      scoreByCriteria: 'Score by criteria',
      actionPlan: 'Action Plan',
      actionPlanByCriteria: 'Action plan by criteria',
      nextStep: 'Next Step',
      openGrammar: 'Open Grammar Analysis',
      aiRewrite: 'AI Rewrite',
      modelDirection: 'Model answer direction',
      grammarAnalysis: 'Grammar Analysis',
      interactiveReport: 'Interactive language report',
      yourAnswer: '> Your Answer',
      noAnswer: 'No answer text was submitted.',
      downloadReport: 'Download HTML Report',
      downloadWaiting: 'Download becomes available when evaluation is complete.',
      criteria: {
        content_relevance: 'Content Relevance',
        perspective_expansion: 'Perspectives Expansion',
        linguistic_expression: 'Linguistic Expression',
        logical_structure: 'Logical Structure'
      },
      stages: {
        queued: 'Waiting for the evaluator',
        problems: 'Identifying the four main issues',
        scores: 'Scoring each criterion',
        improvements: 'Building your action plan',
        ai_rewrite: 'Rewriting the response',
        grammar_analysis: 'Checking grammar and wording',
        finalizing: 'Finalizing the report',
        retrying: 'Checking the result again',
        completed: 'Report is ready',
        failed: 'Evaluation failed'
      }
    }
  },
  zh: {
    rewrite: {
      tab: 'AI 改写',
      entryTitle: '查看文章如何被重新组织',
      entryBody: '按照论证结构对照改写稿与原文，只突出真正影响逻辑和表达的变化。',
      open: '打开 AI 改写',
      stage: '正在按照论证结构对齐改写稿',
      title: 'AI 改写对照',
      subtitle: '左右内容按照论证作用对齐，荧光高亮仅表示重要的结构和表达变化。',
      aiVersion: 'AI 改写',
      originalVersion: '你的原文',
      legendTitle: '荧光含义',
      roles: {
        position: '观点',
        reasoning: '论证',
        evidence: '证据 / 例子',
        conclusion: '结论'
      },
      legend: {
        logicConnector: '逻辑衔接',
        logicBridge: '补充论证',
        removedContent: '删除内容',
        coreExpression: '核心表达'
      }
    },
    nav: {
      bank: '题库',
      example: '示例报告',
      login: '登录',
      dashboard: '控制台',
      settings: '设置',
      inbox: '收件箱'
    },
    actions: {
      start: '开始练习',
      upload: '上传题目',
      submit: '提交',
      save: '保存'
    },
    report: {
      tabs: { answer: '答题页', report: '评分报告', grammar: '语法分析', download: '下载' },
      evaluating: '正在评估你的回答',
      ready: '报告已生成',
      failed: '本次评估未能完成',
      refunded: '本次消耗的积分已退回，请重新开始一次练习后再试。',
      typical: '通常需要 2–3 分钟',
      elapsed: '已用时',
      waiting: '等待生成',
      evaluationReport: '评分报告',
      focusOn: '优先改进：{criterion}',
      focusThesis: '这是下一篇写作最值得优先解决的问题。先完成这一项，再查看完整评分明细。',
      startHere: '从这里开始',
      doNext: '下一步行动',
      question: '第 {number} 题',
      totalScore: '总分',
      converted: '换算分 {score} / 30',
      strongestArea: '最强项',
      languageFlags: '语言问题',
      flagSummary: '{grammar} 处语法 · {spelling} 处拼写',
      breakdown: '评分明细',
      scoreByCriteria: '四项评分',
      actionPlan: '改进计划',
      actionPlanByCriteria: '按评分维度执行',
      nextStep: '下一步',
      openGrammar: '打开语法分析',
      aiRewrite: 'AI 改写',
      modelDirection: '参考改写方向',
      grammarAnalysis: '语法分析',
      interactiveReport: '可交互语言报告',
      yourAnswer: '> 你的回答',
      noAnswer: '没有提交回答。',
      downloadReport: '下载 HTML 报告',
      downloadWaiting: '评估完成后即可下载。',
      criteria: {
        content_relevance: '内容相关性',
        perspective_expansion: '观点拓展',
        linguistic_expression: '语言表达',
        logical_structure: '逻辑结构'
      },
      stages: {
        queued: '正在等待评分任务',
        problems: '正在识别四项核心问题',
        scores: '正在生成四项评分',
        improvements: '正在制定改进计划',
        ai_rewrite: '正在改写回答',
        grammar_analysis: '正在检查语法和措辞',
        finalizing: '正在整理最终报告',
        retrying: '正在重新检查评分结果',
        completed: '报告已生成',
        failed: '评估失败'
      }
    }
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('tawep-locale') || 'en',
  fallbackLocale: 'en',
  messages
})
