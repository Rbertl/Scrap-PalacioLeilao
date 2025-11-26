import os

# Caminhos de Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Garante que a pasta data existe
os.makedirs(DATA_DIR, exist_ok=True)

# Caminhos de Arquivos
RAW_DATA_FILE = os.path.join(DATA_DIR, 'dados_brutos.json')
EMBEDDINGS_FILE = os.path.join(DATA_DIR, 'embeddings.pkl')
PROCESSED_DATA_FILE = os.path.join(DATA_DIR, 'dados_processados.json')

# Configurações do Scraper
URL_ALVO = "https://www.palaciodosleiloes.com.br/site/"
LIMIT_SCRAP = None  # Limite de itens para teste (coloque 0 ou None para rodar tudo)

# Configurações da IA
MODEL_NAME = 'all-MiniLM-L6-v2' # Modelo leve e eficiente para PT-BR/Inglês