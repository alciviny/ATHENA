import axios from 'axios';
import type { StudyPlan } from '../types/athena';

// O proxy no vite.config.ts cuidará do redirecionamento.
const api = axios.create({});

export const studyService = {
  /**
   * Solicita ao Brain a geração de um plano adaptativo.
   * Assume um studentId fixo para este exemplo.
   */
  generatePlan: async (): Promise<StudyPlan> => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    // O /api/ no início da URL será interceptado pelo proxy do Vite.
    const response = await api.post(`/api/study/generate-plan/${studentId}`);
    return response.data;
  },

  /**
   * Envia o feedback de revisão (SRS)
   */
  submitReview: async (
    nodeId: string,
    grade: number,
    responseTime: number
  ) => {
    // O mesmo studentId hardcoded usado em generatePlan.
    // Em um app real, isso viria do estado de autenticação do usuário.
    const student_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

    // O backend espera um booleano `success`, não o `grade` numérico.
    // Mapeamento: 1 (De novo), 2 (Difícil) -> false
    //             3 (Bom), 4 (Fácil) -> true
    const success = grade > 2;

    return api.post(`/api/study/review/${nodeId}`, {
      student_id,
      success,
      response_time_seconds: responseTime,
    });
  },
};

