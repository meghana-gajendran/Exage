'use client'

import { useState } from 'react'
import { LearningGoal } from '@/lib/types'

const GOALS: { value: LearningGoal; label: string; desc: string }[] = [
  { value: 'interview', label: 'Interview prep', desc: 'Gaps most likely to be probed by an interviewer' },
  { value: 'project', label: 'Building a project', desc: 'Gaps that could cause production issues' },
  { value: 'teaching', label: 'Teaching others', desc: 'Gaps in your ability to explain the why' },
  { value: 'exam', label: 'Exam preparation', desc: 'Gaps in theoretical understanding' },
  { value: 'curiosity', label: 'General curiosity', desc: 'Gaps that unlock deeper understanding' },
]

interface Props {
  onAnalyse: (repoInput: string, goal: LearningGoal) => void
  onBack: () => void
}

export default function RepoInputModal({ onAnalyse, onBack }: Props) {
  const [repoInput, setRepoInput] = useState('')
  const [goal, setGoal] = useState<LearningGoal | null>(null)

  const isGitHub = repoInput.trim().startsWith('https://github.com/')
  const isLocal = repoInput.trim().startsWith('/') || repoInput.trim().startsWith('~')
  const isValid = (isGitHub || isLocal) && goal !== null

  const inputHint = repoInput.trim() === ''
    ? 'GitHub URL or local path'
    : isGitHub
      ? '✓ GitHub repository'
      : isLocal
        ? '✓ Local folder path'
        : 'Enter a GitHub URL (https://github.com/…) or local path (/Users/…)'

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
        maxWidth: '520px',
      }}>
        {/* Header */}
        <div style={{ marginBottom: '28px' }}>
          <button
            onClick={onBack}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontFamily: 'var(--font)', fontSize: '12px',
              color: 'var(--text-muted)', marginBottom: '12px',
              padding: 0, display: 'flex', alignItems: 'center', gap: '4px',
            }}
          >
            ← back
          </button>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '15px', fontWeight: 500, marginBottom: '6px' }}>
            Ex<span style={{ color: 'var(--pink)' }}>Age</span>
          </div>
          <div style={{ fontSize: '18px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
            Analyse a repository
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            ExAge will read your repository, infer what you understand, and surface the gaps that matter most for your goal.
          </div>
        </div>

        {/* Repo input */}
        <div style={{ marginBottom: '20px' }}>
          <label style={labelStyle}>Repository</label>
          <input
            type="text"
            value={repoInput}
            onChange={e => setRepoInput(e.target.value)}
            placeholder="https://github.com/owner/repo or /local/path"
            style={{
              width: '100%', padding: '10px 12px',
              border: `1px solid ${isValid || repoInput === '' ? 'var(--border)' : 'var(--border)'}`,
              borderRadius: '8px', fontFamily: 'var(--font)',
              fontSize: '13.5px', color: 'var(--text-primary)',
              background: 'var(--bg)', outline: 'none',
            }}
          />
          <div style={{
            fontSize: '11px', marginTop: '5px',
            color: isGitHub || isLocal || repoInput === '' ? 'var(--text-muted)' : 'var(--pink)',
          }}>
            {inputHint}
          </div>
        </div>

        {/* Goal selector */}
        <div style={{ marginBottom: '28px' }}>
          <label style={labelStyle}>What are you working toward?</label>
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
                  textAlign: 'left', cursor: 'pointer', fontFamily: 'var(--font)',
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

        {/* Submit */}
        <button
          onClick={() => goal && onAnalyse(repoInput.trim(), goal)}
          disabled={!isValid}
          style={{
            width: '100%', padding: '11px',
            background: isValid ? 'var(--pink)' : 'var(--border)',
            color: isValid ? 'white' : 'var(--text-muted)',
            border: 'none', borderRadius: '8px',
            fontFamily: 'var(--font)', fontSize: '13.5px', fontWeight: 500,
            cursor: isValid ? 'pointer' : 'not-allowed',
            transition: 'opacity 0.15s',
          }}
        >
          Analyse repository
        </button>
      </div>
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)',
  letterSpacing: '0.7px', textTransform: 'uppercase',
  display: 'block', marginBottom: '8px',
}
