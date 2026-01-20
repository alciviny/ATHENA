# 🧠 Project Athena | Cognitive Study Intelligence

**Athena** é um ecossistema inteligente de aprendizado adaptativo projetado para **maximizar retenção de conhecimento** e o **ROI (Retorno sobre Investimento) de tempo** em estudos de alto desempenho, como **concursos públicos e certificações técnicas**.

Diferente de plataformas tradicionais de estudo, o Athena combina **Engenharia de Prompt, Grafos de Conhecimento e Arquitetura Modular** para gerar **planos de estudo dinâmicos**, que evoluem continuamente com base na performance real do estudante.

---

## 🎯 Problema que o Athena resolve

* Estudos ineficientes e não personalizados
* Revisões feitas por intuição, não por dados
* Falta de adaptação ao desempenho individual

👉 O Athena transforma estudo em um **sistema cognitivo orientado a dados**.

---

## 🏗️ Arquitetura & Decisões de Engenharia

O sistema foi concebido sob os princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**, garantindo **baixo acoplamento**, **alta testabilidade** e **evolução independente** entre produto, inteligência e infraestrutura.

### 🔄 Fluxo Técnico

```
Frontend
   ↕
BFF (Node.js / TypeScript)
   ↕
Brain (Python / FastAPI)
   ↕
Qdrant (Vector Database)

Workers (Go) ── processamento assíncrono e paralelo
```

### Responsabilidades

* **Frontend ↔ BFF**: Orquestração de UI e proteção de contratos (DTOs)
* **BFF ↔ Brain**: Comunicação com o núcleo inteligente
* **Brain ↔ Qdrant**: Recuperação de contexto semântico via RAG
* **Workers (Go)**: Processamento pesado e sincronização assíncrona

---

## 🧩 Divisão de Módulos (The Hardcore Way)

### 🧠 Athena Brain — Core Intelligence

Implementado em **Python + FastAPI**, é o motor cognitivo do sistema.

**Principais responsabilidades:**

* **RAG (Retrieval-Augmented Generation)**
  Integração com **Qdrant** para fornecer contexto semântico em tempo real às LLMs.

* **Adaptive Rules Engine**
  Lógica de domínio que detecta padrões como *Low Accuracy + High Difficulty* para disparar revisões automáticas.

* **Persistence Layer**
  Repositories sobre **PostgreSQL + SQLAlchemy**, isolando domínio de infraestrutura.

---

### 🛡️ Athena BFF — Backend for Frontend

Implementado em **TypeScript + Express**, atua como **Gateway de Segurança e Orquestração**.

**Principais responsabilidades:**

* **Contract Protection**
  DTOs rigorosos para evitar vazamento de dados e acoplamento indevido.

* **Autenticação & Segurança**
  Gestão de identidade via **JWT**.

* **Escalabilidade**
  Permite escalar IA e API de consumo de forma independente.

---

### ⚙️ Athena Workers — High-Performance Data Layer

Implementado em **Golang**, focado em eficiência computacional máxima.

**Principais responsabilidades:**

* **Concurrency**
  Processamento paralelo e gerenciamento de tarefas assíncronas.

* **Efficiency**
  Redução do custo computacional do Brain em workloads intensivos.

---

## 🔬 Conceitos de Engenharia Aplicados

* **Clean Architecture** — Separação clara entre Entidades, Casos de Uso e Infraestrutura
* **Domain-Driven Design (DDD)** — Regras cognitivas como núcleo do domínio
* **Separation of Concerns**

  * BFF → Produto
  * Brain → Inteligência
  * Workers → Força bruta
* **Vectorial Search** — Busca semântica para detectar lacunas de conhecimento
* **Test-Driven Development (TDD)** — Testes unitários e de integração com **Pytest** e **Jest**

---

## 🚀 Como Executar (Ambiente de Desenvolvimento)

### Pré-requisitos

* Docker & Docker Compose
* Python **3.10+**
* Node.js **18+**
* Go **1.20+**

### Setup Rápido

```bash
# Clone o repositório
git clone https://github.com/alciviny/athena.git

# Suba a infraestrutura (PostgreSQL + Qdrant)
docker-compose up -d

# Setup do Brain (IA)
cd brain
pip install -r requirements.txt
python api/fastapi/main.py

# Setup do BFF (API)
cd ../bff
npm install
npm start
```

---

## 👨‍💻 Autor

**Vinícius**
Software Engineer | IA Aplicada & Sistemas Quantitativos

Este projeto demonstra minha capacidade de **orquestrar sistemas multi-linguagem**, aplicar **padrões arquiteturais robustos** e integrar **Inteligência Artificial em problemas reais de negócio**.

---

## 🔗 Links

* 💼 [LinkedIn](https://www.linkedin.com/in/alcionis-vinicius)
* 🌐 [Portfolio Principal](https://github.com/alciviny)

