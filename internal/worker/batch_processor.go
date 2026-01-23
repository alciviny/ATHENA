package worker

import (
	"log"
	"sync"
	"time"

	"athena/internal/domain"
)

// MaxConcurrency define o limite de goroutines simultâneas
// que processarão os nós. Este valor deve ser ajustado
// com base nos recursos de CPU e no pool de conexão do banco de dados.
const MaxConcurrency = 10

// ProcessBatch processa um lote de KnowledgeNodes em paralelo.
// Ele utiliza um padrão de semáforo com um canal bufferizado para limitar
// a concorrência e um WaitGroup para garantir que todas as goroutines
// terminem antes de a função retornar.
func ProcessBatch(nodes []domain.KnowledgeNode) {
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, MaxConcurrency)

	for _, node := range nodes {
		wg.Add(1)
		// É crucial passar o 'node' como argumento para a goroutine
		// para evitar que a variável do loop seja capturada em seu estado final.
		go func(n domain.KnowledgeNode) {
			defer wg.Done()

			// Adquire um slot do semáforo. Bloqueia se o buffer estiver cheio.
			semaphore <- struct{}{}
			// Libera o slot quando a goroutine terminar.
			defer func() { <-semaphore }()

			processNode(n)
		}(node)
	}

	// Espera que todas as goroutines no WaitGroup completem.
	wg.Wait()
}

// processNode encapsula a lógica de negócio para processar um único nó.
// Isso facilita os testes unitários e a evolução da lógica (ex: adicionar retries, métricas).
func processNode(node domain.KnowledgeNode) {
	// Usar time.UTC para consistência entre sistemas
	now := time.Now().UTC()

	elapsedDays := domain.ElapsedDays(node.LastReview, now)
	retrievability := domain.CalculateRetrievability(
		elapsedDays,
		node.Stability,
	)

	// TODO:
	// - Implementar a lógica de atualização da estabilidade e dificuldade.
	// - Calcular o próximo intervalo de revisão.
	// - Persistir os resultados atualizados do nó no banco de dados.
	// - Opcionalmente, emitir um evento para outros serviços.

	log.Printf(
		"[SRS] node=%s elapsed=%.2f stability=%.2f retrievability=%.4f",
		node.ID,
		elapsedDays,
		node.Stability,
		retrievability,
	)
}
