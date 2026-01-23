package main

import (
	"context"
	"log"
	"os"
	"time"

	"athena/internal/infra"
	"athena/internal/worker"

	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	// BATCH_SIZE define quantos nós são buscados do banco por ciclo.
	BATCH_SIZE = 100
	// TICKER_INTERVAL define a frequência com que o worker verifica por novos nós.
	TICKER_INTERVAL = 5 * time.Minute
)

func main() {
	ctx := context.Background()

	// A URL de conexão deve ser fornecida por uma variável de ambiente.
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://user:pass@localhost:5432/athena"
		log.Println("[WARN] DATABASE_URL não definida, usando valor padrão.")
	}

	pool, err := pgxpool.New(ctx, dbURL)
	if err != nil {
		log.Fatalf("Falha ao conectar ao Postgres: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("Não foi possível pingar o banco de dados: %v", err)
	}

	repo := infra.NewPostgresNodeRepository(pool)
	ticker := time.NewTicker(TICKER_INTERVAL)
	defer ticker.Stop()

	log.Println("[WORKER] Worker cognitivo iniciado. Verificando a cada", TICKER_INTERVAL)

	// Loop principal do worker.
	for {
		select {
		case <-ticker.C:
			log.Println("[WORKER] Buscando nós para processar...")
			nodes, err := repo.GetDueNodes(ctx, BATCH_SIZE)
			if err != nil {
				log.Printf("[ERROR] Falha ao buscar nós: %v", err)
				continue
			}

			if len(nodes) == 0 {
				log.Println("[WORKER] Nenhum nó para processar neste ciclo.")
				continue
			}

			log.Printf("[WORKER] Processando lote de %d nós.", len(nodes))
			worker.ProcessBatch(ctx, nodes, repo)
			log.Println("[WORKER] Lote processado.")

		case <-ctx.Done():
			log.Println("[WORKER] Encerrando o worker...")
			return
		}
	}
}
