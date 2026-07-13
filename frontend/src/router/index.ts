import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/HomePage.vue') },
    { path: '/dashboard', component: () => import('../views/DashboardPage.vue') },
    { path: '/questionbank', component: () => import('../views/QuestionBankPage.vue') },
    { path: '/createyourown', component: () => import('../views/CreateOwnPage.vue') },
    { path: '/:questionNo(\\d+)/prepare', component: () => import('../views/PreparePage.vue') },
    { path: '/:sessionId/answerpage', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'answer' } },
    { path: '/:sessionId/report', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'report' } },
    { path: '/:sessionId/rewrite', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'rewrite' } },
    { path: '/:sessionId/grammaranalysis', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'grammar' } },
    { path: '/:sessionId/download', component: () => import('../views/AnswerWorkspace.vue'), props: { activeTab: 'download' } },
    { path: '/examplereport', redirect: '/00000000-0000-4000-8000-000000000008/report' },
    { path: '/settings', component: () => import('../views/SettingsPage.vue') },
    { path: '/inbox', component: () => import('../views/InboxPage.vue') },
    { path: '/agreements', component: () => import('../views/LegalPage.vue'), props: { slug: 'agreements' } },
    { path: '/creditexplanation', component: () => import('../views/LegalPage.vue'), props: { slug: 'credit-explanation' } },
    { path: '/login', component: () => import('../views/LoginPage.vue') },
    { path: '/manage', component: () => import('../views/admin/ManageLoginPage.vue') },
    { path: '/manage/questionbank', component: () => import('../views/admin/ManageQuestionBankPage.vue') },
    { path: '/manage/reviewquestion', component: () => import('../views/admin/ManageReviewQuestionPage.vue') },
    { path: '/manage/accounts', component: () => import('../views/admin/ManageAccountsPage.vue') }
  ],
  scrollBehavior: () => ({ top: 0 })
})
