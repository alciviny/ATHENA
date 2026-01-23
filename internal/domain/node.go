package domain

import (
	"time"

	"github.com/google/uuid"
)

// KnowledgeNode representa uma unidade de conhecimento no sistema.
// Os campos espelham a entidade definida no serviço Python para
// garantir a paridade e consistência dos dados.
type KnowledgeNode struct {
	ID             uuid.UUID `json:"id"`
	Stability      float64   `json:"stability"`
	Difficulty     float64   `json:"difficulty"`
	Reps           int       `json:"reps"`
	Lapses         int       `json:"lapses"`
	Weight         float64   `json:"weight"`
	LastReviewedAt time.Time `json:"last_reviewed_at"`
	NextReviewAt   time.Time `json:"next_review_at"`
}
