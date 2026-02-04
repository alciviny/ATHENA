import axios from 'axios';
import type { StudyPlan, StudyItem, StudySession, RoiReport, FeynmanResult } from '../types/athena';

interface BackendSession {
  topic: string;
  items: BackendItem[];
}

interface BackendItem {
  id: string;
  topic_roi: string;
  content: {
    front: string;
    back: string;
    options: string[];
    correct_index: number;
  };
}

interface BackendFlashcard {
  pergunta: string;
  explicacao: string;
  opcoes?: string[];
  correta_index?: number;
}

const api = axios.create({
  timeout: 120000, // 2 minutos
});

export const studyService = {
  getRoiReport: async (): Promise<RoiReport> => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const response = await api.get(`/api/students/${studentId}/graph`);
    return response.data;
  },

  generatePlan: async (): Promise<StudyPlan> => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    let response;
    try {
      response = await api.post(`/api/study/generate-plan/${studentId}`);
    } catch (err) {
      // Detecta timeout do Axios de forma segura
      if (axios.isAxiosError(err)) {
        const code = err.code;
        const message = err.message ?? '';
        if (code === 'ECONNABORTED' || message.toLowerCase().includes('timeout')) {
          throw new Error('TIMEOUT_GENERATE_PLAN');
        }
      }
      throw err;
    }
    
    // --- ADAPTADOR (CORREÇÃO) ---
    // O backend retorna uma estrutura aninhada (sessions -> items -> content).
    // O frontend espera uma lista plana de 'study_items'.
    
    const backendData = response.data;
    // DEBUG: expõe payload bruto para inspeção no console do navegador
    try {
      // eslint-disable-next-line no-console
      console.log('studyService.generatePlan - backendData:', backendData);
      // Expor globalmente para fácil inspeção no DevTools
      (window as unknown as { __LAST_STUDY_PLAN_RESPONSE: unknown }).__LAST_STUDY_PLAN_RESPONSE = backendData;
    } catch {
      // ignore
    }
    
    // 1. Constrói as `sessions` no formato que o App espera
    const sessions: StudySession[] = [];

    if (backendData.sessions && Array.isArray(backendData.sessions)) {
      backendData.sessions.forEach((session: BackendSession, sIdx: number) => {
        const items: StudyItem[] = [];
        if (session.items && Array.isArray(session.items)) {
          session.items.forEach((item: BackendItem) => {
            items.push({
              id: item.id,
              type: 'flashcard',
              // mantém o formato aninhado também, para compatibilidade
              content: item.content,
              // campos adicionais antigos mantidos para compatibilidade com componentes mais simples
              front: item.content?.front,
              options: item.content?.options,
              correct_index: item.content?.correct_index,
              explanation: item.content?.back,
              stability: 1.0,
              current_retention: 0.9,
              topic_roi: item.topic_roi, // Mapeia o rótulo estratégico do backend
            });
          });
        }

        sessions.push({
          id: `${backendData.id || 'plan'}-s${sIdx}`,
          topic: session.topic,
          duration_minutes: items.length * 2 || 0,
          items,
          focus_level: backendData.focus_level || 'GERAL'
        });
      });
    }

    // 2. Converte flashcards (se existirem) para o formato interno
    const flashcards = (backendData.flashcards && Array.isArray(backendData.flashcards))
      ? backendData.flashcards.map((c: BackendFlashcard, idx: number) => ({
          id: `fc-${idx}-${c.pergunta?.slice(0,10)}`,
          type: 'flashcard',
          content: {
            front: c.pergunta,
            back: c.explicacao,
            options: c.opcoes || [],
            correct_index: c.correta_index ?? 0,
          }
        }))
      : [];

    // 3. Se não houver sessões, mas houver flashcards, cria uma sessão "Flashcards"
    if ((sessions.length === 0 || !sessions) && flashcards.length > 0) {
      sessions.push({
        id: `${backendData.id || 'plan'}-flashcards`,
        topic: 'Flashcards',
        duration_minutes: flashcards.length * 2,
        items: flashcards,
        focus_level: backendData.focus_level || 'GERAL'
      });
    }

    // 4. Retorna o objeto no formato que o React espera (incluindo `sessions` e `flashcards`)
    return {
      id: backendData.id,
      student_id: backendData.student_id,
      created_at: backendData.created_at,
      estimated_duration_minutes: backendData.estimated_duration_minutes || 15,
      focus_level: backendData.focus_level || 'Deep Work',
      sessions,
      flashcards,
    };
  },

  startSimulator: async (numQuestions?: number, timeLimit?: number, stressLevel?: number): Promise<StudyPlan> => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const response = await api.post(`/api/study/start-simulator/${studentId}`, {
      num_questions: numQuestions,
      time_limit_seconds: timeLimit,
      stress_level: stressLevel,
    });
    
    // Reutiliza a lógica de adaptação do generatePlan
    const backendData = response.data;
    
    const sessions: StudySession[] = [];
    if (backendData.sessions && Array.isArray(backendData.sessions)) {
      backendData.sessions.forEach((session: BackendSession, sIdx: number) => {
        const items: StudyItem[] = [];
        if (session.items && Array.isArray(session.items)) {
          session.items.forEach((item: BackendItem) => {
            items.push({
              id: item.id,
              type: 'flashcard',
              content: item.content,
              front: item.content?.front,
              options: item.content?.options,
              correct_index: item.content?.correct_index,
              explanation: item.content?.back,
              stability: 1.0,
              current_retention: 0.9,
              topic_roi: item.topic_roi,
            });
          });
        }

        sessions.push({
          id: `${backendData.id || 'plan'}-s${sIdx}`,
          topic: session.topic,
          duration_minutes: items.length * 2 || 0,
          items,
          focus_level: backendData.focus_level || 'SIMULATOR'
        });
      });
    }

    return {
      id: backendData.id,
      student_id: backendData.student_id,
      created_at: backendData.created_at,
      estimated_duration_minutes: backendData.estimated_duration_minutes || 15,
      focus_level: backendData.focus_level || 'Simulator Mode',
      sessions,
      flashcards: [], // Simulador foca em sessões
    };
  },

  submitReview: async (nodeId: string, success: boolean, responseTime: number, explicitGrade: number | null, rootCause?: string) => {
    const student_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'; // TODO: Mudar para dinâmico

    const response = await api.post(`/api/study/review/${nodeId}`, {
      student_id,
      success,
      grade: explicitGrade,
      response_time_seconds: responseTime,
      root_cause: rootCause,
    });
    return response.data;
  },

  validateFeynman: async (nodeId: string, explanation: string): Promise<FeynmanResult> => {
    const student_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'; // TODO: Mudar para dinâmico
    const response = await api.post('/api/feynman/validate', {
      student_id,
      node_id: nodeId,
      explanation,
    });
    return response.data;
  },
};
      