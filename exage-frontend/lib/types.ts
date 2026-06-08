export type LearningGoal =
  | "exam"
  | "interview"
  | "project"
  | "teaching"
  | "curiosity";

export type Phase = "onboarding" | "probing" | "synthesis";

export type GapSeverity = "critical" | "important" | "nice-to-know";

export interface Gap {
  concept: string;
  severity: GapSeverity;
  why_it_matters_for_goal: string;
}

export interface Session {
  id: string;
  topic: string;
  learning_goal: LearningGoal;
  phase: Phase;
  turn_count: number;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  gaps?: Gap[];
  isStreaming?: boolean;
  isSynthesis?: boolean;
  synthesisData?: SynthesisData;
}

export interface SynthesisCuriosityPath {
  title: string;
  description: string;
  starter_question: string;
}

export interface SynthesisMisconception {
  concept: string;
  what_to_revisit: string;
}

export interface SynthesisGap {
  concept: string;
  severity: GapSeverity;
  one_line: string;
}

export interface SynthesisData {
  opening: string;
  gaps_summary: SynthesisGap[];
  misconceptions_summary: SynthesisMisconception[];
  curiosity_paths: SynthesisCuriosityPath[];
  closing_thought: string;
}

export type SSEEventType = "status" | "token" | "done" | "error" | "synthesis";

export interface SSEEvent {
  type: SSEEventType;
  text?: string;
  phase?: Phase;
  turn?: number;
  gaps?: Gap[];
  data?: SynthesisData;
}
