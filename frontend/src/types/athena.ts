export enum ReviewGrade {
  AGAIN = 1,
  HARD = 2,
  GOOD = 3,
  EASY = 4,
}

export type ReviewGradeValue = ReviewGrade;

/**
 * Representa um único nó de conhecimento com seus detalhes.
 */
export interface KnowledgeNode {
  id: string;
  title: string;
  context: string;
  difficulty: number;
}

/**
 * Representa o plano de estudos completo retornado pelo BFF.
 * A resposta do BFF/Brain foi enriquecida para incluir os detalhes de cada nó.
 */
export interface StudyPlanDTO {
  knowledge_nodes: KnowledgeNode[];
  focus_level: number;
  student_id: string;
  created_at: string;
  estimated_duration_minutes: number;
}