import google.generativeai as genai
from config.settings import settings

if not settings.GEMINI_API_KEY:
    print("ERRO: GEMINI_API_KEY não configurada")
    exit(1)

genai.configure(api_key=settings.GEMINI_API_KEY)

print("\n=== MODELOS DISPONÍVEIS NO GEMINI ===\n")

try:
    for m in genai.list_models():
        # Verifica se suporta embeddings
        supports_embed = "embedContent" in [method for method in getattr(m, 'supported_generation_methods', [])]
        
        if supports_embed:
            print(f"✅ EMBEDDING: {m.name}")
        elif "gemini" in m.name.lower():
            print(f"📝 TEXTO: {m.name}")
            
except Exception as e:
    print(f"ERRO: {e}")
