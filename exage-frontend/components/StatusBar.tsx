'use client'

interface Props {
  text: string
}

export default function StatusBar({ text }: Props) {
  return (
    <div style={{
      padding: '10px 32px',
      borderTop: '1px solid var(--border-soft)',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      background: 'var(--surface)',
    }}>
      <div style={{
        width: '6px', height: '6px',
        borderRadius: '50%',
        background: 'var(--pink)',
        animation: 'pulse 1.5s ease-in-out infinite',
      }} />
      <span style={{
        fontSize: '11.5px',
        color: 'var(--text-muted)',
        fontFamily: 'var(--mono)',
      }}>
        {text}
      </span>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}
