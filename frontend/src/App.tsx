import { useState } from 'react';
import { Play, Brain, Clock, Zap, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { studyService } from './services/studyService';
import type { StudyPlan, StudyItem } from './types/athena';
import { StudySession } from './components/StudySession'; // <--- Importe aqui

// Componente Helper para o Status do ROI
function ROI_Badge({ status }: { status: StudyItem['topic_roi'] }) {
  if (status === 'VEIO_DE_OURO') {
    return (
      <span className="flex items-center gap-1 px-2 py-1 rounded bg-amber-500/10 text-amber-400 text-[10px] font-bold uppercase tracking-wider border border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.2)] animate-pulse">
        <TrendingUp className="w-3 h-3" />
        Alto ROI Cognitivo
      </span>
    );
  }
  if (status === 'PANTANO') {
    return (
      <span className="flex items-center gap-1 px-2 py-1 rounded bg-slate-700/50 text-slate-400 text-[10px] font-bold uppercase tracking-wider border border-slate-600">
        <AlertTriangle className="w-3 h-3" />
        Baixo Retorno
      </span>
    );
  }
  return null; // Normal não mostra badge
}

// Componente do Item da Lista
function IntelligentStudyCard({ item, index }: { item: StudyItem; index: number }) {
  // Cálculo visual da urgência baseada na estabilidade
  const isUrgent = item.stability < 1.0; 

  return (
    <div className="group relative flex items-center p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-900/10">
      
      {/* Indicador Lateral de Urgência */}
      <div className={`absolute left-0 top-4 bottom-4 w-1 rounded-r-full transition-colors ${isUrgent ? 'bg-red-500' : 'bg-emerald-500/30 group-hover:bg-emerald-500'}`} />

      {/* Número / Índice */}
      <div className="flex-shrink-0 ml-3 mr-4">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-slate-400 font-mono text-sm border border-slate-700 group-hover:text-white group-hover:border-emerald-500/30 transition-colors">
          {index + 1}
        </div>
      </div>

      {/* Conteúdo Principal */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="font-medium text-slate-200 truncate group-hover:text-emerald-400 transition-colors">
            {item.title}
          </h3>
          <ROI_Badge status={item.topic_roi} />
        </div>
        
        <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
          <span className="flex items-center gap-1" title="Dificuldade do Tópico">
            <Brain className="w-3 h-3" />
            Dif: {(item.difficulty).toFixed(1)}
          </span>
          <span className={`flex items-center gap-1 ${isUrgent ? 'text-red-400' : ''}`} title="Estabilidade da Memória">
            <Clock className="w-3 h-3" />
            {item.stability < 1 ? 'Revisão Crítica' : `${item.stability.toFixed(1)} dias`}
          </span>
        </div>
      </div>

      {/* Ação (só aparece no hover ou se for o próximo) */}
      <div className="ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-400">
          <Play className="w-4 h-4 fill-current" />
        </div>
      </div>
    </div>
  );
}


// Estados possíveis da aplicação
type AppView = 'DASHBOARD' | 'SESSION' | 'COMPLETED';

function App() {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [view, setView] = useState<AppView>('DASHBOARD'); // <--- Controle de visualização

  const handleGeneratePlan = async () => {
    setLoading(true);
    try {
      const newPlan = await studyService.generatePlan();
      setPlan(newPlan);
    } catch (error) {
      console.error("Falha ao gerar plano:", error);
      alert("Erro ao conectar com Athena Brain.");
    } finally {
      setLoading(false);
    }
  };

  const startSession = () => {
    if (plan) setView('SESSION');
  };

  const handleSessionComplete = () => {
    setView('COMPLETED');
    setPlan(null); // Limpa o plano para forçar gerar um novo amanhã (ou agora)
  };

  // --- RENDERIZAÇÃO CONDICIONAL ---

  // 1. Modo Sessão (O Dojo)
  if (view === 'SESSION' && plan) {
    return (
      <StudySession 
        plan={plan} 
        onComplete={handleSessionComplete} 
        onExit={() => setView('DASHBOARD')} 
      />
    );
  }

  // 2. Tela de Conclusão (Feedback Loop)
  if (view === 'COMPLETED') {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 relative overflow-hidden">
        
        {/* Background Effect */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-emerald-900/20 via-slate-950 to-slate-950"></div>

        <div className="relative z-10 max-w-md w-full text-center space-y-8 animate-fade-in-up">
          
          {/* Ícone de Sucesso Pulsante */}
          <div className="mx-auto w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
            <CheckCircle2 className="w-12 h-12 text-emerald-500" />
          </div>

          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Grafo Atualizado
            </h1>
            <p className="text-slate-400">
              O Engine rebalanceou as prioridades de revisão com base no seu desempenho.
            </p>
          </div>

          {/* Stats Rápidos (Placeholder para futura integração real) */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">XP Cognitivo</div>
              <div className="text-2xl font-mono text-emerald-400 font-bold">+150 pts</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
               <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Próx. Sessão</div>
               <div className="text-2xl font-mono text-amber-400 font-bold">~12h</div>
            </div>
          </div>

          <button 
            onClick={() => setView('DASHBOARD')}
            className="w-full py-4 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-all hover:scale-[1.02] border border-slate-700"
          >
            Retornar ao Hub
          </button>
        </div>
      </div>
    );
  }

  // 3. Dashboard (Default)
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      
      {/* ... Header anterior ... */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-emerald-500" />
            <span className="font-bold tracking-tight text-lg">ATHENA</span>
          </div>
          {/* ... Avatar ... */}
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        
        {/* Seção Hero - Só aparece se não tiver plano */}
        {!plan && !loading && (
          <div className="text-center py-20 space-y-6">
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
              Pronto para evoluir?
            </h1>
            <p className="text-lg text-slate-400 max-w-lg mx-auto">
              O Athena analisou seus últimos erros e o grafo de conhecimento.
            </p>
            
            <button 
              onClick={handleGeneratePlan}
              className="group relative inline-flex items-center justify-center px-8 py-4 font-semibold text-white transition-all duration-200 bg-emerald-600 rounded-full hover:bg-emerald-500 hover:scale-105 focus:outline-none ring-offset-2 focus:ring-2 ring-emerald-500"
            >
              <Play className="w-5 h-5 mr-2 fill-current" />
              Gerar Plano Adaptativo
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 space-y-4 animate-pulse">
            <Brain className="w-12 h-12 text-emerald-500 animate-bounce" />
            <span className="text-slate-400 font-mono">Calibrando grafo de conhecimento...</span>
          </div>
        )}

        {/* Card do Plano Gerado */}
        {plan && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl animate-fade-in-up">
            <div className="flex items-start justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <span>Plano Tático Gerado</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs uppercase tracking-wider font-bold border border-emerald-500/20">
                    {plan.focus_level}
                  </span>
                </h2>
                <p className="text-slate-400 mt-1">Gerado em {new Date(plan.created_at).toLocaleTimeString()}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 text-emerald-400 font-mono text-xl font-bold">
                  <Clock className="w-5 h-5" />
                  {plan.estimated_duration_minutes} min
                </div>
              </div>
            </div>

            <div className="space-y-3 mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                  Sequência de Otimização Neural
                </h3>
                <span className="text-xs text-slate-600 font-mono">
                  {plan.study_items.length} nós detectados
                </span>
              </div>

              <div className="space-y-2">
                {plan.study_items.map((node, index) => (
                  <IntelligentStudyCard 
                    key={node.id} 
                    item={node} 
                    index={index} 
                  />
                ))}
              </div>
            </div>

            {/* Ação Principal: INICIAR O DOJO */}
            <button 
              onClick={startSession}
              className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-900/20 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
            >
              <Play className="w-5 h-5 fill-current" />
              Iniciar Sessão Focada
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
