import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studyService } from '../services/studyService';
import { useAuthenticatedAuth } from '../contexts/AuthContext';

/**
 * Hooks para dados de estudo (ROI, Performance, Memória)
 * Todos com cache inteligente e invalidação automática
 */

// Query keys centralizadas
export const studyDataKeys = {
  roi: (studentId: string) => ['roi-report', studentId] as const,
  performance: (studentId: string) => ['performance-summary', studentId] as const,
  performanceAnalysis: (studentId: string, subject?: string) => 
    ['performance-analysis', studentId, subject] as const,
  memory: (studentId: string) => ['memory-status', studentId] as const,
  subjects: (studentId: string) => ['student-subjects', studentId] as const,
};

/**
 * Hook para relatório ROI com cache de 5 minutos
 */
export function useRoiReport() {
  const { studentId } = useAuthenticatedAuth();

  return useQuery({
    queryKey: studyDataKeys.roi(studentId),
    queryFn: () => studyService.getRoiReport(studentId),
    staleTime: 5 * 60 * 1000, // Cache válido por 5 minutos
  });
}

/**
 * Hook para resumo de performance com cache
 */
export function usePerformanceSummary() {
  const { studentId } = useAuthenticatedAuth();

  return useQuery({
    queryKey: studyDataKeys.performance(studentId),
    queryFn: () => studyService.getPerformanceSummary(studentId),
    staleTime: 3 * 60 * 1000, // Cache de 3 minutos (mais volátil)
  });
}

/**
 * Hook para análise detalhada de performance
 */
export function usePerformanceAnalysis(subject?: string) {
  const { studentId } = useAuthenticatedAuth();

  return useQuery({
    queryKey: studyDataKeys.performanceAnalysis(studentId, subject),
    queryFn: () => studyService.getPerformanceAnalysis(studentId, subject || ''),
    enabled: !!subject, // Só executa se subject for fornecido
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook para status de memória
 */
export function useMemoryStatus() {
  const { studentId } = useAuthenticatedAuth();

  return useQuery({
    queryKey: studyDataKeys.memory(studentId),
    queryFn: () => studyService.getMemoryStatus(studentId),
    staleTime: 2 * 60 * 1000, // Cache de 2 minutos (dados mais dinâmicos)
  });
}

/**
 * Hook para submeter review e invalidar caches relacionados
 * Invalida ROI, performance e memória após review
 */
export function useSubmitReview() {
  const { studentId } = useAuthenticatedAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      nodeId,
      success,
      responseTime,
      explicitGrade,
      rootCause,
    }: {
      nodeId: string;
      success: boolean;
      responseTime: number;
      explicitGrade: number | null;
      rootCause?: string;
    }) => studyService.submitReview(studentId, nodeId, success, responseTime, explicitGrade, rootCause),
    
    onSuccess: () => {
      // Invalida caches que dependem de reviews
      queryClient.invalidateQueries({ queryKey: studyDataKeys.roi(studentId) });
      queryClient.invalidateQueries({ queryKey: studyDataKeys.performance(studentId) });
      queryClient.invalidateQueries({ queryKey: studyDataKeys.memory(studentId) });
    },
  });
}

/**
 * Hook para validação de Feynman
 */
export function useValidateFeynman() {
  const { studentId } = useAuthenticatedAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ nodeId, explanation }: { nodeId: string; explanation: string }) =>
      studyService.validateFeynman(studentId, nodeId, explanation),
    
    onSuccess: () => {
      // Invalida caches relacionados
      queryClient.invalidateQueries({ queryKey: studyDataKeys.roi(studentId) });
    },
  });
}

/**
 * Hook para buscar matérias disponíveis do estudante
 */
export function useStudentSubjects() {
  const { studentId } = useAuthenticatedAuth();

  return useQuery({
    queryKey: studyDataKeys.subjects(studentId),
    queryFn: () => studyService.getStudentSubjects(studentId),
    staleTime: 10 * 60 * 1000, // 10 minutos
    gcTime: 30 * 60 * 1000, // 30 minutos
  });
}
