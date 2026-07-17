import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const EXAMPLE_SESSION_ID = '00000000-0000-4000-8000-000000000008'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/HomePage.vue') },
    { path: '/dashboard', component: () => import('../views/DashboardPage.vue'), meta: { requiresAuth: true } },
    { path: '/questionbank', component: () => import('../views/QuestionBankPage.vue') },
    { path: '/createyourown', component: () => import('../views/CreateOwnPage.vue'), meta: { requiresAuth: true } },
    { path: '/:questionNo(\\d+)/prepare', component: () => import('../views/PreparePage.vue'), meta: { requiresAuth: true } },
    { path: '/:sessionId/answerpage', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'answer' }, meta: { requiresAuth: true } },
    { path: '/:sessionId/report', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'report' }, meta: { requiresAuth: true } },
    { path: '/:sessionId/rewrite', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'rewrite' }, meta: { requiresAuth: true } },
    { path: '/:sessionId/grammaranalysis', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'grammar' }, meta: { requiresAuth: true } },
    { path: '/:sessionId/download', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'download' }, meta: { requiresAuth: true } },
    { path: '/share/:shareToken/answerpage', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'answer', publicShare: true }, meta: { publicShare: true } },
    { path: '/share/:shareToken/report', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'report', publicShare: true }, meta: { publicShare: true } },
    { path: '/share/:shareToken/rewrite', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'rewrite', publicShare: true }, meta: { publicShare: true } },
    { path: '/share/:shareToken/grammaranalysis', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'grammar', publicShare: true }, meta: { publicShare: true } },
    { path: '/examplereport', redirect: `/${EXAMPLE_SESSION_ID}/report` },
    { path: '/settings', component: () => import('../views/SettingsPage.vue'), meta: { requiresAuth: true } },
    { path: '/inbox', component: () => import('../views/InboxPage.vue'), meta: { requiresAuth: true } },
    { path: '/score-report', component: () => import('../views/ScoreReportPage.vue'), meta: { requiresAuth: true } },
    { path: '/agreements', component: () => import('../views/LegalPage.vue') },
    { path: '/agreements/:slug', component: () => import('../views/LegalPage.vue'), props: true },
    { path: '/creditexplanation', redirect: '/agreements/credit-explanation' },
    { path: '/login', component: () => import('../views/LoginPage.vue'), meta: { guestOnly: true } },
    { path: '/verify-email', component: () => import('../views/VerifyEmailPage.vue'), meta: { guestOnly: true } },
    { path: '/reset-password', component: () => import('../views/ResetPasswordPage.vue'), meta: { guestOnly: true } },
    { path: '/manage', redirect: '/login?redirect=/manage/questionbank' },
    { path: '/manage/questionbank', component: () => import('../views/admin/ManageQuestionBankPage.vue'), meta: { requiresAdmin: true } },
    { path: '/manage/reviewquestion', component: () => import('../views/admin/ManageReviewQuestionPage.vue'), meta: { requiresAdmin: true } },
    { path: '/manage/feedback', component: () => import('../views/admin/ManageFeedbackPage.vue'), meta: { requiresAdmin: true } },
    { path: '/manage/outcomes', component: () => import('../views/admin/ManageOutcomesPage.vue'), meta: { requiresAdmin: true } },
    { path: '/manage/accounts', component: () => import('../views/admin/ManageAccountsPage.vue'), meta: { requiresAdmin: true } },
    { path: '/manage/settings', component: () => import('../views/admin/ManagePlatformSettingsPage.vue'), meta: { requiresAdmin: true } }
  ],
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.publicShare) await auth.initialize()
  const isExample = String(to.params.sessionId ?? '') === EXAMPLE_SESSION_ID
  if (to.meta.requiresAuth && !isExample && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return auth.isAuthenticated ? '/dashboard' : { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) return '/dashboard'
})
