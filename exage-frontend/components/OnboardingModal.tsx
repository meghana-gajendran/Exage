'use client'

import { useState } from 'react'
import { LearningGoal } from '@/lib/types'

const GOALS: { value: LearningGoal; label: string; desc: string }[] = [
  { value: 'interview', label: 'Interview prep', desc: 'Identify gaps before a technical interview' },
  { value: 'exam', label: 'Exam preparation', desc: 'Strengthen weak areas before an exam' },
  { value: 'project', label: 'Building a project', desc: 'Understand what you need to know to ship' },
  { value: 'teaching', label: 'Teaching others', desc: 'Find the gaps in your ability to explain' },
  { value: 'curiosity', label: 'General curiosity', desc: 'Explore a topic more deeply' },
]

interface Props {
  onStart: (topic: string, goal: LearningGoal) => void
}

export default function OnboardingModal({ onStart }: Props) {
  const [topic, setTopic] = useState('')
  const [goal, setGoal] = useState<LearningGoal | null>(null)
  const [loading, setLoading] = useState(false)

  const handleStart = async () => {
    if (!topic.trim() || !goal) return
    setLoading(true)
    await onStart(topic.trim(), goal)
    setLoading(false)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 50,
      background: 'rgba(250,250,249,0.92)',
      backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '24px',
    }}>
      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '36px',
        width: '100%',
        maxWidth: '480px',
      }}>
        <div style={{ marginBottom: '28px' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '15px', fontWeight: 500, marginBottom: '6px' }}>
            Ex<span style={{ color: 'var(--pink)' }}>Age</span>
          </div>
          <div style={{ fontSize: '18px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
            What are you working on?
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            ExAge will probe your understanding and surface what you don't yet know.
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.7px', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
            Topic
          </label>
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            placeholder="e.g. Kubernetes, React Hooks, System Design…"
            onKeyDown={e => e.key === 'Enter' && handleStart()}
            style={{
              width: '100%',
              padding: '10px 12px',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              fontFamily: 'var(--font)',
              fontSize: '13.5px',
              color: 'var(--text-primary)',
              background: 'var(--bg)',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ marginBottom: '28px' }}>
          <label style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.7px', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
            Learning goal
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {GOALS.map(g => (
              <button
                key={g.value}
                onClick={() => setGoal(g.value)}
                style={{
                  padding: '10px 12px',
                  border: `1px solid ${goal === g.value ? 'var(--pink-border)' : 'var(--border)'}`,
                  borderRadius: '8px',
                  background: goal === g.value ? 'var(--pink-soft)' : 'var(--bg)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontFamily: 'var(--font)',
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 500, color: goal === g.value ? 'var(--pink)' : 'var(--text-primary)' }}>
                  {g.label}
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {g.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={!topic.trim() || !goal || loading}
          style={{
            width: '100%',
            padding: '11px',
            background: (!topic.trim() || !goal) ? 'var(--border)' : 'var(--pink)',
            color: (!topic.trim() || !goal) ? 'var(--text-muted)' : 'white',
            border: 'none',
            borderRadius: '8px',
            fontFamily: 'var(--font)',
            fontSize: '13.5px',
            fontWeight: 500,
            cursor: (!topic.trim() || !goal) ? 'not-allowed' : 'pointer',
            transition: 'opacity 0.15s',
          }}
        >
          {loading ? 'Starting…' : 'Begin session'}
        </button>
      </div>
    </div>
  )
}
