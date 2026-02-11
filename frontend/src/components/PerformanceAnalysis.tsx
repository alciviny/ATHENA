import { useState } from 'react';
import { studyService } from '../services/studyService';
import { useAuthenticatedAuth } from '../contexts/AuthContext';
import { useStudentSubjects } from '../hooks/useStudyData';
import { TrendingUp, AlertTriangle, Target, Brain, Sparkles, ArrowLeft } from 'lucide-react';

interface AnalysisData {
  student_id: string;
  subject: string;
  analysis: string;
}

interface PerformanceAnalysisProps {
  onBack: () => void;
}

export function PerformanceAnalysis({ onBack }: PerformanceAnalysisProps) {
  const { studentId } = useAuthenticatedAuth();
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Use hook para buscar assuntos
  const { data: subjectsData, isLoading: subjectsLoading } = useStudentSubjects();
  const subjects = subjectsData?.subjects || [];

  const handleAnalyze = async () => {
    if (!selectedSubject) {
      setError('Selecione uma matéria para análise');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await studyService.getPerformanceAnalysis(studentId, selectedSubject);
      setAnalysis(result);
    } catch (err: unknown) {
      console.error('Error fetching analysis:', err);
      const errorMessage = err && typeof err === 'object' && 'response' in err 
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail 
        : 'Erro ao buscar análise. Tente novamente.';
      setError(errorMessage || 'Erro ao buscar análise. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              aria-label="Voltar"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Análise de Performance</h1>
                <p className="text-sm text-slate-400">Insights gerados por IA sobre seus padrões de estudo</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Subject Selector */}
        <div className="mb-8 bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Target className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-semibold">Selecione a Matéria</h2>
          </div>
          
          {subjectsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-slate-400">Carregando matérias...</p>
            </div>
          ) : (
            <>
              {subjects.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  {subjects.map((subject) => (
                    <button
                      key={subject}
                      onClick={() => setSelectedSubject(subject)}
                      className={`px-4 py-3 rounded-xl font-medium transition-all duration-200 border-2 ${
                        selectedSubject === subject
                          ? 'bg-purple-500/20 border-purple-500 text-purple-300 ring-2 ring-purple-500/30'
                          : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                      }`}
                    >
                      {subject}
                    </button>
                  ))}
                </div>
              )}

              {/* Manual input for custom subjects */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Ou digite uma matéria específica:
                </label>
                <input
                  type="text"
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  placeholder="Ex: Direito Administrativo, Matemática, etc."
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </>
          )}

          <button
            onClick={handleAnalyze}
            disabled={!selectedSubject || isLoading}
            className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-200 flex items-center justify-center gap-2 ${
              !selectedSubject || isLoading
                ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg hover:shadow-purple-500/50'
            }`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Analisando...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Gerar Análise com IA
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-400 mb-1">Erro na Análise</h3>
              <p className="text-sm text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Analysis Result */}
        {analysis && (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold">Análise: {analysis.subject}</h2>
              </div>
              <p className="text-slate-400 text-sm">Insights baseados em seus padrões de erro e desempenho</p>
            </div>

            {/* AI Analysis Content */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8">
              <div className="flex items-start gap-4 mb-6">
                <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-xl">
                  <Brain className="w-6 h-6 text-purple-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                    Diagnóstico Inteligente
                  </h3>
                  <p className="text-slate-400 text-sm">
                    Análise gerada por IA (Groq Llama 3.3 70B) com base em seus dados reais de estudo
                  </p>
                </div>
              </div>

              <div className="prose prose-invert prose-slate max-w-none">
                <div className="whitespace-pre-wrap text-slate-200 leading-relaxed">
                  {analysis.analysis}
                </div>
              </div>
            </div>

            {/* Action Cards */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-green-500/20 rounded-lg">
                    <Target className="w-5 h-5 text-green-400" />
                  </div>
                  <h4 className="font-bold">Próximos Passos</h4>
                </div>
                <p className="text-sm text-slate-400">
                  Use os insights acima para ajustar seu plano de estudos e focar nas áreas críticas identificadas.
                </p>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-blue-500/20 rounded-lg">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                  </div>
                  <h4 className="font-bold">Análise Contínua</h4>
                </div>
                <p className="text-sm text-slate-400">
                  A IA aprende com cada erro registrado. Quanto mais você estuda, mais precisas ficam as análises.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!analysis && !isLoading && !error && (
          <div className="text-center py-16">
            <div className="inline-block p-6 bg-slate-900/50 border border-slate-800 rounded-2xl mb-6">
              <Brain className="w-16 h-16 text-slate-600 mx-auto" />
            </div>
            <h3 className="text-xl font-bold text-slate-400 mb-2">Nenhuma análise gerada ainda</h3>
            <p className="text-slate-500">Selecione uma matéria e clique em "Gerar Análise com IA"</p>
          </div>
        )}
      </div>
    </div>
  );
}
