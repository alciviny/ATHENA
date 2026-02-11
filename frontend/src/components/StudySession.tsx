import { useState, useMemo, useEffect } from 'react';
import type { StudyPlan, StudyItem, FeynmanResult } from '../types/athena';
import { useSubmitReview, useValidateFeynman } from '../hooks/useStudyData';
import { Brain } from 'lucide-react';

// --- Components ---

function MemoryHealthBar({ retention, stability }: { readonly retention: number; readonly stability: number }) {
  let colorClass = "bg-emerald-500";
  if (retention < 0.7) colorClass = "bg-red-500 animate-pulse";
  else if (retention < 0.9) colorClass = "bg-amber-500";

  return (
    <div className="w-full space-y-2 mb-6">
      <div className="flex justify-between text-xs uppercase tracking-widest font-bold text-slate-300">
        <span>Probabilidade de Recall</span>
        <span>Estabilidade: {stability.toFixed(1)} dias</span>
      </div>
      <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden border border-slate-700 relative">
        <div className="absolute left-[70%] top-0 bottom-0 w-0.5 bg-slate-600/50 z-10" title="Zona de Esquecimento"></div>
        <div
          className={`h-full ${colorClass} transition-all duration-1000 ease-out`}
          style={{ width: `${retention * 100}%` }} // NOSONAR: largura precisa refletir percentuais em tempo real
        ></div>
      </div>
      <p className="text-[10px] text-center text-slate-400 font-mono">
        {retention < 0.5 ? "⚠️ CRÍTICO: Risco iminente de falha sináptica" : "Conexão neural estável"}
      </p>
    </div>
  );
}

const rootCauseOptions = [
  { id: 'lack_of_base', label: 'Falta de Base' },
  { id: 'attention', label: 'Falta de Atenção' },
  { id: 'forgetting', label: 'Esquecimento Puro' },
  { id: 'stress', label: 'Pressão do Tempo' },
];

function RootCauseSelector({ selectedCause, onSelectCause }: { readonly selectedCause: string | null; readonly onSelectCause: (cause: string) => void; }) {
  return (
    <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
      <h3 className="text-sm font-bold text-center text-red-400 mb-3">Qual foi a causa principal do erro?</h3>
      <div className="flex flex-wrap justify-center gap-2">
        {rootCauseOptions.map((cause) => (
          <button
            key={cause.id}
            onClick={() => onSelectCause(cause.id)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-all duration-200 border
              ${selectedCause === cause.id
                ? 'bg-red-500/20 text-red-300 border-red-500/50 ring-2 ring-red-500/30'
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700 hover:border-slate-600'
              }`}
          >
            {cause.label}
          </button>
        ))}
      </div>
    </div>
  );
}

const selfRatingOptions = [
    { id: 'wrong', label: 'Errei Longe', grade: 1, color: 'bg-red-500/20 text-red-300 border-red-500/50' },
    { id: 'close', label: 'Quase lá', grade: 2, color: 'bg-amber-500/20 text-amber-300 border-amber-500/50' },
    { id: 'correct', label: 'Acertei na Mosca', grade: 4, color: 'bg-green-500/20 text-green-300 border-green-500/50' },
];

function SelfRatingSelector({ selectedGrade, onSelectGrade }: { readonly selectedGrade: number | null; readonly onSelectGrade: (grade: number) => void; }) {
    return (
      <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
        <h3 className="text-sm font-bold text-center text-sky-400 mb-3">Auto-avaliação da Previsão</h3>
        <div className="flex flex-wrap justify-center gap-3">
          {selfRatingOptions.map((opt) => (
            <button
              key={opt.id}
              onClick={() => onSelectGrade(opt.grade)}
              className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 border
                ${selectedGrade === opt.grade
                  ? `${opt.color} ring-2 ring-sky-500/30`
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700 hover:border-slate-600'
                }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

// --- Main Component ---

interface StudySessionProps {
  readonly plan: StudyPlan;
  readonly onComplete: () => void;
  readonly onExit: () => void;
}

type StudyPhase = 'RECALL' | 'FEEDBACK' | 'FEYNMAN';

// NOSONAR: complexidade inerente ao fluxo de sessão interativa; mantemos por necessidade de produto
export function StudySession({ plan, onComplete, onExit }: StudySessionProps) {
  // React Query mutations
  const { mutate: submitReview } = useSubmitReview();
  const { mutate: validateFeynman, isPending: isAnalyzing } = useValidateFeynman();
  
  const [currentIndex, setCurrentIndex] = useState(0);
  const [phase, setPhase] = useState<StudyPhase>('RECALL');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [startTime, setStartTime] = useState(() => Date.now());
  const [selectedRootCause, setSelectedRootCause] = useState<string | null>(null);
  
  // State for Feynman Challenge
  const [feynmanExplanation, setFeynmanExplanation] = useState('');
  const [feynmanResult, setFeynmanResult] = useState<FeynmanResult | null>(null);

  // --- NEW STATE for Scenario Mode ---
  const [prediction, setPrediction] = useState('');
  const [selfRatedGrade, setSelfRatedGrade] = useState<number | null>(null);

  // --- NEW STATE for Semantic Propagation ---
  const [semanticPropagating, setSemanticPropagating] = useState(false);
  const [showFeynmanChallenge, setShowFeynmanChallenge] = useState(false);

  // Reset state when moving to a new card
  // Note: This is an intentional pattern to sync state with currentIndex changes
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    setStartTime(Date.now());
    setSelectedRootCause(null);
    setSelectedOption(null);
    setPrediction('');
    setSelfRatedGrade(null);
    setFeynmanResult(null);
    setPhase('RECALL');
  }, [currentIndex]);
  /* eslint-enable react-hooks/set-state-in-effect */
  
  const itemsWithMeta = useMemo(() => {
    const arr: Array<{ item: StudyItem; topic?: string; sessionId?: string, focus_level?: string }> = [];
    if (plan?.sessions && Array.isArray(plan.sessions)) {
      plan.sessions.forEach((s) => {
        (s.items || []).forEach((it) => arr.push({ item: it, topic: s.topic, sessionId: s.id, focus_level: s.focus_level }));
      });
    }
    if (arr.length === 0 && plan?.study_items && Array.isArray(plan.study_items)) {
      plan.study_items.forEach((it) => arr.push({ item: it, topic: it.content?.front || 'Sem tópico' }));
    }
    return arr;
  }, [plan]);

  const items: StudyItem[] = itemsWithMeta.map((m) => m.item);

  const currentNode = useMemo(() => items[currentIndex], [items, currentIndex]);
  const currentTopic = itemsWithMeta[currentIndex]?.topic;
  const currentFocusLevel = itemsWithMeta[currentIndex]?.focus_level;

  // --- MODE DETECTION ---
  const isScenario = false; // Funcionalidade de cenário não implementada ainda

  const handleSelectOption = (index: number) => {
    if (phase === 'RECALL') {
      setSelectedOption(index);
      setPhase('FEEDBACK');
    }
  };
  
  const handleConfirmPrediction = () => {
    if (phase === 'RECALL') {
      setPhase('FEEDBACK');
    }
  };

  const handleNext = () => {
    const responseTime = (Date.now() - startTime) / 1000;
    
    // Determine grade and correctness
    const correctIndex = currentNode.correct_index ?? currentNode.content?.correct_index ?? 0;
    const isCorrect = isScenario ? selfRatedGrade === 4 : selectedOption === correctIndex;
    const grade = isScenario ? selfRatedGrade : null; // Use self-rated grade for scenarios

    // Submit review usando React Query mutation
    submitReview({
      nodeId: currentNode.id,
      success: isCorrect,
      responseTime,
      explicitGrade: grade,
      rootCause: isCorrect ? undefined : selectedRootCause || undefined
    }, {
      onSuccess: (reviewResponse) => {
        // Show semantic propagation indicator if error occurred
        if (!isCorrect) {
          setSemanticPropagating(true);
          setTimeout(() => setSemanticPropagating(false), 3000);
        }

        if (reviewResponse.trigger_feynman) {
          setPhase('FEYNMAN');
          setFeynmanResult(null);
          setFeynmanExplanation('');
          return;
        }

        // Move to next item
        if (currentIndex < items.length - 1) {
          setCurrentIndex(currentIndex + 1);
        } else {
          onComplete();
        }
      },
      onError: (error) => {
        console.error("Failed to submit review:", error);
        // Move to next anyway
        if (currentIndex < items.length - 1) {
          setCurrentIndex(currentIndex + 1);
        } else {
          onComplete();
        }
      }
    });
  };

  const handleFeynmanSubmit = () => {
    validateFeynman({
      nodeId: currentNode.id,
      explanation: feynmanExplanation
    }, {
      onSuccess: (result) => {
        setFeynmanResult(result);
        setShowFeynmanChallenge(false);
        setPhase('FEEDBACK');
      },
      onError: (error) => {
        console.error("Failed to validate Feynman explanation:", error);
        setShowFeynmanChallenge(false);
        setPhase('FEEDBACK');
      }
    });
  };

  const handleFeynmanChallenge = () => {
    setShowFeynmanChallenge(true);
    setFeynmanResult(null);
    setFeynmanExplanation('');
  };

  if (!currentNode) {
    return (
      <div className="text-white text-center p-8">
        <h2 className="text-2xl font-bold">Sessão de estudo concluída ou sem itens.</h2>
        <button onClick={onExit} className="mt-4 px-4 py-2 bg-emerald-600 rounded">Voltar</button>
      </div>
    );
  }

  const options = currentNode.options ?? currentNode.content?.options ?? [];
  const correctIndex = currentNode.correct_index ?? currentNode.content?.correct_index ?? 0;
  const isCorrect = selectedOption === correctIndex;

  const canProceed = isScenario ? selfRatedGrade !== null : true;

  // Extract display values - handle both flashcard and regular node format
  const questionText = currentNode.content?.front || currentNode.front || 'Pergunta não disponível';
  const explanationText = currentNode.explanation || currentNode.content?.back || 'Explicação não disponível';

  return (
    <div className="w-full max-w-2xl mx-auto p-4 md:p-8">
      {currentFocusLevel === 'RECOVERY' && (
        <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/50 rounded-lg flex items-center gap-3">
          <span className="text-2xl">🔋</span>
          <div>
            <h4 className="text-amber-400 font-bold text-sm">Modo de Recuperação Ativo</h4>
            <p className="text-amber-200/70 text-xs">Detectamos cansaço. Reduzimos a carga para focar apenas em revisões essenciais.</p>
          </div>
        </div>
      )}
      
      {semanticPropagating && (
        <div className="mb-6 p-4 bg-purple-500/10 border border-purple-500/50 rounded-lg flex items-center gap-3 animate-pulse">
          <span className="text-2xl">🧠</span>
          <div>
            <h4 className="text-purple-400 font-bold text-sm">Propagação Semântica Ativa</h4>
            <p className="text-purple-200/70 text-xs">Ajustando trilha de aprendizado e priorizando pré-requisitos...</p>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className={`text-sm font-bold uppercase tracking-wider ${isScenario ? 'text-purple-400' : 'text-slate-400'}`}>
            {isScenario ? 'SIMULAÇÃO' : 'Tópico'}
          </h3>
          <h2 className="text-xl font-bold text-white">{currentTopic ?? 'Geral'}</h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleFeynmanChallenge}
            className="flex items-center gap-1 px-3 py-1 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-medium transition-all hover:scale-105"
            title="Explicar usando a Técnica de Feynman"
          >
            🧠 Feynman
          </button>
          <div className="text-sm text-slate-400">
            {currentIndex + 1}/{items.length}
          </div>
        </div>
      </div>
      
      {/* --- RECALL PHASE --- */}
      {phase === 'RECALL' && (
        <div className="text-center space-y-6 animate-fade-in">
          <div className={`p-4 rounded-xl ${isScenario ? 'bg-slate-900 border-purple-800/50' : 'bg-slate-900 border-slate-700'} border`}>
            <MemoryHealthBar 
              retention={currentNode.current_retention || 0.5}
              stability={currentNode.stability || 1}
            />
          </div>

          {isScenario ? (
            // --- SCENARIO RECALL VIEW ---
            <div className="p-6 bg-slate-900/80 rounded-lg border border-slate-700/50 space-y-4 text-left font-mono">
                <h2 className="text-2xl font-bold text-slate-100 leading-relaxed">{questionText}</h2>
                <textarea
                  value={prediction}
                  onChange={(e) => setPrediction(e.target.value)}
                  className="w-full h-32 p-3 bg-slate-950 border border-slate-700 rounded-md text-slate-200 focus:ring-2 focus:ring-purple-500 focus:outline-none transition-colors"
                  placeholder="Descreva sua previsão ou solução aqui..."
                />
                <button
                    onClick={handleConfirmPrediction}
                    disabled={prediction.length < 10}
                    className="w-full p-3 bg-purple-600 rounded-lg text-white font-bold hover:bg-purple-500 transition-colors duration-200 disabled:bg-slate-700 disabled:cursor-not-allowed"
                >
                    Confirmar Previsão
                </button>
            </div>
          ) : (
            // --- QUIZ RECALL VIEW ---
            <>
              {currentNode.topic_roi && (
                  <div className="flex justify-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-tighter ${
                          currentNode.topic_roi.includes("ALTO") ? "bg-red-500/20 text-red-400 border border-red-500/50" :
                          "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                      }`}>
                          {currentNode.topic_roi}
                      </span>
                  </div>
              )}
              <h1 className="text-3xl font-bold text-white">{questionText}</h1>
              {options.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {options.map((option: string, index: number) => (
                    <button
                      key={`${currentNode.id}-opt-${index}`}
                      onClick={() => handleSelectOption(index)}
                      className="p-4 bg-slate-800 rounded-lg text-white hover:bg-slate-700 transition-colors duration-200"
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-6 bg-red-900/20 border border-red-500/50 rounded-lg">
                  <p className="text-red-400 text-sm">⚠️ Nenhuma opção disponível para esta questão.</p>
                  <p className="text-slate-400 text-xs mt-2">Debug: {JSON.stringify({ id: currentNode.id, hasContent: !!currentNode.content, hasOptions: !!currentNode.options })}</p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* --- FEYNMAN PHASE --- */}
      {(phase === 'FEYNMAN' || showFeynmanChallenge) && (
        <div className="space-y-6 animate-fade-in">
          <div className="text-center">
            <h2 className="text-xl font-bold text-indigo-400 mb-2">🧠 Desafio Feynman</h2>
            <p className="text-slate-400 text-sm">Explique este conceito como se estivesse ensinando para uma criança de 5 anos.</p>
          </div>
          
          <div className="p-4 bg-slate-900/80 rounded-lg border border-slate-700/50">
            <h3 className="text-white font-semibold mb-2">Conceito:</h3>
            <p className="text-slate-300 text-sm">{questionText}</p>
          </div>
          
          <textarea
            value={feynmanExplanation}
            onChange={(e) => setFeynmanExplanation(e.target.value)}
            className="w-full h-32 p-4 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Descreva o conceito de forma simples e clara..."
          />
          
          <div className="flex gap-3">
            {showFeynmanChallenge && (
              <button
                onClick={() => setShowFeynmanChallenge(false)}
                className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
              >
                Cancelar
              </button>
            )}
            <button
              onClick={handleFeynmanSubmit}
              disabled={isAnalyzing || feynmanExplanation.length < 20}
              className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <Brain className="w-4 h-4 animate-pulse" />
                  Analisando...
                </>
              ) : (
                'Validar Explicação'
              )}
            </button>
          </div>
        </div>
      )}

      {/* --- FEEDBACK PHASE --- */}
      {phase === 'FEEDBACK' && (
        <div className="text-center space-y-6 animate-fade-in">
          {feynmanResult ? (
            // Feynman Feedback
            <div className="space-y-6">
              {(() => {
                const scorePercent = Math.round(feynmanResult.score * 100);
                const scoreClass = feynmanResult.score >= 0.8 ? 'text-green-400' : feynmanResult.score >= 0.6 ? 'text-yellow-400' : 'text-red-400';
                const scoreLabel = feynmanResult.score >= 0.8 ? 'Excelente explicação!' : feynmanResult.score >= 0.6 ? 'Quase lá!' : 'Precisa melhorar';
                const barClass = feynmanResult.score >= 0.8 ? 'bg-green-500' : feynmanResult.score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500';
                return (
                  <>
                    <h2 className={`text-3xl font-bold ${scoreClass}`}>{scoreLabel}</h2>
                    <div className="flex items-center justify-center gap-3">
                      <span className="text-slate-400 text-sm font-medium">Score:</span>
                      <div className="w-48 h-3 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${barClass}`}
                          style={{ width: `${scorePercent}%` }} // NOSONAR: barra de progresso depende de percentuais calculados em runtime
                        />
                      </div>
                      <span className="text-white font-bold">{scorePercent}%</span>
                    </div>
                  </>
                );
              })()}

              {/* Feedback da IA */}
              <div className="p-6 bg-slate-900 rounded-lg text-left space-y-4 border border-slate-700">
                <div>
                  <h3 className="font-bold text-sky-400 text-sm uppercase tracking-wider mb-2">Feedback</h3>
                  <p className="text-slate-200">{feynmanResult.feedback}</p>
                </div>

                {/* Conceitos faltando */}
                {feynmanResult.missing_concepts && feynmanResult.missing_concepts.length > 0 && (
                  <div>
                    <h3 className="font-bold text-amber-400 text-sm uppercase tracking-wider mb-2">Conceitos para revisar</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {feynmanResult.missing_concepts.map((concept) => (
                        <li key={concept} className="text-slate-300">{concept}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <button
                onClick={handleNext}
                className="w-full p-4 bg-indigo-600 rounded-lg text-white font-bold hover:bg-indigo-500 transition-colors duration-200"
              >
                Próximo
              </button>
            </div>
          ) : isScenario ? (
            // --- SCENARIO FEEDBACK VIEW ---
            <div className='space-y-6'>
                <h2 className="text-3xl font-bold text-sky-400">Resultado Esperado</h2>
                <div className="p-6 bg-slate-900 rounded-lg text-left space-y-6 border border-slate-700">
                    <div>
                        <h3 className="font-bold text-slate-400 text-sm uppercase tracking-wider mb-2">Sua Previsão</h3>
                        <p className="text-slate-200 p-4 bg-slate-800/50 rounded-md">{prediction || "Nenhuma previsão foi fornecida."}</p>
                    </div>
                    <div>
                        <h3 className="font-bold text-green-400 text-sm uppercase tracking-wider mb-2">Previsão Correta / Resultado</h3>
                        <p className="text-slate-200 p-4 bg-slate-800/50 rounded-md">Resultado esperado não disponível</p>
                    </div>
                </div>
                <SelfRatingSelector selectedGrade={selfRatedGrade} onSelectGrade={setSelfRatedGrade} />
                <button
                    onClick={handleNext}
                    disabled={!canProceed}
                    className="w-full p-4 bg-indigo-600 rounded-lg text-white font-bold hover:bg-indigo-500 transition-colors duration-200 disabled:bg-slate-700 disabled:cursor-not-allowed"
                >
                    Próximo
                </button>
            </div>
          ) : (
            // --- QUIZ FEEDBACK VIEW ---
            <>
              <h2 className={`text-4xl font-bold ${isCorrect ? 'text-green-400' : 'text-red-400'}`}>
                  {isCorrect ? 'Correto!' : 'Incorreto'}
              </h2>
              <div className="p-6 bg-slate-800 rounded-lg text-left space-y-4">
                  <p className="text-white"><strong className="font-bold">Resposta correta:</strong> {options[correctIndex]}</p>
                  <p className="text-slate-300"><strong className="font-bold text-white">Explicação:</strong> {explanationText}</p>
              </div>
              {!isCorrect && (
                <RootCauseSelector selectedCause={selectedRootCause} onSelectCause={setSelectedRootCause} />
              )}
              <button
                  onClick={handleNext}
                  className="w-full p-4 bg-indigo-600 rounded-lg text-white font-bold hover:bg-indigo-500 transition-colors"
              >
                  Próximo
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
