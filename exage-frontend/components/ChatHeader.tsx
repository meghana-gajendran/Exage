'use client'

import { Session } from '@/lib/types'

interface Props {
  session: Session | null
}

const PHASE_LABELS: Record<string, string> = {
  onboarding: 'Onboarding',
  probing: 'Probing',
  synthesis: 'Synthesis',
}

const GOAL_LABELS: Record<string, string> = {
  interview: 'Interview prep',
  exam: 'Exam prep',
  project: 'Project',
  teaching: 'Teaching',
  curiosity: 'Curiosity',
}

export default function ChatHeader({ session }: Props) {
  if (!session) {
    return (
      <header style={{
        padding: '16px 32px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        minHeight: '61px',
      }} />
    )
  }

  return (
    <header style={{
      padding: '16px 32px',
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: 'var(--surface)',
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ fontSize: '14px', fontWeight: 500 }}>{session.topic}</div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{
            fontSize: '10.5px', padding: '2px 8px', borderRadius: '20px',
            fontWeight: 500, letterSpacing: '0.2px',
            background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text-secondary)',
          }}>
            {GOAL_LABELS[session.learning_goal] || session.learning_goal}
          </span>
          <span style={{
            fontSize: '10.5px', padding: '2px 8px', borderRadius: '20px',
            fontWeight: 500, letterSpacing: '0.2px',
            background: 'var(--pink-soft)', border: '1px solid var(--pink-border)', color: 'var(--pink)',
          }}>
            {PHASE_LABELS[session.phase] || session.phase}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {session.turn_count} {session.turn_count === 1 ? 'turn' : 'turns'}
        </span>
        <div style={{ width: '80px', height: '3px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
          <div style={{
            width: `${Math.min(100, (session.turn_count / 10) * 100)}%`,
            height: '100%',
            background: 'var(--pink)',
            borderRadius: '2px',
            transition: 'width 0.4s ease',
          }} />
        </div>
      </div>
    </header>
  )
}
