import React, { useEffect, useMemo, useState } from 'react';
import type { StudyPlan, StudyItem } from '../types/athena';

interface ExamSimulatorProps {
  plan: StudyPlan;
  onComplete: () => void;
}

export function ExamSimulator({ plan, onComplete }: ExamSimulatorProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [phase, setPhase] = useState<'RECALL' | 'FEEDBACK'>('RECALL');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(plan.time_limit_seconds ?? 0);
  const [finalized, setFinalized] = useState(false);

  useEffect(() => {
    if (!timeLeft) return;
    const timer = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timer);
          setFinalized(true);
          // Auto submit when time elapses
          onComplete();
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  const itemsWithMeta = useMemo(() => {
    const arr: Array<{ item: StudyItem; topic?: string }> = [];
    if (plan?.sessions && Array.isArray(plan.sessions)) {
      plan.sessions.forEach((s) => {
        (s.items || []).forEach((it) => arr.push({ item: it, topic: s.topic }));
      });
    }
    if (arr.length === 0 && plan?.study_items && Array.isArray(plan.study_items)) {
      plan.study_items.forEach((it) => arr.push({ item: it, topic: undefined }));
    }
    return arr;
  }, [plan]);

  const items: StudyItem[] = itemsWithMeta.map((m) => m.item);
  const currentNode = items[currentIndex];

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
      setFinalized(true);
      onComplete();
    }
  };

  if (!currentNode) return <div>Nenhum item do simulador.</div>;

  const options = currentNode ? (currentNode.options ?? currentNode.content?.options ?? []) : [];
  const correctIndex = currentNode ? (currentNode.correct_index ?? currentNode.content?.correct_index ?? 0) : 0;
  const isCorrect = selectedOption === correctIndex;

  const isExam = (plan.plan_type ?? 'learning') === 'exam';

  return (
    <div className="w-full max-w-2xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-sm text-slate-400">Simulador</h3>
          <h2 className="text-xl font-bold text-white">{itemsWithMeta[currentIndex]?.topic ?? 'Geral'}</h2>
        </div>
        <div className="text-sm text-slate-300">
          Tempo restante: {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
        </div>
      </div>

      {phase === 'RECALL' && (
        <div className="space-y-6 text-center">
          <h1 className="text-3xl font-bold text-white">{currentNode.front}</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {options.map((option: string, index: number) => (
              <button key={index} onClick={() => handleSelectOption(index)} className="p-4 bg-slate-800 rounded-lg text-white">
                {option}
              </button>
            ))}
          </div>
        </div>
      )}

      {phase === 'FEEDBACK' && selectedOption !== null && (
        <div className="text-center space-y-6">
          <h2 className={`text-4xl font-bold ${isCorrect ? 'text-green-400' : 'text-red-400'}`}>{isCorrect ? 'Correto!' : 'Incorreto'}</h2>
          <div className="p-6 bg-slate-800 rounded-lg text-left">
            <p className="text-white"><strong>Resposta correta:</strong> {options[correctIndex]}</p>
            {/* Mostrar explicação apenas se NÃO for EXAM ou se finalizado */}
            {(!isExam || finalized) ? (
              <p className="text-slate-300 mt-2"><strong>Explicação:</strong> {currentNode.explanation || currentNode.content?.back}</p>
            ) : (
              <p className="text-slate-500 italic mt-2">Explicação ficará oculta até a submissão final.</p>
            )}
          </div>

          <button onClick={handleNext} className="w-full p-4 bg-indigo-600 rounded-lg text-white">Próximo</button>
        </div>
      )}
    </div>
  );
}

export default ExamSimulator;
