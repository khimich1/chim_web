export type Role = "teacher" | "student";
export type Track = "ege" | "oge";

export interface User {
  id: string;
  email: string;
  role: Role;
  track: Track | null;
}

export interface Student {
  id: string;
  email: string;
  track: Track;
  created_at: string;
}

export interface TextbookTopic {
  topic: string;
  chunk_count: number;
}

export interface ChunkSummary {
  chunk_idx: number;
  chunk_title: string;
  has_audio: boolean;
}

export interface TextbookChunk extends ChunkSummary {
  topic: string;
  lecture: string;
}

export type TestSessionStatus = "in_progress" | "completed";
export type StepStatus = "unseen" | "answered" | "checked";

export interface TestVariant {
  filename: string;
}

export interface TestStep {
  position: number;
  test_id: number;
  type: number;
  question: string;
  options: string | null;
  status: StepStatus;
  answer: string | null;
  is_correct: boolean | null;
  hint_used: boolean;
}

export interface TestSession {
  id: string;
  track: Track;
  variant_ref: string;
  status: TestSessionStatus;
  score: number | null;
  max_score: number | null;
  total_steps: number;
  steps: TestStep[];
}

export interface StepCheckResult {
  position: number;
  is_correct: boolean;
  status: StepStatus;
  detailed_explanation: string | null;
}

export interface HintResult {
  hint: string | null;
}
