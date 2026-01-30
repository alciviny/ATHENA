import os
import glob
import logging
import asyncio
from typing import List
from uuid import uuid4

import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuração de Log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
# Ajuste conforme suas variáveis de ambiente ou settings.py
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Certifique-se de ter essa ENV definida
COLLECTION_NAME = "knowledge_base"

# Configura o Gemini
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_pdf(filepath: str) -> str:
    """Extrai texto puro de um PDF."""
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Erro ao ler PDF {filepath}: {e}")
        return ""

def load_documents(data_dir: str = "data") -> List[dict]:
    """Lê todos os arquivos .md e .pdf da pasta data."""
    docs = []
    
    # Busca arquivos Markdown
    for filepath in glob.glob(os.path.join(data_dir, "**/*.md"), recursive=True):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            docs.append({"content": content, "source": os.path.basename(filepath), "type": "markdown"})
            
    # Busca arquivos PDF
    for filepath in glob.glob(os.path.join(data_dir, "**/*.pdf"), recursive=True):
        content = extract_text_from_pdf(filepath)
        if content:
            docs.append({"content": content, "source": os.path.basename(filepath), "type": "pdf"})
    
    logger.info(f"Encontrados {len(docs)} documentos.")
    return docs

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Quebra o texto em pedaços menores (chunks) para vetorização."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)

async def generate_embedding(text: str) -> List[float]:
    """Gera o vetor usando o modelo do Google."""
    try:
        # O modelo 'embedding-001' é otimizado para tarefas de busca
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document",
            title="Educational Content"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Erro ao gerar embedding: {e}")
        return []

async def seed():
    """Função principal de semeadura."""
    logger.info("--- Iniciando Seed RAG ---")
    
    # 1. Conectar ao Qdrant
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # 2. Criar coleção se não existir
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        logger.info(f"Criando coleção '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=768, # Tamanho do vetor do modelo embedding-001 do Google
                distance=models.Distance.COSINE
            )
        )
    else:
        logger.info(f"Coleção '{COLLECTION_NAME}' já existe.")

    # 3. Carregar Documentos
    docs = load_documents("brain/data") # Certifique-se que seus PDFs estão aqui!
    
    points = []
    
    # 4. Processar e Vetorizar
    for doc in docs:
        logger.info(f"Processando: {doc['source']}")
        chunks = split_text(doc['content'])
        
        for i, chunk in enumerate(chunks):
            vector = await generate_embedding(chunk)
            
            if not vector:
                continue
                
            # Cria o ponto para o Qdrant
            point = models.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": chunk,
                    "source": doc['source'],
                    "chunk_index": i,
                    "type": doc['type']
                }
            )
            points.append(point)
            
            # Batch upload a cada 50 chunks para não sobrecarregar
            if len(points) >= 50:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                logger.info(f"Upload de {len(points)} chunks realizado.")
                points = []
                await asyncio.sleep(1) # Rate limit friendly

    # Upload final
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"Upload final de {len(points)} chunks realizado.")

    logger.info("--- Seed RAG Concluído com Sucesso! ---")

if __name__ == "__main__":
    asyncio.run(seed())
