import { useState, useEffect, useRef } from 'react';
import { Clock, ArrowLeft } from 'lucide-react';
import { ReviewGrade } from '../types/athena';
import type { StudyPlanDTO, ReviewGradeValue } from '../types/athena';
import { studyService } from '../services/studyService';
import clsx from 'clsx';

interface StudySessionProps {
  plan: StudyPlanDTO;
  onComplete: () => void;
  onExit: () => void;
}

export function StudySession({ plan, onComplete, onExit }: StudySessionProps) {
  // Estado do progresso
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnswerRevealed, setIsAnswerRevealed] = useState(false);
  const [startTime, setStartTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Timer visual
  const timerRef = useRef<number>(0);

  const currentNodeId = plan.knowledge_nodes[currentIndex];
  const totalNodes = plan.knowledge_nodes.length;

  useEffect(() => {
    // Inicia contagem de tempo para o card atual
    setStartTime(Date.now());
    setElapsed(0);
    
    timerRef.current = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [currentIndex]);

  const handleReveal = () => {
    setIsAnswerRevealed(true);
  };

  const handleGrade = async (grade: ReviewGradeValue) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    clearInterval(timerRef.current);

    const timeSpent = (Date.now() - startTime) / 1000; // Segundos exatos

    try {
      await studyService.submitReview(currentNodeId, grade, timeSpent);

      if (currentIndex < totalNodes - 1) {
        // Próximo card
        setCurrentIndex((prev) => prev + 1);
        setIsAnswerRevealed(false);
      } else {
        // Fim da sessão
        onComplete();
      }
    } catch (error) {
      console.error("Erro ao enviar review:", error);
      alert("Erro de conexão. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Cores dos botões de SRS baseadas no Anki/SuperMemo
  const gradeButtons = [
    { label: 'Errei', value: ReviewGrade.AGAIN, color: 'bg-rose-600 hover:bg-rose-500', shortcut: '1' },
    { label: 'Difícil', value: ReviewGrade.HARD, color: 'bg-orange-600 hover:bg-orange-500', shortcut: '2' },
    { label: 'Bom', value: ReviewGrade.GOOD, color: 'bg-emerald-600 hover:bg-emerald-500', shortcut: '3' },
    { label: 'Fácil', value: ReviewGrade.EASY, color: 'bg-blue-600 hover:bg-blue-500', shortcut: '4' },
  ];

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100">
      {/* Topbar Focada */}
      <header className="h-16 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-900/50">
        <div className="flex items-center gap-4">
          <button onClick={onExit} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-slate-300">Modo Foco</span>
            <span className="text-xs text-slate-500">
              Card {currentIndex + 1} de {totalNodes}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full text-sm border border-emerald-500/20">
          <Clock className="w-4 h-4" />
          {new Date(elapsed * 1000).toISOString().substr(14, 5)}
        </div>
      </header>

      {/* Área Central (O Card) */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 relative">
        <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl min-h-[400px] flex flex-col justify-between">
          
          <div className="space-y-6 text-center">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
              Tópico de Conhecimento
            </h2>
            <div className="text-2xl md:text-3xl font-medium text-white">
              {/* TODO: Substituir UUID pelo Nome real vindo do Backend */}
              <span className="font-mono text-slate-400 text-lg block mb-2">ID: {currentNodeId.split('-')[0]}...</span>
              Conceito ou Questão sobre o tópico
            </div>

            {isAnswerRevealed && (
              <div className="pt-8 border-t border-slate-800 animate-fade-in">
                <p className="text-lg text-slate-300">
                  Aqui seria exibida a resposta, explicação ou solução detalhada do nó de conhecimento.
                </p>
              </div>
            )}
          </div>

          {/* Controles */}
          <div className="mt-12">
            {!isAnswerRevealed ? (
              <button 
                onClick={handleReveal}
                className="w-full py-4 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl border border-slate-700 transition-all active:scale-[0.98]"
              >
                Mostrar Resposta (Espaço)
              </button>
            ) : (
              <div className="grid grid-cols-4 gap-3">
                {gradeButtons.map((btn) => (
                  <button
                    key={btn.value}
                    onClick={() => handleGrade(btn.value)}
                    disabled={isSubmitting}
                    className={clsx(
                      "py-4 rounded-xl font-bold text-white transition-all active:scale-[0.95] flex flex-col items-center gap-1",
                      btn.color,
                      isSubmitting && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    <span>{btn.label}</span>
                    <span className="text-[10px] font-mono opacity-60">({btn.shortcut})</span>
                  </button>
                ))}
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}
