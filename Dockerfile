# Estágio de Compilação (Build)
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Baixa dependências (cacheado pelo Docker se não mudar)
COPY go.mod go.sum ./
RUN go mod download

# Copia o código fonte
COPY . .

# Compila o binário otimizado
RUN CGO_ENABLED=0 GOOS=linux go build -o athena-worker cmd/worker/main.go

# Estágio Final (Imagem Leve para Produção)
FROM alpine:latest

WORKDIR /app

# Instala certificados SSL para conexões seguras
RUN apk --no-cache add ca-certificates

# Copia apenas o executável do estágio anterior
COPY --from=builder /app/athena-worker .

# Comando para rodar
CMD ["./athena-worker"]
