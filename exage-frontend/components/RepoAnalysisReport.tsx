'use client'

import { RepoAnalysisResult, RankedGap } from '@/lib/types'

interface Props {
  result: RepoAnalysisResult
  onStartProbing?: (result: RepoAnalysisResult) => void
  isCreatingSession?: boolean
  readOnly?: boolean   // true when rendered inside chat as session history
}

const URGENCY_COLORS: Record<string, string> = {
  immediate: 'var(--pink)',
  soon: '#f0a070',
  eventually: 'var(--border)',
}

export default function RepoAnalysisReport({
  result,
  onStartProbing,
  isCreatingSession,
  readOnly = false,
}: Props) {
  return (
    <div style={{
      flex: 1, overflowY: readOnly ? 'visible' : 'auto',
      padding: readOnly ? '0' : '40px 48px',
      maxWidth: '760px',
      margin: readOnly ? '0' : '0 auto',
      width: '100%',
    }}>

      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '0.5px' }}>
            {result.repo_name}
          </div>
          <div style={{ width: '1px', height: '12px', background: 'var(--border)' }} />
          <div style={{ fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
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
          {readOnly && (
            <span style={{
              fontSize: '10.5px', padding: '2px 8px', borderRadius: '20px',
              fontWeight: 500, background: 'var(--bg)',
              border: '1px solid var(--border)', color: 'var(--text-muted)',
            }}>
              analysis
            </span>
          )}
        </div>

        <div style={{ fontSize: '18px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '8px' }}>
          {result.framework_context}
        </div>

        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {result.overall_assessment}
        </div>
      </div>

      {/* Coverage score */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <div style={{ flex: 1, height: '3px', background: 'var(--border)', borderRadius: '2px' }}>
          <div style={{
            width: `${result.technology_coverage_score}%`,
            height: '100%', background: 'var(--pink)', borderRadius: '2px',
          }} />
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          {result.technology_coverage_score}% coverage
        </div>
      </div>

      {/* Strongest areas */}
      {result.strongest_areas.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
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
      <div style={{ marginBottom: '24px' }}>
        <div style={sectionLabel}>Top gaps for {result.learning_goal}</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {result.ranked_gaps.map((gap, i) => (
            <GapCard key={i} gap={gap} />
          ))}
        </div>
      </div>

      {/* Analysis summary */}
      <div style={{
        padding: '14px 16px',
        background: 'var(--bg)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        marginBottom: readOnly ? '0' : '32px',
      }}>
        <div style={sectionLabel}>Analysis</div>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.65 }}>
          {result.analysis_summary}
        </div>
      </div>

      {/* Start probing button — only in non-readOnly mode */}
      {!readOnly && onStartProbing && (
        <>
          <button
            onClick={() => onStartProbing(result)}
            disabled={isCreatingSession}
            style={{
              width: '100%', padding: '13px', marginTop: '24px',
              background: isCreatingSession ? 'var(--border)' : 'var(--pink)',
              color: isCreatingSession ? 'var(--text-muted)' : 'white',
              border: 'none', borderRadius: '8px',
              fontFamily: 'var(--font)', fontSize: '14px', fontWeight: 500,
              cursor: isCreatingSession ? 'not-allowed' : 'pointer',
            }}
          >
            {isCreatingSession ? 'Starting session…' : 'Start probing these gaps →'}
          </button>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '10px' }}>
            Opens an ExAge chat session pre-loaded with your top {result.ranked_gaps.length} gaps
          </div>
        </>
      )}
    </div>
  )
}

function GapCard({ gap }: { gap: RankedGap }) {
  return (
    <div style={{
      padding: '14px 16px',
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '7px', height: '7px', borderRadius: '50%', flexShrink: 0,
            background: URGENCY_COLORS[gap.urgency] || 'var(--border)',
          }} />
          <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
            {gap.concept}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '5px' }}>
          {gap.gap_category === 'domain_core' && (
            <span style={{
              fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
              background: 'var(--pink-soft)', border: '1px solid var(--pink-border)',
              color: 'var(--pink)', fontWeight: 500,
            }}>core</span>
          )}
          <span style={{
            fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
            background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text-muted)',
          }}>{gap.gap_type}</span>
          <span style={{
            fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
            background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text-muted)',
          }}>{gap.urgency}</span>
        </div>
      </div>
      <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '8px' }}>
        {gap.consequence_for_goal}
      </div>
      <div style={{
        padding: '8px 12px', background: 'var(--bg)', borderRadius: '6px',
        borderLeft: '2px solid var(--border)',
      }}>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
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
  letterSpacing: '0.7px', textTransform: 'uppercase', marginBottom: '10px',
}
