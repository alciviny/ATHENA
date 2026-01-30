import { useState, useEffect } from 'react';
import { X, Lightbulb, Sparkles, ThumbsUp, ThumbsDown, Repeat, ChevronsRight } from 'lucide-react';
import type { StudyPlanDTO, StudyItem, ReviewGrade } from '../types/athena';
import { studyService } from '../services/studyService';

interface StudySessionProps {
  plan: StudyPlanDTO;
  onComplete: () => void;
  onExit: () => void;
}

type SessionPhase = 'RECALL' | 'GRADE';

export function StudySession({ plan, onComplete, onExit }: StudySessionProps) {
  const [currentNodeIndex, setCurrentNodeIndex] = useState(0);
  const [phase, setPhase] = useState<SessionPhase>('RECALL');
  const [reviewStartTime, setReviewStartTime] = useState(0);

  const currentNode: StudyItem = plan.study_items[currentNodeIndex];
  const progress = ((currentNodeIndex + 1) / plan.study_items.length) * 100;

  useEffect(() => {
    setPhase('RECALL');
  }, [currentNodeIndex]);

  const handleReveal = () => {
    setPhase('GRADE');
    setReviewStartTime(Date.now());
  };

  const handleGrade = async (grade: ReviewGrade) => {
    const responseTime = (Date.now() - reviewStartTime) / 1000; // em segundos
    
    try {
      await studyService.submitReview(currentNode.id, grade, responseTime);
    } catch (error) {
      console.error("Erro ao submeter revisão:", error);
      // Opcional: Adicionar um toast/alerta para o usuário
    }
    
    // Avança para o próximo card ou finaliza a sessão
    if (currentNodeIndex < plan.study_items.length - 1) {
      setCurrentNodeIndex(currentNodeIndex + 1);
    } else {
      onComplete();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 selection:bg-amber-500/30">
      
      {/* Header da Sessão */}
      <header className="w-full max-w-2xl fixed top-0 left-1/2 -translate-x-1/2 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="font-mono text-sm text-amber-400">{`${currentNodeIndex + 1}/${plan.study_items.length}`}</span>
            <div className="w-64 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-amber-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
          <button onClick={onExit} className="text-slate-500 hover:text-slate-300">
            <X className="w-6 h-6" />
          </button>
        </div>
      </header>

      <main className="w-full max-w-2xl flex-1 flex flex-col justify-center items-center">
        {/* Card de Estudo */}
        <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-8">
          
          {/* Fase de "Recall" (Lembrar) */}
          {phase === 'RECALL' && (
            <div className="text-center space-y-6 animate-fade-in">
              <h1 className="text-3xl font-bold text-white">{currentNode.question}</h1>
              <p className="text-slate-400">Tente se lembrar do conceito principal.</p>
              <button 
                onClick={handleReveal}
                className="w-full py-3 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-xl shadow-lg shadow-amber-900/20 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
              >
                <Lightbulb className="w-5 h-5" />
                Revelar Conteúdo
              </button>
            </div>
          )}

          {/* Fase de "Grade" (Avaliar) */}
          {phase === 'GRADE' && (
            <div className="space-y-6 animate-fade-in">
              <h1 className="text-2xl font-bold text-white border-b border-slate-700 pb-3 mb-4">{currentNode.question}</h1>
              <p className="text-slate-300 whitespace-pre-wrap">{currentNode.explanation}</p>
              
              <div className="pt-6">
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4 text-center">Como você se sentiu ao lembrar disso?</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                  <GradeButton onClick={() => handleGrade(1)} color="red" icon={Repeat}>De novo</GradeButton>
                  <GradeButton onClick={() => handleGrade(2)} color="orange" icon={ThumbsDown}>Difícil</GradeButton>
                  <GradeButton onClick={() => handleGrade(3)} color="sky" icon={ThumbsUp}>Bom</GradeButton>
                  <GradeButton onClick={() => handleGrade(4)} color="emerald" icon={Sparkles}>Fácil</GradeButton>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>

    </div>
  );
}

// Componente auxiliar para os botões de avaliação
function GradeButton({ children, onClick, color, icon: Icon }) {
  const colorClasses = {
    red: 'bg-red-500/10 border-red-500/20 text-red-400 hover:bg-red-500/20',
    orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400 hover:bg-orange-500/20',
    sky: 'bg-sky-500/10 border-sky-500/20 text-sky-400 hover:bg-sky-500/20',
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20',
  };

  return (
    <button 
      onClick={onClick}
      className={`p-4 rounded-lg font-semibold w-full transition-colors flex flex-col items-center justify-center text-center border ${colorClasses[color]}`}
    >
      <Icon className="w-6 h-6 mb-2" />
      {children}
    </button>
  );
}