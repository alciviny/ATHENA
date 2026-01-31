import json
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from brain.infrastructure.persistence.database import SessionLocal
from brain.infrastructure.persistence.models import KnowledgeNodeModel
from brain.domain.services.graph_validator import KnowledgeGraphValidator, GraphValidationError
from brain.domain.entities.knowledge_node import KnowledgeNode

async def seed_knowledge_graph():
    # Carregamento do currículo estruturado
    with open("brain/data/initial_curriculum.json", "r") as f:
        data = json.load(f)

    # --- VALIDAÇÃO DE NÍVEL DE PRODUÇÃO ---
    try:
        print("🔍 Validando a estrutura do grafo de conhecimento...")
        
        # 1. Criar instâncias de domínio temporárias para validação
        # É preciso simular o grafo com objetos de domínio antes de persistir
        temp_node_map = {
            n_data["id"]: KnowledgeNode(id=n_data["id"], name=n_data["name"])
            for n_data in data["nodes"]
        }

        # 2. Conectar as dependências usando os objetos criados
        for n_data in data["nodes"]:
            node = temp_node_map[n_data["id"]]
            dep_ids = n_data.get("dependencies", [])
            node.dependencies = [temp_node_map[dep_id] for dep_id in dep_ids]
        
        # 3. Validar com o algoritmo de ordenação topológica (que também detecta ciclos)
        temp_nodes_list = list(temp_node_map.values())
        KnowledgeGraphValidator.get_topological_order(temp_nodes_list)
        
        print("✅ Estrutura do Grafo validada. O currículo é acíclico.")

    except GraphValidationError as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        return # Aborta antes de corromper o banco
    except KeyError as e:
        print(f"❌ ERRO CRÍTICO: Dependência não encontrada no JSON: {e}")
        return

    async with SessionLocal() as session:
        print("🔄 Iniciando persistência no banco de dados...")
        # Lógica de persistência (mapeamento de UUIDs e commit)
        db_node_map = {}
        for item in data["nodes"]:
            # Usar o ID do JSON como referência, mas gerar um UUID novo para o banco
            node = KnowledgeNodeModel(
                id=uuid4(),
                name=item["name"],
                difficulty=item.get("difficulty", 0.5),
                importance_weight=item.get("importance", 1.0)
            )
            db_node_map[item["id"]] = node
            session.add(node)

        # Estabelecer as conexões de dependência usando os novos modelos do DB
        for item in data["nodes"]:
            if "dependencies" in item:
                current_db_node = db_node_map[item["id"]]
                for dep_id in item["dependencies"]:
                    if dep_id in db_node_map:
                        parent_db_node = db_node_map[dep_id]
                        current_db_node.dependencies.append(parent_db_node)
        
        await session.commit()
        print("✅ Grafo de Conhecimento carregado com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed_knowledge_graph())