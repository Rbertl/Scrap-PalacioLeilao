import sys
import os
import time

# Adiciona a pasta atual ao path para importação funcionar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules import scraper, ai_processor, searcher
from colorama import init, Fore, Back, Style

# Inicializa o colorama (necessário para Windows)
init(autoreset=True)

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    print(Fore.CYAN + Style.BRIGHT + "="*60)
    print(Fore.CYAN + Style.BRIGHT + "         🤖 LEILÃO INTELLIGENT SEARCH SYSTEM v2.2")
    print(Fore.CYAN + Style.BRIGHT + "         >>> Powered by Playwright & AI <<<")
    print(Fore.CYAN + Style.BRIGHT + "="*60 + "\n")

def menu_scraping():
    """Sub-menu para escolher o tipo de raspagem e disparar a IA em seguida"""
    print(Fore.YELLOW + "Escolha a categoria para raspar e atualizar a IA:")
    print("1. 🏗️  Materiais Genéricos (Móveis, Ferramentas, Sucata)")
    print("2. 🚗  Veículos")
    print("3. 🌎  Tudo (Misto)")
    print("0. 🔙  Voltar")
    
    op = input(Fore.GREEN + "Opção > " + Style.RESET_ALL)
    
    url_base = "https://www.palaciodosleiloes.com.br/site/index.php?categoria_pesquisa="
    target_url = None
    
    if op == '1':
        # Materiais
        target_url = url_base + "15%2C14%2C23"
    elif op == '2':
        # Veiculos
        target_url = url_base + "1"
    elif op == '3':
        # Tudo
        target_url = url_base + "1%2C15%2C14"
    elif op == '0':
        return
    else:
        print(Fore.RED + "Opção inválida!")
        return

    if target_url:
        # PASSO 1: Baixar dados do site
        scraper.executar_scraping(target_url)
        
        # PASSO 2: Atualizar a Inteligência Artificial automaticamente
        print(Fore.MAGENTA + "\n🧠 Iniciando processamento automático da Inteligência Artificial..." + Style.RESET_ALL)
        ai_processor.gerar_inteligencia()
        print(Fore.GREEN + "✅ Ciclo completo (Download + IA) finalizado com sucesso!" + Style.RESET_ALL)

def menu_principal():
    while True:
        limpar_tela()
        print_logo()
        
        print(Fore.WHITE + "1. " + Fore.GREEN + "📥 Atualizar Tudo (Scraping do Site + Processar IA)")
        print(Fore.WHITE + "2. " + Fore.MAGENTA + "🧠 Reprocessar Apenas IA (Sem acessar o site)")
        print(Fore.WHITE + "3. " + Fore.CYAN + "🔎 Pesquisar Item (Busca Híbrida)")
        print(Fore.WHITE + "4. " + Fore.RED + "🚪 Sair")
        print("-" * 60)
        
        opcao = input(Fore.YELLOW + "Escolha uma ação: " + Style.RESET_ALL)

        if opcao == '1':
            menu_scraping()
            input(Fore.BLUE + "\nPressione Enter para voltar ao menu...")
        
        elif opcao == '2':
            # Opção mantida para caso você mude a lógica da IA e queira testar sem baixar tudo de novo
            print(Fore.MAGENTA + "Reprocessando dados locais..." + Style.RESET_ALL)
            ai_processor.gerar_inteligencia()
            input(Fore.BLUE + "\nPressione Enter para voltar ao menu...")
        
        elif opcao == '3':
            termo = input(Fore.CYAN + "\nDigite o que procura (ex: 'Furadeira', 'Mesa'): " + Style.RESET_ALL)
            searcher.realizar_busca(termo)
            input(Fore.BLUE + "\nPressione Enter para voltar ao menu...")
        
        elif opcao == '4':
            print(Fore.RED + "Encerrando sistema... Até logo!")
            break
        else:
            print(Fore.RED + "❌ Opção inválida!")
            time.sleep(1)

if __name__ == "__main__":
    # Verificação básica de libs
    try:
        import playwright
        import sentence_transformers
        menu_principal()
    except ImportError as e:
        print(Fore.RED + "❌ Erro de Dependências!")
        print(f"Falta instalar: {e.name}")
        print("Rode: pip install playwright sentence-transformers torch colorama")