import { createI18n } from 'vue-i18n'

const messages = {
  en: {
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
    }
  },
  zh: {
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
    }
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('tawep-locale') || 'en',
  fallbackLocale: 'en',
  messages
})
