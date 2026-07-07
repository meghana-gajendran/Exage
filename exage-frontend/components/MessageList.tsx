'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage, RepoAnalysisResult } from '@/lib/types'
import Message from './Message'
import RepoAnalysisReport from './RepoAnalysisReport'

interface Props {
  messages: ChatMessage[]
  onExplorePath?: (question: string) => void
  repoAnalysisResult?: RepoAnalysisResult | null
}

export default function MessageList({ messages, onExplorePath, repoAnalysisResult }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '32px',
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
    }}>
      {messages.length === 0 && !repoAnalysisResult && (
        <div style={{
          margin: 'auto',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '13px',
          lineHeight: 1.6,
        }}>
          <div style={{ fontSize: '24px', marginBottom: '12px' }}>◎</div>
          Start a session to begin exploring your understanding.
        </div>
      )}

      {/* Issue #3 fix: render repo analysis report at top of chat
          for repo-originated sessions. readOnly=true hides the CTA button.
          Only shows when session_context has the full analysis data.
          Normal chat sessions pass null here — no effect on existing behaviour. */}
      {repoAnalysisResult && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          padding: '24px',
          maxWidth: '680px',
          alignSelf: 'flex-start',
          width: '100%',
        }}>
          <div style={{
            fontSize: '10px', fontWeight: 500, color: 'var(--text-muted)',
            letterSpacing: '0.7px', textTransform: 'uppercase', marginBottom: '16px',
          }}>
            Repo analysis
          </div>
          <RepoAnalysisReport result={repoAnalysisResult} readOnly={true} />
        </div>
      )}

      {messages.map(msg => (
        <Message key={msg.id} message={msg} onExplorePath={onExplorePath} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
