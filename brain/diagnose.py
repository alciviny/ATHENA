import google.generativeai as genai
import os
import sys

print(f"--- DIAGNÓSTICO ATHENA ---")
print(f"Versão da biblioteca Python: {genai.__version__}")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERRO CRÍTICO: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
    sys.exit(1)

print(f"API Key detectada: {api_key[:5]}...{api_key[-3:]}")

genai.configure(api_key=api_key)

print("\n--- TENTANDO LISTAR MODELOS DISPONÍVEIS ---")
print("(Se sua chave estiver válida, você verá uma lista abaixo)")
try:
    found_flash = False
    found_embed = False
    for m in genai.list_models():
        print(f"✅ Modelo disponível: {m.name}")
        if "gemini-1.5-flash" in m.name:
            found_flash = True
        if "text-embedding-004" in m.name:
            found_embed = True
            
    if not found_flash:
        print("\n❌ ALERTA: 'gemini-1.5-flash' NÃO apareceu na lista. Sua conta não tem acesso a ele!")
    if not found_embed:
        print("\n❌ ALERTA: 'text-embedding-004' NÃO apareceu na lista.")

except Exception as e:
    print(f"\n💀 ERRO FATAL AO LISTAR MODELOS: {e}")
    print("Isso geralmente confirma que a API Key é inválida, o projeto foi suspenso ou a API Generative Language não está ativada no Google Cloud.")

print("\n--- FIM DO DIAGNÓSTICO ---")