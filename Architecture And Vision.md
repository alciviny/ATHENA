# 🎯 Sistema Inteligente de Preparação para Concursos Públicos

## Visão Geral

Este documento consolida **a visão, os objetivos e o plano técnico** do sistema que estamos construindo. Ele existe para **não perder o fio da meada**, alinhar decisões futuras e servir como **guia permanente** do projeto.

O sistema não é apenas uma plataforma de estudo. Ele é um **mentor digital inteligente**, projetado para maximizar desempenho em provas de concurso público, atuando de forma adaptativa, estratégica e orientada a dados.

---

## 🧠 Objetivo Central

> Criar um sistema que **maximize a probabilidade de aprovação** do candidato, transformando estudo em uma atividade **eficiente, personalizada e orientada a resultado**, não a esforço bruto.

O sistema deve:

* Identificar fraquezas antes da prova
* Priorizar conteúdos com maior impacto na nota
* Adaptar-se ao perfil cognitivo do usuário
* Treinar conhecimento, estratégia e psicológico de prova

---

## 🚫 O Que Este Sistema NÃO É

* ❌ Um simples banco de questões
* ❌ Um cronograma fixo de estudos
* ❌ Um repositório de PDFs
* ❌ Um app genérico de flashcards

Essas abordagens ignoram **como pessoas realmente aprendem e erram em provas**.

---

## 🧩 Princípios Fundamentais (Não Negociáveis)

1. **Separação clara de responsabilidades**
2. **Domínio independente de infraestrutura**
3. **Decisão baseada em dados, não em achismo**
4. **Arquitetura preparada para evolução sem reescrita**
5. **IA como ferramenta, não como muleta**
6. **Foco em resultado de prova, não em métricas vazias**

---

## 🏗️ Arquitetura Geral do Sistema

### Visão Macro

```
Frontend (HTML + Tailwind)
        ↓
BFF (TypeScript)
        ↓
Brain (Python)
        ↓
Workers (Go)
```

Cada camada possui **uma responsabilidade única e bem definida**.

---

## 🧠 Brain — Núcleo Inteligente (Python)

### Papel

O Brain é o **cérebro do sistema**. Ele toma todas as decisões importantes relacionadas ao aprendizado.

### Responsabilidades

* Modelar o perfil cognitivo do estudante
* Manter o grafo de conhecimento do edital
* Executar o algoritmo de estudo adaptativo
* Analisar erros e padrões de falha
* Gerar recomendações de estudo e revisão
* Orquestrar uso de LLMs

### Arquitetura Interna

Utiliza **Clean Architecture / Hexagonal**, garantindo isolamento total do domínio.

```
brain/
 ├── domain/
 │    ├── entities/
 │    ├── value_objects/
 │    ├── services/
 │    ├── policies/
 │    └── events/
 ├── application/
 │    ├── use_cases/
 │    ├── dto/
 │    └── ports/
 ├── infrastructure/
 │    ├── persistence/
 │    ├── llm/
 │    ├── vector_store/
 │    └── messaging/
 └── api/
      └── fastapi/
```

### Regra de Ouro

> O domínio **não conhece banco, API, frameworks ou IA externa**.

---

## 🧩 BFF — Orquestrador de Produto (TypeScript)

### Papel

O BFF atua como **ponte entre o frontend e o Brain**, protegendo ambos.

### Responsabilidades

* Autenticação e sessões
* Validação de dados
* Cache
* Agregação de respostas
* Anticorrupção de contratos

### Estrutura

```
bff/
 ├── modules/
 │    ├── auth/
 │    ├── user/
 │    ├── study/
 │    ├── dashboard/
 │    └── metrics/
 ├── contracts/
 ├── middlewares/
 ├── cache/
 └── server.ts
```

### Regra de Ouro

> TypeScript **não implementa regra de negócio**.

---

## ⚙️ Workers — Execução Pesada (Go)

### Papel

Executar tarefas **assíncronas, paralelas e computacionalmente caras**.

### Responsabilidades

* Simulações de prova
* Cálculo estatístico
* Agendamento de revisões
* Processamento em lote

### Estrutura

```
workers/
 ├── simulator/
 ├── scheduler/
 ├── analytics/
 └── common/
```

### Regra de Ouro

> Go **não contém regras de negócio**.

---

## 🎨 Frontend — Interface de Estudo

### Tecnologias

* HTML
* TailwindCSS
* JavaScript mínimo (fetch / Alpine.js opcional)

### Objetivo

* Interface limpa
* Foco total no estudo
* Zero distração

---

## 🗄️ Dados

* **PostgreSQL** → dados transacionais
* **Qdrant** → embeddings e vetores
* Grafo inicialmente modelado no relacional

---

## 🧠 Conceitos-Chave do Sistema

### Perfil Cognitivo

Modelo dinâmico que representa:

* Ritmo de aprendizado
* Retenção
* Tipos de erro
* Impacto do estresse

### Grafo de Conhecimento

* Edital quebrado em microconceitos
* Relações de dependência
* Frequência em provas

### Estudo Adaptativo

Decide:

* O que estudar
* Quando revisar
* O que evitar temporariamente

---

## 🧪 Estratégia de Evolução

### Fase 1 — Fundação

* Domínio sólido
* MVP funcional

### Fase 2 — Inteligência

* Vetores
* Simulador
* Métricas

### Fase 3 — Otimização

* IA avançada
* Grafos dedicados
* Análises preditivas

---

## 🧭 Diretriz Final

> Este sistema deve sempre responder à pergunta:
>
> **“Isso aumenta a chance real de aprovação?”**

Se a resposta for não, a funcionalidade não entra.

---

## 📌 Nota Final

Este documento é **a âncora do projeto**.
Ele deve ser revisitado sempre que houver dúvida, mudança ou crescimento do sistema.
