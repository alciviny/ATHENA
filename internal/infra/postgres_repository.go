package infra

import (
	"context"
	"fmt"

	"brain-worker-go/internal/domain"

	"github.com/jackc/pgx/v5/pgxpool"
)

// PostgresNodeRepository implementa a porta de acesso aos dados para KnowledgeNodes
// usando um pool de conexões PostgreSQL.
type PostgresNodeRepository struct {
	pool *pgxpool.Pool
}

// NewPostgresNodeRepository é a fábrica para criar uma nova instância do repositório.
// Isso facilita a injeção de dependência.
func NewPostgresNodeRepository(pool *pgxpool.Pool) *PostgresNodeRepository {
	return &PostgresNodeRepository{pool: pool}
}

// GetDueNodes seleciona nós cujo next_review expirou.
// A ordenação por 'weight' permite que o worker processe primeiro os nós
// cognitivamente mais importantes ou frágeis.
func (r *PostgresNodeRepository) GetDueNodes(
	ctx context.Context,
	limit int,
) ([]domain.KnowledgeNode, error) {

	const query = `
		SELECT
			id,
			stability,
			difficulty,
			reps,
			lapses,
			weight,
			last_reviewed_at,
			next_review_at
		FROM knowledge_nodes
		WHERE next_review_at <= NOW()
		ORDER BY weight DESC
		LIMIT $1
	`

	rows, err := r.pool.Query(ctx, query, limit)
	if err != nil {
		return nil, fmt.Errorf("falha ao consultar nós devidos: %w", err)
	}
	defer rows.Close()

	// Pré-aloca a slice com a capacidade máxima para evitar realocações.
	nodes := make([]domain.KnowledgeNode, 0, limit)

	for rows.Next() {
		var n domain.KnowledgeNode

		if err := rows.Scan(
			&n.ID,
			&n.Stability,
			&n.Difficulty,
			&n.Reps,
			&n.Lapses,
			&n.Weight,
			&n.LastReviewedAt,
			&n.NextReviewAt,
		); err != nil {
			return nil, fmt.Errorf("falha ao escanear linha de knowledge_node: %w", err)
		}

		nodes = append(nodes, n)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("erro durante a iteração das linhas: %w", err)
	}

	return nodes, nil
}

// UpdateNode persiste o estado modificado de um nó no banco de dados.
// A atualização é atômica e mira apenas nos campos que o worker gerencia.
func (r *PostgresNodeRepository) UpdateNode(
	ctx context.Context,
	n domain.KnowledgeNode,
) error {

	const query = `
		UPDATE knowledge_nodes
		SET
			weight = $1,
			next_review_at = $2,
			stability = $3
		WHERE id = $4
	`

	cmdTag, err := r.pool.Exec(
		ctx,
		query,
		n.Weight,
		n.NextReviewAt,
		n.Stability,
		n.ID,
	)
	if err != nil {
		return fmt.Errorf("falha ao atualizar o nó %s: %w", n.ID, err)
	}
	if cmdTag.RowsAffected() == 0 {
		return fmt.Errorf("nenhuma linha afetada ao atualizar o nó %s", n.ID)
	}

	return nil
}

