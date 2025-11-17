#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo Web Downloader
Automatiza o download de arquivos do Google Drive através dos links encontrados nos Google Sites
Suporte a multiprocessamento para acelerar o processo
"""

import requests
import time
import os
import re
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
import urllib.parse
import multiprocessing
from multiprocessing import Pool, Queue, Manager
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import sys

# Suprimir logs do Selenium e bibliotecas relacionadas
logging.getLogger('selenium').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('webdriver_manager').setLevel(logging.ERROR)
logging.getLogger('WDM').setLevel(logging.ERROR)

# Suprimir warnings do multiprocessing no Windows
if sys.platform == 'win32':
    multiprocessing.set_start_method('spawn', force=True)

def worker_banco_independente(args):
    """Função worker independente para multiprocessamento (fora da classe)"""
    banco_info, pasta_downloads = args
    
    # Suprimir logs completamente
    import os
    import sys
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    
    # Redirecionar stderr
    original_stderr = sys.stderr
    devnull = open(os.devnull, 'w')
    sys.stderr = devnull
    
    # Suprimir todos os logs
    for logger_name in ['selenium', 'urllib3', 'webdriver_manager', 'WDM']:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        logging.getLogger(logger_name).disabled = True
    
    driver_local = None
    arquivos_baixados = 0
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        
        # Configurar Chrome headless com máxima supressão
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-gcm-support")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Configurações de download
        if pasta_downloads:
            prefs = {
                "download.default_directory": pasta_downloads,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)
        
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        
        # Inicializar driver com service silencioso
        try:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                if 'chromedriver-win32' in driver_path and not driver_path.endswith('.exe'):
                    driver_path = os.path.join(os.path.dirname(driver_path), 'chromedriver-win32', 'chromedriver.exe')
                
                service_args = ['--log-level=OFF', '--silent']
                service = Service(driver_path, service_args=service_args)
                
                if sys.platform == 'win32':
                    import subprocess
                    service.creation_flags = subprocess.CREATE_NO_WINDOW
                
                driver_local = webdriver.Chrome(service=service, options=chrome_options)
            except:
                driver_local = webdriver.Chrome(options=chrome_options)
        except:
            driver_local = webdriver.Chrome(options=chrome_options)
        
        driver_local.implicitly_wait(5)
        
        # Processar banco com download imediato
        print(f"[Worker] {banco_info['nome']}")
        
        # Navegar para a página do banco
        driver_local.get(banco_info['url'])
        time.sleep(2)
        
        # Encontrar e processar cada Drive imediatamente
        links_drive = []
        try:
            links = driver_local.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and "drive.google.com" in href:
                    links_drive.append(href)
            
            # Remover duplicatas
            links_drive = list(set(links_drive))
        except:
            pass
        
        print(f"[Worker] {banco_info['nome']}: {len(links_drive)} drives")
        
        # BAIXAR IMEDIATAMENTE cada Drive encontrado
        for i, link_drive in enumerate(links_drive[:3], 1):  # Limitar a 3 drives por banco
            try:
                print(f"[Worker] {banco_info['nome']} - Drive {i}/{min(len(links_drive), 3)}")
                
                # Navegar para o Drive
                driver_local.get(link_drive)
                time.sleep(2)
                
                # Estratégias de download imediato
                arquivos_drive = 0
                
                try:
                    # Estratégia 1: Links diretos de download
                    elementos = driver_local.find_elements(By.CSS_SELECTOR, "a[download]")
                    if not elementos:
                        # Estratégia 2: Elementos com tooltip de download
                        elementos = driver_local.find_elements(By.CSS_SELECTOR, "[title*='Download'], [data-tooltip*='Download']")
                    if not elementos:
                        # Estratégia 3: Botões de download
                        elementos = driver_local.find_elements(By.CSS_SELECTOR, "button[aria-label*='Download']")
                    if not elementos:
                        # Estratégia 4: Buscar por texto de arquivo
                        elementos = driver_local.find_elements(By.XPATH, "//div[contains(text(),'.pdf') or contains(text(),'.doc') or contains(text(),'.xls')]")
                    
                    # Tentar baixar arquivos encontrados
                    for elemento in elementos[:2]:  # Máximo 2 arquivos por drive
                        try:
                            # Verificar se é um arquivo válido
                            texto = elemento.text.lower() if elemento.text else ""
                            if any(ext in texto for ext in ['.pdf', '.doc', '.xls', '.csv', 'download']) or elemento.tag_name == 'a':
                                driver_local.execute_script("arguments[0].click();", elemento)
                                time.sleep(1)
                                arquivos_baixados += 1
                                arquivos_drive += 1
                                print(f"[Worker] {banco_info['nome']} - Arquivo {arquivos_drive} baixado")
                        except:
                            continue
                    
                    if arquivos_drive == 0:
                        print(f"[Worker] {banco_info['nome']} - Drive {i}: Nenhum arquivo encontrado")
                    
                except Exception as e_estrategia:
                    print(f"[Worker] {banco_info['nome']} - Drive {i}: Erro na estratégia")
                    continue
                    
            except Exception as e_drive:
                print(f"[Worker] {banco_info['nome']} - Drive {i}: Erro no acesso")
                continue
        
        return {
            'banco': banco_info['nome'],
            'arquivos_baixados': arquivos_baixados,
            'links_drive': len(links_drive),
            'sucesso': True
        }
        
    except Exception as e:
        return {
            'banco': banco_info['nome'],
            'arquivos_baixados': 0,
            'links_drive': 0,
            'erro': str(e)[:50],
            'sucesso': False
        }
        
    finally:
        # Restaurar stderr
        sys.stderr = original_stderr
        devnull.close()
        
        if driver_local:
            try:
                driver_local.quit()
            except:
                pass

class WebDownloader:
    def __init__(self):
        self.console = Console()
        self.site_base = "https://sites.google.com/view/capitaldoisconhecimento/p%C3%A1gina-inicial/conv%C3%AAnios"
        self.pasta_downloads = ""
        self.driver = None
        self.num_processos = min(4, multiprocessing.cpu_count())
        self.max_threads_por_processo = 2
        self._suprimir_logs_chrome()

    def _suprimir_logs_chrome(self):
        """Suprimir todos os logs do Chrome e bibliotecas relacionadas"""
        import warnings
        warnings.filterwarnings("ignore")
        
        # Configurar logging para suprimir mensagens
        loggers_to_suppress = [
            'selenium', 'urllib3', 'webdriver_manager', 'WDM',
            'selenium.webdriver.remote.remote_connection',
            'selenium.webdriver.chrome.service',
            'selenium.webdriver.chrome.options'
        ]
        
        for logger_name in loggers_to_suppress:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).disabled = True

    def menu_downloader(self):
        """Menu principal de opções do web downloader"""
        return inquirer.select(
            message="Selecione uma opção:",
            choices=[
                Choice("1", name="Download Sequencial Inteligente (Baixa imediatamente cada Drive)"),
                Choice("2", name="Download Multiprocessamento (Paralelo - RÁPIDO)"),
                Choice("3", name="Download de Link Específico (Informe URL do Google Sites)"),
                Choice("4", name="Navegar e baixar arquivos específicos"),
                Choice("5", name="Configurar pasta de downloads"),
                Choice("6", name="Configurar número de processos paralelos"),
                Choice("7", name="Voltar ao menu principal"),
            ],
        ).execute()

    def configurar_pasta_downloads(self):
        """Permite configurar a pasta onde os arquivos serão baixados"""
        pasta = inquirer.filepath(
            message="Selecione a pasta onde os arquivos serão salvos:",
            only_directories=True,
            filter=lambda x: x.strip(),
        ).execute()
        
        if pasta and pasta.strip():
            self.pasta_downloads = pasta.strip()
            self.console.print(Panel(
                f"[green]Pasta de downloads configurada:[/green]\n{self.pasta_downloads}",
                title="Configuração",
                border_style="green"
            ))
        else:
            # Se usuário cancelou ou não informou, usar pasta padrão CURTA
            pasta_padrao = "C:\\Downloads\\Drive"
            os.makedirs(pasta_padrao, exist_ok=True)
            self.pasta_downloads = pasta_padrao
            self.console.print(Panel(
                f"[yellow]Pasta padrão configurada (caminho curto):[/yellow]\n{self.pasta_downloads}\n\n"
                f"[blue]💡 Dica:[/blue] Caminhos curtos evitam o limite de 260 caracteres do Windows",
                title="Configuração Padrão",
                border_style="yellow"
            ))
        
        return self.pasta_downloads

    def configurar_processos(self):
        """Permite configurar o número de processos paralelos"""
        cpu_count = multiprocessing.cpu_count()
        
        self.console.print(Panel(
            f"[cyan]Configuração de Multiprocessamento[/cyan]\n\n"
            f"CPU Cores disponíveis: {cpu_count}\n"
            f"Processos atuais: {self.num_processos}\n"
            f"Threads por processo: {self.max_threads_por_processo}\n\n"
            f"[yellow]Recomendações:[/yellow]\n"
            f"• Para máxima velocidade: {min(cpu_count, 6)} processos\n"
            f"• Para uso equilibrado: {min(cpu_count//2, 4)} processos\n"
            f"• Para uso leve: 2 processos",
            title="Multiprocessamento",
            border_style="cyan"
        ))
        
        novo_num = inquirer.number(
            message=f"Número de processos paralelos (1-{min(cpu_count, 8)}):",
            min_allowed=1,
            max_allowed=min(cpu_count, 8),
            default=self.num_processos
        ).execute()
        
        if novo_num:
            self.num_processos = int(novo_num)
            
        nova_threads = inquirer.number(
            message="Threads por processo (1-4):",
            min_allowed=1,
            max_allowed=4,
            default=self.max_threads_por_processo
        ).execute()
        
        if nova_threads:
            self.max_threads_por_processo = int(nova_threads)
        
        self.console.print(Panel(
            f"[green]Configuração atualizada![/green]\n\n"
            f"Processos: {self.num_processos}\n"
            f"Threads por processo: {self.max_threads_por_processo}\n"
            f"Total de workers: {self.num_processos * self.max_threads_por_processo}",
            title="Configuração Salva",
            border_style="green"
        ))

    def inicializar_driver(self):
        """Inicializa o driver do Chrome com configurações otimizadas"""
        chrome_options = Options()
        
        # Configurações básicas de segurança
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Desabilitar recursos que causam erros de logging
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-breakpad")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-domain-reliability")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-permissions-api")
        chrome_options.add_argument("--disable-web-resources")
        chrome_options.add_argument("--disable-gcm-support")
        chrome_options.add_argument("--disable-background-mode")
        chrome_options.add_argument("--disable-add-to-shelf")
        chrome_options.add_argument("--disable-print-preview")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--password-store=basic")
        chrome_options.add_argument("--use-mock-keychain")
        
        # Configurações de download
        if self.pasta_downloads:
            prefs = {
                "download.default_directory": self.pasta_downloads,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
        
        # Desabilitar extensões e automação
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        
        # Tentar múltiplas estratégias de inicialização
        estrategias = [
            self._inicializar_com_webdriver_manager,
            self._inicializar_com_chrome_simples,
            self._inicializar_com_chrome_basico
        ]
        
        for i, estrategia in enumerate(estrategias, 1):
            try:
                self.console.print(f"[cyan]Tentativa {i}: {estrategia.__name__}[/cyan]")
                self.driver = estrategia(chrome_options)
                
                if self.driver:
                    self.driver.implicitly_wait(10)
                    
                    # Executar script completo anti-detecção
                    try:
                        self.driver.execute_script("""
                            // Remover propriedades de automação
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined,
                            });
                            
                            // Mascarar plugins
                            Object.defineProperty(navigator, 'plugins', {
                                get: () => [1, 2, 3, 4, 5],
                            });
                            
                            // Mascarar languages
                            Object.defineProperty(navigator, 'languages', {
                                get: () => ['pt-BR', 'pt', 'en'],
                            });
                            
                            // Remover chrome.runtime se existir
                            if (window.chrome && window.chrome.runtime) {
                                delete window.chrome.runtime;
                            }
                            
                            // Adicionar propriedades de navegador real
                            Object.defineProperty(navigator, 'permissions', {
                                get: () => ({
                                    query: () => Promise.resolve({ state: 'granted' }),
                                }),
                            });
                            
                            // Mascarar user agent
                            Object.defineProperty(navigator, 'userAgent', {
                                get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            });
                        """)
                        self.console.print("[green]✓ Driver Chrome inicializado com STEALTH MODE![/green]")
                    except Exception as e:
                        self.console.print(f"[yellow]Aviso: Script anti-detecção falhou: {str(e)[:50]}[/yellow]")
                        self.console.print("[green]✓ Driver Chrome inicializado![/green]")
                    
                    return True
                    
            except Exception as e:
                self.console.print(f"[yellow]Tentativa {i} falhou: {str(e)[:100]}[/yellow]")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                continue
        
        # Se chegou aqui, todas as estratégias falharam
        self.console.print(Panel(
            f"[red]Erro ao inicializar o Chrome:[/red]\n\n"
            f"Todas as estratégias de inicialização falharam.\n\n"
            f"[yellow]Certifique-se de que:[/yellow]\n"
            f"• O Chrome está instalado\n"
            f"• O ChromeDriver está no PATH\n"
            f"• Todas as dependências estão instaladas\n\n"
            f"[cyan]Para instalar as dependências:[/cyan]\n"
            f"pip install selenium beautifulsoup4 requests webdriver-manager",
            title="Erro de Inicialização",
            border_style="red"
        ))
        return False

    def _inicializar_com_webdriver_manager(self, chrome_options):
        """Estratégia 1: Usar WebDriverManager"""
        if not ChromeDriverManager:
            raise Exception("WebDriverManager não disponível")
            
        driver_path = ChromeDriverManager().install()
        
        # Corrigir caminho do ChromeDriver se necessário
        if 'chromedriver-win32' in driver_path and not driver_path.endswith('.exe'):
            driver_path = os.path.join(os.path.dirname(driver_path), 'chromedriver-win32', 'chromedriver.exe')
        
        if not os.path.exists(driver_path):
            # Procurar pelo executável na pasta
            pasta_driver = os.path.dirname(driver_path)
            for arquivo in os.listdir(pasta_driver):
                if arquivo.endswith('.exe') and 'chromedriver' in arquivo:
                    driver_path = os.path.join(pasta_driver, arquivo)
                    break
        
        service = Service(driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    def _inicializar_com_chrome_simples(self, chrome_options):
        """Estratégia 2: Usar Chrome simples (assumindo que está no PATH)"""
        return webdriver.Chrome(options=chrome_options)

    def _inicializar_com_chrome_basico(self, chrome_options):
        """Estratégia 3: Chrome com configurações mínimas"""
        options_basicas = Options()
        options_basicas.add_argument("--no-sandbox")
        options_basicas.add_argument("--disable-dev-shm-usage")
        options_basicas.add_argument("--disable-gpu")
        
        if self.pasta_downloads:
            prefs = {
                "download.default_directory": self.pasta_downloads,
                "download.prompt_for_download": False
            }
            options_basicas.add_experimental_option("prefs", prefs)
        
        return webdriver.Chrome(options=options_basicas)

    def processar_banco_worker(self, args):
        """Worker para processar um banco específico em multiprocessamento"""
        banco_info, pasta_downloads = args
        
        # Suprimir logs localmente no worker
        import os
        import sys
        import logging
        
        # Redirecionar stderr para suprimir logs do Chrome
        original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        # Suprimir logs do Selenium
        logging.getLogger('selenium').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        logging.getLogger('webdriver_manager').setLevel(logging.CRITICAL)
        
        driver_local = None
        arquivos_baixados = 0
        
        try:
            # Configurar Chrome para este worker com máxima supressão
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-breakpad")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-permissions-api")
            chrome_options.add_argument("--disable-web-resources")
            chrome_options.add_argument("--disable-gcm-support")
            chrome_options.add_argument("--disable-background-mode")
            chrome_options.add_argument("--disable-add-to-shelf")
            chrome_options.add_argument("--disable-print-preview")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--password-store=basic")
            chrome_options.add_argument("--use-mock-keychain")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Configurações de download
            if pasta_downloads:
                prefs = {
                    "download.default_directory": pasta_downloads,
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": False,
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.default_content_settings.popups": 0,
                    "profile.managed_default_content_settings.images": 2
                }
                chrome_options.add_experimental_option("prefs", prefs)
            
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            
            # Inicializar driver local com service silencioso
            try:
                if ChromeDriverManager:
                    driver_path = ChromeDriverManager().install()
                    if 'chromedriver-win32' in driver_path and not driver_path.endswith('.exe'):
                        driver_path = os.path.join(os.path.dirname(driver_path), 'chromedriver-win32', 'chromedriver.exe')
                    
                    service_args = ['--log-level=OFF', '--silent']
                    service = Service(driver_path, service_args=service_args)
                    
                    # Configurar para Windows
                    if sys.platform == 'win32':
                        import subprocess
                        service.creation_flags = subprocess.CREATE_NO_WINDOW
                    
                    driver_local = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    driver_local = webdriver.Chrome(options=chrome_options)
            except:
                driver_local = webdriver.Chrome(options=chrome_options)
            
            driver_local.implicitly_wait(5)
            
            # Processar banco
            print(f"[Worker] Processando banco: {banco_info['nome']}")
            
            # Extrair links do Drive
            driver_local.get(banco_info['url'])
            time.sleep(3)
            
            links_drive = []
            links = driver_local.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                href = link.get_attribute("href")
                if href and "drive.google.com" in href:
                    links_drive.append(href)
            
            print(f"[Worker] {banco_info['nome']}: {len(links_drive)} links do Drive encontrados")
            
            # Baixar arquivos de cada link do Drive
            for link_drive in links_drive:
                try:
                    driver_local.get(link_drive)
                    time.sleep(3)
                    
                    # Estratégias de download simplificadas
                    estrategias = [
                        lambda: driver_local.find_elements(By.CSS_SELECTOR, "a[download]"),
                        lambda: driver_local.find_elements(By.CSS_SELECTOR, "[data-tooltip*='Download'], [title*='Download']"),
                        lambda: driver_local.find_elements(By.CSS_SELECTOR, "button[aria-label*='Download']"),
                        lambda: driver_local.find_elements(By.XPATH, "//div[contains(text(),'.pdf')]"),
                        lambda: driver_local.find_elements(By.CSS_SELECTOR, "a[href*='download']")
                    ]
                    
                    elementos_arquivo = []
                    for estrategia in estrategias:
                        try:
                            elementos = estrategia()
                            if elementos:
                                elementos_arquivo.extend(elementos[:3])  # Limitar elementos
                                break
                        except:
                            continue
                    
                    # Tentar baixar arquivos
                    for elemento in elementos_arquivo[:3]:  # Limitar a 3 arquivos por Drive
                        try:
                            texto_elemento = elemento.text.lower()
                            if any(ext in texto_elemento for ext in ['.pdf', '.doc', '.xls', 'download']):
                                driver_local.execute_script("arguments[0].click();", elemento)
                                time.sleep(1)
                                arquivos_baixados += 1
                        except:
                            continue
                    
                    time.sleep(1)
                    
                except Exception as e:
                    continue
            
            return {
                'banco': banco_info['nome'],
                'arquivos_baixados': arquivos_baixados,
                'links_drive': len(links_drive),
                'sucesso': True
            }
            
        except Exception as e:
            return {
                'banco': banco_info['nome'],
                'arquivos_baixados': 0,
                'links_drive': 0,
                'erro': str(e)[:100],
                'sucesso': False
            }
            
        finally:
            # Restaurar stderr
            sys.stderr = original_stderr
            
            if driver_local:
                try:
                    driver_local.quit()
                except:
                    pass

    def baixar_todos_multiprocessamento(self):
        """Executa o download com multiprocessamento para máxima velocidade"""
        if not self.pasta_downloads:
            if not self.configurar_pasta_downloads():
                return
        
        # Usar driver principal apenas para extrair links iniciais
        if not self.inicializar_driver():
            return
        
        try:
            self.console.print(Panel(
                f"[cyan]Iniciando download com multiprocessamento![/cyan]\n\n"
                f"Processos paralelos: {self.num_processos}\n"
                f"Threads por processo: {self.max_threads_por_processo}\n"
                f"Total de workers: {self.num_processos * self.max_threads_por_processo}\n\n"
                f"Este processo será muito mais rápido!",
                title="Download Multiprocessamento",
                border_style="cyan"
            ))
            
            inicio_tempo = time.time()
            
            # Extrair links de convênios
            self.console.print("[yellow]Extraindo links de convênios...[/yellow]")
            links_convenios = self.extrair_links_convenios(self.site_base)
            
            if not links_convenios:
                self.console.print("[red]Nenhum convênio encontrado![/red]")
                return
            
            self.console.print(f"[green]✓ {len(links_convenios)} convênio(s) encontrado(s)[/green]")
            
            # Coletar todos os bancos de todos os convênios
            todos_bancos = []
            
            for convenio in track(links_convenios, description="Coletando bancos..."):
                self.console.print(f"[cyan]Coletando bancos de: {convenio['nome']}[/cyan]")
                links_bancos = self.extrair_links_bancos(convenio['url'])
                
                for banco in links_bancos:
                    banco['convenio'] = convenio['nome']
                    todos_bancos.append(banco)
            
            self.console.print(f"[green]✓ Total de bancos coletados: {len(todos_bancos)}[/green]")
            
            if not todos_bancos:
                self.console.print("[red]Nenhum banco encontrado![/red]")
                return
            
            # Finalizar driver principal antes do multiprocessamento
            self.finalizar_driver()
            
            # Preparar argumentos para multiprocessamento
            args_multiprocessamento = [(banco, self.pasta_downloads) for banco in todos_bancos]
            
            # Executar multiprocessamento
            self.console.print(f"[green]Iniciando processamento paralelo de {len(todos_bancos)} bancos...[/green]")
            
            resultados = []
            
            try:
                # Usar multiprocessing.Pool com função independente
                with Pool(processes=self.num_processos) as pool:
                    resultados = pool.map(worker_banco_independente, args_multiprocessamento)
                
            except Exception as e:
                self.console.print(f"[yellow]Erro no multiprocessamento: {str(e)[:50]}[/yellow]")
                self.console.print("[cyan]Tentando ThreadPoolExecutor...[/cyan]")
                
                # Fallback para ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=self.num_processos) as executor:
                    futures = [executor.submit(worker_banco_independente, args) for args in args_multiprocessamento]
                    resultados = [future.result() for future in as_completed(futures)]
            
            # Processar resultados
            total_arquivos = 0
            bancos_sucesso = 0
            bancos_erro = 0
            
            for resultado in resultados:
                if resultado['sucesso']:
                    total_arquivos += resultado['arquivos_baixados']
                    bancos_sucesso += 1
                    self.console.print(f"[green]✓ {resultado['banco']}: {resultado['arquivos_baixados']} arquivos ({resultado['links_drive']} drives)[/green]")
                else:
                    bancos_erro += 1
                    self.console.print(f"[red]✗ {resultado['banco']}: {resultado.get('erro', 'Erro desconhecido')}[/red]")
            
            tempo_total = time.time() - inicio_tempo
            
            self.console.print(Panel(
                f"[green]Download multiprocessamento concluído![/green]\n\n"
                f"Tempo total: {tempo_total:.1f} segundos\n"
                f"Bancos processados: {bancos_sucesso}\n"
                f"Bancos com erro: {bancos_erro}\n"
                f"Total de arquivos baixados: {total_arquivos}\n"
                f"Pasta de destino: {self.pasta_downloads}\n\n"
                f"[cyan]Velocidade estimada: {len(todos_bancos)/tempo_total:.1f} bancos/segundo[/cyan]",
                title="Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro durante o download multiprocessamento:[/red]\n\n"
                f"Erro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
        
        finally:
            if self.driver:
                self.finalizar_driver()

    def finalizar_driver(self):
        """Finaliza o driver do Chrome"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def obter_lista_bancos(self):
        """Retorna a lista completa de bancos conhecidos"""
        return [
            "AMIGOZ", "BANCO DO BRASIL", "BANRISUL", "BMG", "BRB", "C6",
            "DAYCOVAL", "DIGIO", "FACTA", "GO! CONSIG", "ICRED", "INBURSA",
            "ITAU", "MASTER", "MERCANTIL", "OLE/SANTANDER", "PAN", "PRESENÇA BANK",
            "QUALIBANK", "QUALICARD", "QUERO+", "SAFRA", "TOTAL CASH", "V8"
        ]

    def eh_nome_banco(self, texto):
        """Verifica se o texto corresponde a um nome de banco conhecido"""
        bancos_conhecidos = self.obter_lista_bancos()
        return any(banco in texto for banco in bancos_conhecidos)

    def extrair_links_convenios(self, url):
        """Extrai todos os links de convênios da página principal"""
        try:
            self.driver.get(url)
            time.sleep(3)
            
            links = self.driver.find_elements(By.TAG_NAME, "a")
            links_convenios = []
            
            for link in links:
                href = link.get_attribute("href")
                if href and "conv%C3%AAnios" in href and href != url:
                    texto = link.text.strip()
                    if texto and texto not in ["Página inicial", "CONVÊNIOS"]:
                        links_convenios.append({
                            "nome": texto,
                            "url": href
                        })
            
            links_unicos = []
            urls_vistas = set()
            for link in links_convenios:
                if link["url"] not in urls_vistas:
                    links_unicos.append(link)
                    urls_vistas.add(link["url"])
            
            return links_unicos
            
        except Exception as e:
            self.console.print(f"[red]Erro ao extrair links de convênios: {str(e)}[/red]")
            return []

    def extrair_links_bancos(self, url):
        """Extrai links de bancos de uma página de convênio"""
        try:
            self.driver.get(url)
            time.sleep(5)
            
            elementos_banco = []
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            elementos_possiveis = []
            
            seletores = [
                "div[style*='background']",
                "button",
                "a[href*='drive.google.com']",
                "*[onclick]",
                "div[role='button']",
                "*[style*='cursor: pointer']"
            ]
            
            for seletor in seletores:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    elementos_possiveis.extend(elementos)
                except:
                    continue
            
            for banco_nome in self.obter_lista_bancos():
                try:
                    xpath_texto = f"//*[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{banco_nome}')]"
                    elementos_texto = self.driver.find_elements(By.XPATH, xpath_texto)
                    elementos_possiveis.extend(elementos_texto)
                except:
                    continue
            
            for elemento in elementos_possiveis:
                try:
                    texto = elemento.text.strip().upper()
                    if self.eh_nome_banco(texto) and texto not in ["PÁGINA INICIAL", "BANCOS", "LISTAGEM EM ORDEM ALFABÉTICA"]:
                        
                        href = None
                        
                        if elemento.tag_name == "a":
                            href = elemento.get_attribute("href")
                        elif elemento.get_attribute("onclick"):
                            try:
                                url_atual = self.driver.current_url
                                self.driver.execute_script("arguments[0].click();", elemento)
                                time.sleep(3)
                                nova_url = self.driver.current_url
                                if nova_url != url_atual:
                                    href = nova_url
                                    self.driver.back()
                                    time.sleep(2)
                            except:
                                pass
                        
                        if not href:
                            try:
                                link_elemento = elemento.find_element(By.XPATH, ".//a | ./ancestor::a[1]")
                                href = link_elemento.get_attribute("href")
                            except:
                                pass
                        
                        if href and href not in [elem["url"] for elem in elementos_banco]:
                            elementos_banco.append({
                                "nome": texto,
                                "url": href
                            })
                            self.console.print(f"    [green]✓ Banco encontrado: {texto}[/green]")
                
                except Exception as e:
                    continue
            
            elementos_unicos = []
            urls_vistas = set()
            for elem in elementos_banco:
                if elem["url"] not in urls_vistas:
                    elementos_unicos.append(elem)
                    urls_vistas.add(elem["url"])
            
            return elementos_unicos
            
        except Exception as e:
            self.console.print(f"[red]Erro ao extrair links de bancos: {str(e)}[/red]")
            return []

    def extrair_links_drive(self, url):
        """Extrai links do Google Drive de uma página"""
        try:
            self.driver.get(url)
            time.sleep(3)
            
            links_drive = []
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                href = link.get_attribute("href")
                if href and "drive.google.com" in href:
                    links_drive.append(href)
            
            return links_drive
            
        except Exception as e:
            self.console.print(f"[red]Erro ao extrair links do Drive: {str(e)}[/red]")
            return []

    def extrair_file_id_drive(self, url_drive):
        """Extrai o FILE_ID do link do Google Drive"""
        import re
        
        # Padrões para extrair FILE_ID
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',  # drive.google.com/file/d/FILE_ID
            r'id=([a-zA-Z0-9_-]+)',       # drive.google.com/open?id=FILE_ID
            r'/folders/([a-zA-Z0-9_-]+)', # drive.google.com/drive/folders/FOLDER_ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_drive)
            if match:
                return match.group(1)
        
        return None

    def verificar_arquivo_publico(self, url_drive):
        """Verifica se o arquivo do Drive é público (sem necessidade de login)"""
        try:
            response = requests.head(url_drive, allow_redirects=True, timeout=10)
            
            # Se redireciona para accounts.google.com, precisa de login
            if 'accounts.google.com' in response.url:
                return False
            
            # Se retorna 200 ou 302, provavelmente é público
            if response.status_code in [200, 302]:
                return True
                
            return False
            
        except Exception as e:
            return False

    def limpar_url_drive(self, url_drive):
        """Remove parâmetros de query da URL do Drive (tudo após '?')"""
        if '?' in url_drive:
            url_limpa = url_drive.split('?')[0]
            self.console.print(f"        [blue]🔧 URL limpa: {url_limpa}[/blue]")
            return url_limpa
        return url_drive

    def baixar_com_gdown(self, url_drive):
        """Baixa usando gdown - método mais eficiente e confiável"""
        try:
            self.console.print(f"        [cyan]🚀 Usando gdown para download eficiente...[/cyan]")
            
            # Verificar se gdown está instalado e versão
            gdown_version = None
            try:
                import subprocess
                import re
                result = subprocess.run(['gdown', '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    raise Exception("gdown não encontrado")
                
                # Verificar versão do gdown com regex robusto
                vers_match = re.search(r'(\d+)\.(\d+)', result.stdout)  # captura major e minor
                if vers_match:
                    major, minor = map(int, vers_match.groups())
                    gdown_version = (major, minor)  # Armazenar para uso posterior
                    if (major, minor) < (5, 3):
                        self.console.print(
                            f"        [yellow]⚠ Sua versão do gdown é antiga "
                            f"(v{major}.{minor}). Recomendo atualizar: "
                            f"pip install -U gdown==5.3.0[/yellow]"
                        )
                    
            except:
                self.console.print(f"        [red]❌ gdown não está instalado ou não está no PATH[/red]")
                self.console.print(f"        [yellow]💡 Para instalar: pip install gdown[/yellow]")
                return []
            
            # CORRIGIR: Limpar URL removendo parâmetros de query (?usp=drive_link, etc.)
            url_limpa = self.limpar_url_drive(url_drive)
            
            # CORRIGIR: Verificar e configurar pasta de downloads (CAMINHO CURTO)
            if not self.pasta_downloads or self.pasta_downloads.strip() == "":
                # Pasta padrão CURTA para evitar limite 260 caracteres Windows
                pasta_padrao = "C:\\Downloads\\Drive"
                os.makedirs(pasta_padrao, exist_ok=True)
                self.pasta_downloads = pasta_padrao
                self.console.print(f"        [yellow]📁 Pasta padrão criada (caminho curto): {pasta_padrao}[/yellow]")
            
            # Preparar comando gdown baseado nas regras do CLI
            cmd_gdown = ['gdown']
            
            # Adicionar --folder apenas para pastas
            if self.eh_pasta_drive(url_limpa):
                cmd_gdown.append('--folder')
            
            # Adicionar outros parâmetros
            cmd_gdown.extend(['--fuzzy', url_limpa])
            
            # Adicionar paralelismo apenas se gdown suporta (≥5.4)
            # --threads foi introduzido no gdown 5.4, não existe em versões anteriores
            if self.eh_pasta_drive(url_limpa) and gdown_version:
                major, minor = gdown_version
                if (major, minor) >= (5, 4):  # --threads disponível a partir de 5.4
                    cmd_gdown.extend(['--threads', '4'])
                    self.console.print(f"        [blue]⚡ Paralelismo ativado (gdown v{major}.{minor})[/blue]")
            
            # Adicionar --output apenas se temos pasta válida
            if self.pasta_downloads and self.pasta_downloads.strip():
                cmd_gdown.extend(['--output', self.pasta_downloads])
            
            self.console.print(f"        [blue]📋 Comando: {' '.join(cmd_gdown)}[/blue]")
            
            # Executar gdown (CORRIGIDO: sem cwd para evitar conflito com --output)
            try:
                result = subprocess.run(
                    cmd_gdown,
                    capture_output=True,
                    text=True,
                    timeout=900,  # 15 minutos timeout (mais folga)
                    encoding='utf-8',  # Forçar UTF-8
                    errors='ignore'  # Ignorar caracteres problemáticos
                    # cwd removido - usar diretório padrão como no PowerShell
                )
                
                # Analisar resultado
                if result.returncode == 0:
                    # Contar arquivos baixados no output
                    output_lines = result.stdout.split('\n')
                    arquivos_baixados = []
                    
                    for line in output_lines:
                        if 'Processing file' in line:
                            # Extrair nome do arquivo da linha
                            try:
                                filename = line.split('Processing file')[1].strip()
                                if filename:
                                    arquivos_baixados.append(filename[:50])  # Limitar tamanho
                            except:
                                arquivos_baixados.append("arquivo_processado")
                        elif 'Download completed' in line:
                            break
                    
                    if not arquivos_baixados and 'completed' in result.stdout.lower():
                        arquivos_baixados = ["download_gdown_sucesso"]
                    
                    self.console.print(f"        [green]✅ gdown concluído: {len(arquivos_baixados)} arquivo(s)[/green]")
                    
                    # Mostrar alguns arquivos baixados
                    if arquivos_baixados:
                        for i, arquivo in enumerate(arquivos_baixados[:3], 1):
                            self.console.print(f"        [green]  {i}. {arquivo}[/green]")
                        if len(arquivos_baixados) > 3:
                            self.console.print(f"        [green]  ... e mais {len(arquivos_baixados) - 3} arquivo(s)[/green]")
                    
                    # CORREÇÃO: Pausa para evitar rate limiting (429/403)
                    time.sleep(2)
                    return arquivos_baixados
                
                else:
                    # Erro no gdown - capturar mensagem completa
                    error_msg = result.stderr.strip() if result.stderr else ""
                    stdout_msg = result.stdout.strip() if result.stdout else ""
                    
                    # Combinar stderr e stdout para análise completa
                    full_output = f"{stdout_msg}\n{error_msg}".strip()
                    
                    # Verificar tipos específicos de erro
                    if "403" in full_output or "Forbidden" in full_output:
                        self.console.print(f"        [yellow]⚠ Pasta/arquivo não público ou sem permissão[/yellow]")
                    elif "429" in full_output or "rate limit" in full_output.lower():
                        self.console.print(f"        [yellow]⚠ Rate limiting detectado - muitas requisições[/yellow]")
                        self.console.print(f"        [blue]💡 Aguardando mais tempo antes do próximo download...[/blue]")
                        time.sleep(5)  # Pausa extra para rate limiting
                    elif "too many files" in full_output.lower():
                        self.console.print(f"        [yellow]⚠ Muitos arquivos - limitação do gdown[/yellow]")
                        # Fallback para rclone se disponível
                        return self.tentar_rclone_fallback(url_drive)
                    elif "Building directory structure" in full_output and result.returncode != 0:
                        # Erro específico - interrupção durante building (bug gdown ≤5.2)
                        self.console.print(f"        [yellow]⚠ Processo interrompido durante estruturação de pastas[/yellow]")
                        self.console.print(f"        [blue]💡 Bug conhecido do gdown ≤5.2: considere atualizar para versão 5.3+[/blue]")
                    else:
                        # Mostrar a mensagem de erro mais completa
                        display_msg = full_output[:200] + "..." if len(full_output) > 200 else full_output
                        self.console.print(f"        [red]❌ Erro no gdown: {display_msg}[/red]")
                        # Debug: mostrar código de retorno
                        self.console.print(f"        [blue]🔍 Return code: {result.returncode}[/blue]")
                    
                    return []
                    
            except subprocess.TimeoutExpired:
                self.console.print(f"        [yellow]⏰ Timeout no gdown (>15min) - pasta muito grande[/yellow]")
                self.console.print(f"        [blue]💡 Tentando estratégia alternativa com timeout menor...[/blue]")
                
                # Retry com timeout menor para ver se completa pelo menos parte
                try:
                    result_retry = subprocess.run(
                        cmd_gdown,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minutos (aumentado do retry)
                        encoding='utf-8',
                        errors='ignore'
                        # cwd removido - usar diretório padrão como no PowerShell
                    )
                    
                    if result_retry.returncode == 0:
                        self.console.print(f"        [green]✅ Sucesso com timeout menor[/green]")
                        # Processar resultado normalmente
                        arquivos_baixados = []
                        output_lines = result_retry.stdout.split('\n')
                        
                        for line in output_lines:
                            if 'Processing file' in line:
                                try:
                                    filename = line.split('Processing file')[1].strip()
                                    if filename:
                                        arquivos_baixados.append(filename[:50])
                                except:
                                    arquivos_baixados.append("arquivo_processado")
                        
                        if not arquivos_baixados and 'completed' in result_retry.stdout.lower():
                            arquivos_baixados = ["download_gdown_sucesso"]
                        
                        return arquivos_baixados
                    else:
                        self.console.print(f"        [yellow]⚠ Retry também falhou - pasta pode ser muito complexa[/yellow]")
                        return []
                        
                except subprocess.TimeoutExpired:
                    self.console.print(f"        [yellow]⚠ Timeout mesmo com 3min - pasta inacessível[/yellow]")
                    return []
                except Exception as e:
                    self.console.print(f"        [yellow]⚠ Erro no retry: {str(e)[:50]}[/yellow]")
                    return []
            except Exception as e_subprocess:
                self.console.print(f"        [red]❌ Erro ao executar gdown: {str(e_subprocess)[:50]}[/red]")
                return []
            
        except Exception as e:
            self.console.print(f"        [red]❌ Erro geral no gdown: {str(e)[:50]}[/red]")
            return []

    def tentar_rclone_fallback(self, url_drive):
        """Fallback usando rclone para pastas com muitos arquivos"""
        try:
            self.console.print(f"        [cyan]🔄 Tentando fallback com rclone...[/cyan]")
            
            # Verificar se rclone está disponível
            try:
                result_check = subprocess.run(['rclone', '--version'], capture_output=True, text=True, timeout=10)
                if result_check.returncode != 0:
                    self.console.print(f"        [yellow]⚠ rclone não encontrado, usando fallback Selenium[/yellow]")
                    return []
            except:
                self.console.print(f"        [yellow]⚠ rclone não encontrado, usando fallback Selenium[/yellow]")
                return []
            
            # Extrair folder ID da URL
            folder_id = self.extrair_file_id_drive(url_drive)
            if not folder_id:
                self.console.print(f"        [red]❌ Não foi possível extrair ID da pasta[/red]")
                return []
            
            # Comando rclone (configuração Google Drive necessária)
            cmd_rclone = [
                'rclone', 'copy',
                f'gdrive,root_folder_id={folder_id}:',
                self.pasta_downloads,
                '--progress',
                '--transfers', '4'
            ]
            
            self.console.print(f"        [blue]📋 Comando rclone: {' '.join(cmd_rclone[:4])}...[/blue]")
            self.console.print(f"        [yellow]💡 Nota: rclone precisa estar configurado com Google Drive[/yellow]")
            
            # Executar rclone
            result = subprocess.run(
                cmd_rclone,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutos para pastas muito grandes
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                # Contar arquivos baixados (estimativa baseada na saída)
                arquivos_estimados = result.stdout.count('Transferred:')
                if arquivos_estimados == 0:
                    arquivos_estimados = 1  # Pelo menos tentou
                
                self.console.print(f"        [green]✅ rclone concluído: ~{arquivos_estimados} arquivo(s)[/green]")
                return [f"rclone_arquivo_{i}" for i in range(arquivos_estimados)]
            else:
                self.console.print(f"        [red]❌ rclone falhou: {result.stderr[:100]}[/red]")
                return []
                
        except subprocess.TimeoutExpired:
            self.console.print(f"        [yellow]⏰ Timeout rclone (30min) - pasta muito grande[/yellow]")
            return []
        except Exception as e:
            self.console.print(f"        [red]❌ Erro no rclone: {str(e)[:50]}[/red]")
            return []

    def baixar_drive_direto(self, file_id, nome_arquivo="arquivo_drive"):
        """Baixa arquivo do Drive usando URL direta (sem Selenium) - FALLBACK"""
        try:
            # URL direta do Google Drive
            url_download = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            self.console.print(f"        [cyan]Tentando download direto (fallback): {file_id[:20]}...[/cyan]")
            
            session = requests.Session()
            response = session.get(url_download, stream=True, timeout=30)
            
            # Verificar se precisa de confirmação (arquivos grandes)
            if 'download_warning' in response.cookies:
                # Extrair token de confirmação
                for line in response.text.split('\n'):
                    if 'confirm=' in line:
                        import re
                        match = re.search(r'confirm=([^&"]+)', line)
                        if match:
                            token = match.group(1)
                            url_confirm = f"{url_download}&confirm={token}"
                            response = session.get(url_confirm, stream=True, timeout=30)
                            break
            
            if response.status_code == 200:
                # Determinar nome do arquivo
                filename = nome_arquivo
                if 'content-disposition' in response.headers:
                    import re
                    match = re.search(r'filename="?([^"]+)"?', response.headers['content-disposition'])
                    if match:
                        filename = match.group(1)
                
                # Salvar arquivo em chunks
                filepath = os.path.join(self.pasta_downloads, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=32768):  # 32KB chunks
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(filepath)
                self.console.print(f"        [green]✓ Arquivo baixado: {filename} ({file_size} bytes)[/green]")
                return [filename]
            
            else:
                self.console.print(f"        [yellow]Status HTTP: {response.status_code}[/yellow]")
                return []
                
        except Exception as e:
            self.console.print(f"        [red]Erro no download direto: {str(e)[:50]}[/red]")
            return []

    def eh_pasta_drive(self, url_drive):
        """Verifica se o URL é de uma pasta do Google Drive"""
        return '/folders/' in url_drive or '/drive/folders/' in url_drive

    def navegar_pasta_drive(self, url_pasta):
        """Navega dentro de uma pasta do Drive e extrai links dos arquivos individuais"""
        try:
            self.console.print(f"        [cyan]📁 Navegando dentro da pasta...[/cyan]")
            
            self.driver.get(url_pasta)
            time.sleep(5)  # Aguardar carregamento da pasta
            
            # Verificar se há login necessário
            if "accounts.google.com" in self.driver.current_url or "signin" in self.driver.current_url.lower():
                self.console.print(f"        [yellow]⚠ Pasta requer autenticação - pulando[/yellow]")
                return []
            
            # Verificar se há acesso negado
            page_text = self.driver.page_source.lower()
            if any(termo in page_text for termo in ['access denied', 'acesso negado', 'sign in', 'fazer login']):
                self.console.print(f"        [yellow]⚠ Acesso restrito à pasta - pulando[/yellow]")
                return []
            
            arquivos_encontrados = []
            
            # Estratégias para encontrar arquivos na pasta
            try:
                # Estratégia 1: Buscar por elementos com data-id (arquivos individuais)
                elementos_arquivo = self.driver.find_elements(By.CSS_SELECTOR, "[data-id]")
                
                if not elementos_arquivo:
                    # Estratégia 2: Buscar por divs que contêm arquivos
                    elementos_arquivo = self.driver.find_elements(By.CSS_SELECTOR, "div[role='option'], div[role='gridcell']")
                
                if not elementos_arquivo:
                    # Estratégia 3: Buscar por spans com nomes de arquivo
                    elementos_arquivo = self.driver.find_elements(By.CSS_SELECTOR, "span[title*='.'], span[aria-label*='.']")
                
                self.console.print(f"        [blue]🔍 Encontrados {len(elementos_arquivo)} elementos na pasta[/blue]")
                
                # Processar cada arquivo encontrado
                for i, elemento in enumerate(elementos_arquivo[:10], 1):  # Limitar a 10 arquivos por pasta
                    try:
                        # Tentar extrair nome do arquivo
                        nome_arquivo = ""
                        try:
                            nome_arquivo = elemento.get_attribute("title") or elemento.get_attribute("aria-label") or elemento.text
                        except:
                            nome_arquivo = f"arquivo_{i}"
                        
                        # Verificar se é um arquivo (tem extensão)
                        if any(ext in nome_arquivo.lower() for ext in ['.pdf', '.doc', '.xls', '.csv', '.txt', '.zip', '.rar']):
                            self.console.print(f"        [cyan]📄 Arquivo {i}: {nome_arquivo[:40]}...[/cyan]")
                            
                            try:
                                # Scroll para o elemento
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                                time.sleep(1)
                                
                                # Tentar clique duplo para download
                                self.driver.execute_script("arguments[0].click(); arguments[0].click();", elemento)
                                time.sleep(2)
                                
                                # Procurar e clicar no botão de download que aparece
                                try:
                                    # Aguardar menu de contexto ou opções
                                    time.sleep(2)
                                    
                                    # Procurar botão de download
                                    botoes_download = self.driver.find_elements(By.CSS_SELECTOR, 
                                        "[aria-label*='Download'], [aria-label*='Baixar'], "
                                        "[title*='Download'], [title*='Baixar'], "
                                        "button[data-tooltip*='Download']")
                                    
                                    for botao in botoes_download:
                                        try:
                                            if botao.is_displayed():
                                                botao.click()
                                                arquivos_encontrados.append(nome_arquivo)
                                                self.console.print(f"        [green]✅ Download iniciado: {nome_arquivo[:30]}[/green]")
                                                time.sleep(2)
                                                break
                                        except:
                                            continue
                                    
                                    # Se não encontrou botão, tentar tecla de atalho
                                    if nome_arquivo not in [arq for arq in arquivos_encontrados]:
                                        # Pressionar Ctrl+Alt+D (atalho de download do Drive)
                                        try:
                                            from selenium.webdriver.common.keys import Keys
                                            from selenium.webdriver.common.action_chains import ActionChains
                                            
                                            actions = ActionChains(self.driver)
                                            actions.key_down(Keys.CONTROL).key_down(Keys.ALT).send_keys('d').key_up(Keys.ALT).key_up(Keys.CONTROL).perform()
                                            time.sleep(2)
                                            
                                            arquivos_encontrados.append(nome_arquivo)
                                            self.console.print(f"        [green]✅ Download via atalho: {nome_arquivo[:30]}[/green]")
                                        except:
                                            self.console.print(f"        [yellow]⚠ Não foi possível baixar: {nome_arquivo[:30]}[/yellow]")
                                
                                except Exception as e_download:
                                    self.console.print(f"        [yellow]⚠ Erro ao baixar {nome_arquivo[:20]}: {str(e_download)[:30]}[/yellow]")
                                    continue
                                
                            except Exception as e_click:
                                continue
                        
                    except Exception as e_arquivo:
                        continue
                
                if arquivos_encontrados:
                    self.console.print(f"        [green]✅ {len(arquivos_encontrados)} arquivo(s) processado(s) da pasta[/green]")
                else:
                    self.console.print(f"        [yellow]⚠ Nenhum arquivo baixado da pasta[/yellow]")
                
                return arquivos_encontrados
                
            except Exception as e_navegacao:
                self.console.print(f"        [red]Erro ao navegar na pasta: {str(e_navegacao)[:50]}[/red]")
                return []
            
        except Exception as e:
            self.console.print(f"        [red]Erro geral na pasta: {str(e)[:50]}[/red]")
            return []

    def baixar_drive_stealth(self, url_drive):
        """Baixa usando Selenium com técnicas stealth para evitar detecção"""
        try:
            # Verificar se é uma pasta
            if self.eh_pasta_drive(url_drive):
                self.console.print(f"        [blue]📁 Detectada pasta do Drive - navegando internamente...[/blue]")
                return self.navegar_pasta_drive(url_drive)
            
            self.console.print(f"        [cyan]Tentando download stealth...[/cyan]")
            
            # Verificar se há indicação de login necessário
            self.driver.get(url_drive)
            time.sleep(3)
            
            # Verificar se apareceu tela de login
            if "accounts.google.com" in self.driver.current_url or "signin" in self.driver.current_url.lower():
                self.console.print(f"        [yellow]⚠ Arquivo requer autenticação - pulando[/yellow]")
                return []
            
            # Verificar se há mensagem de erro ou acesso negado
            page_text = self.driver.page_source.lower()
            if any(termo in page_text for termo in ['access denied', 'acesso negado', 'sign in', 'fazer login']):
                self.console.print(f"        [yellow]⚠ Acesso restrito - pulando[/yellow]")
                return []
            
            # Procurar botões de download
            arquivos_baixados = []
            
            # Estratégias de download stealth para arquivo individual
            estrategias = [
                # Estratégia 1: Botão de download direto
                lambda: self.driver.find_elements(By.CSS_SELECTOR, "a[download], button[download]"),
                # Estratégia 2: Botões com aria-label de download
                lambda: self.driver.find_elements(By.CSS_SELECTOR, "[aria-label*='Download'], [aria-label*='Baixar']"),
                # Estratégia 3: Links com texto de download
                lambda: self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Download') or contains(text(), 'Baixar')]"),
                # Estratégia 4: Ícones de download
                lambda: self.driver.find_elements(By.CSS_SELECTOR, "[title*='Download'], [data-tooltip*='Download']"),
            ]
            
            for i, estrategia in enumerate(estrategias, 1):
                try:
                    elementos = estrategia()
                    if elementos:
                        self.console.print(f"        [green]Estratégia {i}: {len(elementos)} elementos encontrados[/green]")
                        
                        for elemento in elementos[:3]:  # Limitar a 3 tentativas
                            try:
                                # Scroll para o elemento
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                                time.sleep(1)
                                
                                # Tentar click
                                self.driver.execute_script("arguments[0].click();", elemento)
                                time.sleep(2)
                                
                                arquivos_baixados.append(f"Arquivo_stealth_{len(arquivos_baixados)+1}")
                                self.console.print(f"        [green]✓ Download iniciado via stealth[/green]")
                                
                            except Exception as e_click:
                                continue
                        
                        if arquivos_baixados:
                            break
                            
                except Exception as e_estrategia:
                    continue
            
            return arquivos_baixados
            
        except Exception as e:
            self.console.print(f"        [red]Erro no download stealth: {str(e)[:50]}[/red]")
            return []

    def baixar_arquivos_drive(self, url_drive):
        """Agente de Download do Google Drive - Prioriza gdown (mais eficiente)"""
        self.console.print(f"      [cyan]🎯 Processando Drive: {url_drive[:60]}...[/cyan]")
        
        arquivos_baixados = []
        
        try:
            # ETAPA 1: PRIORIZAR GDOWN - Método mais eficiente e confiável
            self.console.print(f"        [blue]🚀 Estratégia prioritária: gdown (baseado em regras CLI)[/blue]")
            arquivos_gdown = self.baixar_com_gdown(url_drive)
            
            if arquivos_gdown:
                self.console.print(f"        [green]✅ Sucesso com gdown: {len(arquivos_gdown)} arquivo(s)[/green]")
                return arquivos_gdown
            
            # ETAPA 2: Fallback - Verificar se é pasta para navegação stealth
            if self.eh_pasta_drive(url_drive):
                self.console.print(f"        [yellow]📁 gdown falhou, tentando navegação stealth na pasta...[/yellow]")
                return self.baixar_drive_stealth(url_drive)
            
            # ETAPA 3: Para arquivos individuais, tentar método direto
            file_id = self.extrair_file_id_drive(url_drive)
            if file_id:
                self.console.print(f"        [yellow]📄 gdown falhou, tentando download direto...[/yellow]")
                
                # Verificar se é público
                is_public = self.verificar_arquivo_publico(url_drive)
                
                if is_public:
                    arquivos = self.baixar_drive_direto(file_id)
                    if arquivos:
                        arquivos_baixados.extend(arquivos)
                        return arquivos_baixados
            
            # ETAPA 4: Último recurso - Selenium stealth
            self.console.print(f"        [yellow]🔄 Tentando último recurso: método stealth...[/yellow]")
            arquivos_stealth = self.baixar_drive_stealth(url_drive)
            arquivos_baixados.extend(arquivos_stealth)
            
            if not arquivos_baixados:
                self.console.print(f"        [red]❌ Todas as estratégias falharam para este Drive[/red]")
                self.console.print(f"        [yellow]💡 Verifique se o link é público ou se o gdown está instalado[/yellow]")
            
            return arquivos_baixados
            
        except Exception as e:
            self.console.print(f"        [red]Erro no agente de download: {str(e)[:50]}[/red]")
            return []

    def baixar_link_especifico(self):
        """Permite ao usuário informar um link específico do Google Sites para download direcionado"""
        self.console.print(Panel(
            "[bold cyan]Download de Link Específico[/bold cyan]\n\n"
            "[yellow]Instruções:[/yellow]\n"
            "• Informe o link completo do Google Sites\n"
            "• O sistema extrairá APENAS os links do Drive dessa página\n"
            "• Download direcionado e preciso\n"
            "• Evita baixar arquivos desnecessários\n\n"
            "[green]Exemplo de link válido:[/green]\n"
            "https://sites.google.com/view/capitaldoisconhecimento/conv%C3%AAnios/banco-do-brasil",
            title="Download Direcionado",
            border_style="cyan"
        ))
        
        url_informada = inquirer.text(
            message="Cole o link do Google Sites:",
            filter=lambda x: x.strip(),
            validate=lambda x: self._validar_url_google_sites(x.strip())
        ).execute()
        
        if not url_informada:
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return
        
        url_informada = url_informada.strip()
        self.console.print(f"\n[cyan]🎯 Processando link específico:[/cyan] {url_informada[:80]}...")
        
        # Inicializar driver se necessário
        if not self.driver:
            if not self.inicializar_driver():
                return
        
        try:
            # Extrair informações da página
            self.console.print(f"[cyan]📄 Acessando página...[/cyan]")
            self.driver.get(url_informada)
            time.sleep(3)
            
            # Extrair título da página para identificação
            try:
                titulo_pagina = self.driver.title
                if not titulo_pagina:
                    titulo_pagina = "Página sem título"
            except:
                titulo_pagina = "Página do Google Sites"
            
            # Extrair links do Drive da página específica
            links_drive = self.extrair_links_drive(url_informada)
            
            if not links_drive:
                self.console.print(Panel(
                    "[yellow]Nenhum link do Google Drive encontrado nesta página.[/yellow]\n\n"
                    "[cyan]Possíveis causas:[/cyan]\n"
                    "• A página não contém links diretos para o Drive\n"
                    "• Os links estão em subpáginas\n"
                    "• A página requer navegação adicional\n\n"
                    "[green]Sugestões:[/green]\n"
                    "• Verifique se o link está correto\n"
                    "• Tente navegar até a página que contém os arquivos\n"
                    "• Use a opção 'Navegar específico' para explorar manualmente",
                    title="Nenhum Drive Encontrado",
                    border_style="yellow"
                ))
                return
            
            # Mostrar resumo dos drives encontrados
            self.console.print(Panel(
                f"[green]✓ {len(links_drive)} link(s) do Google Drive encontrado(s)[/green]\n\n"
                f"[bold]Página:[/bold] {titulo_pagina}\n"
                f"[bold]URL:[/bold] {url_informada[:60]}...\n"
                f"[bold]Drives encontrados:[/bold] {len(links_drive)}\n\n"
                f"[cyan]Pasta de downloads:[/cyan] {self.pasta_downloads}",
                title="Drives Detectados",
                border_style="green"
            ))
            
            # Listar os links encontrados (primeiros 5 para preview)
            self.console.print("[cyan]🔗 Links do Drive encontrados:[/cyan]")
            for i, link in enumerate(links_drive[:5], 1):
                link_exibido = link[:70] + "..." if len(link) > 70 else link
                self.console.print(f"  {i}. {link_exibido}")
            
            if len(links_drive) > 5:
                self.console.print(f"  ... e mais {len(links_drive) - 5} link(s)")
            
            # Confirmar se quer prosseguir
            confirmar = inquirer.select(
                message="Deseja prosseguir com o download?",
                choices=[
                    Choice("sim", name="✅ Sim, baixar todos os arquivos dos Drives encontrados"),
                    Choice("nao", name="❌ Não, voltar ao menu"),
                ],
            ).execute()
            
            if confirmar != "sim":
                self.console.print("[yellow]Download cancelado pelo usuário.[/yellow]")
                return
            
            # Iniciar download sequencial inteligente dos drives encontrados
            self.console.print(f"\n[bold green]🚀 Iniciando Download Sequencial Inteligente[/bold green]")
            self.console.print(f"[cyan]Total de Drives: {len(links_drive)}[/cyan]")
            
            total_arquivos = 0
            drives_com_sucesso = 0
            drives_com_erro = 0
            drives_sem_arquivos = 0
            
            for i, link_drive in enumerate(links_drive, 1):
                self.console.print(f"\n[bold blue]📁 Drive {i}/{len(links_drive)}[/bold blue]")
                
                try:
                    # Download imediato do drive atual
                    arquivos_baixados = self.baixar_arquivos_drive(link_drive)
                    
                    if arquivos_baixados:
                        total_arquivos += len(arquivos_baixados)
                        drives_com_sucesso += 1
                        self.console.print(f"      [green]✅ {len(arquivos_baixados)} arquivo(s) baixado(s)[/green]")
                    else:
                        drives_sem_arquivos += 1
                        self.console.print(f"      [yellow]⚠ Nenhum arquivo baixado (pode ser privado ou vazio)[/yellow]")
                        
                except Exception as e:
                    drives_com_erro += 1
                    self.console.print(f"      [red]❌ Erro: {str(e)[:50]}[/red]")
                
                # CORREÇÃO: Pausa maior para evitar rate limiting (429/403)
                time.sleep(3)
            
            # Relatório final
            self.console.print(Panel(
                f"[bold green]📊 Relatório Final do Download Específico[/bold green]\n\n"
                f"[bold]Página processada:[/bold] {titulo_pagina}\n"
                f"[bold]Total de Drives processados:[/bold] {len(links_drive)}\n"
                f"[green]✅ Drives com arquivos baixados:[/green] {drives_com_sucesso}\n"
                f"[yellow]⚠ Drives sem arquivos:[/yellow] {drives_sem_arquivos}\n"
                f"[red]❌ Drives com erro:[/red] {drives_com_erro}\n"
                f"[bold cyan]📁 Total de arquivos baixados:[/bold cyan] {total_arquivos}\n\n"
                f"[cyan]Pasta de downloads:[/cyan] {self.pasta_downloads}",
                title="Download Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao processar o link:[/red]\n\n"
                f"{str(e)}\n\n"
                f"[yellow]Verifique se:[/yellow]\n"
                f"• O link está correto e acessível\n"
                f"• Você tem conexão com a internet\n"
                f"• O Chrome está funcionando corretamente",
                title="Erro no Processamento",
                border_style="red"
            ))

    def _validar_url_google_sites(self, url):
        """Valida se a URL é de um Google Sites"""
        if not url:
            return "Por favor, informe uma URL"
        
        if not url.startswith(('http://', 'https://')):
            return "URL deve começar com http:// ou https://"
        
        if 'sites.google.com' not in url:
            return "URL deve ser de um Google Sites (sites.google.com)"
        
        return True

    def baixar_todos_automaticamente(self):
        """Executa o download automático - baixa imediatamente quando encontra cada Drive"""
        if not self.pasta_downloads:
            if not self.configurar_pasta_downloads():
                return
        
        if not self.inicializar_driver():
            return
        
        try:
            self.console.print(Panel(
                "[cyan]Iniciando download sequencial inteligente![/cyan]\n\n"
                "O sistema baixa arquivos imediatamente quando encontra cada Drive.\n"
                "Isso garante que erros pontuais não afetem outros downloads.",
                title="Download Sequencial Inteligente",
                border_style="cyan"
            ))
            
            self.console.print("[yellow]Extraindo links de convênios...[/yellow]")
            links_convenios = self.extrair_links_convenios(self.site_base)
            
            if not links_convenios:
                self.console.print(Panel(
                    "[red]Nenhum convênio encontrado![/red]\n\n"
                    "Possíveis causas:\n"
                    "• Site pode estar com layout diferente\n"
                    "• Problemas de conectividade\n"
                    "• Site pode ter mudado a estrutura\n\n"
                    "Tente novamente ou verifique o site manualmente.",
                    title="Erro na Extração",
                    border_style="red"
                ))
                return
            
            self.console.print(f"[green]✓ {len(links_convenios)} convênio(s) encontrado(s)[/green]")
            for conv in links_convenios:
                self.console.print(f"  • {conv['nome']}")
            
            total_arquivos = 0
            total_drives_processados = 0
            total_drives_com_sucesso = 0
            
            for convenio in track(links_convenios, description="Processando convênios..."):
                self.console.print(f"\n[cyan]Processando: {convenio['nome']}[/cyan]")
                self.console.print(f"  URL: {convenio['url']}")
                
                try:
                    links_bancos = self.extrair_links_bancos(convenio['url'])
                    self.console.print(f"  [blue]Bancos encontrados: {len(links_bancos)}[/blue]")
                    
                    if not links_bancos:
                        self.console.print(f"  [yellow]⚠ Nenhum banco encontrado em {convenio['nome']}[/yellow]")
                        continue
                    
                    for banco in links_bancos:
                        self.console.print(f"\n    [yellow]🏦 Processando banco: {banco['nome']}[/yellow]")
                        self.console.print(f"      URL: {banco['url']}")
                        
                        try:
                            # Navegar para a página do banco
                            self.driver.get(banco['url'])
                            time.sleep(3)
                            
                            # Encontrar links do Drive na página atual
                            links_drive = []
                            links = self.driver.find_elements(By.TAG_NAME, "a")
                            
                            for link in links:
                                href = link.get_attribute("href")
                                if href and "drive.google.com" in href:
                                    links_drive.append(href)
                            
                            # Remover duplicatas
                            links_drive = list(set(links_drive))
                            
                            self.console.print(f"      [blue]✓ {len(links_drive)} Drive(s) encontrado(s)[/blue]")
                            
                            if not links_drive:
                                self.console.print(f"      [yellow]⚠ Nenhum Drive encontrado para {banco['nome']}[/yellow]")
                                continue
                            
                            # BAIXAR IMEDIATAMENTE cada Drive encontrado
                            for j, link_drive in enumerate(links_drive, 1):
                                total_drives_processados += 1
                                
                                self.console.print(f"\n      [green]📁 Drive {j}/{len(links_drive)}: {link_drive[:60]}...[/green]")
                                
                                try:
                                    arquivos = self.baixar_arquivos_drive(link_drive)
                                    total_arquivos += len(arquivos)
                                    total_drives_com_sucesso += 1
                                    
                                    if len(arquivos) > 0:
                                        self.console.print(f"      [green]✓ {len(arquivos)} arquivo(s) baixado(s) com sucesso![/green]")
                                    else:
                                        self.console.print(f"      [yellow]⚠ Nenhum arquivo encontrado neste Drive[/yellow]")
                                    
                                except Exception as e_drive:
                                    self.console.print(f"      [red]✗ Erro no Drive {j}: {str(e_drive)[:50]}[/red]")
                                    continue
                                
                                # Pequena pausa entre drives
                                if j < len(links_drive):
                                    time.sleep(1)
                            
                        except Exception as e_banco:
                            self.console.print(f"      [red]✗ Erro ao processar banco {banco['nome']}: {str(e_banco)[:50]}[/red]")
                            continue
                    
                except Exception as e_convenio:
                    self.console.print(f"  [red]✗ Erro ao processar convênio {convenio['nome']}: {str(e_convenio)[:50]}[/red]")
                    continue
            
            # Relatório final detalhado
            sucesso_rate = (total_drives_com_sucesso / total_drives_processados * 100) if total_drives_processados > 0 else 0
            
            self.console.print(Panel(
                f"[green]Download sequencial concluído![/green]\n\n"
                f"📊 Estatísticas:\n"
                f"• Total de arquivos baixados: {total_arquivos}\n"
                f"• Drives processados: {total_drives_processados}\n"
                f"• Drives com sucesso: {total_drives_com_sucesso}\n"
                f"• Taxa de sucesso: {sucesso_rate:.1f}%\n"
                f"• Pasta de destino: {self.pasta_downloads}\n\n"
                f"[cyan]✓ Estratégia sequencial garante máxima recuperação![/cyan]",
                title="Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro durante o download automático:[/red]\n\n"
                f"Erro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
        
        finally:
            self.finalizar_driver()

    def navegar_especifico(self):
        """Permite navegar e baixar arquivos específicos"""
        if not self.pasta_downloads:
            if not self.configurar_pasta_downloads():
                return
        
        if not self.inicializar_driver():
            return
        
        try:
            links_convenios = self.extrair_links_convenios(self.site_base)
            
            if not links_convenios:
                self.console.print("[red]Nenhum convênio encontrado![/red]")
                return
            
            choices_convenios = [Choice(i, name=conv['nome']) for i, conv in enumerate(links_convenios)]
            choices_convenios.append(Choice("voltar", name="Voltar"))
            
            convenio_idx = inquirer.select(
                message="Selecione um convênio:",
                choices=choices_convenios,
            ).execute()
            
            if convenio_idx == "voltar":
                return
            
            convenio_selecionado = links_convenios[convenio_idx]
            
            links_bancos = self.extrair_links_bancos(convenio_selecionado['url'])
            
            if not links_bancos:
                self.console.print("[red]Nenhum banco encontrado neste convênio![/red]")
                return
            
            choices_bancos = [Choice(i, name=banco['nome']) for i, banco in enumerate(links_bancos)]
            choices_bancos.append(Choice("voltar", name="Voltar"))
            
            banco_idx = inquirer.select(
                message="Selecione um banco:",
                choices=choices_bancos,
            ).execute()
            
            if banco_idx == "voltar":
                return
            
            banco_selecionado = links_bancos[banco_idx]
            
            links_drive = self.extrair_links_drive(banco_selecionado['url'])
            
            if not links_drive:
                self.console.print("[red]Nenhum link do Drive encontrado neste banco![/red]")
                return
            
            total_arquivos = 0
            for link_drive in links_drive:
                self.console.print(f"[green]Baixando arquivos do Drive...[/green]")
                arquivos = self.baixar_arquivos_drive(link_drive)
                total_arquivos += len(arquivos)
            
            self.console.print(Panel(
                f"[green]Download concluído![/green]\n\n"
                f"Convênio: {convenio_selecionado['nome']}\n"
                f"Banco: {banco_selecionado['nome']}\n"
                f"Arquivos baixados: {total_arquivos}",
                title="Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro durante a navegação:[/red]\n\n"
                f"Erro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
        
        finally:
            self.finalizar_driver()

    def executar(self):
        """Função principal do módulo"""
        self.console.print(Panel.fit(
            "[bold blue]Web Downloader[/bold blue]\n"
            "[italic]Download automático de arquivos de sites[/italic]",
            border_style="blue"
        ))
        
        while True:
            opcao = self.menu_downloader()
            
            if opcao == "1":
                self.baixar_todos_automaticamente()
            elif opcao == "2":
                self.baixar_todos_multiprocessamento()
            elif opcao == "3":
                self.baixar_link_especifico()
            elif opcao == "4":
                self.navegar_especifico()
            elif opcao == "5":
                self.configurar_pasta_downloads()
            elif opcao == "6":
                self.configurar_processos()
            else:
                break 