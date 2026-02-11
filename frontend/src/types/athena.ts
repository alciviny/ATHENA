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

  flashcards?: StudyItem[];

  status?: string;

}



export interface KnowledgeNode {
  id: string;
  name?: string; // Algumas vezes vem como name
  topic?: string; // Backend pode enviar como topic
  subject?: string;
  roi_score: number;
  roi_status?: string; // High, Medium, Low
  difficulty: number;
  stability: number;
  weight?: number;
  status?: string;
  x?: number;
  y?: number;
}

export interface RoiReport {
  nodes: KnowledgeNode[];
  links: { source: string; target: string; }[];
  overall_roi?: number;
}



  export interface FeynmanResult {

    score: number;

    is_accurate: boolean;

    missing_concepts: string[];

    feedback: string;

  }

    