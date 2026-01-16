// src/modules/study/study.service.ts
import axios from 'axios';
import { StudyPlanResponse } from '../../contracts/study.dto';
import { isAxiosError } from './isAxiosError';

// ================================
// Configurações
// ================================

// URL base da API do Brain
const BRAIN_API_URL =
  process.env.BRAIN_API_URL || 'http://localhost:8000/api/v1';

// Timeout padrão para evitar requests penduradas
const REQUEST_TIMEOUT_MS = 5000;

// ================================
// Service
// ================================

/**
 * Chama o Brain para gerar um novo plano de estudo.
 *
 * @param studentId O ID do estudante.
 * @returns Plano de estudo gerado pelo Brain.
 */
export async function generateStudyPlan(
  studentId: string
): Promise<StudyPlanResponse> {
  try {
    const response = await axios.post<StudyPlanResponse>(
      `${BRAIN_API_URL}/study/generate-plan/${studentId}`,
      undefined,
      {
        timeout: REQUEST_TIMEOUT_MS,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    return response.data;

  } catch (error: unknown) {
    // ================================
    // Erro conhecido (Axios)
    // ================================
    if (isAxiosError(error)) {
      const status = error.response?.status;
      const detail =
        (error.response?.data as any)?.detail ??
        error.message;

      console.error('Brain API request failed', {
        method: error.config?.method,
        url: error.config?.url,
        status,
        detail,
      });

      throw new Error(
        `Failed to generate study plan from Brain API (${status ?? 'unknown'}): ${detail}`
      );
    }

    // ================================
    // Erro desconhecido
    // ================================
    console.error('Unexpected error while calling Brain API', error);

    throw new Error(
      'Unexpected error occurred while contacting the Brain API.'
    );
  }
}
