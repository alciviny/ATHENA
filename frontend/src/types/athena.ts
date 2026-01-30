export interface StudyItem {
  id: string;
  title: string;
  type: 'flashcard' | 'problem';
  difficulty: number;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  // Novos metadados
  stability: number;
  current_retention: number;
  topic_roi: 'VEIO_DE_OURO' | 'PANTANO' | 'NORMAL';
}

export interface StudyPlan {
  id: string;
  student_id: string;
  created_at: string;
  study_items: StudyItem[];
  estimated_duration_minutes: number;
  focus_level: string;
}
