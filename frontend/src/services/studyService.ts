import axios from 'axios';
import type { StudyPlanDTO } from '../types/athena';

// O proxy no vite.config.ts cuidará do redirecionamento.
const api = axios.create({});

export const studyService = {
  /**
   * Solicita ao Brain a geração de um plano adaptativo.
   * Assume um studentId fixo para este exemplo.
   */
  generatePlan: async (): Promise<StudyPlanDTO> => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    // O /api/ no início da URL será interceptado pelo proxy do Vite.
    const response = await api.post('/api/study/generate', { studentId });
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
    return api.post(`/api/study/review/${nodeId}`, {
      grade,
      response_time_seconds: responseTime,
    });
  },
};

