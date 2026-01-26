// Baseado em brain/domain/entities/study_plan.py
export type StudyFocusLevel = 'review' | 'new_content' | 'reinforcement';

// Baseado em brain/application/dto/study_plan_dto.py
export interface StudyPlanDTO {
  id: string; // UUID
  student_id: string; // UUID
  created_at: string; // ISO Date
  knowledge_nodes: string[]; // Lista de UUIDs dos nós
  estimated_duration_minutes: number;
  focus_level: StudyFocusLevel;
}

// Baseado em brain/domain/entities/knowledge_node.py
export const ReviewGrade = {
  AGAIN: 1,
  HARD: 2,
  GOOD: 3,
  EASY: 4
} as const;

export type ReviewGradeValue = typeof ReviewGrade[keyof typeof ReviewGrade];
