'use client'

import { useState, useCallback, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Session, ChatMessage, LearningGoal, Gap, SynthesisData, RepoAnalysisResult, RankedGap } from '@/lib/types'
import { createSession, streamChat, getAllSessions, getSessionMessages, getSession } from '@/lib/api'
import Sidebar from '@/components/Sidebar'
import ChatHeader from '@/components/ChatHeader'
import MessageList from '@/components/MessageList'
import StatusBar from '@/components/StatusBar'
import InputArea from '@/components/InputArea'
import OnboardingModal from '@/components/OnboardingModal'

let msgCounter = 0
const newId = () => `msg-${++msgCounter}`

function tryParseSynthesis(content: string): SynthesisData | null {
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object' && 'opening' in parsed) {
      return parsed as SynthesisData
    }
    return null
  } catch {
    return null
  }
}

/**
 * Reconstructs a RepoAnalysisResult from the persisted session_context.
 * This is what gets rendered as the report at the top of the chat.
 * Returns null for normal chat sessions (session_context is {}).
 */
function repoAnalysisFromSession(session: Session): RepoAnalysisResult | null {
  const ctx = session.session_context
  if (!ctx || !ctx.repo_context) return null

  const repoCtx = ctx.repo_context
  const openGaps = (ctx as any).open_gaps || []

  // Reconstruct ranked gaps from open_gaps stored in session_context.
  // These were persisted at session creation time from the consequence ranker output.
  const ranked_gaps: RankedGap[] = openGaps.map((g: any, i: number) => ({
    rank: i + 1,
    concept: g.concept || '',
    gap_type: g.gap_type || 'missing',
    gap_category: g.gap_category || 'domain_core',
    consequence_for_goal: g.why_it_matters_for_goal || '',
    urgency: g.severity === 'critical' ? 'immediate' : 'soon',
    probing_question: (repoCtx.probing_questions || [])[i] || '',
    what_a_good_answer_shows: '',
  }))

  return {
    repo_name: repoCtx.repo_name || session.topic,
    input_type: 'github',
    learning_goal: session.learning_goal,
    frameworks: [],
    framework_context: repoCtx.framework_context || '',
    domain: repoCtx.domain || '',
    overall_assessment: repoCtx.overall_assessment || '',
    strongest_areas: (ctx as any).known_concepts || [],
    weakest_signals: [],
    ranked_gaps,
    analysis_summary: '',
    technology_coverage_score: 0,
    session_context: ctx as any,
  }
}

function ChatPageInner() {
  const searchParams = useSearchParams()
  const [session, setSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [sessions, setSessions] = useState<Session[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [repoAnalysis, setRepoAnalysis] = useState<RepoAnalysisResult | null>(null)

  useEffect(() => {
    async function init() {
      const sessionParam = searchParams.get('session')

      if (sessionParam) {
        try {
          const s = await getSession(sessionParam)
          setSessions(prev => {
            const exists = prev.find(x => x.id === s.id)
            return exists ? prev : [...prev, s]
          })
          setSession(s)
          setRepoAnalysis(repoAnalysisFromSession(s))
          await loadMessages(s)
          window.history.replaceState({}, '', '/chat')
        } catch (err) {
          console.error('Failed to load session from param:', err)
        }
        return
      }

      const existing = await getAllSessions()
      if (existing.length > 0) {
        setSessions(existing)
        const latest = existing[existing.length - 1]
        setSession(latest)
        setRepoAnalysis(repoAnalysisFromSession(latest))
        await loadMessages(latest)
      } else {
        setShowOnboarding(true)
      }
    }
    init()
  }, [])

  const loadMessages = async (s: Session) => {
    setLoadingHistory(true)
    const msgs = await getSessionMessages(s.id)
    if (msgs.length > 0) {
      setMessages(msgs.map(m => {
        if (m.role === 'assistant') {
          const synthesisData = tryParseSynthesis(m.content)
          if (synthesisData) {
            return {
              id: newId(),
              role: 'assistant' as const,
              content: '',
              isSynthesis: true,
              synthesisData,
            }
          }
        }
        return {
          id: newId(),
          role: m.role as 'user' | 'assistant',
          content: m.content,
        }
      }))
    } else {
      setMessages([{
        id: newId(),
        role: 'assistant',
        content: `What do you already feel confident about in ${s.topic}? Walk me through what you know.`,
      }])
    }
    setLoadingHistory(false)
  }

  const startSession = useCallback(async (topic: string, goal: LearningGoal) => {
    const newSession = await createSession(topic, goal)
    setSessions(prev => [...prev, newSession])
    setSession(newSession)
    setRepoAnalysis(null)
    setMessages([{
      id: newId(),
      role: 'assistant',
      content: `What do you already feel confident about in ${topic}? Walk me through what you know.`,
    }])
    setShowOnboarding(false)
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    if (!session || isStreaming) return

    const userMsg: ChatMessage = { id: newId(), role: 'user', content: text }
    const assistantMsgId = newId()
    const assistantMsg: ChatMessage = { id: assistantMsgId, role: 'assistant', content: '', isStreaming: true }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)
    setStatus('Analyzing your explanation…')

    let accumulatedText = ''
    let detectedGaps: Gap[] = []
    let synthesisData: SynthesisData | null = null
    let hasError = false

    try {
      for await (const event of streamChat(session.id, text)) {
        if (event.type === 'status' && event.text) {
          setStatus(event.text)
        } else if (event.type === 'token' && event.text) {
          accumulatedText += event.text
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId ? { ...m, content: accumulatedText } : m
          ))
        } else if (event.type === 'synthesis' && event.data) {
          synthesisData = event.data
          const updated = { ...session, phase: event.phase || session.phase, turn_count: event.turn || session.turn_count }
          setSession(updated)
          setSessions(prev => prev.map(s => s.id === updated.id ? updated : s))
        } else if (event.type === 'error') {
          hasError = true
          accumulatedText = 'Something went wrong. Please try again.'
        } else if (event.type === 'done') {
          if (event.gaps) detectedGaps = event.gaps
          const updated = { ...session, phase: event.phase || session.phase, turn_count: event.turn || session.turn_count }
          setSession(updated)
          setSessions(prev => prev.map(s => s.id === updated.id ? updated : s))
        }
      }
    } catch (err) {
      console.error('Stream error:', err)
      hasError = true
      accumulatedText = 'Connection lost. Please check the backend is running and try again.'
    }

    if (!accumulatedText && !synthesisData && !hasError) {
      setMessages(prev => prev.filter(m => m.id !== assistantMsgId))
    } else if (synthesisData) {
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? { ...m, content: '', isStreaming: false, isSynthesis: true, synthesisData } : m
      ))
    } else {
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId
          ? { ...m, content: accumulatedText, isStreaming: false, gaps: detectedGaps.length ? detectedGaps : undefined }
          : m
      ))
    }

    setIsStreaming(false)
    setStatus(null)
  }, [session, isStreaming])

  const handleExplorePath = useCallback((question: string) => {
    if (session && !isStreaming) sendMessage(question)
  }, [session, isStreaming, sendMessage])

  const switchSession = useCallback(async (s: Session) => {
    setSession(s)
    setRepoAnalysis(repoAnalysisFromSession(s))
    await loadMessages(s)
  }, [])

  const handleDeleteSession = useCallback((sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId))
    if (session?.id === sessionId) {
      setSession(null)
      setMessages([])
      setRepoAnalysis(null)
      setShowOnboarding(true)
    }
  }, [session])

  const isSynthesisDone = session?.phase === 'synthesis'
  const repoContext = session?.session_context?.repo_context

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {showOnboarding && <OnboardingModal onStart={startSession} />}

      <Sidebar
        sessions={sessions}
        activeSessionId={session?.id}
        onSelectSession={switchSession}
        onNewSession={() => setShowOnboarding(true)}
        onDeleteSession={handleDeleteSession}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <ChatHeader session={session} repoContext={repoContext} />
        {loadingHistory
          ? <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>Loading…</div>
          : <MessageList
              messages={messages}
              onExplorePath={handleExplorePath}
              repoAnalysisResult={repoAnalysis}
            />
        }
        {status && <StatusBar text={status} />}
        {isSynthesisDone
          ? <div style={{ padding: '14px 32px', borderTop: '1px solid var(--border)', background: 'var(--surface)', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
              Session complete — start a new session or click a curiosity path above to continue
            </div>
          : <InputArea onSend={sendMessage} disabled={!session || isStreaming} />
        }
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatPageInner />
    </Suspense>
  )
}
