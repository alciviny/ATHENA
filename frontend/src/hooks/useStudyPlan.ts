import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { studyService } from '../services/studyService';
import { useAuthenticatedAuth } from '../contexts/AuthContext';
import type { StudyPlan } from '../types/athena';

/**
 * Hook para gerenciar planos de estudo com cache inteligente
 * Usa React Query para otimizar requisições e estado
 */

// Query keys centralizadas (evita typos e facilita invalidação)
export const studyPlanKeys = {
  all: ['study-plans'] as const,
  byStudent: (studentId: string) => [...studyPlanKeys.all, studentId] as const,
  current: (studentId: string) => [...studyPlanKeys.byStudent(studentId), 'current'] as const,
};

/**
 * Hook para gerar plano de estudos
 * Invalida cache anterior e armazena novo plano
 */
export function useGenerateStudyPlan() {
  const { studentId } = useAuthenticatedAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => studyService.generatePlan(studentId),
    
    onSuccess: (newPlan: StudyPlan) => {
      // Armazena novo plano no cache
      queryClient.setQueryData(studyPlanKeys.current(studentId), newPlan);
      
      // Invalida outras queries relacionadas (força refetch se necessário)
      queryClient.invalidateQueries({ queryKey: studyPlanKeys.byStudent(studentId) });
    },
    
    onError: (error) => {
      console.error('Erro ao gerar plano:', error);
    },
  });
}

/**
 * Hook para obter plano atual do cache
 * Não faz requisição, apenas lê do cache do React Query
 */
export function useCurrentStudyPlan() {
  const { studentId } = useAuthenticatedAuth();
  
  return useQuery<StudyPlan | undefined>({
    queryKey: studyPlanKeys.current(studentId),
    queryFn: (): Promise<StudyPlan | undefined> => {
      // Retorna undefined se não houver plano em cache
      // Componente decide se deve gerar um novo
      return Promise.resolve(undefined);
    },
    enabled: false, // Nunca faz fetch automático, usa apenas cache
    staleTime: Infinity, // Plano nunca fica stale (só muda manualmente)
  });
}

/**
 * Hook para iniciar simulador
 * Similar ao generatePlan, mas para modo simulador
 */
export function useStartSimulator() {
  const { studentId } = useAuthenticatedAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ numQuestions, timeLimit, stressLevel }: {
      numQuestions?: number;
      timeLimit?: number;
      stressLevel?: number;
    }) => studyService.startSimulator(studentId, numQuestions, timeLimit, stressLevel),
    
    onSuccess: (simulatorPlan: StudyPlan) => {
      // Armazena plano do simulador
      queryClient.setQueryData(studyPlanKeys.current(studentId), simulatorPlan);
    },
  });
}

/**
 * Hook para limpar plano atual
 * Útil ao sair da sessão ou resetar estado
 */
export function useClearStudyPlan() {
  const { studentId } = useAuthenticatedAuth();
  const queryClient = useQueryClient();

  return () => {
    queryClient.setQueryData(studyPlanKeys.current(studentId), undefined);
  };
}
