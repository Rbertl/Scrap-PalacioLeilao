import json
import pickle
import os
import config

try:
    from sentence_transformers import SentenceTransformer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

def gerar_inteligencia():
    if not AI_AVAILABLE:
        print("❌ Erro: Biblioteca 'sentence-transformers' não instalada.")
        print("   Rode: pip install sentence-transformers")
        return

    if not os.path.exists(config.RAW_DATA_FILE):
        print("❌ Erro: Arquivo de dados brutos não encontrado.")
        print("   Rode a opção 1 (Scraper) primeiro.")
        return

    print("🧠 Carregando modelo de IA (isso pode demorar na primeira vez)...")
    model = SentenceTransformer(config.MODEL_NAME)

    print("📂 Lendo dados brutos...")
    with open(config.RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    textos_para_vetorizar = []
    dados_processados = []

    print(f"⚙️  Processando {len(dados)} itens...")
    
    for item in dados:
        # Criamos um texto rico para a IA entender
        # Juntamos Lote + Data + Descrição para a busca pegar qualquer coisa
        conteudo_vetor = f"Lote {item['lote']} Data {item['data']}. {item['texto_completo']}"
        textos_para_vetorizar.append(conteudo_vetor)
        dados_processados.append(item)

    print("🔢 Gerando Embeddings (Cálculos matemáticos)...")
    embeddings = model.encode(textos_para_vetorizar, convert_to_tensor=True, show_progress_bar=True)

    # Salvando os vetores (Embeddings)
    with open(config.EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(embeddings, f)
    
    # Salvando os dados correspondentes (para sabermos qual vetor é qual produto)
    with open(config.PROCESSED_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_processados, f, ensure_ascii=False, indent=4)

    print("✅ Processamento de IA concluído! Sistema pronto para buscas.")