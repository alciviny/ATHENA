Project Athena | Cognitive Study Intelligence
O Athena é um ecossistema inteligente de aprendizado adaptativo projetado para maximizar a retenção de conhecimento e o ROI (Retorno sobre Investimento) de tempo em estudos de alto desempenho (concursos e certificações).

Diferente de sistemas de estudo tradicionais, o Athena utiliza Engenharia de Prompt, Grafos de Conhecimento e uma arquitetura modular para criar planos de estudo dinâmicos que evoluem com a performance do estudante.

🏗️ Arquitetura e Decisões de Engenharia
O sistema foi concebido sob os princípios de Clean Architecture e Domain-Driven Design (DDD) para garantir o desacoplamento entre a lógica de negócio cognitiva e os motores de IA.

Diagrama de Fluxo Técnico
Frontend ↔ BFF (Node/TS): Orquestração de UI e proteção de contratos de dados (DTOs).

BFF ↔ Brain (Python/FastAPI): O núcleo inteligente que executa algoritmos adaptativos.

Brain ↔ Qdrant (Vector DB): Recuperação de contexto semântico via RAG.

Workers (Go): Processamento paralelo de fluxos de dados pesados e sincronização assíncrona.

🛠️ Divisão de Módulos (The Hardcore Way)
1. 🧠 Athena Brain (Core Intelligence)
Implementado em Python/FastAPI, este módulo é o motor de decisão.

RAG (Retrieval-Augmented Generation): Integração com bancos vetoriais (Qdrant) para fornecer contexto em tempo real às LLMs.

Adaptive Rules Engine: Lógica de domínio que detecta padrões de erro (ex: Low Accuracy + High Difficulty) para disparar revisões automáticas.

Persistence: Implementação de Repositories sobre PostgreSQL/SQLAlchemy.

2. 🛡️ Athena BFF (Backend for Frontend)
Implementado em TypeScript/Express, atua como o Security & Orchestration Gateway.

Contract Protection: Uso de DTOs rigorosos para garantir que o frontend receba apenas o necessário.

Auth: Gestão de identidade e segurança via JWT.

Scalability: Desacoplamento que permite escalar a lógica de IA independente da API de consumo.

3. ⚙️ Athena Workers (Data High-Performance)
Implementado em Golang para máxima eficiência computacional.

Concurrency: Gerenciamento de tarefas assíncronas e processamento de grandes volumes de dados de performance.

Efficiency: Camada de execução otimizada para reduzir o custo computacional do "Brain".

🔬 Conceitos de Engenharia Aplicados
Clean Architecture: Divisão clara entre Entidades, Casos de Uso e Gateways de Infraestrutura.

Separation of Concerns: O BFF cuida do produto; o Brain cuida da inteligência; o Worker cuida da força bruta.

Vectorial Search: Busca semântica para encontrar lacunas de conhecimento no histórico do aluno.

Test-Driven Development (TDD): Cobertura de testes unitários e de integração utilizando Pytest e Jest.

🚀 Como Executar (Ambiente de Dev)
Pré-requisitos
Docker & Docker Compose

Python 3.10+

Node.js 18+

Go 1.20+

Setup Rápido
Bash

# Clone o repositório
git clone https://github.com/alciviny/athena.git

# Suba a infraestrutura (PostgreSQL + Qdrant)
docker-compose up -d

# Setup do Brain (IA)
cd brain && pip install -r requirements.txt
python api/fastapi/main.py

# Setup do BFF (API)
cd bff && npm install
npm start
👨‍💻 Autor: Vinícius
Software Engineer | AI & Quant Enthusiast

Este projeto demonstra minha capacidade de orquestrar sistemas multi-linguagem, aplicar padrões arquiteturais robustos e integrar Inteligência Artificial em problemas de negócio reais.

LinkedIn

Portfolio Principal
