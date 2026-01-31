import { useState, useMemo } from 'react';
import type { StudyPlan, StudyItem } from '../types/athena';

// --- NOVO COMPONENTE ---
// Componente da Barra de Saúde da Memória
function MemoryHealthBar({ retention, stability }: { retention: number, stability: number }) {
  // Cor baseada na urgência: Vermelho (<70%), Amarelo (<90%), Verde (>=90%)
  let colorClass = "bg-emerald-500";
  if (retention < 0.7) colorClass = "bg-red-500 animate-pulse";
  else if (retention < 0.9) colorClass = "bg-amber-500";

  return (
    <div className="w-full space-y-2 mb-6">
      <div className="flex justify-between text-xs uppercase tracking-widest font-bold text-slate-500">
        <span>Probabilidade de Recall</span>
        <span>Estabilidade: {stability.toFixed(1)} dias</span>
      </div>
      <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden border border-slate-700 relative">
        {/* Marca de perigo em 70% */}
        <div className="absolute left-[70%] top-0 bottom-0 w-0.5 bg-slate-600/50 z-10" title="Zona de Esquecimento"></div>
        
        <div 
          className={`h-full ${colorClass} transition-all duration-1000 ease-out`}
          style={{ width: `${retention * 100}%` }}
        ></div>
      </div>
      <p className="text-[10px] text-center text-slate-600 font-mono">
        {retention < 0.5 ? "⚠️ CRÍTICO: Risco iminente de falha sináptica" : "Conexão neural estável"}
      </p>
    </div>
  );
}


interface StudySessionProps {
  plan: StudyPlan;
  onComplete: () => void;
  onExit: () => void;
}

type StudyPhase = 'RECALL' | 'FEEDBACK';

export function StudySession({ plan, onComplete, onExit }: StudySessionProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [phase, setPhase] = useState<StudyPhase>('RECALL');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  // Flatten all sessions -> items while keeping session metadata (topic)
  const itemsWithMeta = useMemo(() => {
    const arr: Array<{ item: StudyItem; topic?: string; sessionId?: string, focus_level?: string }> = [];
    if (plan?.sessions && Array.isArray(plan.sessions)) {
      plan.sessions.forEach((s) => {
        (s.items || []).forEach((it) => arr.push({ item: it, topic: s.topic, sessionId: s.id, focus_level: s.focus_level }));
      });
    }
    // Fallback to study_items if sessions were not provided
    if (arr.length === 0 && plan?.study_items && Array.isArray(plan.study_items)) {
      plan.study_items.forEach((it) => arr.push({ item: it, topic: undefined }));
    }
    return arr;
  }, [plan]);

  const items: StudyItem[] = itemsWithMeta.map((m) => m.item);

  const currentNode = useMemo(() => items[currentIndex], [items, currentIndex]);
  const currentTopic = itemsWithMeta[currentIndex]?.topic;
  const currentFocusLevel = itemsWithMeta[currentIndex]?.focus_level;


  const handleSelectOption = (index: number) => {
    if (phase === 'RECALL') {
      setSelectedOption(index);
      setPhase('FEEDBACK');
    }
  };

  const handleNext = () => {
    if (currentIndex < items.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setPhase('RECALL');
      setSelectedOption(null);
    } else {
      onComplete();
    }
  };

  if (!currentNode) {
    return (
      <div className="text-white text-center p-8">
        <h2 className="text-2xl font-bold">Sessão de estudo concluída ou sem itens.</h2>
        <button onClick={onExit} className="mt-4 px-4 py-2 bg-emerald-600 rounded">Voltar</button>
      </div>
    );
  }

  const options = currentNode ? (currentNode.options ?? currentNode.content?.options ?? []) : [];
  const correctIndex = currentNode ? (currentNode.correct_index ?? currentNode.content?.correct_index ?? 0) : 0;
  const isCorrect = selectedOption === correctIndex;

  return (
    <div className="w-full max-w-2xl mx-auto p-8">
      {currentFocusLevel === 'RECOVERY' && (
        <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/50 rounded-lg flex items-center gap-3">
          <span className="text-2xl">🔋</span>
          <div>
            <h4 className="text-amber-400 font-bold text-sm">Modo de Recuperação Ativo</h4>
            <p className="text-amber-200/70 text-xs">Detectamos cansaço. Reduzimos a carga para focar apenas em revisões essenciais.</p>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-sm text-slate-400">Tópico</h3>
          <h2 className="text-xl font-bold text-white">{currentTopic ?? 'Geral'}</h2>
        </div>
        <div className="text-sm text-slate-400">
          {currentIndex + 1}/{items.length}
        </div>
      </div>
      {phase === 'RECALL' && (
        <div className="text-center space-y-6 animate-fade-in">
          
          {/* --- INSERÇÃO DOS DADOS DO CÉREBRO --- */}
          <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50">
            <MemoryHealthBar 
              retention={currentNode.current_retention || 0.5} // Fallback
              stability={currentNode.stability || 1}
            />
          </div>

          {currentNode.topic_roi && (
              <div className="flex justify-center mb-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-tighter ${
                      currentNode.topic_roi.includes("ALTO") ? "bg-red-500/20 text-red-400 border border-red-500/50" :
                      currentNode.topic_roi.includes("ESTRATÉGICO") ? "bg-amber-500/20 text-amber-400 border border-amber-500/50" :
                      "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                  }`}>
                      {currentNode.topic_roi}
                  </span>
              </div>
          )}

          <h1 className="text-3xl font-bold text-white">{currentNode.front}</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(currentNode.options || currentNode.content?.options || []).map((option: string, index: number) => (
              <button
                key={index}
                onClick={() => handleSelectOption(index)}
                className="p-4 bg-slate-800 rounded-lg text-white hover:bg-slate-700 transition-colors duration-200"
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      )}

      {phase === 'FEEDBACK' && selectedOption !== null && (
        <div className="text-center space-y-6 animate-fade-in">
            <h2 className={`text-4xl font-bold ${isCorrect ? 'text-green-400' : 'text-red-400'}`}>
                {isCorrect ? 'Correto!' : 'Incorreto'}
            </h2>
            <div className="p-6 bg-slate-800 rounded-lg text-left space-y-4">
                <p className="text-white"><strong className="font-bold">Resposta correta:</strong> {options[correctIndex]}</p>
                <p className="text-slate-300"><strong className="font-bold text-white">Explicação:</strong> {currentNode.explanation}</p>
            </div>
            <button
                onClick={handleNext}
                className="w-full p-4 bg-indigo-600 rounded-lg text-white font-bold hover:bg-indigo-500 transition-colors duration-200"
            >
                Próximo
            </button>
        </div>
      )}
    </div>
  );
}
