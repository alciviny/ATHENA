package infra

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"brain-worker-go/internal/domain"

	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresNodeRepository struct {
	pool *pgxpool.Pool
}

func NewPostgresNodeRepository(pool *pgxpool.Pool) *PostgresNodeRepository {
	return &PostgresNodeRepository{pool: pool}
}

// GetDueNodes implementa o padrão "Atomic Job Queue" do Postgres.
func (r *PostgresNodeRepository) GetDueNodes(
	ctx context.Context,
	limit int,
) ([]domain.KnowledgeNode, error) {

	// 🧠 QUERY BLINDADA (Atomic Fetch-and-Update)
	const query = `
		WITH locked_rows AS (
			SELECT id
			FROM knowledge_nodes
			WHERE next_review_at <= NOW()
			ORDER BY weight DESC
			LIMIT $1
			FOR UPDATE SKIP LOCKED
		)
		UPDATE knowledge_nodes
		SET next_review_at = NOW() + INTERVAL '15 minutes' -- Reserva de segurança
		FROM locked_rows
		WHERE knowledge_nodes.id = locked_rows.id
		RETURNING
			knowledge_nodes.id,
			knowledge_nodes.stability,
			knowledge_nodes.difficulty,
			knowledge_nodes.reps,
			knowledge_nodes.lapses,
			knowledge_nodes.weight,
			knowledge_nodes.last_reviewed_at,
			knowledge_nodes.next_review_at
	`

	rows, err := r.pool.Query(ctx, query, limit)
	if err != nil {
		return nil, fmt.Errorf("falha crítica ao reservar nós (Locking): %w", err)
	}
	defer rows.Close()

	nodes := make([]domain.KnowledgeNode, 0, limit)

	for rows.Next() {
		var n domain.KnowledgeNode
		var lastReview sql.NullTime
		var nextReview time.Time

		if err := rows.Scan(
			&n.ID,
			&n.Stability,
			&n.Difficulty,
			&n.Reps,
			&n.Lapses,
			&n.Weight,
			&lastReview,
			&nextReview,
		); err != nil {
			return nil, fmt.Errorf("falha ao escanear linha reservada: %w", err)
		}

		if lastReview.Valid {
			n.LastReviewedAt = lastReview.Time.UTC()
		}
		n.NextReviewAt = nextReview.UTC()

		nodes = append(nodes, n)
	}

	return nodes, nil
}

// UpdateNode persiste o estado final calculado pelo Worker.
func (r *PostgresNodeRepository) UpdateNode(
	ctx context.Context,
	n domain.KnowledgeNode,
) error {
	const query = `
		UPDATE knowledge_nodes
		SET
			weight = $1,
			difficulty = $2,
			next_review_at = $3
		WHERE id = $4
	`
	cmdTag, err := r.pool.Exec(
		ctx,
		query,
		n.Weight,
		n.Difficulty,
		n.NextReviewAt,
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
