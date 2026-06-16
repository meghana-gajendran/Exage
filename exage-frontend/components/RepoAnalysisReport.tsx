'use client'

import { RepoAnalysisResult, RankedGap } from '@/lib/types'

interface Props {
  result: RepoAnalysisResult
  onStartProbing: () => void
  isCreatingSession: boolean
}

const URGENCY_COLORS: Record<string, string> = {
  immediate: 'var(--pink)',
  soon: '#f0a070',
  eventually: 'var(--border)',
}

const URGENCY_LABELS: Record<string, string> = {
  immediate: 'immediate',
  soon: 'soon',
  eventually: 'eventually',
}

export default function RepoAnalysisReport({ result, onStartProbing, isCreatingSession }: Props) {
  return (
    <div style={{
      flex: 1, overflowY: 'auto',
      padding: '40px 48px',
      maxWidth: '760px',
      margin: '0 auto',
      width: '100%',
    }}>

      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div style={{
            fontFamily: 'var(--mono)', fontSize: '12px',
            color: 'var(--text-muted)', letterSpacing: '0.5px',
          }}>
            {result.repo_name}
          </div>
          <div style={{ width: '1px', height: '12px', background: 'var(--border)' }} />
          <div style={{
            fontFamily: 'var(--mono)', fontSize: '12px',
            color: 'var(--text-muted)',
          }}>
            {result.domain || result.frameworks.join(', ')}
          </div>
          <div style={{ width: '1px', height: '12px', background: 'var(--border)' }} />
          <span style={{
            fontSize: '10.5px', padding: '2px 8px', borderRadius: '20px',
            fontWeight: 500, background: 'var(--pink-soft)',
            border: '1px solid var(--pink-border)', color: 'var(--pink)',
          }}>
            {result.learning_goal}
          </span>
        </div>

        <div style={{ fontSize: '22px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '10px' }}>
          {result.framework_context}
        </div>

        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {result.overall_assessment}
        </div>
      </div>

      {/* Coverage score */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        marginBottom: '32px',
      }}>
        <div style={{ flex: 1, height: '3px', background: 'var(--border)', borderRadius: '2px' }}>
          <div style={{
            width: `${result.technology_coverage_score}%`,
            height: '100%', background: 'var(--pink)', borderRadius: '2px',
            transition: 'width 0.6s ease',
          }} />
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {result.technology_coverage_score}% coverage
        </div>
      </div>

      {/* Strongest areas */}
      {result.strongest_areas.length > 0 && (
        <div style={{ marginBottom: '32px' }}>
          <div style={sectionLabel}>Likely strong</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {result.strongest_areas.map((area, i) => (
              <span key={i} style={{
                fontSize: '12px', padding: '4px 10px',
                background: 'var(--bg)', border: '1px solid var(--border)',
                borderRadius: '20px', color: 'var(--text-secondary)',
              }}>
                {area}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Ranked gaps */}
      <div style={{ marginBottom: '32px' }}>
        <div style={sectionLabel}>
          Top gaps for {result.learning_goal}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {result.ranked_gaps.map((gap, i) => (
            <GapCard key={i} gap={gap} />
          ))}
        </div>
      </div>

      {/* Analysis summary */}
      <div style={{
        padding: '16px',
        background: 'var(--bg)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        marginBottom: '32px',
      }}>
        <div style={sectionLabel}>Analysis</div>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.65 }}>
          {result.analysis_summary}
        </div>
      </div>

      {/* Start probing CTA */}
      <button
        onClick={onStartProbing}
        disabled={isCreatingSession}
        style={{
          width: '100%', padding: '13px',
          background: isCreatingSession ? 'var(--border)' : 'var(--pink)',
          color: isCreatingSession ? 'var(--text-muted)' : 'white',
          border: 'none', borderRadius: '8px',
          fontFamily: 'var(--font)', fontSize: '14px', fontWeight: 500,
          cursor: isCreatingSession ? 'not-allowed' : 'pointer',
          transition: 'opacity 0.15s',
        }}
      >
        {isCreatingSession ? 'Starting session…' : 'Start probing these gaps →'}
      </button>

      <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '10px' }}>
        Opens an ExAge chat session pre-loaded with your top {result.ranked_gaps.length} gaps
      </div>
    </div>
  )
}

function GapCard({ gap }: { gap: RankedGap }) {
  const isCoreGap = gap.gap_category === 'domain_core'
  return (
    <div style={{
      padding: '16px',
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '7px', height: '7px', borderRadius: '50%', flexShrink: 0,
            background: URGENCY_COLORS[gap.urgency] || 'var(--border)',
          }} />
          <span style={{ fontSize: '13.5px', fontWeight: 500, color: 'var(--text-primary)' }}>
            {gap.concept}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
          {isCoreGap && (
            <span style={{
              fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
              background: 'var(--pink-soft)', border: '1px solid var(--pink-border)',
              color: 'var(--pink)', fontWeight: 500,
            }}>
              core
            </span>
          )}
          <span style={{
            fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
            background: 'var(--bg)', border: '1px solid var(--border)',
            color: 'var(--text-muted)',
          }}>
            {gap.gap_type}
          </span>
          <span style={{
            fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
            background: 'var(--bg)', border: '1px solid var(--border)',
            color: 'var(--text-muted)',
          }}>
            {URGENCY_LABELS[gap.urgency]}
          </span>
        </div>
      </div>

      <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '10px' }}>
        {gap.consequence_for_goal}
      </div>

      <div style={{
        padding: '10px 12px',
        background: 'var(--bg)',
        borderRadius: '6px',
        borderLeft: '2px solid var(--border)',
      }}>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
          Probing question
        </div>
        <div style={{ fontSize: '12.5px', color: 'var(--text-primary)', lineHeight: 1.55, fontStyle: 'italic' }}>
          "{gap.probing_question}"
        </div>
      </div>
    </div>
  )
}

const sectionLabel: React.CSSProperties = {
  fontSize: '10px', fontWeight: 500, color: 'var(--text-muted)',
  letterSpacing: '0.7px', textTransform: 'uppercase', marginBottom: '12px',
}
