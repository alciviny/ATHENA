import asyncio
import os
import logging
from typing import List, Dict

import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# --- Configuração ---
# MUDANÇA: Usa o nome do host do Docker se disponível, ou fallback para localhost
QDRANT_HOST = os.getenv("QDRANT_HOST", "athena_vector_db") 
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "athena_knowledge"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Dados de Exemplo (Knowledge Base) ---
RAW_DATA = [
    {
        "topic": "Python Basics",
        "text": "Python é uma linguagem de programação de alto nível, interpretada e de propósito geral. Suas filosofias de design enfatizam a legibilidade do código com o uso de indentação significativa. Python suporta múltiplos paradigmas, incluindo procedural, orientado a objetos e funcional."
    },
    {
        "topic": "REST API",
        "text": "REST (Representational State Transfer) é um estilo arquitetural para sistemas distribuídos. APIs RESTful usam métodos HTTP (GET, POST, PUT, DELETE) para manipular recursos. Uma característica chave é ser stateless, ou seja, cada requisição contém toda a informação necessária."
    },
    {
        "topic": "FastAPI",
        "text": "FastAPI é um framework web moderno e rápido (alta performance) para construir APIs com Python 3.8+ baseado em type hints. Ele é construído sobre Starlette (para web) e Pydantic (para dados). Ele gera documentação automática (Swagger UI) e suporta programação assíncrona nativa."
    },
    {
        "topic": "Docker",
        "text": "Docker é uma plataforma aberta para desenvolver, enviar e executar aplicações. Ele permite separar a aplicação da infraestrutura usando contêineres. Contêineres são leves e contêm tudo o que é necessário para rodar o software: código, runtime, ferramentas de sistema e bibliotecas."
    },
     {
        "topic": "Arquitetura Hexagonal",
        "text": "A Arquitetura Hexagonal (Ports and Adapters) visa criar sistemas fracamente acoplados. O núcleo da aplicação (Domínio) fica no centro, isolado de detalhes externos como banco de dados ou UI. A comunicação ocorre através de Portas (interfaces) e Adaptadores (implementações)."
    }
]

async def generate_embedding(text: str) -> List[float]:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não encontrada.")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    try:
        # Usa o modelo novo de embedding
        result = await asyncio.to_thread(
            genai.embed_content,
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Erro ao gerar embedding: {e}")
        return []

async def seed():
    logger.info("--- Iniciando Seed RAG ---")
    logger.info(f"Conectando ao Qdrant em: {QDRANT_URL}")

    # Cliente Síncrono (Estável)
    client = QdrantClient(url=QDRANT_URL)

    # Verifica coleção
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        
        if not exists:
            logger.info(f"Criando coleção '{COLLECTION_NAME}'...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        else:
            logger.info(f"Coleção '{COLLECTION_NAME}' já existe.")
    except Exception as e:
        logger.error(f"Erro ao conectar/criar coleção no Qdrant: {e}")
        return

    # Processa e insere dados
    points = []
    logger.info("Gerando embeddings e preparando pontos...")
    
    for idx, item in enumerate(RAW_DATA):
        emb = await generate_embedding(item["text"])
        if not emb:
            logger.warning(f"Skipping {item['topic']} (Falha no embedding)")
            continue
            
        point = PointStruct(
            id=idx + 1,
            vector=emb,
            payload={
                "topic": item["topic"],
                "text": item["text"],
                "source": "seed_script"
            }
        )
        points.append(point)
        # Pausa para não estourar cota do Gemini (se necessário)
        await asyncio.sleep(1)

    if points:
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            logger.info(f"Sucesso! {len(points)} documentos inseridos no RAG.")
        except Exception as e:
             logger.error(f"Erro ao inserir pontos: {e}")
    else:
        logger.warning("Nenhum ponto gerado para inserção.")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        logger.error("ERRO: GEMINI_API_KEY não definida no ambiente.")
    else:
        asyncio.run(seed())