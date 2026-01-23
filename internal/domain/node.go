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
	LastReview     time.Time `json:"last_review"`
	NextReview     time.Time `json:"next_review"`
}
