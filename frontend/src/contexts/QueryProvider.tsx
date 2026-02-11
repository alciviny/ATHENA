import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { ReactNode } from 'react';

/**
 * Configuração global do React Query
 * Gerencia cache, retry, stale time e outras otimizações
 */

// Configuração otimizada para o Athena
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache válido por 5 minutos antes de considerar "stale"
      staleTime: 5 * 60 * 1000,
      
      // Mantém cache por 10 minutos antes de garbage collection
      gcTime: 10 * 60 * 1000,
      
      // Retry 1 vez em caso de erro (IA pode ser instável)
      retry: 1,
      
      // Não refetch automaticamente ao focar janela (evita flicker)
      refetchOnWindowFocus: false,
      
      // Refetch ao reconectar (usuário voltou online)
      refetchOnReconnect: true,
      
      // Timeout de 2 minutos (IA pode demorar)
      // Nota: Axios já tem timeout, isso é adicional
      networkMode: 'online',
    },
    mutations: {
      // Retry mutations mais cautelosamente
      retry: 0,
      
      // Network mode para mutations
      networkMode: 'online',
    },
  },
});

interface QueryProviderProps {
  readonly children: ReactNode;
}

/**
 * Provider do React Query
 * Envolve a aplicação para habilitar cache inteligente
 */
export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* DevTools apenas em desenvolvimento */}
      {import.meta.env.DEV && (
        <ReactQueryDevtools 
          initialIsOpen={false} 
        />
      )}
    </QueryClientProvider>
  );
}

// Exporta instância para uso direto se necessário
// export { queryClient };
