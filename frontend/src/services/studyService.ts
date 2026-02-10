import axios from 'axios';
import type { StudyPlan, StudyItem, StudySession, RoiReport, FeynmanResult } from '../types/athena';

interface BackendSession {
  topic: string;
  items: BackendItem[];
}

interface BackendItem {
  id: string;
  topic_roi: string;
  stability?: number;
  current_retention?: number;
  difficulty?: number;
  estimated_time_minutes?: number;
  content: {
    front: string;
    back: string;
    options: string[];
    correct_index: number;
  };
}

interface BackendFlashcard {
  id?: string;
  type?: string;
  stability?: number;
  current_retention?: number;
  difficulty?: number;
  estimated_time_minutes?: number;
  topic_roi?: string;
  // Formato aninhado que vem do backend
  content?: {
    front: string;
    back: string;
    options: string[];
    correct_index: number;
  };
  // Mantém compatibilidade com formato antigo
  pergunta?: string;
  explicacao?: string;
  opcoes?: string[];
  correta_index?: number;
}

const api = axios.create({
  timeout: 120000, // 2 minutos
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
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
              stability: item.stability ?? 1.0,
              current_retention: item.current_retention ?? 0.9,
              topic_roi: item.topic_roi, // Mapeia o rótulo estratégico do backend
              // CORRIGINDO: Adicionando propriedades que estavam faltando
              difficulty: item.difficulty ?? 0.5,
              estimated_time_minutes: item.estimated_time_minutes ?? 2,
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
      ? backendData.flashcards.map((c: BackendFlashcard, idx: number) => {
          console.log(`studyService - Processando flashcard ${idx}:`, c); // Debug
          // Verifica se já vem com o formato aninhado (novo backend)
          if (c.content) {
            console.log(`studyService - Flashcard ${idx} já tem content aninhado`); // Debug
            return {
              id: c.id || `fc-${idx}`,
              type: c.type || 'flashcard',
              content: c.content,
              stability: c.stability ?? 1.0,
              current_retention: c.current_retention ?? 0.5,
              // CORRIGINDO: Adicionando propriedades que estavam faltando
              difficulty: c.difficulty ?? 0.5,
              estimated_time_minutes: c.estimated_time_minutes ?? 2,
              topic_roi: c.topic_roi || 'MANUTENÇÃO',
            };
          }
          // Fallback para formato antigo
          console.log(`studyService - Flashcard ${idx} usando formato antigo`); // Debug
          return {
            id: `fc-${idx}-${c.pergunta?.slice(0,10)}`,
            type: 'flashcard',
            content: {
              front: c.pergunta || '',
              back: c.explicacao || '',
              options: c.opcoes || [],
              correct_index: c.correta_index ?? 0,
            },
            stability: c.stability ?? 1.0,
            current_retention: c.current_retention ?? 0.5,
            // CORRIGINDO: Adicionando propriedades que estavam faltando
            difficulty: 0.5,
            estimated_time_minutes: 2,
            topic_roi: 'MANUTENÇÃO',
          };
        })
      : [];
    
    console.log('studyService - Flashcards mapeados:', flashcards); // Debug

    // 3. Se não houver sessões, mas houver flashcards, cria uma sessão para cada flashcard
    if ((sessions.length === 0 || !sessions) && flashcards.length > 0) {
      console.log('studyService - Criando sessões a partir dos flashcards'); // Debug
      flashcards.forEach((flashcard: any, idx: number) => {
        const topic = flashcard.content?.front || `Questão ${idx + 1}`;
        sessions.push({
          id: `${backendData.id || 'plan'}-fc-${idx}`,
          topic: topic.length > 60 ? topic.substring(0, 57) + '...' : topic, // Limita o tamanho do tópico
          duration_minutes: flashcard.estimated_time_minutes || 2,
          items: [flashcard],
          focus_level: backendData.focus_level || 'GERAL'
        });
      });
    }
    
    console.log('studyService - Sessions finais:', sessions); // Debug

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
              stability: item.stability ?? 1.0,
              current_retention: item.current_retention ?? 0.9,
              topic_roi: item.topic_roi,
              // CORRIGINDO: Adicionando propriedades que estavam faltando no simulator também
              difficulty: item.difficulty ?? 0.5,
              estimated_time_minutes: item.estimated_time_minutes ?? 2,
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
    const response = await api.post('/api/study/feynman/validate', {
      student_id,
      node_id: nodeId,
      explanation,
    });
    return response.data;
  },

  getMemoryStatus: async () => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const response = await api.get(`/api/students/${studentId}/memory-status`);
    return response.data;
  },

  getPerformanceAnalysis: async (subject: string) => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const response = await api.get(`/api/performance/analysis/${studentId}`, {
      params: { subject }
    });
    return response.data;
  },
};
      