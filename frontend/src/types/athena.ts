export interface StudyContent {
  front: string;
  options: string[];
  correct_index: number;
  back: string;
}

export interface StudyItem {
  id: string;
  type: string;
  content: StudyContent;
  estimated_time_minutes: number;
  difficulty: number;
  status: string;
}

export interface StudySession {
  id: string;
  topic: string;
  start_time: string;
  duration_minutes: number;
  items: StudyItem[];
  focus_level: string;
  method: string;
}

export interface StudyPlan {
  id: string;
  student_id: string;
  goals: string[];
  created_at: string;
  sessions: StudySession[]; // Nova estrutura hierárquica
  status: string;
}