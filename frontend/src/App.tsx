import { useState, useMemo } from 'react';
import { Play, Brain, Clock, TrendingUp, CheckCircle2 } from 'lucide-react';
import { studyService } from './services/studyService';
import type { StudyPlan, StudyItem } from './types/athena';

// --- TIPO INTERNO PARA COMPATIBILIDADE VISUAL ---
interface UIStudyItem extends StudyItem {
  ui_title: string;       // O 'topic' da sessão vira o título do card
  ui_stability: number;   // Placeholder para estabilidade
  ui_roi: 'VEIO_DE_OURO' | 'PANTANO' | 'NORMAL'; // Placeholder para ROI
}

// Componente Helper para o Status do ROI
function ROI_Badge({ status }: { status: 'VEIO_DE_OURO' | 'PANTANO' | 'NORMAL' }) {
  if (status === 'VEIO_DE_OURO') {
    return (
      <span className="flex items-center gap-1 px-2 py-1 rounded bg-amber-500/10 text-amber-400 text-[10px] font-bold uppercase tracking-wider border border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.2)] animate-pulse">
        <TrendingUp className="w-3 h-3" />
        Alto ROI
      </span>
    );
  }
  return null;
}

// Componente do Item da Lista
function IntelligentStudyCard({ item, index }: { item: UIStudyItem; index: number }) {
  const isUrgent = item.ui_stability < 1.0; 

  return (
    <div className="group relative flex items-center p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-900/10">
      <div className={`absolute left-0 top-4 bottom-4 w-1 rounded-r-full transition-colors ${isUrgent ? 'bg-red-500' : 'bg-emerald-500/30 group-hover:bg-emerald-500'}`} />

      <div className="flex-shrink-0 ml-3 mr-4">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-slate-400 font-mono text-sm border border-slate-700 group-hover:text-white group-hover:border-emerald-500/30 transition-colors">
          {index + 1}
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="font-medium text-slate-200 truncate group-hover:text-emerald-400 transition-colors">
            {item.ui_title}
          </h3>
          <ROI_Badge status={item.ui_roi} />
        </div>
        
        <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
          <span className="flex items-center gap-1">
            <Brain className="w-3 h-3" />
            Dif: {(item.difficulty).toFixed(1)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {item.estimated_time_minutes} min
          </span>
        </div>
      </div>

      <div className="ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-400">
          <Play className="w-4 h-4 fill-current" />
        </div>
      </div>
    </div>
  );
}

type AppView = 'DASHBOARD' | 'SESSION' | 'COMPLETED';

function App() {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [view, setView] = useState<AppView>('DASHBOARD');

  const handleGeneratePlan = async () => {
    setLoading(true);
    try {
      const newPlan = await studyService.generatePlan();
      console.log("Plano Recebido:", newPlan); // Debug no console
      setPlan(newPlan);
    } catch (error) {
      console.error("Falha ao gerar plano:", error);
      alert("Erro ao conectar com Athena Brain.");
    } finally {
      setLoading(false);
    }
  };

  // --- TRATAMENTO DOS DADOS (ADAPTER) ---
  // Transforma a estrutura hierárquica (Sessions) em lista plana para o Dashboard
  const { flatItems, totalDuration, mainFocus } = useMemo(() => {
    if (!plan || !plan.sessions) return { flatItems: [], totalDuration: 0, mainFocus: 'N/A' };

    const items: UIStudyItem[] = [];
    let duration = 0;
    
    // Pega o foco da primeira sessão como principal (simplificação)
    const focus = plan.sessions.length > 0 ? plan.sessions[0].focus_level : 'GERAL';

    plan.sessions.forEach(session => {
      duration += session.duration_minutes;
      session.items.forEach((item: StudyItem) => {
        items.push({
          ...item,
          ui_title: session.topic, // Usa o tópico da sessão como título
          ui_stability: 2.0,       // Default (Backend ainda não envia)
          ui_roi: 'NORMAL'         // Default (Backend ainda não envia)
        } as UIStudyItem);
      });
    });

    return { flatItems: items, totalDuration: duration, mainFocus: focus };
  }, [plan]);


  const startSession = () => {
    if (plan && flatItems.length > 0) {
      setView('SESSION');
    }
  };

  // 1. Modo Sessão
  if (view === 'SESSION' && plan) {
    // Nota: O componente StudySession também precisará de ajustes futuros para suportar a nova tipagem completa.
    // Por enquanto, renderizamos um aviso se ele quebrar, ou passamos os dados adaptados se possível.
    return (
       <div className="text-white p-10 text-center">
         <h1 className="text-2xl mb-4">Sessão Iniciada</h1>
         <p>Integração do modo "Sessão" pendente de atualização no componente StudySession.tsx</p>
         <button onClick={() => setView('DASHBOARD')} className="mt-4 px-4 py-2 bg-emerald-600 rounded">Voltar</button>
       </div>
    );
  }

  if (view === 'COMPLETED') {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-emerald-900/20 via-slate-950 to-slate-950"></div>
        <div className="relative z-10 max-w-md w-full text-center space-y-8 animate-fade-in-up">
          <div className="mx-auto w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
            <CheckCircle2 className="w-12 h-12 text-emerald-500" />
          </div>
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">Sessão Concluída</h1>
            <p className="text-slate-400">Dados sincronizados com o Engine.</p>
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-emerald-500" />
            <span className="font-bold tracking-tight text-lg">ATHENA</span>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        
        {/* Lógica: Mostra botão de gerar se não tem plano OU se o plano veio vazio (0 sessions) */}
        {(!plan || flatItems.length === 0) && !loading && (
          <div className="text-center py-20 space-y-6">
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
              {plan ? "Nenhum ponto de melhoria detectado." : "Pronto para evoluir?"}
            </h1>
            <p className="text-lg text-slate-400 max-w-lg mx-auto">
              {plan ? "O grafo de conhecimento parece vazio ou você dominou tudo!" : "O Athena analisou seus últimos erros e o grafo de conhecimento."}
            </p>
            
            <button 
              onClick={handleGeneratePlan}
              className="group relative inline-flex items-center justify-center px-8 py-4 font-semibold text-white transition-all duration-200 bg-emerald-600 rounded-full hover:bg-emerald-500 hover:scale-105 focus:outline-none ring-offset-2 focus:ring-2 ring-emerald-500"
            >
              <Play className="w-5 h-5 mr-2 fill-current" />
              {plan ? "Tentar Novamente" : "Gerar Plano Adaptativo"}
            </button>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 space-y-4 animate-pulse">
            <Brain className="w-12 h-12 text-emerald-500 animate-bounce" />
            <span className="text-slate-400 font-mono">Calibrando grafo de conhecimento...</span>
          </div>
        )}

        {plan && flatItems.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl animate-fade-in-up">
            <div className="flex items-start justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <span>Plano Tático</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs uppercase tracking-wider font-bold border border-emerald-500/20">
                    {mainFocus}
                  </span>
                </h2>
                <p className="text-slate-400 mt-1">Gerado em {new Date(plan.created_at).toLocaleTimeString()}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 text-emerald-400 font-mono text-xl font-bold">
                  <Clock className="w-5 h-5" />
                  {totalDuration} min
                </div>
              </div>
            </div>

            <div className="space-y-3 mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                  Sequência de Otimização
                </h3>
                <span className="text-xs text-slate-600 font-mono">
                  {flatItems.length} atividades
                </span>
              </div>

              <div className="space-y-2">
                {flatItems.map((item, index) => (
                  <IntelligentStudyCard 
                    key={item.id} 
                    item={item} 
                    index={index} 
                  />
                ))}
              </div>
            </div>

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