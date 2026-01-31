export interface StudyContent {
  front: string;
  options: string[];
  correct_index: number;
  back?: string;
}

export interface StudyItem {
  id: string;
  type: string;

  // Formato plano (frontend antigo)
  front?: string;
  options?: string[];
  correct_index?: number;
  explanation?: string;

  // Formato aninhado (backend)
  content?: StudyContent;

  // Metadados opcionais
  estimated_time_minutes?: number;
  difficulty?: number;
  status?: string;
  stability?: number;
  current_retention?: number;
  topic_roi?: string;
}

export interface StudySession {
  id: string;
  topic: string;
  start_time?: string;
  duration_minutes?: number;
  items?: StudyItem[];
  focus_level?: string;
  method?: string;
}

export interface StudyPlan {
  id: string;
  student_id: string;
  goals?: string[];
  created_at?: string;
  estimated_duration_minutes?: number;
  focus_level?: string;
  study_items?: StudyItem[];
  sessions?: StudySession[];
  status?: string;
}