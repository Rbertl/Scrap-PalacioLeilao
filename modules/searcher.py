import json
import pickle
import os
import unicodedata
import re
import csv
import time
from datetime import datetime
import config
from colorama import Fore, Style

try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# --- OTIMIZAÇÃO DE VELOCIDADE: CACHE GLOBAL ---
# Mantém o modelo na memória RAM para não recarregar a cada busca
MODELO_CACHE = None

def get_model():
    """Carrega o modelo apenas se ainda não estiver na memória."""
    global MODELO_CACHE
    if not AI_AVAILABLE:
        return None
        
    if MODELO_CACHE is None:
        print(Fore.YELLOW + "🧠 Carregando modelo de IA pela primeira vez (isso acontece só uma vez)..." + Style.RESET_ALL)
        MODELO_CACHE = SentenceTransformer(config.MODEL_NAME)
    return MODELO_CACHE

def normalizar_texto(texto):
    """
    Remove acentos, coloca em minúsculas e TROCA PONTUAÇÃO POR ESPAÇO.
    """
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acentos = u"".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    texto_limpo = re.sub(r'[^a-z0-9]', ' ', sem_acentos)
    return " ".join(texto_limpo.split())

def exportar_para_csv(resultados, termo):
    """Gera um arquivo CSV compatível com Excel."""
    if not resultados:
        print("Nada para exportar.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    termo_limpo = re.sub(r'[^a-zA-Z0-9]', '_', termo)
    nome_arquivo = f"resultado_{termo_limpo}_{timestamp}.csv"
    caminho_arquivo = os.path.join(config.DATA_DIR, nome_arquivo)

    try:
        # encoding='utf-8-sig' é essencial para o Excel ler acentos corretamente
        with open(caminho_arquivo, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';') # Ponto e vírgula é o padrão Excel Brasil
            
            # Cabeçalho
            writer.writerow(['Relevância', 'Tipo Match', 'Lote', 'Data', 'Local', 'Descrição', 'Link'])
            
            for item in resultados:
                writer.writerow([
                    f"{item['score']:.2f}",
                    item['tipo_match'],
                    item['lote'],
                    item['data'],
                    item['local'],
                    item['texto_completo'],
                    item['url']
                ])
        
        print(Fore.GREEN + f"\n✅ Relatório salvo com sucesso em: {caminho_arquivo}")
        print(f"   (Abra com o Excel)")
    except Exception as e:
        print(Fore.RED + f"Erro ao salvar arquivo: {e}")

def realizar_busca(termo):
    if not AI_AVAILABLE:
        print(Fore.RED + "❌ Biblioteca de IA faltando (sentence-transformers)." + Style.RESET_ALL)
        return

    if not os.path.exists(config.EMBEDDINGS_FILE) or not os.path.exists(config.PROCESSED_DATA_FILE):
        print(Fore.RED + "❌ Dados de inteligência não encontrados. Rode a opção 2 (Processar) primeiro." + Style.RESET_ALL)
        return

    # Usa o Cache para velocidade instantânea nas buscas subsequentes
    model = get_model()
    
    with open(config.EMBEDDINGS_FILE, 'rb') as f:
        embeddings_banco = pickle.load(f)
    
    with open(config.PROCESSED_DATA_FILE, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # --- ESTRATÉGIA 1: BUSCA SEMÂNTICA (IA) ---
    query_embedding = model.encode(termo, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings_banco, top_k=50)[0]
    
    resultados_combinados = {}
    for hit in hits:
        idx = hit['corpus_id']
        resultados_combinados[idx] = hit['score']

    # --- ESTRATÉGIA 2: BUSCA TEXTUAL INTELIGENTE ---
    termo_norm = normalizar_texto(termo)
    palavras_busca = termo_norm.split() 
    itens_com_match_textual = set()
    
    print(Fore.CYAN + "🔍 Cruzando dados (IA + Texto)..." + Style.RESET_ALL)
    
    for idx, item in enumerate(dados):
        texto_item = normalizar_texto(item['texto_completo'])
        palavras_item_set = set(texto_item.split())
        bonus_texto = 0.0
        
        # 1. Match Exato
        if termo_norm in texto_item:
            bonus_texto += 0.4
            
        # 2. Match Palavra/Raiz
        matches_palavras = 0
        for palavra in palavras_busca:
            match_encontrado = False
            if len(palavra) < 4:
                if palavra in palavras_item_set: match_encontrado = True
            else:
                if palavra in texto_item:
                    match_encontrado = True
                else:
                    # Stemming simples (raízes)
                    raiz = palavra.rstrip('s')
                    if raiz.endswith(('o', 'a', 'e')): raiz = raiz[:-1]
                    if len(raiz) >= 3 and raiz in palavras_item_set:
                        match_encontrado = True

            if match_encontrado: matches_palavras += 1
        
        if matches_palavras > 0:
            fator_match = matches_palavras / len(palavras_busca)
            bonus_texto += (fator_match * 0.3)
            itens_com_match_textual.add(idx)

        if bonus_texto > 0:
            score_atual = resultados_combinados.get(idx, 0.0)
            resultados_combinados[idx] = score_atual + bonus_texto

    # --- ORDENAÇÃO E EXIBIÇÃO ---
    ranking_final = sorted(resultados_combinados.items(), key=lambda x: x[1], reverse=True)
    
    lista_exportacao = [] # Lista para guardar dados para o Excel
    encontrou = False
    
    print(f"\n🔎 Resultados para: '{termo}'\n" + "="*60)
    
    contador = 0
    for idx, score in ranking_final:
        limite_minimo = 0.10 if idx in itens_com_match_textual else 0.35
        
        if score > limite_minimo: 
            item = dados[idx]
            encontrou = True
            contador += 1
            if contador > 20: break # Limite de exibição no terminal
            
            desc_curta = item['texto_completo'][:150].replace('\n', ' ') + "..."
            
            tipo_match = "Conceito IA"
            if idx in itens_com_match_textual:
                cor_score = Fore.GREEN
                tipo_match = "Texto + IA"
            else:
                cor_score = Fore.MAGENTA
            
            print(f"{cor_score}#{contador} [Score: {score:.2f}] ({tipo_match}) {Style.RESET_ALL}Lote: {item['lote']}")
            print(f"   📝 {desc_curta}")
            print(f"   🔗 {item['url']}")
            print(Fore.CYAN + "-" * 60 + Style.RESET_ALL)
            
            # Prepara objeto para exportação
            item_export = item.copy()
            item_export['score'] = score
            item_export['tipo_match'] = tipo_match
            lista_exportacao.append(item_export)
    
    if not encontrou:
        print(Fore.RED + "😕 Nenhum item relevante encontrado." + Style.RESET_ALL)
    elif lista_exportacao:
        # Pergunta se quer exportar
        print(f"\nForam encontrados {len(lista_exportacao)} itens relevantes.")
        opt = input(Fore.YELLOW + "Deseja exportar estes resultados para Excel (CSV)? [S/N]: " + Style.RESET_ALL).upper()
        if opt == 'S':
            exportar_para_csv(lista_exportacao, termo)