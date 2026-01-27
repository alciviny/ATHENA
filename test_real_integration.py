import os
import uuid
import time
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# --- Configuração ---
load_dotenv()  # Carrega variáveis de ambiente de um arquivo .env
DATABASE_URL = os.getenv("DATABASE_URL")
POLLING_INTERVAL_SECONDS = 1
TIMEOUT_SECONDS = 20
TARGET_TABLE = "knowledge_nodes"

def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados."""
    if not DATABASE_URL:
        print("❌ Erro: A variável de ambiente DATABASE_URL não foi definida.")
        sys.exit(1)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Erro de conexão com o Postgres: {e}")
        sys.exit(1)

def cleanup_node(conn, node_id):
    """Remove o nó de teste do banco de dados."""
    try:
        with conn.cursor() as cursor:
            query = sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(TARGET_TABLE))
            cursor.execute(query, (str(node_id),))
            conn.commit()
            print(f"\n🧹 Nó de teste {node_id} removido com sucesso.")
    except Exception as e:
        print(f"⚠️ Aviso: Falha ao remover o nó de teste {node_id}. Limpeza manual pode ser necessária. Erro: {e}")


def main():
    """Função principal que executa o teste de integração."""
    conn = get_db_connection()
    test_node_id = uuid.uuid4()
    
    print("--- INICIANDO TESTE DE INTEGRAÇÃO REAL (Python -> Go Worker) ---")
    print(f"🆔 ID do Nó de Teste: {test_node_id}")

    try:
        with conn.cursor() as cursor:
            print("\n1. Inserindo nó de teste com 'weight' crítico (2.0)...")
            # Insere um nó que deve ser pego imediatamente pelo worker, agora com todos os campos NOT NULL
            insert_query = sql.SQL("""
                INSERT INTO {} (id, name, subject, weight_in_exam, weight, difficulty, stability, reps, lapses, last_reviewed_at, next_review_at)
                VALUES (%s, %s, %s, %s, 2.0, 0.5, 10.0, 0, 0, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 minute')
            """).format(sql.Identifier(TARGET_TABLE))
            cursor.execute(insert_query, (str(test_node_id), 'Nó de Teste de Integração', 'Testes', 10.0))
            conn.commit()
            print("   -> Nó inserido com sucesso.")

        print("\n2. Monitorando o nó no banco de dados (Polling)...")
        print("   Aguardando o Go Worker processar a intervenção e resetar o peso para 1.0.")
        
        start_time = time.time()
        while time.time() - start_time < TIMEOUT_SECONDS:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                select_query = sql.SQL("SELECT weight FROM {} WHERE id = %s").format(sql.Identifier(TARGET_TABLE))
                cursor.execute(select_query, (str(test_node_id),))
                node = cursor.fetchone()

            if node and node['weight'] == 1.0:
                print("\n✅ SUCESSO! O peso do nó foi resetado para 1.0 pelo Go Worker.")
                elapsed_time = time.time() - start_time
                print(f"   -> Tempo decorrido: {elapsed_time:.2f} segundos.")
                cleanup_node(conn, test_node_id)
                conn.close()
                sys.exit(0)
            
            print(f"   ... peso atual: {node['weight'] if node else 'N/A'}. Aguardando...", end="\r")
            time.sleep(POLLING_INTERVAL_SECONDS)

        # Se o loop terminar, o teste falhou por timeout
        print("\n\n❌ FALHA: Timeout atingido!")
        print(f"   O peso do nó não foi alterado para 1.0 em {TIMEOUT_SECONDS} segundos.")
        cleanup_node(conn, test_node_id)
        conn.close()
        sys.exit(1)

    except (Exception, KeyboardInterrupt) as e:
        print(f"\n\n🚨 Um erro ocorreu durante o teste: {e}")
        cleanup_node(conn, test_node_id)
        conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
