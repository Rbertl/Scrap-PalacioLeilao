import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules import scraper, ai_processor
from colorama import init, Fore, Style

init(autoreset=True)

def main():
    print(Fore.CYAN + "="*60)
    print("🤖 INICIANDO AUTOMAÇÃO DE NUVEM - PALÁCIO DOS LEILÕES")
    print(Fore.CYAN + "="*60)

    # URL que pega TUDO (Veículos + Materiais + Diversos)
    # Códigos: 1 (Veículos), 15 (Móveis/Eletro), 14 (Sucata/Materiais), 23 (Outros)
    url_completa = "https://www.palaciodosleiloes.com.br/site/index.php?categoria_pesquisa=1%2C15%2C14%2C23"

    try:
        # PASSO 1: Scraping
        print(Fore.YELLOW + "\n>>> Passo 1: Iniciando Scraping do Site...")
        scraper.executar_scraping(url_completa)

        # PASSO 2: Inteligência Artificial
        print(Fore.MAGENTA + "\n>>> Passo 2: Processando Inteligência Artificial...")
        ai_processor.gerar_inteligencia()

        print(Fore.GREEN + "\n✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    
    except Exception as e:
        print(Fore.RED + f"\n❌ ERRO FATAL NA AUTOMAÇÃO: {e}")
        sys.exit(1) # Código de erro para avisar o GitHub que falhou

if __name__ == "__main__":
    main()