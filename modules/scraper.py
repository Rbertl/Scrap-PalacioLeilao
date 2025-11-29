import json
import re
import time
import random
from playwright.sync_api import sync_playwright
from colorama import Fore, Style
import config


def limpar_texto(texto):
    if not texto:
        return ""
    return " ".join(texto.split())


def fechar_popups_e_cookies(page):
    """
    Força o fechamento de modais e cookies via JavaScript.
    Agora mais agressivo para pegar modais que aparecem com delay.
    """
    # Pequeno delay para garantir que animações de entrada do modal iniciaram
    try:
        page.wait_for_timeout(500)

        # Executa JS no navegador para destruir os elementos
        page.evaluate("""
            () => {
                const removeEl = (el) => {
                    if (el) {
                        el.style.setProperty('display', 'none', 'important');
                        el.style.setProperty('visibility', 'hidden', 'important');
                        el.remove();
                    }
                };

                // 1. Banner de Cookies
                removeEl(document.querySelector('.rodape_cookies'));
                
                // 2. Modal de Aviso Específico (#modalAviso)
                const modal = document.getElementById('modalAviso');
                if (modal) {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    removeEl(modal);
                }

                // 3. Limpeza Genérica (Remove qualquer fundo escuro 'backdrop')
                document.querySelectorAll('.modal-backdrop').forEach(el => removeEl(el));
                document.querySelectorAll('.modal.show').forEach(el => removeEl(el));
                
                // 4. Destrava o scroll do corpo da página
                document.body.classList.remove('modal-open');
                document.body.style.paddingRight = '';
                document.body.style.overflow = 'auto';
            }
        """)
    except Exception as e:
        # Não falha o script se der erro ao fechar popup, apenas segue
        pass


def extrair_metadados_tabela(page):
    """
    Analisa a tabela HTML específica do Palácio dos Leilões 
    para extrair Lote, Data e Local de forma precisa.
    """
    dados = {"lote": "N/A", "data": "N/A", "local": "N/A"}

    try:
        # OTIMIZAÇÃO: Espera a tabela aparecer antes de ler
        try:
            page.wait_for_selector("table.table-sm", timeout=5000)
        except:
            pass  # Se não aparecer em 5s, tenta ler o que tiver

        # Seleciona todas as linhas da tabela de informações
        linhas = page.locator("table.table-sm tr").all()

        for linha in linhas:
            colunas = linha.locator("td").all_inner_texts()

            if len(colunas) >= 2:
                chave = colunas[0].strip().lower()
                valor = colunas[1].strip()

                if "lote" == chave:
                    dados["lote"] = valor
                elif "leilão e data" in chave:
                    dados["data"] = valor
                elif "local" in chave:
                    dados["local"] = valor

    except Exception as e:
        print(Fore.RED + f"   ⚠️ Erro ao ler tabela: {e}" + Style.RESET_ALL)

    return dados


def executar_scraping(target_url=config.URL_ALVO):
    print(Fore.CYAN + f"\n🚀 Iniciando Scraper..." + Style.RESET_ALL)
    print(f"Alvo: {target_url}")

    dados_coletados = []

    with sync_playwright() as p:
        print(Fore.WHITE + "   Iniciando navegador (pode levar alguns segundos)..." + Style.RESET_ALL)

        # --- DEFININDO USER-AGENT REAL (Anti-bloqueio) ---
        # Simula um navegador Chrome real no Windows 10
        user_agent_real = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        browser = p.chromium.launch(headless=True)

        # Injetamos o User-Agent aqui
        context = browser.new_context(user_agent=user_agent_real)
        page = context.new_page()

        try:
            print("   Carregando listagem principal...")
            page.goto(target_url, timeout=60000)

            # --- LIMPEZA INICIAL ---
            print(Fore.YELLOW + "   🧹 Varrendo bloqueios visuais..." + Style.RESET_ALL)
            fechar_popups_e_cookies(page)

            # --- ESPERA PELO CONTAINER PRINCIPAL ---
            try:
                page.wait_for_selector(
                    "#div_lotes", state="visible", timeout=15000)
            except:
                print(
                    Fore.RED + "❌ Erro: Container '#div_lotes' não encontrado ou demorou demais." + Style.RESET_ALL)
                return

            container_lotes = page.locator("#div_lotes")

            # --- BOTÃO EXIBIR TODOS (Com Lógica de Força Bruta) ---
            try:
                botao_exibir = container_lotes.locator(".btn_exibir_todos")

                # Verifica se o botão existe antes de tentar qualquer coisa
                if botao_exibir.count() > 0 and botao_exibir.is_visible():
                    print(
                        Fore.YELLOW + "   Botão 'Exibir todos' detectado. Clicando..." + Style.RESET_ALL)

                    try:
                        # Tenta clique normal primeiro
                        botao_exibir.click(timeout=3000)
                    except Exception:
                        print(
                            Fore.RED + "   ⚠️ Clique bloqueado por modal. Tentando força bruta..." + Style.RESET_ALL)
                        # Se falhar (modal na frente), roda limpeza de novo e força o clique
                        fechar_popups_e_cookies(page)
                        botao_exibir.click(force=True, timeout=5000)

                    print("   ✅ Clique realizado. Aguardando carregamento dos itens...")
                    # Tempo de espera para a lista carregar
                    page.wait_for_timeout(5000)
                else:
                    print("   Lista parece completa ou botão não visível.")
            except Exception as e:
                print(
                    Fore.YELLOW + f"   Nota: Botão 'Exibir todos' ignorado: {e}" + Style.RESET_ALL)

            # --- COLETA DE LINKS ---
            print("   Mapeando itens dentro de '#div_lotes'...")
            urls_unicas = set()

            # Busca cards apenas dentro da área de resultados
            cards = container_lotes.locator("div.col-md-3").all()

            print(
                Fore.BLUE + f"   Cards encontrados na área correta: {len(cards)}" + Style.RESET_ALL)

            for card in cards:
                # Busca elementos clicáveis dentro do card
                elementos_clicaveis = card.locator(
                    "[onclick*='exibir_lote']").all()

                for el in elementos_clicaveis:
                    onclick_text = el.get_attribute("onclick")
                    # Extrai ID: exibir_lote(1466396,8135) -> Pega 1466396
                    match = re.search(r'exibir_lote\(\s*(\d+)', onclick_text)
                    if match:
                        urls_unicas.add(
                            f"https://www.palaciodosleiloes.com.br/site/lotem.php?cl={match.group(1)}")

            lista_urls = list(urls_unicas)

            if config.LIMIT_SCRAP:
                print(
                    Fore.YELLOW + f"⚠️  Modo Teste: Limitando a {config.LIMIT_SCRAP} itens." + Style.RESET_ALL)
                lista_urls = lista_urls[:config.LIMIT_SCRAP]

            print(
                Fore.GREEN + f"📦 Encontrados {len(lista_urls)} lotes VÁLIDOS para analisar." + Style.RESET_ALL)

            # --- PROCESSAMENTO INDIVIDUAL ---
            for i, url in enumerate(lista_urls):
                print(f"[{i+1}/{len(lista_urls)}] Acessando lote...", end="\r")

                # --- PAUSA ALEATÓRIA (Anti-bloqueio) ---
                # Essencial para não ser detectado como robô pelo servidor
                # Espera entre 2 e 5 segundos
                tempo_espera = random.uniform(2, 5)
                time.sleep(tempo_espera)

                try:
                    # Aumentei o timeout geral da página
                    page.goto(url, timeout=60000)

                    # OTIMIZAÇÃO: Espera a rede acalmar (garante que AJAX carregou)
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except:
                        # Se networkidle falhar (timeout), segue o jogo
                        pass

                    meta = extrair_metadados_tabela(page)

                    seletor_desc = "div.bg-cinza-claro"
                    texto_desc = ""

                    # OTIMIZAÇÃO: Espera explícita pelo elemento de descrição
                    try:
                        # Aguarda até 5 segundos para o elemento aparecer no DOM
                        page.wait_for_selector(
                            seletor_desc, state="visible", timeout=5000)
                    except:
                        pass

                    if page.locator(seletor_desc).count() > 0:
                        texto_desc = page.locator(
                            seletor_desc).first.inner_text()
                    else:
                        texto_desc = "Descrição não localizada (Elemento não carregou ou não existe)."

                    item = {
                        "url": url,
                        "lote": meta['lote'],
                        "data": meta['data'],
                        "local": meta['local'],
                        "texto_completo": limpar_texto(texto_desc),
                        "texto_bruto_com_quebras": texto_desc
                    }

                    dados_coletados.append(item)

                    # Feedback visual
                    resumo = item['texto_completo'][:40] + "..." if len(
                        item['texto_completo']) > 40 else item['texto_completo']
                    print(Fore.GREEN +
                          f"   ✅ [{meta['lote']}] {resumo}" + Style.RESET_ALL)

                except Exception as e:
                    print(
                        Fore.RED + f"   ❌ Falha na URL {url}: {e}" + Style.RESET_ALL)

        except Exception as e:
            print(
                Fore.RED + f"Erro crítico na navegação: {e}" + Style.RESET_ALL)
        finally:
            browser.close()

    if dados_coletados:
        with open(config.RAW_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados_coletados, f, ensure_ascii=False, indent=4)
        print(
            Fore.CYAN + f"\n✨ Concluído! {len(dados_coletados)} itens salvos em '{config.RAW_DATA_FILE}'" + Style.RESET_ALL)
    else:
        print(Fore.RED + "\nNenhum dado foi coletado." + Style.RESET_ALL)
