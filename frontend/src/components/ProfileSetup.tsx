import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface ProfileSetupProps {
  onComplete: () => void;
}

export function ProfileSetup({ onComplete }: ProfileSetupProps) {
  const [goal, setGoal] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { token, isAuthenticated } = useAuth();

  // Verificar se o usuário está autenticado
  useEffect(() => {
    console.log('ProfileSetup - isAuthenticated:', isAuthenticated);
    console.log('ProfileSetup - token:', token);
    if (!isAuthenticated) {
      setError('Você precisa estar logado para configurar seu perfil');
    }
  }, [isAuthenticated, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) {
      setError('Por favor, descreva seu interesse de estudo');
      return;
    }

    if (!token) {
      setError('Você precisa estar logado para continuar');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/auth/goal', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ goal: goal.trim() }),
      });

      if (!response.ok) {
        throw new Error('Erro ao salvar interesse');
      }

      onComplete();
    } catch (err) {
      setError('Erro ao salvar. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Configurar Perfil
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Conte-nos sobre seus interesses de estudo
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-2">
              Qual seu objetivo de estudo?
            </label>
            <textarea
              id="goal"
              required
              rows={4}
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Ex: Desenvolvimento Full-Stack, Ciência de Dados, Engenharia de Software..."
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
            />
            <p className="mt-1 text-xs text-gray-500">
              Descreva seu interesse principal para personalizar seu plano de estudos
            </p>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Salvando...' : 'Salvar e Continuar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}