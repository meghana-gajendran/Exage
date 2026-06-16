import { Session, LearningGoal, SSEEvent, RepoAnalysisResult, RepoSSEEvent } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Option 1 API ──────────────────────────────────────────────────

export async function createSession(topic: string, learning_goal: LearningGoal): Promise<Session> {
  const res = await fetch(`${BASE}/sessions/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, learning_goal }),
  })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json()
}

export async function getSession(sessionId: string): Promise<Session> {
  const res = await fetch(`${BASE}/sessions/${sessionId}`)
  if (!res.ok) throw new Error('Session not found')
  return res.json()
}

export async function getAllSessions(): Promise<Session[]> {
  try {
    const res = await fetch(`${BASE}/sessions/`)
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function getSessionMessages(sessionId: string): Promise<{ role: string; content: string }[]> {
  try {
    const res = await fetch(`${BASE}/sessions/${sessionId}/messages`)
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function* streamChat(sessionId: string, message: string): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) throw new Error('Chat request failed')
  if (!res.body) throw new Error('No response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try { yield JSON.parse(line.slice(6)) } catch { /* skip */ }
      }
    }
  }
}

// ── Option 2 API ──────────────────────────────────────────────────

export async function* streamRepoAnalysis(
  repoInput: string,
  learningGoal: LearningGoal,
  githubToken?: string,
): AsyncGenerator<RepoSSEEvent> {
  const res = await fetch(`${BASE}/repo-analysis/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_input: repoInput,
      learning_goal: learningGoal,
      github_token: githubToken || null,
    }),
  })
  if (!res.ok) throw new Error('Repo analysis failed')
  if (!res.body) throw new Error('No response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try { yield JSON.parse(line.slice(6)) } catch { /* skip */ }
      }
    }
  }
}

export async function createSessionFromAnalysis(
  sessionContext: object,
): Promise<{ session_id: string; topic: string; phase: string; opening_message: string }> {
  const res = await fetch(`${BASE}/repo-analysis/create-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sessionContext),
  })
  if (!res.ok) throw new Error('Failed to create session from analysis')
  return res.json()
}
