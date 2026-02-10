import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config.settings import settings

async def main():
    print("=== CORRIGINDO DIMENSÕES DO QDRANT ===\n")
    
    client = QdrantClient(url=settings.QDRANT_URL)
    collections = ["knowledge_base", "athena_knowledge"]  # Ambas as coleções
    
    for collection_name in collections:
        try:
            # Verifica coleção atual
            collection_info = client.get_collection(collection_name)
            current_dim = collection_info.config.params.vectors.size
            print(f"📊 {collection_name}: dimensão atual = {current_dim}")
            
            if current_dim == 3072:
                print(f"✅ {collection_name}: dimensões corretas!\n")
                continue
            
            # Apaga coleção antiga
            print(f"🗑️  Deletando {collection_name} (dim={current_dim})...")
            client.delete_collection(collection_name)
            print(f"✅ {collection_name} deletada\n")
            
        except Exception as e:
            print(f"⚠️  {collection_name} não existe: {e}\n")
        
        # Recria com dimensão correta
        print(f"🔨 Criando {collection_name} (dim=3072)...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=3072,
                distance=Distance.COSINE
            )
        )
        print(f"✅ {collection_name} recriada!\n")
    
    print("✅ CONCLUÍDO! Execute: python seed_rag.py\n")

if __name__ == "__main__":
    asyncio.run(main())
