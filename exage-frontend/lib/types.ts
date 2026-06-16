// ── Option 1 types ────────────────────────────────────────────────

export type LearningGoal = 'exam' | 'interview' | 'project' | 'teaching' | 'curiosity'
export type Phase = 'onboarding' | 'probing' | 'synthesis'
export type GapSeverity = 'critical' | 'important' | 'nice-to-know'

export interface Gap {
  concept: string
  severity: GapSeverity
  why_it_matters_for_goal: string
}

export interface Session {
  id: string
  topic: string
  learning_goal: LearningGoal
  phase: Phase
  turn_count: number
}

export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  gaps?: Gap[]
  isStreaming?: boolean
  isSynthesis?: boolean
  synthesisData?: SynthesisData
}

export interface SynthesisCuriosityPath {
  title: string
  description: string
  starter_question: string
}

export interface SynthesisMisconception {
  concept: string
  what_to_revisit: string
}

export interface SynthesisGap {
  concept: string
  severity: GapSeverity
  one_line: string
}

export interface SynthesisData {
  opening: string
  gaps_summary: SynthesisGap[]
  misconceptions_summary: SynthesisMisconception[]
  curiosity_paths: SynthesisCuriosityPath[]
  closing_thought: string
}

export type SSEEventType = 'status' | 'token' | 'done' | 'error' | 'synthesis'

export interface SSEEvent {
  type: SSEEventType
  text?: string
  phase?: Phase
  turn?: number
  gaps?: Gap[]
  data?: SynthesisData
}

// ── Option 2 types ────────────────────────────────────────────────

export type GapCategory = 'domain_core' | 'general_practice'
export type GapUrgency = 'immediate' | 'soon' | 'eventually'

export interface RankedGap {
  rank: number
  concept: string
  gap_type: 'missing' | 'shallow'
  gap_category: GapCategory
  consequence_for_goal: string
  urgency: GapUrgency
  probing_question: string
  what_a_good_answer_shows: string
}

export interface RepoAnalysisResult {
  repo_name: string
  input_type: 'local' | 'github'
  learning_goal: LearningGoal
  frameworks: string[]
  framework_context: string
  domain: string
  overall_assessment: string
  strongest_areas: string[]
  weakest_signals: string[]
  ranked_gaps: RankedGap[]
  analysis_summary: string
  technology_coverage_score: number
  session_context: RepoSessionContext
}

export interface RepoSessionContext {
  topic: string
  learning_goal: LearningGoal
  phase: Phase
  known_concepts: string[]
  open_gaps: Gap[]
  asked_gaps: string[]
  misconceptions: string[]
  repo_context: {
    repo_name: string
    domain: string
    framework_context: string
    overall_assessment: string
    probing_questions: string[]
  }
}

export type RepoSSEEvent =
  | { type: 'status'; text: string }
  | { type: 'done'; result: RepoAnalysisResult }
  | { type: 'error'; text: string }
