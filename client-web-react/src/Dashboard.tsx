import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Line, Doughnut } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
)

interface ScoreBucket {
  bucket: string
  count: number
}

interface PassRate {
  task: string
  avg_score: number
  attempts: number
}

interface TimelineEntry {
  date: string
  submissions: number
}

interface GroupEntry {
  group: string
  avg_score: number
  students: number
}

interface ItemRecord {
  id: number
  type: string
  title: string
}

interface LabOption {
  id: number
  value: string
  label: string
  hidden: boolean
}

interface LabApiRecord {
  id: number
  title: string
  hidden: boolean
}

interface CompletionRate {
  lab: string
  completion_rate: number
  passed: number
  total: number
}

interface TopLearner {
  learner_id: number
  avg_score: number
  attempts: number
}

interface AssistantMetrics {
  lab: string
  lab_title: string
  completion_rate: number
  passed: number
  total: number
  weakest_task: string | null
  weakest_task_score: number | null
  strongest_group: string | null
  strongest_group_score: number | null
  recent_submissions: number
  previous_submissions: number
}

interface AssistantResponse {
  answer: string
  focus_points: string[]
  metrics: AssistantMetrics
  sources: string[]
  mode: 'llm' | 'fallback'
}

type AssistantLanguage = 'ru' | 'en'

const TEXT = {
  ru: {
    heroTitle: 'Один экран для прогресса по лабам, слабых мест и следующих действий.',
    heroDesc: 'Дашборд собирает сырые LMS-данные из прошлых лаб в понятный рабочий обзор.',
    lab: 'Лаба',
    noLabs: 'Лабы не найдены',
    selectLab: 'Выберите лабу',
    hideLab: 'Скрыть лабу',
    disconnect: 'Отключиться',
    waitingLabs: 'Ожидание данных по лабам от backend.',
    completion: 'Завершение',
    latestLab: 'Последняя лаба',
    totalItems: 'всего элементов в каталоге',
    weakestTask: 'Самая слабая задача',
    lowestScore: 'Минимальный средний балл сейчас',
    bestGroup: 'Лучшая группа',
    highestAverage: 'Максимальный средний балл',
    forSelectedLab: 'Для выбранной лабы',
    assistant: 'Ассистент',
    askTitle: 'Спросить se-toolkit-hackathon',
    askPlaceholder: 'Что мне делать дальше?',
    ask: 'Спросить',
    thinking: 'Думаю...',
    assistantError: 'Ошибка ассистента',
    sources: 'Источники',
    trend: 'Тренд',
    recent: 'недавние',
    previous: 'предыдущие',
    summary: 'Сводка',
    summaryTitle: 'Что говорят данные',
    updating: 'Обновление',
    health: 'Состояние лабы',
    completionHint: 'Завершение по студентам с баллом выше 60.',
    groupLeader: 'Лидер группы',
    noDataYet: 'Пока нет данных',
    waitingGroup: 'Ожидание данных по группам.',
    improveFirst: 'Что улучшить в первую очередь',
    waitingTask: 'Ожидание данных по задачам.',
    topLearners: 'Топ студентов',
    noRanked: 'Пока нет ранжированных студентов.',
    attempts: 'попыток',
    manager: 'Управление лабами',
    managerTitle: 'Добавление, скрытие и разбиение лаб',
    working: 'В работе',
    newLab: 'Название новой лабы',
    labDesc: 'Описание',
    splitPrompt: 'Промпт для разбиения (AI)',
    taskCount: 'Количество задач',
    splitPreview: 'AI предпросмотр',
    addLab: 'Добавить лабу',
    hideSelected: 'Скрыть выбранную лабу',
    managerError: 'Ошибка менеджера',
    hiddenLabs: 'Скрытые лабы',
    unhide: 'Вернуть',
    timeline: 'Динамика сдач',
    scoreDist: 'Распределение баллов',
    groupPerf: 'Результаты групп',
    passRates: 'Средний балл по задачам',
    breakdown: 'Детализация',
    perTask: 'Детализация баллов по задачам',
    task: 'Задача',
    avgScore: 'Средний балл',
    modeLLM: 'Режим: AI',
    modeFallback: 'Режим: Fallback',
  },
  en: {
    heroTitle: 'One screen for lab progress, weak spots, and next actions.',
    heroDesc: 'The dashboard turns raw LMS data from previous labs into a clear action cockpit.',
    lab: 'Lab',
    noLabs: 'No labs found',
    selectLab: 'Select a lab',
    hideLab: 'Hide Lab',
    disconnect: 'Disconnect',
    waitingLabs: 'Waiting for lab data from the backend.',
    completion: 'Completion',
    latestLab: 'Latest lab',
    totalItems: 'total items in the catalog',
    weakestTask: 'Weakest task',
    lowestScore: 'Lowest average score right now',
    bestGroup: 'Best group',
    highestAverage: 'Highest current average',
    forSelectedLab: 'For selected lab',
    assistant: 'Assistant',
    askTitle: 'Ask se-toolkit-hackathon',
    askPlaceholder: 'What should I focus on next?',
    ask: 'Ask',
    thinking: 'Thinking...',
    assistantError: 'Assistant error',
    sources: 'Sources',
    trend: 'Trend',
    recent: 'recent',
    previous: 'previous',
    summary: 'Summary',
    summaryTitle: 'What the data says',
    updating: 'Updating',
    health: 'Laboratory health',
    completionHint: 'Completion based on learners with scores above 60.',
    groupLeader: 'Group leader',
    noDataYet: 'No data yet',
    waitingGroup: 'Waiting for group data.',
    improveFirst: 'Task to improve first',
    waitingTask: 'Waiting for task data.',
    topLearners: 'Top learners',
    noRanked: 'No ranked learners yet.',
    attempts: 'attempts',
    manager: 'Lab Manager',
    managerTitle: 'Add, Hide, and Split Labs',
    working: 'Working',
    newLab: 'New lab title',
    labDesc: 'Description',
    splitPrompt: 'Split prompt (AI)',
    taskCount: 'Task count',
    splitPreview: 'AI Split Preview',
    addLab: 'Add Lab',
    hideSelected: 'Hide Selected Lab',
    managerError: 'Manager error',
    hiddenLabs: 'Hidden labs',
    unhide: 'Unhide',
    timeline: 'Submissions timeline',
    scoreDist: 'Score distribution',
    groupPerf: 'Group performance',
    passRates: 'Average score by task',
    breakdown: 'Breakdown',
    perTask: 'Per-task score breakdown',
    task: 'Task',
    avgScore: 'Avg Score',
    modeLLM: 'Mode: AI',
    modeFallback: 'Mode: Fallback',
  },
} as const

async function checkedJson<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  return res.json() as Promise<T>
}

function Dashboard({
  token,
  onDisconnect,
}: {
  token: string
  onDisconnect: () => void
}) {
  const [labs, setLabs] = useState<LabOption[]>([])
  const [hiddenLabs, setHiddenLabs] = useState<LabOption[]>([])
  const [lab, setLab] = useState('')
  const [scores, setScores] = useState<ScoreBucket[]>([])
  const [passRates, setPassRates] = useState<PassRate[]>([])
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [groups, setGroups] = useState<GroupEntry[]>([])
  const [completion, setCompletion] = useState<CompletionRate | null>(null)
  const [topLearners, setTopLearners] = useState<TopLearner[]>([])
  const [assistantQuery, setAssistantQuery] = useState('What should I focus on next?')
  const [assistantLanguage, setAssistantLanguage] = useState<AssistantLanguage>('ru')
  const [assistantResponse, setAssistantResponse] = useState<AssistantResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [assistantLoading, setAssistantLoading] = useState(false)
  const [error, setError] = useState('')
  const [assistantError, setAssistantError] = useState('')
  const [itemsCount, setItemsCount] = useState(0)
  const [newLabTitle, setNewLabTitle] = useState('')
  const [newLabDescription, setNewLabDescription] = useState('')
  const [splitPrompt, setSplitPrompt] = useState('')
  const [taskCount, setTaskCount] = useState(5)
  const [managerLoading, setManagerLoading] = useState(false)
  const [managerError, setManagerError] = useState('')
  const [splitPreview, setSplitPreview] = useState<string[]>([])
  const t = TEXT[assistantLanguage]

  async function loadLabs() {
    const headers = { Authorization: `Bearer ${token}` }

    try {
      const [items, visibleLabRecords, allLabRecords] = await Promise.all([
        fetch('/items/', { headers }).then((r) => checkedJson<ItemRecord[]>(r)),
        fetch('/items/labs', { headers }).then((r) => checkedJson<LabApiRecord[]>(r)),
        fetch('/items/labs?include_hidden=true', { headers }).then((r) => checkedJson<LabApiRecord[]>(r)),
      ])

      setItemsCount(items.length)
      const normalizeLab = (labItem: LabApiRecord) => {
        const m = labItem.title.match(/Lab\s+(\d+)/i)
        return {
          id: labItem.id,
          value: m ? `lab-${m[1].padStart(2, '0')}` : `lab-${labItem.id}`,
          label: labItem.title,
          hidden: labItem.hidden,
        }
      }

      const labOptions = visibleLabRecords
        .map((labItem) => {
          return normalizeLab(labItem)
        })
        .sort((a, b) => a.label.localeCompare(b.label))

      const hiddenLabOptions = allLabRecords
        .filter((labItem) => labItem.hidden)
        .map((labItem) => normalizeLab(labItem))
        .sort((a, b) => a.label.localeCompare(b.label))

      setLabs(labOptions)
      setHiddenLabs(hiddenLabOptions)
      if (labOptions.length > 0) {
        setLab((current) => current || labOptions[labOptions.length - 1].value)
      } else {
        setLab('')
      }
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load labs')
    }
  }

  useEffect(() => {
    void loadLabs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  useEffect(() => {
    if (!lab) return
    const headers = { Authorization: `Bearer ${token}` }
    setLoading(true)

    Promise.all([
      fetch(`/analytics/scores?lab=${lab}`, { headers }).then((r) => checkedJson<ScoreBucket[]>(r)),
      fetch(`/analytics/pass-rates?lab=${lab}`, { headers }).then((r) => checkedJson<PassRate[]>(r)),
      fetch(`/analytics/timeline?lab=${lab}`, { headers }).then((r) => checkedJson<TimelineEntry[]>(r)),
      fetch(`/analytics/groups?lab=${lab}`, { headers }).then((r) => checkedJson<GroupEntry[]>(r)),
      fetch(`/analytics/completion-rate?lab=${lab}`, { headers }).then((r) => checkedJson<CompletionRate>(r)),
      fetch(`/analytics/top-learners?lab=${lab}&limit=3`, { headers }).then((r) => checkedJson<TopLearner[]>(r)),
    ])
      .then(([s, p, t, g, c, top]) => {
        setScores(s)
        setPassRates(p)
        setTimeline(t)
        setGroups(g)
        setCompletion(c)
        setTopLearners(top)
        setError('')
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [token, lab])

  useEffect(() => {
    if (!lab) return
    void askAssistant(t.askPlaceholder)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lab, assistantLanguage])

  const bestGroup = useMemo(
    () => groups.slice().sort((a, b) => b.avg_score - a.avg_score)[0],
    [groups],
  )
  const weakestTask = useMemo(
    () => passRates.slice().sort((a, b) => a.avg_score - b.avg_score)[0],
    [passRates],
  )

  async function askAssistant(question: string) {
    if (!lab) return
    setAssistantLoading(true)
    setAssistantError('')

    try {
      const response = await fetch('/assistant/insights', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ lab, question, language: assistantLanguage }),
      })

      const data = await checkedJson<AssistantResponse>(response)
      setAssistantResponse(data)
    } catch (err) {
      setAssistantError(err instanceof Error ? err.message : 'Assistant failed')
    } finally {
      setAssistantLoading(false)
    }
  }

  function handleAsk(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    void askAssistant(assistantQuery)
  }

  const selectedLab = labs.find((option) => option.value === lab)

  async function handleHideSelectedLab() {
    if (!selectedLab) return
    setManagerLoading(true)
    setManagerError('')
    try {
      const response = await fetch(`/items/labs/${selectedLab.id}/hide?hidden=true`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      await checkedJson(response)
      await loadLabs()
      setLab('')
      setSplitPreview([])
    } catch (err) {
      setManagerError(err instanceof Error ? err.message : 'Failed to hide lab')
    } finally {
      setManagerLoading(false)
    }
  }

  async function handleUnhideLab(labId: number) {
    setManagerLoading(true)
    setManagerError('')
    try {
      const response = await fetch(`/items/labs/${labId}/hide?hidden=false`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      await checkedJson(response)
      await loadLabs()
    } catch (err) {
      setManagerError(err instanceof Error ? err.message : 'Failed to unhide lab')
    } finally {
      setManagerLoading(false)
    }
  }

  async function handleSplitPreview() {
    if (!newLabTitle.trim()) {
      setManagerError('Enter a lab title first')
      return
    }
    setManagerLoading(true)
    setManagerError('')
    try {
      const response = await fetch('/items/labs/split', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newLabTitle.trim(),
          description: newLabDescription.trim(),
          task_count: taskCount,
          split_prompt: splitPrompt.trim(),
        }),
      })
      const tasks = await checkedJson<string[]>(response)
      setSplitPreview(tasks)
    } catch (err) {
      setManagerError(err instanceof Error ? err.message : 'Failed to split lab')
    } finally {
      setManagerLoading(false)
    }
  }

  async function handleCreateLab() {
    if (!newLabTitle.trim()) {
      setManagerError('Enter a lab title first')
      return
    }
    setManagerLoading(true)
    setManagerError('')
    try {
      const response = await fetch('/items/labs', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newLabTitle.trim(),
          description: newLabDescription.trim(),
          task_count: taskCount,
          generate_with_ai: true,
          split_prompt: splitPrompt.trim(),
        }),
      })
      await checkedJson(response)
      setNewLabTitle('')
      setNewLabDescription('')
      setSplitPrompt('')
      setSplitPreview([])
      await loadLabs()
    } catch (err) {
      setManagerError(err instanceof Error ? err.message : 'Failed to create lab')
    } finally {
      setManagerLoading(false)
    }
  }

  const latestLabLabel = labs.at(-1)?.label ?? '—'
  const currentLabLabel = labs.find((option) => option.value === lab)?.label ?? latestLabLabel
  const completionRate = completion?.completion_rate ?? 0
  const passedCount = completion?.passed ?? 0
  const totalCount = completion?.total ?? 0
  const topGroupLabel = bestGroup ? `${bestGroup.group} · ${bestGroup.avg_score.toFixed(1)}` : t.noDataYet
  const weakTaskLabel = weakestTask ? `${weakestTask.task} · ${weakestTask.avg_score.toFixed(1)}` : t.noDataYet

  if (error) return <p>Error loading analytics: {error}</p>

  const scoreData = {
    labels: scores.map((s) => s.bucket),
    datasets: [
      {
        label: 'Students',
        data: scores.map((s) => s.count),
        backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#22c55e'],
      },
    ],
  }

  const timelineData = {
    labels: timeline.map((t) => t.date),
    datasets: [
      {
        label: 'Submissions',
        data: timeline.map((t) => t.submissions),
        borderColor: '#3b82f6',
        tension: 0.3,
      },
    ],
  }

  const groupData = {
    labels: groups.map((g) => g.group),
    datasets: [
      {
        label: 'Avg Score',
        data: groups.map((g) => g.avg_score),
        backgroundColor: '#3b82f6',
      },
    ],
  }

  const passRateData = {
    labels: passRates.map((p) => p.task),
    datasets: [
      {
        data: passRates.map((p) => p.avg_score),
        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'],
      },
    ],
  }

  return (
    <main className="dashboard-shell">
      <header className="hero-panel">
        <div className="hero-copy">
          <div className="eyebrow">se-toolkit-hackathon</div>
          <h1>{t.heroTitle}</h1>
          <p>{t.heroDesc}</p>
          <div className="hero-actions">
            <label className="field-inline">
              <span>{t.lab}</span>
              <select
                value={lab}
                onChange={(e) => setLab(e.target.value)}
                disabled={labs.length === 0}
              >
                <option value="" disabled>
                  {labs.length === 0 ? t.noLabs : t.selectLab}
                </option>
                {labs.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="ghost-button"
              onClick={() => void handleHideSelectedLab()}
              type="button"
              disabled={!selectedLab || managerLoading}
            >
              {t.hideLab}
            </button>
            <button className="ghost-button" onClick={onDisconnect} type="button">
              {t.disconnect}
            </button>
          </div>
          {labs.length === 0 && <p className="helper-text">{t.waitingLabs}</p>}
        </div>

        <div className="hero-stats">
          <div className="stat-card primary-stat">
            <span className="stat-label">{t.completion}</span>
            <strong>{completionRate.toFixed(1)}%</strong>
            <p>{passedCount} / {totalCount}</p>
          </div>
          <div className="stat-card">
            <span className="stat-label">{t.latestLab}</span>
            <strong>{latestLabLabel}</strong>
            <p>{itemsCount} {t.totalItems}</p>
          </div>
          <div className="stat-card">
            <span className="stat-label">{t.weakestTask}</span>
            <strong>{weakTaskLabel}</strong>
            <p>{t.lowestScore}. {t.forSelectedLab}: {currentLabLabel}</p>
          </div>
          <div className="stat-card">
            <span className="stat-label">{t.bestGroup}</span>
            <strong>{topGroupLabel}</strong>
            <p>{t.highestAverage}. {t.forSelectedLab}: {currentLabLabel}</p>
          </div>
        </div>
      </header>

      <section className="insight-grid">
        <article className="assistant-panel card-surface">
          <div className="panel-head">
            <div>
              <span className="eyebrow">Assistant</span>
              <h2>{t.askTitle}</h2>
            </div>
            <div className="assistant-head-tools">
              <label className="assistant-lang">
                <span>Lang</span>
                <select
                  value={assistantLanguage}
                  onChange={(e) => setAssistantLanguage(e.target.value as AssistantLanguage)}
                >
                  <option value="ru">RU</option>
                  <option value="en">EN</option>
                </select>
              </label>
              {assistantResponse && (
                <span className="assistant-mode-pill">
                  {assistantResponse.mode === 'llm' ? t.modeLLM : t.modeFallback}
                </span>
              )}
              <span className="pill">{assistantResponse?.metrics.lab_title ?? lab}</span>
            </div>
          </div>

          <form className="assistant-form" onSubmit={handleAsk}>
            <input
              type="text"
              value={assistantQuery}
              onChange={(e) => setAssistantQuery(e.target.value)}
              placeholder={t.askPlaceholder}
            />
            <button type="submit">{t.ask}</button>
          </form>

          {assistantLoading && <p className="helper-text">{t.thinking}</p>}
          {assistantError && <p className="error-text">{t.assistantError}: {assistantError}</p>}

          {assistantResponse && (
            <div className="assistant-answer">
              <p>{assistantResponse.answer}</p>
              <ul>
                {assistantResponse.focus_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          )}
        </article>

        <article className="card-surface summary-panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">Summary</span>
              <h2>{t.summaryTitle}</h2>
            </div>
            {loading && <span className="pill">{t.updating}</span>}
          </div>

          <div className="summary-list">
            <div>
              <span>{t.health}</span>
              <strong>{completionRate.toFixed(1)}%</strong>
              <p>{t.completionHint}</p>
            </div>
            <div>
              <span>{t.groupLeader}</span>
              <strong>{bestGroup ? bestGroup.group : t.noDataYet}</strong>
              <p>{bestGroup ? `${bestGroup.students} ${t.attempts}` : t.waitingGroup}</p>
            </div>
            <div>
              <span>{t.improveFirst}</span>
              <strong>{weakestTask ? weakestTask.task : t.noDataYet}</strong>
              <p>{weakestTask ? `${weakestTask.attempts} ${t.attempts}, ${t.avgScore} ${weakestTask.avg_score.toFixed(1)}` : t.waitingTask}</p>
            </div>
          </div>

          <div className="top-learners">
            <h3>{t.topLearners}</h3>
            <p className="helper-text">{t.forSelectedLab}: {currentLabLabel}</p>
            <div>
              {topLearners.length === 0 ? (
                <p className="helper-text">{t.noRanked}</p>
              ) : (
                topLearners.map((learner) => (
                  <div key={learner.learner_id} className="top-learner-row">
                    <span>#{learner.learner_id}</span>
                    <strong>{learner.avg_score.toFixed(1)}</strong>
                    <span>{learner.attempts} {t.attempts}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </article>
      </section>

      <section className="card-surface manager-panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">Lab Manager</span>
            <h2>{t.managerTitle}</h2>
          </div>
          {managerLoading && <span className="pill">{t.working}</span>}
        </div>

        <div className="manager-grid">
          <label className="manager-field">
            <span>{t.newLab}</span>
            <input
              value={newLabTitle}
              onChange={(e) => setNewLabTitle(e.target.value)}
              placeholder="Lab 09 — Quiz and Hackathon"
            />
          </label>

          <label className="manager-field">
            <span>{t.labDesc}</span>
            <input
              value={newLabDescription}
              onChange={(e) => setNewLabDescription(e.target.value)}
              placeholder="What this lab is about"
            />
          </label>

          <label className="manager-field">
            <span>{t.splitPrompt}</span>
            <input
              value={splitPrompt}
              onChange={(e) => setSplitPrompt(e.target.value)}
              placeholder="Split into practical implementation tasks"
            />
          </label>

          <label className="manager-field">
            <span>{t.taskCount}</span>
            <input
              type="number"
              min={1}
              max={12}
              value={taskCount}
              onChange={(e) => setTaskCount(Number(e.target.value || 5))}
            />
          </label>
        </div>

        <div className="manager-actions">
          <button type="button" onClick={handleSplitPreview} disabled={managerLoading}>
            {t.splitPreview}
          </button>
          <button type="button" onClick={handleCreateLab} disabled={managerLoading}>
            {t.addLab}
          </button>
          <button
            type="button"
            onClick={handleHideSelectedLab}
            disabled={managerLoading || !selectedLab}
          >
            {t.hideSelected}
          </button>
        </div>

        {managerError && <p className="error-text">{t.managerError}: {managerError}</p>}

        {splitPreview.length > 0 && (
          <div className="split-preview">
            <h3>{t.splitPreview}</h3>
            <ul>
              {splitPreview.map((task) => (
                <li key={task}>{task}</li>
              ))}
            </ul>
          </div>
        )}

        {hiddenLabs.length > 0 && (
          <div className="hidden-labs">
            <h3>{t.hiddenLabs}</h3>
            <div>
              {hiddenLabs.map((hiddenLab) => (
                <div className="hidden-lab-row" key={hiddenLab.id}>
                  <span>{hiddenLab.label}</span>
                  <button
                    type="button"
                    onClick={() => void handleUnhideLab(hiddenLab.id)}
                    disabled={managerLoading}
                  >
                    {t.unhide}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="charts-grid">
        <div className="chart-card card-surface">
          <h3>{t.timeline}</h3>
          <Line data={timelineData} />
        </div>

        <div className="chart-card card-surface">
          <h3>{t.scoreDist}</h3>
          <Bar data={scoreData} options={{ plugins: { legend: { display: false } } }} />
        </div>

        <div className="chart-card card-surface">
          <h3>{t.groupPerf}</h3>
          <Bar data={groupData} options={{ plugins: { legend: { display: false } } }} />
        </div>

        <div className="chart-card card-surface">
          <h3>{t.passRates}</h3>
          <Doughnut data={passRateData} />
        </div>
      </section>

      {passRates.length > 0 && (
        <section className="card-surface table-card">
          <div className="panel-head">
            <div>
              <span className="eyebrow">Breakdown</span>
              <h2>{t.perTask}</h2>
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th>{t.task}</th>
                <th>{t.avgScore}</th>
                <th>{t.attempts}</th>
              </tr>
            </thead>
            <tbody>
              {passRates.map((p) => (
                <tr key={p.task}>
                  <td>{p.task}</td>
                  <td>{p.avg_score.toFixed(1)}</td>
                  <td>{p.attempts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  )
}

export default Dashboard
