const path = require('path')
const { chromium } = require('playwright')

const appUrl = process.env.TAWEP_APP_URL || 'http://127.0.0.1:5173'
const exampleSessionId = '00000000-0000-4000-8000-000000000008'
const outputDirectory = path.resolve(__dirname, 'assets/zh')

const problems = [
  '存在多处语法、拼写和词形问题，包括 helpfull、help、teach、advise、cheaper price 和 small parts。',
  '例子比较具体，但展开不够充分。服务体验的例子需要更多细节，价格与付款方式的论点也没有解释完整。',
  '整体结构可以理解，但观点之间的过渡有限，部分句子衔接显得突兀。',
  '回答完整回应了题目，并比较了小商店与大型商店，没有明显的偏题问题。'
]

const improvements = [
  '打开语法分析，修正原文中的拼写、语法和措辞问题。',
  '补充服务体验的具体细节，并说明灵活付款方式为何对学生有帮助。',
  '使用清晰的连接词衔接观点，并在每个例子后说明它如何支持中心论点。',
  '继续保持对题目的直接回应，并确保每个例子都服务于核心立场。'
]

function localizeReport({ problems, improvements }) {
  const priorityProblem = document.querySelector('.report-priority-card > p.section-reveal')
  const priorityImprovement = document.querySelector('.report-priority-card .priority-next > p.section-reveal')
  if (priorityProblem) priorityProblem.textContent = problems[0]
  if (priorityImprovement) priorityImprovement.textContent = improvements[0]

  document.querySelectorAll('.criteria-row').forEach((row, index) => {
    const problem = row.querySelector(':scope > p.section-reveal')
    if (problem) problem.textContent = problems[index]
  })

  document.querySelectorAll('.priority-step').forEach((step, index) => {
    const columns = step.querySelectorAll('.priority-step-body > div')
    const problem = columns[0]?.querySelector('p')
    const improvement = columns[1]?.querySelector('p')
    if (problem) problem.textContent = problems[index]
    if (improvement) improvement.textContent = improvements[index]
  })
}

function localizeGrammar() {
  const legendLabels = ['语法', '拼写', '措辞']
  document.querySelectorAll('.grammar-legend > span').forEach((item, index) => {
    const textNode = [...item.childNodes].find((node) => node.nodeType === Node.TEXT_NODE)
    if (textNode) textNode.textContent = legendLabels[index]
  })

  const firstSpelling = document.querySelector('.essay-mark.spelling .issue-detail')
  const lines = firstSpelling?.querySelectorAll(':scope > span')
  if (lines?.[0]) lines[0].textContent = '问题：拼写错误。'
  if (lines?.[1]) lines[1].textContent = '建议：helpful'
}

async function capture() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
  })
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1
  })
  await context.addInitScript(() => localStorage.setItem('tawep-locale', 'zh'))
  const page = await context.newPage()

  try {
    await page.goto(`${appUrl}/${exampleSessionId}/report`, { waitUntil: 'networkidle' })
    await page.waitForSelector('.report-modern')
    await page.evaluate(localizeReport, { problems, improvements })

    for (const [filename, scrollY] of [
      ['report.png', 0],
      ['score-details.png', 648],
      ['action.png', 950]
    ]) {
      await page.evaluate((top) => window.scrollTo(0, top), scrollY)
      await page.waitForTimeout(120)
      await page.screenshot({ path: path.join(outputDirectory, filename) })
    }

    await page.goto(`${appUrl}/${exampleSessionId}/grammaranalysis`, { waitUntil: 'networkidle' })
    await page.waitForSelector('.legacy-report')
    await page.evaluate(localizeGrammar)
    await page.screenshot({ path: path.join(outputDirectory, 'grammar.png') })

    await page.locator('.essay-mark.spelling').first().hover()
    await page.waitForTimeout(180)
    await page.screenshot({ path: path.join(outputDirectory, 'grammar-spelling.png') })
  } finally {
    await browser.close()
  }
}

capture().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
