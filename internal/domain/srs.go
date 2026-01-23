package domain

import (
	"math"
	"time"
)

// FSRSWeights espelha exatamente os pesos definidos em SRSPolicy.py.
// A ordem e os valores NÃO devem ser alterados sem versionamento explícito.
var FSRSWeights = []float64{
	0.4, 0.6, 2.4, 5.8, 4.93,
	0.94, 0.86, 0.01, 1.49,
	0.14, 0.94, 2.18, 0.05,
	0.34, 1.26, 0.29, 2.66,
}

// CalculateRetrievability calcula a probabilidade de recuperação
// usando exatamente a mesma fórmula do Python:
//
// exp(log(0.9) * elapsed_days / stability)
//
// Qualquer divergência aqui quebra a sincronia Go <-> Python.
func CalculateRetrievability(elapsedDays float64, stability float64) float64 {
	if stability <= 0 {
		return 0
	}
	return math.Exp(math.Log(0.9) * elapsedDays / stability)
}

// ElapsedDays calcula dias decorridos com precisão flutuante,
// evitando erros de arredondamento por truncamento.
// Utiliza UTC para garantir consistência entre diferentes fusos horários.
func ElapsedDays(lastReview time.Time, now time.Time) float64 {
	return now.UTC().Sub(lastReview.UTC()).Hours() / 24.0
}
