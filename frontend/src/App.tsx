import { useState } from 'react';
import { Play, Brain, Clock, Zap } from 'lucide-react';
import { studyService } from './services/studyService';
import type { StudyPlanDTO } from './types/athena';
import { StudySession } from './components/StudySession'; // <--- Importe aqui


// Estados possíveis da aplicação
type AppView = 'DASHBOARD' | 'SESSION' | 'COMPLETED';

function App() {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<StudyPlanDTO | null>(null);
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
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-center p-6 space-y-6">
        <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center border border-emerald-500/20 mb-4">
          <Zap className="w-10 h-10 text-emerald-500" />
        </div>
        <h1 className="text-4xl font-bold text-white">Sessão Finalizada</h1>
        <p className="text-slate-400 max-w-md">
          Seus dados de performance foram enviados para o Brain. 
          O grafo de conhecimento foi atualizado para otimizar sua próxima revisão.
        </p>
        <button 
          onClick={() => setView('DASHBOARD')}
          className="px-8 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
        >
          Voltar ao Dashboard
        </button>
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
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Sequência de Estudo</h3>
              {plan.study_items.map((node, index) => (
                <div key={node.id} className="flex items-center p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                   <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-800 text-slate-400 font-mono text-sm border border-slate-700">
                    {index + 1}
                  </div>
                  <div className="ml-4">
                    <p className="font-medium text-slate-200">{node.title}</p>
                  </div>
                </div>
              ))}
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
