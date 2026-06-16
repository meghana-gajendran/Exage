'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { LearningGoal, RepoAnalysisResult } from '@/lib/types'
import { streamRepoAnalysis, createSessionFromAnalysis } from '@/lib/api'
import RepoInputModal from '@/components/RepoInputModal'
import RepoAnalysisReport from '@/components/RepoAnalysisReport'

type PageState = 'input' | 'analysing' | 'report'

export default function RepoPage() {
  const router = useRouter()
  const [pageState, setPageState] = useState<PageState>('input')
  const [status, setStatus] = useState<string | null>(null)
  const [result, setResult] = useState<RepoAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isCreatingSession, setIsCreatingSession] = useState(false)

  const handleAnalyse = useCallback(async (repoInput: string, goal: LearningGoal) => {
    setPageState('analysing')
    setStatus('Reading repository…')
    setError(null)

    try {
      for await (const event of streamRepoAnalysis(repoInput, goal)) {
        if (event.type === 'status') {
          setStatus(event.text)
        } else if (event.type === 'done') {
          setResult(event.result)
          setPageState('report')
          setStatus(null)
        } else if (event.type === 'error') {
          setError(event.text)
          setPageState('input')
          setStatus(null)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setPageState('input')
      setStatus(null)
    }
  }, [])

  const handleStartProbing = useCallback(async () => {
    if (!result) return
    setIsCreatingSession(true)
    try {
      const { session_id, opening_message } = await createSessionFromAnalysis(result.session_context)
      // Pass opening_message as a query param so chat page can use it
      const params = new URLSearchParams({
        session: session_id,
        opening: encodeURIComponent(opening_message),
      })
      router.push(`/chat?${params.toString()}`)
    } catch (err) {
      console.error('Failed to create session:', err)
      setIsCreatingSession(false)
    }
  }, [result, router])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>

      <header style={{
        padding: '16px 32px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        display: 'flex', alignItems: 'center', gap: '12px',
      }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '15px', fontWeight: 500 }}>
          Ex<span style={{ color: 'var(--pink)' }}>Age</span>
        </div>
        <div style={{ width: '1px', height: '14px', background: 'var(--border)' }} />
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Repo analysis</div>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => router.push('/chat')}
          style={{
            padding: '6px 12px', border: '1px solid var(--border)',
            borderRadius: '6px', background: 'none',
            fontFamily: 'var(--font)', fontSize: '12px',
            color: 'var(--text-muted)', cursor: 'pointer',
          }}
        >
          Switch to chat mode
        </button>
      </header>

      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>

        {pageState === 'analysing' && (
          <div style={{
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            height: '100%', gap: '24px',
          }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '13px', color: 'var(--text-muted)' }}>
              {status || 'Analysing…'}
            </div>
            <div style={{ width: '200px', height: '2px', background: 'var(--border)', borderRadius: '1px', overflow: 'hidden' }}>
              <div style={{
                height: '100%', background: 'var(--pink)', borderRadius: '1px',
                animation: 'progress-pulse 2s ease-in-out infinite',
              }} />
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Running 4 analysis agents — takes about 30–60 seconds
            </div>
            <style>{`
              @keyframes progress-pulse {
                0% { width: 0%; }
                50% { width: 70%; }
                100% { width: 100%; }
              }
            `}</style>
          </div>
        )}

        {pageState === 'report' && result && (
          <div style={{ height: '100%', overflowY: 'auto' }}>
            <RepoAnalysisReport
              result={result}
              onStartProbing={handleStartProbing}
              isCreatingSession={isCreatingSession}
            />
          </div>
        )}

        {error && pageState === 'input' && (
          <div style={{
            position: 'absolute', bottom: '20px', left: '50%',
            transform: 'translateX(-50%)',
            padding: '10px 16px',
            background: 'var(--surface)', border: '1px solid var(--pink-border)',
            borderRadius: '8px', fontSize: '13px', color: 'var(--pink)',
          }}>
            {error}
          </div>
        )}
      </div>

      {pageState === 'input' && (
        <RepoInputModal
          onAnalyse={handleAnalyse}
          onBack={() => router.push('/chat')}
        />
      )}
    </div>
  )
}
