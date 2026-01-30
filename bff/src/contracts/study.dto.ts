// Contratos que espelham os DTOs expostos pelo serviço "brain"
// Obs: mantemos snake_case para compatibilidade direta com a API

/**
 * Representa um item individual de estudo, como um flashcard gerado.
 */
export interface StudyItem {
  /** Identificador único do nó de conhecimento original (UUID) */
  id: string;

  /** Título do tópico */
  title: string;

  /** Tipo de item (ex: 'flashcard') */
  type: string;

  /** Nível de dificuldade (0.0 a 1.0) */
  difficulty: number;

  /** A pergunta do flashcard */
  question: string;

  /** Lista de opções de resposta */
  options: string[];

  /** Índice da resposta correta na lista de opções */
  correct_index: number;

  /** Explicação da resposta correta */
  explanation: string;
}


/**
 * Resposta retornada pelo Brain ao gerar um plano de estudo.
 */
export interface StudyPlanResponse {
  /** Identificador único do plano (UUID) */
  id: string;

  /** Identificador do estudante (UUID) */
  student_id: string;

  /** Data de criação do plano (ISO 8601) */
  created_at: string;

  /** Lista de itens de estudo detalhados que compõem o plano. */
  study_items: StudyItem[];

  /** Duração estimada do plano em minutos */
  estimated_duration_minutes: number;

  /** Nível de foco esperado (ex: LOW | MEDIUM | HIGH) */
  focus_level: string;
}

/**
 * Corpo da requisição recebida pelo BFF para gerar um plano de estudo.
 */
export interface GeneratePlanRequest {
  /** Identificador do estudante */
  studentId: string;
}
