
export interface KnowledgeNode {
  id: string;
  name: string;
  subject: string;
  weight_in_exam: number;
  stability: number;
  difficulty: number;
  reps: number;
  lapses: number;
  last_reviewed_at: string | null;
  next_review_at: string;
  roi_score: number;
  status: 'VEIO_DE_OURO' | 'PANTANO' | 'NORMAL' | 'DOMINADO';
}

export interface RoiReport {
  nodes: KnowledgeNode[];
  links: { source: string; target: string; }[];
}

export interface StudyPlan {
  id: string;
  student_id: string;
  created_at: string;
  estimated_duration_minutes: number;
  focus_level: string;
  sessions: StudySession[];
  flashcards: StudyItem[];
}

export interface StudySession {
    id: string;
    topic: string;
    duration_minutes: number;
    items: StudyItem[];
    focus_level: string;
}

export interface StudyItem {
  id: string;
  type: string;
  content: {
    front: string;
    back: string;
    options: string[];
    correct_index: number;
  };
  front: string;
  options: string[];
  correct_index: number;
  explanation: string;
  stability: number;
  current_retention: number;
  topic_roi: string;
}
