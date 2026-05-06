#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para extração de CNPJs de arquivos CSV
"""

import os
import pandas as pd
import chardet
import re
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, track
from pathlib import Path

class ExtratorCNPJ:
    def __init__(self):
        self.console = Console()

    def detectar_encoding(self, arquivo_path):
        """Detecta a codificação do arquivo"""
        try:
            with open(arquivo_path, 'rb') as arquivo:
                resultado = chardet.detect(arquivo.read())
                return resultado['encoding']
        except Exception as e:
            self.console.print(f"[red]Erro ao detectar encoding: {e}[/red]")
            return None

    def limpar_cnpj(self, cnpj):
        """Remove caracteres especiais do CNPJ, mantendo apenas números"""
        if pd.isna(cnpj) or cnpj == '':
            return None
        
        # Converte para string e remove caracteres especiais
        cnpj_str = str(cnpj).strip()
        cnpj_limpo = re.sub(r'[^\d]', '', cnpj_str)
        
        # Verifica se tem 14 dígitos (CNPJ válido)
        if len(cnpj_limpo) == 14:
            return cnpj_limpo
        return None

    def extrair_cnpjs(self, arquivo_csv, coluna_cnpj, pasta_destino, nome_arquivo_saida=None, cnpjs_por_arquivo=None):
        """Extrai CNPJs de uma coluna específica do CSV"""
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(arquivo_csv):
                self.console.print(f"[red]Arquivo não encontrado: {arquivo_csv}[/red]")
                return False

            # Verificar se a pasta de destino existe, se não, criar
            if not os.path.exists(pasta_destino):
                try:
                    os.makedirs(pasta_destino)
                    self.console.print(f"[blue]Pasta criada: {pasta_destino}[/blue]")
                except Exception as e:
                    self.console.print(f"[red]Erro ao criar pasta: {e}[/red]")
                    return False

            # Detectar encoding
            encoding = self.detectar_encoding(arquivo_csv)
            if not encoding:
                self.console.print(f"[red]Não foi possível detectar o encoding de {arquivo_csv}[/red]")
                return False

            self.console.print(f"[blue]Encoding detectado: {encoding}[/blue]")

            # Tentar detectar delimitador
            with open(arquivo_csv, 'r', encoding=encoding) as arquivo:
                primeira_linha = arquivo.readline()
                if ';' in primeira_linha:
                    delimitador = ';'
                elif ',' in primeira_linha:
                    delimitador = ','
                else:
                    delimitador = ','

            self.console.print(f"[blue]Delimitador detectado: '{delimitador}'[/blue]")

            # Ler arquivo CSV
            df = pd.read_csv(arquivo_csv, encoding=encoding, delimiter=delimitador)
            
            # Verificar se a coluna existe
            if coluna_cnpj not in df.columns:
                self.console.print(f"[red]Coluna '{coluna_cnpj}' não encontrada no arquivo![/red]")
                self.console.print(f"[yellow]Colunas disponíveis: {list(df.columns)}[/yellow]")
                return False

            # Extrair CNPJs da coluna
            cnpjs = []
            total_linhas = len(df)
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Processando CNPJs...", total=total_linhas)
                
                for _, linha in df.iterrows():
                    cnpj = linha[coluna_cnpj]
                    cnpj_limpo = self.limpar_cnpj(cnpj)
                    
                    if cnpj_limpo:
                        cnpjs.append(cnpj_limpo)
                    
                    progress.update(task, advance=1)

            # Remover duplicatas mantendo a ordem
            cnpjs_unicos = list(dict.fromkeys(cnpjs))

            # Definir nome base do arquivo
            if not nome_arquivo_saida:
                nome_base = Path(arquivo_csv).stem
                nome_arquivo_saida = f"{nome_base}_cnpjs"
            else:
                # Remove extensão se existir
                nome_arquivo_saida = nome_arquivo_saida.replace('.txt', '')

            # Salvar CNPJs em arquivos
            if cnpjs_por_arquivo and cnpjs_por_arquivo > 0:
                # Dividir em múltiplos arquivos
                total_cnpjs = len(cnpjs_unicos)
                num_arquivos = (total_cnpjs + cnpjs_por_arquivo - 1) // cnpjs_por_arquivo  # Arredonda para cima
                
                self.console.print(f"[blue]Dividindo {total_cnpjs} CNPJs em {num_arquivos} arquivos de {cnpjs_por_arquivo} CNPJs cada...[/blue]")
                
                for i in range(num_arquivos):
                    inicio = i * cnpjs_por_arquivo
                    fim = min((i + 1) * cnpjs_por_arquivo, total_cnpjs)
                    cnpjs_lote = cnpjs_unicos[inicio:fim]
                    
                    # Nome do arquivo com número
                    nome_arquivo = f"{nome_arquivo_saida}_parte_{i+1:03d}.txt"
                    arquivo_saida = os.path.join(pasta_destino, nome_arquivo)
                    
                    # Salvar lote de CNPJs
                    with open(arquivo_saida, 'w', encoding='utf-8') as arquivo:
                        arquivo.write(','.join(cnpjs_lote))
                    
                    self.console.print(f"[green]Arquivo criado: {nome_arquivo} ({len(cnpjs_lote)} CNPJs)[/green]")
                
                self.console.print(f"[green]Extração concluída com sucesso![/green]")
                self.console.print(f"[green]Total de arquivos criados: {num_arquivos}[/green]")
                self.console.print(f"[green]Total de CNPJs extraídos: {total_cnpjs}[/green]")
                self.console.print(f"[green]Total de linhas processadas: {total_linhas}[/green]")
            else:
                # Salvar em um único arquivo
                nome_arquivo = f"{nome_arquivo_saida}.txt"
                arquivo_saida = os.path.join(pasta_destino, nome_arquivo)
                
                # Salvar CNPJs no arquivo .txt separados por vírgula
                with open(arquivo_saida, 'w', encoding='utf-8') as arquivo:
                    arquivo.write(','.join(cnpjs_unicos))

                self.console.print(f"[green]Extração concluída com sucesso![/green]")
                self.console.print(f"[green]Arquivo de saída: {arquivo_saida}[/green]")
                self.console.print(f"[green]Total de CNPJs extraídos: {len(cnpjs_unicos)}[/green]")
                self.console.print(f"[green]Total de linhas processadas: {total_linhas}[/green]")
            
            return True

        except Exception as e:
            self.console.print(f"[red]Erro durante a extração: {e}[/red]")
            return False

    def listar_arquivos_csv(self, diretorio="."):
        """Lista arquivos CSV no diretório"""
        try:
            arquivos_csv = []
            for arquivo in os.listdir(diretorio):
                if arquivo.lower().endswith('.csv'):
                    arquivos_csv.append(arquivo)
            
            if not arquivos_csv:
                self.console.print("[yellow]Nenhum arquivo CSV encontrado no diretório atual![/yellow]")
                return []
            
            return sorted(arquivos_csv)
            
        except Exception as e:
            self.console.print(f"[red]Erro ao listar arquivos: {e}[/red]")
            return []

    def menu_opcoes_divisao(self):
        """Menu com opções pré-definidas de divisão da base por linhas"""
        return inquirer.select(
            message="Selecione como deseja dividir a base:",
            choices=[
                Choice("1", name="1.000 linhas por arquivo"),
                Choice("2", name="5.000 linhas por arquivo"),
                Choice("3", name="10.000 linhas por arquivo"),
                Choice("4", name="30.000 linhas por arquivo"),
                Choice("5", name="100.000 linhas por arquivo"),
                Choice("6", name="150.000 linhas por arquivo"),
                Choice("7", name="200.000 linhas por arquivo"),
                Choice("8", name="250.000 linhas por arquivo"),
                Choice("9", name="500.000 linhas por arquivo"),
                Choice("10", name="Personalizado (informar quantidade)"),
                Choice("11", name="Não dividir (salvar tudo em um arquivo)"),
            ],
        ).execute()

    def obter_quantidade_por_arquivo(self, opcao_selecionada):
        """Converte a opção selecionada em quantidade de linhas por arquivo"""
        opcoes = {
            "1": 1000,
            "2": 5000,
            "3": 10000,
            "4": 30000,
            "5": 100000,
            "6": 150000,
            "7": 200000,
            "8": 250000,
            "9": 500000,
            "10": None,  # Personalizado
            "11": 0,     # Não dividir
        }
        return opcoes.get(opcao_selecionada, 0)

    def menu_extrair_cnpj(self):
        """Menu para extração de CNPJs"""
        return inquirer.select(
            message="Selecione uma operação:",
            choices=[
                Choice("1", name="Extrair CNPJs de arquivo específico"),
                Choice("2", name="Voltar ao menu principal"),
            ],
        ).execute()

    def extrair_arquivo_especifico(self):
        """Extrai CNPJs de um arquivo específico"""
        try:
            # Perguntar se quer usar arquivo do diretório atual ou caminho completo
            opcao_arquivo = inquirer.select(
                message="Como deseja informar o arquivo?",
                choices=[
                    Choice("1", name="Selecionar arquivo do diretório atual"),
                    Choice("2", name="Informar caminho completo do arquivo"),
                ],
            ).execute()

            arquivo_selecionado = None
            
            if opcao_arquivo == "1":
                # Listar arquivos CSV disponíveis
                arquivos_csv = self.listar_arquivos_csv()
                if not arquivos_csv:
                    return

                # Selecionar arquivo
                arquivo_selecionado = inquirer.select(
                    message="Selecione o arquivo CSV:",
                    choices=arquivos_csv,
                ).execute()

                if not arquivo_selecionado:
                    return
            else:
                # Informar caminho completo
                arquivo_selecionado = inquirer.text(
                    message="Informe o caminho completo do arquivo CSV:",
                    default=""
                ).execute()

                if not arquivo_selecionado.strip():
                    self.console.print("[red]Caminho do arquivo não informado![/red]")
                    return

                arquivo_selecionado = arquivo_selecionado.strip()

            # Verificar se o arquivo existe
            if not os.path.exists(arquivo_selecionado):
                self.console.print(f"[red]Arquivo não encontrado: {arquivo_selecionado}[/red]")
                return

            # Ler o arquivo para mostrar as colunas
            encoding = self.detectar_encoding(arquivo_selecionado)
            if not encoding:
                return

            # Detectar delimitador
            with open(arquivo_selecionado, 'r', encoding=encoding) as arquivo:
                primeira_linha = arquivo.readline()
                if ';' in primeira_linha:
                    delimitador = ';'
                elif ',' in primeira_linha:
                    delimitador = ','
                else:
                    delimitador = ','

            # Ler apenas o cabeçalho para mostrar as colunas
            df_colunas = pd.read_csv(arquivo_selecionado, encoding=encoding, delimiter=delimitador, nrows=0)
            colunas = list(df_colunas.columns)

            if not colunas:
                self.console.print("[red]Nenhuma coluna encontrada no arquivo![/red]")
                return

            # Selecionar coluna de CNPJ
            coluna_selecionada = inquirer.select(
                message="Selecione a coluna que contém os CNPJs:",
                choices=colunas,
            ).execute()

            if not coluna_selecionada:
                return

            # Informar pasta de destino
            pasta_destino = inquirer.text(
                message="Informe a pasta onde salvar o arquivo .txt:",
                default="."
            ).execute()

            if not pasta_destino.strip():
                pasta_destino = "."

            pasta_destino = pasta_destino.strip()
            
            # Validar caminho da pasta
            pasta_original = pasta_destino
            
            # Verificar se o caminho começa com padrão inválido
            if pasta_destino.startswith('.C:') or pasta_destino.startswith('.c:'):
                self.console.print(f"[red]Caminho inválido detectado: {pasta_original}[/red]")
                self.console.print("[yellow]Removendo caracteres inválidos do início...[/yellow]")
                pasta_destino = pasta_destino[2:]  # Remove '.C' ou '.c'
            
            # Remove caracteres problemáticos no início
            if pasta_destino.startswith('.') and len(pasta_destino) > 1:
                pasta_destino = pasta_destino[1:]
                if pasta_destino.startswith('\\') or pasta_destino.startswith('/'):
                    pasta_destino = pasta_destino[1:]
            
            # Verificar se o caminho é válido
            try:
                # Testa se é um caminho válido
                pasta_destino = os.path.normpath(pasta_destino)
                
                # Verificar se não tem caracteres inválidos
                if any(char in pasta_destino for char in ['<', '>', '"', '|', '?', '*']):
                    raise ValueError("Caracteres inválidos no caminho")
                    
            except Exception as e:
                self.console.print(f"[red]Caminho inválido: {pasta_original}[/red]")
                self.console.print(f"[red]Erro: {str(e)}[/red]")
                self.console.print("[yellow]Usando diretório atual como padrão.[/yellow]")
                pasta_destino = "."

            # Definir nome do arquivo de saída
            nome_arquivo_saida = inquirer.text(
                message="Nome do arquivo de saída (deixe vazio para usar nome padrão):",
                default=""
            ).execute()

            nome_arquivo_saida = nome_arquivo_saida.strip() if nome_arquivo_saida else None

            # Menu de opções de divisão
            self.console.print(Panel(
                "[bold cyan]Opções de Divisão da Base[/bold cyan]\n\n"
                "Selecione como deseja dividir o arquivo em partes:",
                title="Divisão da Base",
                border_style="blue"
            ))

            opcao_divisao = self.menu_opcoes_divisao()
            cnpjs_por_arquivo = self.obter_quantidade_por_arquivo(opcao_divisao)

            # Se for personalizado, perguntar a quantidade
            if opcao_divisao == "10":
                cnpjs_por_arquivo_input = inquirer.text(
                    message="Quantos CNPJs por arquivo .txt?",
                    default="1000"
                ).execute()

                try:
                    cnpjs_por_arquivo = int(cnpjs_por_arquivo_input.strip())
                    if cnpjs_por_arquivo <= 0:
                        self.console.print("[red]Quantidade deve ser maior que zero! Salvando em um arquivo único.[/red]")
                        cnpjs_por_arquivo = 0
                except ValueError:
                    self.console.print("[red]Valor inválido! Salvando em um arquivo único.[/red]")
                    cnpjs_por_arquivo = 0

            # Se não quiser dividir, definir como None para salvar tudo em um arquivo
            if opcao_divisao == "11" or cnpjs_por_arquivo == 0:
                cnpjs_por_arquivo = None
                self.console.print("[blue]Arquivo será salvo completo em um único arquivo .txt[/blue]")
            else:
                self.console.print(f"[blue]Arquivo será dividido em partes de {cnpjs_por_arquivo:,} CNPJs cada[/blue]")

            # Executar extração
            self.extrair_cnpjs(arquivo_selecionado, coluna_selecionada, pasta_destino, nome_arquivo_saida, cnpjs_por_arquivo)

        except Exception as e:
            self.console.print(f"[red]Erro: {e}[/red]")

    def executar(self):
        """Função principal do extrator de CNPJs"""
        self.console.print(Panel.fit(
            "[bold green]Extrator de CNPJs[/bold green]\n"
            "[italic]Extrai CNPJs de arquivos CSV e salva em arquivo .txt[/italic]\n\n"
            "[bold cyan]✨ Novidade: Opções pré-definidas de divisão da base![/bold cyan]",
            border_style="green"
        ))

        while True:
            opcao = self.menu_extrair_cnpj()
            
            if opcao == "1":
                self.extrair_arquivo_especifico()
            else:
                break 