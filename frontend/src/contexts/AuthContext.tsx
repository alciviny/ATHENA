import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

/**
 * Context de Autenticação e Usuário
 * Gerencia estado global de autenticação JWT, student_id e configurações
 */

interface AuthContextType {
  studentId: string | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [studentId, setStudentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Carrega token do localStorage na inicialização
  useEffect(() => {
    console.log('AuthContext - useEffect inicializando');
    const storedToken = localStorage.getItem('athena_token');
    const storedStudentId = localStorage.getItem('athena_student_id');
    
    console.log('AuthContext - storedToken:', !!storedToken);
    console.log('AuthContext - storedStudentId:', !!storedStudentId);
    
    if (storedToken && storedStudentId) {
      setToken(storedToken);
      setStudentId(storedStudentId);
    }
    
    setLoading(false);
    console.log('AuthContext - loading definido como false');
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Credenciais inválidas');
      }
      
      const data = await response.json();
      const { access_token } = data;
      
      // Decodificar token para obter student_id (simplificado)
      const payload = JSON.parse(atob(access_token.split('.')[1]));
      const studentIdFromToken = payload.sub;
      
      setToken(access_token);
      setStudentId(studentIdFromToken);
      
      // Persistir no localStorage
      localStorage.setItem('athena_token', access_token);
      localStorage.setItem('athena_student_id', studentIdFromToken);
      
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setStudentId(null);
    localStorage.removeItem('athena_token');
    localStorage.removeItem('athena_student_id');
  };

  const value = {
    studentId,
    token,
    isAuthenticated: !!token,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook para acessar o contexto de autenticação
 * @throws Error se usado fora do AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
}

/**
 * Hook que garante acesso ao studentId quando autenticado
 * @throws Error se não estiver autenticado
 */
export function useAuthenticatedAuth() {
  const context = useAuth();
  if (!context.isAuthenticated || !context.studentId) {
    throw new Error('useAuthenticatedAuth deve ser usado apenas quando autenticado');
  }
  return {
    ...context,
    studentId: context.studentId, // Garantido como string
  };
}
