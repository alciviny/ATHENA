import { Brain, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react';
import { useMemoryStatus } from '../hooks/useStudyData';

interface MemoryStatus {
  subject_name: string;
  current_retention: number;
  stability_days: number;
  needs_review: boolean;
  status: string;
}

export function MemoryDashboard() {
  // React Query hook - cache automático
  const { data: memoryData = [], isLoading: loading } = useMemoryStatus();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <Brain className="w-12 h-12 text-emerald-500 animate-pulse" />
        <span className="text-slate-400 font-mono">Analisando memória...</span>
      </div>
    );
  }

  const criticalTopics = memoryData.filter((m: MemoryStatus) => m.needs_review || m.current_retention < 0.7);
  const warningTopics = memoryData.filter((m: MemoryStatus) => !m.needs_review && m.current_retention >= 0.7 && m.current_retention < 0.9);
  const solidTopics = memoryData.filter((m: MemoryStatus) => m.current_retention >= 0.9);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold text-white tracking-tight flex items-center justify-center gap-3">
          <Brain className="w-10 h-10 text-emerald-500" />
          Estado da Memória
        </h1>
        <p className="text-slate-400 text-lg">
          Acompanhe o que você está consolidando e o que precisa revisar
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-red-400">{criticalTopics.length}</div>
          <div className="text-sm text-slate-400 mt-1">Críticos - Revisar Agora</div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-amber-400">{warningTopics.length}</div>
          <div className="text-sm text-slate-400 mt-1">Atenção - Reforçar</div>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-emerald-400">{solidTopics.length}</div>
          <div className="text-sm text-slate-400 mt-1">Consolidados</div>
        </div>
      </div>

      {/* Critical Topics */}
      {criticalTopics.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-red-400 flex items-center gap-2">
            <AlertCircle className="w-6 h-6 animate-pulse" />
            Urgente - Risco de Esquecimento
          </h2>
          <div className="space-y-3">
            {criticalTopics.map((topic: MemoryStatus) => (
              <MemoryCard key={topic.subject_name} topic={topic} />
            ))}
          </div>
        </div>
      )}

      {/* Warning Topics */}
      {warningTopics.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-amber-400 flex items-center gap-2">
            <TrendingDown className="w-6 h-6" />
            Requer Atenção
          </h2>
          <div className="space-y-3">
            {warningTopics.map((topic: MemoryStatus) => (
              <MemoryCard key={topic.subject_name} topic={topic} />
            ))}
          </div>
        </div>
      )}

      {/* Solid Topics */}
      {solidTopics.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-emerald-400 flex items-center gap-2">
            <CheckCircle className="w-6 h-6" />
            Bem Consolidados
          </h2>
          <div className="space-y-3">
            {solidTopics.map((topic: MemoryStatus) => (
              <MemoryCard key={topic.subject_name} topic={topic} />
            ))}
          </div>
        </div>
      )}

      {memoryData.length === 0 && (
        <div className="text-center py-20 space-y-4">
          <Brain className="w-16 h-16 text-slate-600 mx-auto" />
          <p className="text-slate-500 text-lg">
            Nenhum dado de memória disponível ainda.
          </p>
          <p className="text-slate-600 text-sm">
            Comece a estudar para acompanhar seu progresso!
          </p>
        </div>
      )}
    </div>
  );
}

function MemoryCard({ topic }: { topic: MemoryStatus }) {
  const retentionPercent = Math.round(topic.current_retention * 100);
  const retentionColor = topic.current_retention >= 0.9 ? 'bg-emerald-500' : 
                         topic.current_retention >= 0.7 ? 'bg-amber-500' : 'bg-red-500';
  
  return (
    <div className={`border rounded-xl p-5 transition-all hover:scale-[1.01] ${
      topic.needs_review 
        ? 'bg-red-500/5 border-red-500/30 hover:border-red-500/50' 
        : topic.current_retention < 0.9 
          ? 'bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50'
          : 'bg-emerald-500/5 border-emerald-500/30 hover:border-emerald-500/50'
    }`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3 flex-1">
          {topic.needs_review || topic.current_retention < 0.7 ? (
            <AlertCircle className="w-5 h-5 text-red-400 animate-pulse mt-1" />
          ) : topic.current_retention < 0.9 ? (
            <TrendingDown className="w-5 h-5 text-amber-400 mt-1" />
          ) : (
            <CheckCircle className="w-5 h-5 text-emerald-400 mt-1" />
          )}
          <div className="flex-1">
            <h3 className="font-semibold text-white text-lg">{topic.subject_name}</h3>
            <p className={`text-sm mt-1 ${
              topic.needs_review ? 'text-red-400 font-medium' : 'text-slate-400'
            }`}>
              {topic.status}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${
            topic.current_retention >= 0.9 ? 'text-emerald-400' :
            topic.current_retention >= 0.7 ? 'text-amber-400' : 'text-red-400'
          }`}>
            {retentionPercent}%
          </div>
          <div className="text-xs text-slate-500 mt-1">retenção</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-3">
        <div 
          className={`h-full ${retentionColor} transition-all duration-500`}
          style={{ width: `${retentionPercent}%` }} // NOSONAR: barra de retenção precisa refletir percentual em tempo real
        />
      </div>

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
        <span>Estabilidade: {topic.stability_days.toFixed(1)} dias</span>
        {topic.needs_review && (
          <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 font-bold uppercase">
            Revisar Agora
          </span>
        )}
      </div>
    </div>
  );
}

export default MemoryDashboard;
