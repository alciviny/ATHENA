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
