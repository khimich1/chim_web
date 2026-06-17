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
export type HomeworkStatus = "assigned" | "in_progress" | "submitted" | "reviewed";
export type HomeworkItemKind =
  | "lecture"
  | "test_variant"
  | "test_partial"
  | "test_by_type";
export type NotificationType = "homework_submitted";

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
  variant_ref: string | null;
  homework_assignment_id: string | null;
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
}

export interface ActiveSessionResult {
  session_id: string | null;
}

export interface LectureHomeworkItem {
  kind: "lecture";
  topic: string;
  chunk_idxs?: number[] | null;
}

export interface TestVariantHomeworkItem {
  kind: "test_variant";
  variant: string;
}

export interface TestPartialHomeworkItem {
  kind: "test_partial";
  variant: string;
  types: number[];
}

export interface TestByTypeHomeworkItem {
  kind: "test_by_type";
  types: number[];
}

export type HomeworkItem =
  | LectureHomeworkItem
  | TestVariantHomeworkItem
  | TestPartialHomeworkItem
  | TestByTypeHomeworkItem;

export interface HomeworkSubmission {
  id: string;
  submitted_at: string;
  test_session_id: string | null;
  score: number | null;
  max_score: number | null;
}

export interface HomeworkItemProgress {
  item_index: number;
  kind: HomeworkItemKind;
  completed: boolean;
}

export interface HomeworkAssignment {
  id: string;
  student_id: string;
  student_email: string | null;
  title: string;
  description: string | null;
  due_at: string | null;
  items: HomeworkItem[];
  status: HomeworkStatus;
  created_at: string;
  submission: HomeworkSubmission | null;
  progress: HomeworkItemProgress[];
  active_test_session_id: string | null;
}

export interface CreateHomeworkInput {
  student_id: string;
  title: string;
  description?: string | null;
  due_at?: string | null;
  items: HomeworkItem[];
}

export interface Notification {
  id: string;
  type: NotificationType;
  payload: {
    homework_id: string;
    homework_title: string;
    student_id: string;
    student_email: string;
  };
  read_at: string | null;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}
