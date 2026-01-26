import axios from 'axios';
import type { StudyPlanDTO } from '../types/athena';

// Aponta para o BFF (Backend for Frontend)
const api = axios.create({
  baseURL: 'http://localhost:3000', // Porta padrão do Express/BFF
});

export const studyService = {
  /**
   * Solicita ao Brain a geração de um plano adaptativo
   */
  generatePlan: async (studentId: string): Promise<StudyPlanDTO> => {
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
