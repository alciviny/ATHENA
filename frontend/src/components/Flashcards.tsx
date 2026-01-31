import React, { useState } from 'react';
import type { StudyItem } from '../types/athena';

export function Flashcards({ cards }: { cards: StudyItem[] }) {
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [revealed, setRevealed] = useState(false);

  if (!cards || cards.length === 0) return null;

  const card = cards[current];
  const front = card.content?.front ?? card.front ?? '—';
  const options = card.content?.options ?? card.options ?? [];
  const explanation = card.content?.back ?? card.explanation ?? '';
  const correct = card.content?.correct_index ?? card.correct_index ?? 0;

  const choose = (i: number) => {
    if (revealed) return; // já revelado
    setSelected(i);
    setRevealed(true);
  };

  const next = () => {
    setSelected(null);
    setRevealed(false);
    setCurrent((c) => Math.min(cards.length - 1, c + 1));
  };

  const prev = () => {
    setSelected(null);
    setRevealed(false);
    setCurrent((c) => Math.max(0, c - 1));
  };

  return (
    <div className="mb-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-start justify-between mb-4">
        <h4 className="text-lg font-semibold">Flashcard</h4>
        <div className="text-sm text-slate-400">{current + 1} / {cards.length}</div>
      </div>

      <div className="py-4">
        <div className="mb-4 text-white font-medium">{front}</div>
        <div className="grid grid-cols-1 gap-2">
          {options.map((opt, i) => {
            const isSelected = selected === i;
            const isCorrect = revealed && i === correct;
            const isWrong = revealed && isSelected && i !== correct;
            const base = 'p-3 rounded';
            const cls = isCorrect ? `${base} bg-emerald-700 text-white` : isWrong ? `${base} bg-red-700 text-white` : `${base} bg-slate-800 text-slate-200`;
            return (
              <button key={i} disabled={revealed} onClick={() => choose(i)} className={cls}>
                {opt}
              </button>
            );
          })}
        </div>
      </div>

      {revealed && (
        <div className="mt-4 text-sm text-slate-400">
          <strong>Explicação:</strong> {explanation}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button onClick={prev} className="px-3 py-2 bg-slate-800 rounded">Anterior</button>
        <button onClick={next} className="px-3 py-2 bg-emerald-600 rounded text-white">Próximo</button>
      </div>
    </div>
  );
}

export default Flashcards;
