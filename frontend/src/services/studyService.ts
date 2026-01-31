import axios from 'axios';
import type { StudyPlan, StudyItem } from '../types/athena';

interface BackendSession {
  topic: string;
  items: BackendItem[];
}

interface BackendItem {
  id: string;
  difficulty?: number;
  content: {
    front: string;
    back: string;
    options: string[];
    correct_index: number;
  };
}

const api = axios.create({});

export const studyService = {
  generatePlan: async (): Promise<StudyPlan> => {
    const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const response = await api.post(`/api/study/generate-plan/${studentId}`);
    
    // --- ADAPTADOR (CORREÇÃO) ---
    // O backend retorna uma estrutura aninhada (sessions -> items -> content).
    // O frontend espera uma lista plana de 'study_items'.
    
    const backendData = response.data;
    
    // 1. Extrair todos os itens de todas as sessões
    const flatItems: StudyItem[] = [];
    
    if (backendData.sessions && Array.isArray(backendData.sessions)) {
        backendData.sessions.forEach((session: BackendSession) => {
            if (session.items && Array.isArray(session.items)) {
                session.items.forEach((item: BackendItem) => {
                    // Mapeia do formato DTO (backend) para Interface (frontend)
                    flatItems.push({
                        id: item.id,
                        type: 'flashcard',
                        difficulty: item.difficulty || 0,
                        
                        // Mapeamento crucial aqui: content -> propriedades planas
                        front: item.content.front || "Questão sem texto",
                        options: item.content.options || [],
                        correct_index: item.content.correct_index || 0,
                        explanation: item.content.back || "Sem explicação",
                        
                        // Metadados simulados (pois o backend ainda não manda tudo isso)
                        stability: 1.0, 
                        current_retention: 0.9,
                        topic_roi: 'NORMAL'
                    });
                });
            }
        });
    }

    // 2. Retorna o objeto no formato que o React espera
    return {
        id: backendData.id,
        student_id: backendData.student_id,
        created_at: backendData.created_at,
        estimated_duration_minutes: 15, // Valor padrão
        focus_level: "Deep Work",       // Valor padrão
        study_items: flatItems          // A lista plana que o componente StudySession usa
    };
  },

  submitReview: async (nodeId: string, grade: number, responseTime: number) => {
    const student_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const success = grade > 2;

    return api.post(`/api/study/review/${nodeId}`, {
      student_id,
      success,
      response_time_seconds: responseTime,
    });
  },
};