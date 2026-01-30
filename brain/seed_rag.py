import json
import uuid
import asyncio
import os
from typing import List, Dict

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding

from brain.infrastructure.persistence.models import KnowledgeNodeModel
from brain.config.settings import Settings

# --- Configuração ---
DATA_FILE = "brain/data/initial_curriculum.json"
COLLECTION_NAME = "athena_knowledge"

async def main():
    settings = Settings()
    
    # 1. Conexão Postgres
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    # 2. Conexão Qdrant
    qdrant = AsyncQdrantClient(url=settings.QDRANT_URL)
    
    # 3. Carregar Modelo de Embedding (Local e Rápido)
    print("Carregando modelo de embedding (pode demorar na 1ª vez)...")
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5") # Leve e eficiente

    # 4. Carregar JSON
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Carregados {len(data)} tópicos do arquivo.")

    # 5. Resetar Bancos (Opcional - Cuidado em Prod)
    print("Resetando dados antigos...")
    with Session.begin() as session:
        session.execute(text("TRUNCATE TABLE public.node_dependencies RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE public.knowledge_nodes RESTART IDENTITY CASCADE"))
    
    await qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )

    # 6. Processamento
    node_map: Dict[str, uuid.UUID] = {}
    
    with Session() as session:
        print("Iniciando ingestão...")
        
        # Passo A: Inserir no Postgres (Grafo)
        for item in data:
            new_uuid = uuid.uuid4()
            node_map[item["id"]] = new_uuid
            
            node = KnowledgeNodeModel(
                id=new_uuid,
                name=item["name"],
                subject=item["subject"],
                weight_in_exam=item["weight"],
                difficulty=float(item["difficulty"]),
                weight=1.0 # Peso inicial padrão do algoritmo
            )
            session.add(node)
        
        session.commit()
        
        # Passo B: Criar Dependências
        for item in data:
            if not item["dependencies"]:
                continue
                
            current_uuid = node_map[item["id"]]
            current_node = session.get(KnowledgeNodeModel, current_uuid)
            
            for dep_id in item["dependencies"]:
                if dep_id in node_map:
                    dep_uuid = node_map[dep_id]
                    dep_node = session.get(KnowledgeNodeModel, dep_uuid)
                    current_node.dependencies.append(dep_node)
        
        session.commit()
        print("Postgres populado com grafo relacional.")

        # Passo C: Gerar Vetores e Popular Qdrant
        print("Gerando embeddings e enviando para Qdrant...")
        
        documents = [item["content"] for item in data]
        # Gera embeddings em batch
        embeddings = list(embedding_model.embed(documents))
        
        points = []
        for i, item in enumerate(data):
            node_uuid = node_map[item["id"]]
            vector = embeddings[i]
            
            points.append(models.PointStruct(
                id=str(node_uuid),
                vector=vector.tolist(),
                payload={
                    "name": item["name"],
                    "subject": item["subject"],
                    "text": item["content"], # CRÍTICO: O texto que a IA vai ler
                    "node_id": str(node_uuid)
                }
            ))
            
        await qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Qdrant populado com {len(points)} vetores.")

if __name__ == "__main__":
    asyncio.run(main())