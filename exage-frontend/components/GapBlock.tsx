'use client'

import { Gap } from '@/lib/types'

interface Props {
  gaps: Gap[]
}

const DOT_COLORS: Record<string, string> = {
  'critical': 'var(--pink)',
  'important': '#f0a070',
  'nice-to-know': 'var(--border)',
}

export default function GapBlock({ gaps }: Props) {
  if (!gaps.length) return null

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '14px 16px',
      maxWidth: '480px',
      marginTop: '6px',
    }}>
      <div style={{
        fontSize: '10px',
        fontWeight: 500,
        color: 'var(--text-muted)',
        letterSpacing: '0.7px',
        textTransform: 'uppercase',
        marginBottom: '10px',
      }}>
        Gaps detected this turn
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {gaps.map((gap, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '6px', height: '6px',
              borderRadius: '50%',
              flexShrink: 0,
              background: DOT_COLORS[gap.severity] || 'var(--border)',
            }} />
            <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
              {gap.concept}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
