package worker

import (
	"context"
	"log"
	"sync"
	"time"

	"brain-worker-go/internal/domain"
    "brain-worker-go/internal/infra"
)

const (
	MaxConcurrency         = 8
	CriticalRetrievability = 0.8
	SevereRetrievability   = 0.7
)

func ProcessBatch(
	ctx context.Context,
	nodes []domain.KnowledgeNode,
	repo *infra.PostgresNodeRepository,
) {
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, MaxConcurrency)

	for _, node := range nodes {
		wg.Add(1)

		go func(n domain.KnowledgeNode) {
			defer wg.Done()

			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			processNode(ctx, n, repo)
		}(node)
	}

	wg.Wait()
}

func processNode(
	ctx context.Context,
	node domain.KnowledgeNode,
	repo *infra.PostgresNodeRepository,
) {
	// Se o peso é crítico (ex: > 2.0), aciona uma intervenção.
	// Este é o gatilho para o nosso ciclo de validação.
	if node.Weight >= 2.0 {
		processIntervention(ctx, node, repo)
		return // Finaliza o processamento para este nó aqui.
	}

	now := time.Now().UTC()

	elapsedDays := domain.ElapsedDays(node.LastReviewedAt, now)

	R := domain.CalculateRetrievability(
		elapsedDays,
		node.Stability,
	)

	if R < CriticalRetrievability {
		applyPreventiveBoost(ctx, node, R, repo)
	} else {
		log.Printf(
			"[SRS] OK | node=%s R=%.4f",
			node.ID,
			R,
		)
	}
}

// processIntervention simula uma ação corretiva em um nó problemático.
func processIntervention(
	ctx context.Context,
	node domain.KnowledgeNode,
	repo *infra.PostgresNodeRepository,
) {
	log.Printf("🔥 Iniciando intervenção no Node %s (peso atual: %.2f)", node.ID, node.Weight)

	// Simula um trabalho pesado (ex: consulta a um LLM, análise complexa)
	time.Sleep(2 * time.Second)

	// A intervenção foi um sucesso, então resetamos o peso do nó.
	node.Weight = 1.0
	// A data de revisão também é atualizada para evitar re-processamento imediato.
	node.NextReviewAt = time.Now().UTC().Add(5 * time.Minute)

	// Salva o estado "resolvido" no banco de dados.
	if err := repo.UpdateNode(ctx, node); err != nil {
		log.Printf(
			"[ERROR][INTERVENTION] Falha ao atualizar node %s: %v",
			node.ID,
			err,
		)
		return
	}

	log.Printf("✅ Intervenção concluída. Node %s peso resetado para 1.0", node.ID)
}

func applyPreventiveBoost(
	ctx context.Context,
	node domain.KnowledgeNode,
	R float64,
	repo *infra.PostgresNodeRepository,
) {
	// 1️⃣ Aumenta prioridade cognitiva
	node.Weight *= 1.5

	// 2️⃣ Penaliza estabilidade se esquecimento for iminente
	if R < SevereRetrievability {
		node.Stability *= 0.9
	}

	// 3️⃣ Força reaparecimento rápido
	node.NextReviewAt = time.Now().UTC().Add(1 * time.Hour)

	// 4️⃣ Persiste comando cognitivo
	if err := repo.UpdateNode(ctx, node); err != nil {
		log.Printf(
			"[ERROR][BOOST] node=%s R=%.4f err=%v",
			node.ID,
			R,
			err,
		)
		return
	}

	log.Printf(
		"[BOOST APPLIED] node=%s R=%.4f weight=%.2f stability=%.2f",
		node.ID,
		R,
		node.Weight,
		node.Stability,
	)
}
