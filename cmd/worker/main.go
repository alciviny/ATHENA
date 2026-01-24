package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"runtime"
	"syscall"
	"time"

	
	"brain-worker-go/internal/infra"
	"brain-worker-go/internal/worker"

	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	// Configurações do Polling
	POLLING_INTERVAL = 5 * time.Second
	BATCH_SIZE       = 100 // Pega 100 itens por vez do banco
)

func main() {
	// 1. Contexto com cancelamento gracioso (CTRL+C)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Captura sinais do SO para desligar sem perder dados
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// 2. Conexão com o Banco
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://user:pass@localhost:5432/athena"
	}

	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		log.Fatalf("Erro na config do DB: %v", err)
	}
	// Ajuste fino para produção
	config.MaxConns = int32(runtime.NumCPU() * 8) 
	
	log.Println("🔌 [WORKER] Conectando ao ecossistema Athena...")
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		log.Fatalf("Falha crítica ao conectar: %v", err)
	}
	defer pool.Close()

	repo := infra.NewPostgresNodeRepository(pool)
	log.Println("🚀 [WORKER] Sistema Operacional. Aguardando tarefas...")

	// 3. Loop Principal (The Heartbeat)
	ticker := time.NewTicker(POLLING_INTERVAL)
	defer ticker.Stop()

	for {
		select {
		case <-sigChan:
			log.Println("🛑 [SHUTDOWN] Encerrando worker graciosamente...")
			return

		case <-ticker.C:
			// Busca nós vencidos no banco real
			nodes, err := repo.GetDueNodes(ctx, BATCH_SIZE)
			if err != nil {
				log.Printf("⚠️ Erro ao buscar tarefas: %v", err)
				continue
			}

			if len(nodes) == 0 {
				// Nada a fazer, dorme até o próximo tick
				continue
			}

			log.Printf("📦 [BATCH] Processando %d nós vencidos...", len(nodes))
			
			// Processa o lote usando a lógica paralela que já validamos
			worker.ProcessBatch(ctx, nodes, repo)
		}
	}
}
