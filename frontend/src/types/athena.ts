export enum ReviewGrade {
  AGAIN = 1,
  HARD = 2,
  GOOD = 3,
  EASY = 4,
}

export type ReviewGradeValue = ReviewGrade;

/**
 * Representa um único item de estudo, como um flashcard gerado por IA.
 */
export interface StudyItem {
  id: string;
  title: string;
  type: string;
  difficulty: number;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

/**
 * Representa o plano de estudos completo retornado pelo BFF.
 */
export interface StudyPlanDTO {
  id: string;
  student_id: string;
  created_at: string;
  study_items: StudyItem[];
  estimated_duration_minutes: number;
  focus_level: string;
}