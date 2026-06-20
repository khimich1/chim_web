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
  first_login_at: string | null;
  onboarding_completed_at: string | null;
  is_activated: boolean;
}

export interface OnboardingChecklist {
  login: boolean;
  first_action: boolean;
  lecture: boolean;
}

export interface OnboardingStatus {
  first_login_at: string | null;
  onboarding_completed_at: string | null;
  checklist: OnboardingChecklist;
  needs_welcome: boolean;
}

export type RecommendedActionKind = "homework" | "diagnostic_test" | "textbook";

export interface RecommendedAction {
  kind: RecommendedActionKind;
  label: string;
  homework_id: string | null;
  variant_ref: string | null;
  textbook_topic: string | null;
}

export interface OnboardingWelcome extends OnboardingStatus {
  recommended_action: RecommendedAction;
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
export type TestSessionSource = "exam" | "custom";
export type StepStatus = "unseen" | "answered" | "checked";
export type GradingMode = "auto" | "self_check";

export interface ContentBlock {
  type: "text" | "image";
  content?: string | null;
  url?: string | null;
}
export type HomeworkStatus = "assigned" | "in_progress" | "submitted" | "reviewed";
export type HomeworkItemKind =
  | "lecture"
  | "test_variant"
  | "test_partial"
  | "test_by_type"
  | "custom_theme";
export type NotificationType = "homework_submitted";

export interface TestVariant {
  filename: string;
}

export interface TestTaskType {
  type: number;
  variant_count: number;
}

export interface TestStep {
  position: number;
  test_id: number | null;
  custom_task_id?: string | null;
  type: number | null;
  question: string | null;
  options: string | null;
  question_blocks?: ContentBlock[] | null;
  grading_mode?: GradingMode | null;
  status: StepStatus;
  answer: string | null;
  is_correct: boolean | null;
  hint_used: boolean;
}

export interface TestSession {
  id: string;
  track: Track;
  source?: TestSessionSource;
  variant_ref: string | null;
  homework_assignment_id: string | null;
  custom_theme_id?: string | null;
  status: TestSessionStatus;
  score: number | null;
  max_score: number | null;
  total_steps: number;
  steps: TestStep[];
  created_at: string;
}

export interface StudentStats {
  student_id: string;
  total_points: number;
  week_points: number;
  current_streak: number;
  longest_streak: number;
  last_active_date: string | null;
  tasks_solved: number;
  total_minutes: number;
  updated_at: string | null;
}

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  points: number;
}

/** GET /api/teacher/students/stats — teacher-facing student metrics (Task 62). */
export interface TeacherStudentStats {
  id: string;
  email: string;
  display_name: string | null;
  total_points: number;
  week_points: number;
  streak: number;
  tasks_solved: number;
  total_minutes: number;
  last_active_date: string | null;
}

export interface StepCheckResult {
  position: number;
  is_correct: boolean;
  status: StepStatus;
}

export interface StepCompareResult {
  position: number;
  status: StepStatus;
  reference_answer: ContentBlock[];
}

export interface UploadImageResponse {
  id: string;
  url: string;
}

export interface TeacherTheme {
  id: string;
  teacher_id: string;
  title: string;
  description: string | null;
  is_published: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface TeacherThemeCreateInput {
  title: string;
  description?: string | null;
  is_published?: boolean;
  sort_order?: number;
}

export interface TeacherThemeUpdateInput {
  title?: string;
  description?: string | null;
  is_published?: boolean;
  sort_order?: number;
}

export interface CustomTask {
  id: string;
  theme_id: string;
  title: string | null;
  sort_order: number;
  grading_mode: GradingMode;
  question_blocks: ContentBlock[];
  reference_answer: ContentBlock[] | null;
  correct_value: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomTaskCreateInput {
  title?: string | null;
  sort_order?: number;
  grading_mode: GradingMode;
  question_blocks: ContentBlock[];
  reference_answer?: ContentBlock[] | null;
  correct_value?: string | null;
}

export interface CustomTaskUpdateInput {
  title?: string | null;
  sort_order?: number;
  grading_mode?: GradingMode;
  question_blocks?: ContentBlock[];
  reference_answer?: ContentBlock[] | null;
  correct_value?: string | null;
}

export interface CustomThemeListItem {
  id: string;
  title: string;
  description: string | null;
  task_count: number;
  sort_order: number;
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
  variants?: string[] | null;
}

export interface CustomThemeHomeworkItem {
  kind: "custom_theme";
  theme_id: string;
  task_ids?: string[] | null;
}

export type HomeworkItem =
  | LectureHomeworkItem
  | TestVariantHomeworkItem
  | TestPartialHomeworkItem
  | TestByTypeHomeworkItem
  | CustomThemeHomeworkItem;

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
