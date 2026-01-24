package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"runtime"
	"sync"
	"time"

	"brain-worker-go/internal/domain"
	"brain-worker-go/internal/infra"
	"brain-worker-go/internal/worker"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	TOTAL_NODES = 100_000
	BATCH_SIZE  = 1_000
)

func main() {
	ctx := context.Background()

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://user:pass@localhost:5432/athena"
	}

	log.Println("🔥 [STRESS] Conectando ao banco...")
	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		log.Fatalf("Erro na config do DB: %v", err)
	}
	// Ajuste para suportar a carga teórica máxima (Workers * MaxConcurrency)
	config.MaxConns = int32(runtime.NumCPU() * 10)
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		log.Fatalf("Falha crítica: %v", err)
	}
	defer pool.Close()

	repo := infra.NewPostgresNodeRepository(pool)

	// =======================
	// 1. SEED
	// =======================
	log.Printf("🌱 [STRESS] Semeando %d nós com COPY...", TOTAL_NODES)
	ids := seedDatabase(ctx, pool)
	log.Printf("✅ Seed concluído (%d nós)", len(ids))

	// =======================
	// 2. WORKER POOL
	// =======================
	workers := runtime.NumCPU()
	jobs := make(chan []domain.KnowledgeNode)
	var wg sync.WaitGroup

	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for batch := range jobs {
				worker.ProcessBatch(ctx, batch, repo)
			}
		}()
	}

	// =======================
	// 3. STREAM + MÉTRICAS
	// =======================
	var (
		minLatency = time.Hour
		maxLatency time.Duration
		totalTime  time.Duration
		batches    int
	)

	start := time.Now()
	batch := make([]domain.KnowledgeNode, 0, BATCH_SIZE)

	for node := range streamTestNodes(ids) {
		batch = append(batch, node)

		if len(batch) == BATCH_SIZE {
			batchStart := time.Now()
			jobs <- batch
			elapsed := time.Since(batchStart)

			updateLatency(&minLatency, &maxLatency, &totalTime, elapsed)
			batches++

			batch = make([]domain.KnowledgeNode, 0, BATCH_SIZE)
		}
	}

	if len(batch) > 0 {
		batchStart := time.Now()
		jobs <- batch
		elapsed := time.Since(batchStart)

		updateLatency(&minLatency, &maxLatency, &totalTime, elapsed)
		batches++
	}

	close(jobs)
	wg.Wait()

	duration := time.Since(start)
	throughput := float64(TOTAL_NODES) / duration.Seconds()
	avgLatency := totalTime / time.Duration(batches)

	// =======================
	// 4. RELATÓRIO
	// =======================
	fmt.Println("\n========================================")
	fmt.Println("📊 RESULTADO DO STRESS TEST")
	fmt.Println("========================================")
	fmt.Printf("Nós Processados: %d\n", TOTAL_NODES)
	fmt.Printf("Workers:         %d\n", workers)
	fmt.Printf("Batch Size:      %d\n", BATCH_SIZE)
	fmt.Printf("Tempo Total:     %v\n", duration)
	fmt.Printf("Throughput:      %.2f nós/seg\n", throughput)
	fmt.Println("\nLatência por Batch:")
	fmt.Printf("  min: %v\n", minLatency)
	fmt.Printf("  avg: %v\n", avgLatency)
	fmt.Printf("  max: %v\n", maxLatency)
	fmt.Println("========================================")

	if throughput < 1000 {
		fmt.Println("⚠️  ALERTA: Performance abaixo do esperado")
	} else {
		fmt.Println("🚀 SUCESSO: Sistema performando como gente grande")
	}

	// =======================
	// 5. CLEANUP
	// =======================
	cleanup(ctx, pool)
}

// =======================================================
// HELPERS
// =======================================================

func seedDatabase(ctx context.Context, pool *pgxpool.Pool) []uuid.UUID {
	ids := make([]uuid.UUID, TOTAL_NODES)

	conn, err := pool.Acquire(ctx)
	if err != nil {
		log.Fatalf("Erro ao adquirir conexão: %v", err)
	}
	defer conn.Release()

	_, err = conn.Conn().CopyFrom(
		ctx,
		pgx.Identifier{"knowledge_nodes"},
		[]string{
			"id",
			"title",
			"stability",
			"difficulty",
			"weight",
			"reps",
			"lapses",
			"next_review_at",
			"last_reviewed_at",
		},
		pgx.CopyFromSlice(TOTAL_NODES, func(i int) ([]any, error) {
			id := uuid.New()
			ids[i] = id
			return []any{
				id,
				fmt.Sprintf("Stress Node %s", id),
				1.5,
				8.0,
				1.0,
				0,
				0,
				time.Now().Add(-24 * time.Hour),
				time.Now().Add(-48 * time.Hour),
			}, nil
		}),
	)

	if err != nil {
		log.Fatalf("Erro no COPY: %v", err)
	}

	return ids
}

func streamTestNodes(ids []uuid.UUID) <-chan domain.KnowledgeNode {
	out := make(chan domain.KnowledgeNode, 256)

	go func() {
		defer close(out)
		now := time.Now()

		for _, id := range ids {
			out <- domain.KnowledgeNode{
				ID:             id,
				Stability:      1.5,
				LastReviewedAt: now.Add(-200 * time.Hour),
				NextReviewAt:   now.Add(-24 * time.Hour),
				Weight:         1.0,
			}
		}
	}()

	return out
}

func updateLatency(min, max *time.Duration, total *time.Duration, current time.Duration) {
	if current < *min {
		*min = current
	}
	if current > *max {
		*max = current
	}
	*total += current
}

func cleanup(ctx context.Context, pool *pgxpool.Pool) {
	log.Println("🧹 [STRESS] Limpando dados de teste...")
	_, err := pool.Exec(ctx, "DELETE FROM knowledge_nodes WHERE title LIKE 'Stress Node%'")
	if err != nil {
		log.Printf("Erro na limpeza: %v", err)
	}
}
