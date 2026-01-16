// Contratos que espelham os DTOs expostos pelo serviço "brain"
// Obs: mantemos snake_case para compatibilidade direta com a API

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

  /** Lista de IDs dos nós de conhecimento incluídos no plano */
  knowledge_nodes: string[];

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
