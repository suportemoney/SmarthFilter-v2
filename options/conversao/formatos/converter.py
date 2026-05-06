#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para conversão de arquivos CSV
"""

import os
import pandas as pd
import chardet
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, track
from pathlib import Path

class Converter:
    def __init__(self):
        self.console = Console()

    def tratar_colunas_numericas(self, df):
        """Trata colunas numéricas que devem permanecer como string (telefones, CPFs, códigos)"""
        df_tratado = df.copy()
        
        # Palavras-chave para identificar colunas que devem ser string
        keywords_string = ['telefone', 'celular', 'fone', 'cpf', 'cnpj', 'codigo', 'cod', 'id']
        
        for coluna in df_tratado.columns:
            coluna_lower = coluna.lower()
            
            # Verifica se a coluna contém alguma das palavras-chave
            if any(keyword in coluna_lower for keyword in keywords_string):
                # Converte para string e remove .0 e 'nan'
                df_tratado[coluna] = df_tratado[coluna].astype(str)
                df_tratado[coluna] = df_tratado[coluna].replace(['nan', 'None', 'NULL'], '')
                df_tratado[coluna] = df_tratado[coluna].str.replace('.0', '', regex=False)
        
        return df_tratado

    def detectar_encoding(self, arquivo_path):
        """Detecta a codificação do arquivo"""
        try:
            with open(arquivo_path, 'rb') as arquivo:
                resultado = chardet.detect(arquivo.read())
                return resultado['encoding']
        except Exception as e:
            self.console.print(f"[red]Erro ao detectar encoding: {e}[/red]")
            return None

    def converter_csv_para_utf8(self, arquivo_entrada, arquivo_saida=None, delimitador_entrada=None):
        """Converte arquivo CSV para UTF-8"""
        try:
            # Detectar encoding original
            encoding_original = self.detectar_encoding(arquivo_entrada)
            if not encoding_original:
                self.console.print(f"[red]Não foi possível detectar o encoding de {arquivo_entrada}[/red]")
                return False

            self.console.print(f"[blue]Encoding detectado: {encoding_original}[/blue]")

            # Tentar detectar delimitador se não foi fornecido
            if not delimitador_entrada:
                with open(arquivo_entrada, 'r', encoding=encoding_original) as arquivo:
                    primeira_linha = arquivo.readline()
                    if ';' in primeira_linha:
                        delimitador_entrada = ';'
                    elif ',' in primeira_linha:
                        delimitador_entrada = ','
                    else:
                        delimitador_entrada = ','

            self.console.print(f"[blue]Delimitador detectado: '{delimitador_entrada}'[/blue]")

            # Ler arquivo com encoding original
            df = pd.read_csv(arquivo_entrada, encoding=encoding_original, delimiter=delimitador_entrada)

            # Definir arquivo de saída se não foi fornecido
            if not arquivo_saida:
                nome_base = Path(arquivo_entrada).stem
                diretorio = Path(arquivo_entrada).parent
                arquivo_saida = diretorio / f"{nome_base}_utf8.csv"

            # Trata colunas numéricas que devem permanecer como string
            df = self.tratar_colunas_numericas(df)
            
            # Salvar em UTF-8 com delimitador ';'
            df.to_csv(arquivo_saida, encoding='utf-8', sep=';', index=False)

            self.console.print(f"[green]Arquivo convertido com sucesso![/green]")
            self.console.print(f"[green]Arquivo de saída: {arquivo_saida}[/green]")
            self.console.print(f"[green]Total de linhas: {len(df)}[/green]")
            
            return True

        except Exception as e:
            self.console.print(f"[red]Erro durante a conversão: {e}[/red]")
            return False

    def listar_arquivos_csv(self, diretorio="."):
        """Lista arquivos CSV no diretório"""
        try:
            arquivos_csv = []
            for arquivo in Path(diretorio).glob("*.csv"):
                if arquivo.is_file():
                    arquivos_csv.append(str(arquivo))
            return arquivos_csv
        except Exception as e:
            self.console.print(f"[red]Erro ao listar arquivos: {e}[/red]")
            return []

    def menu_converter_csv(self):
        """Menu para conversão de CSV"""
        opcoes = [
            "Selecionar arquivo específico",
            "Converter todos os CSV de um diretório",
            "Voltar ao menu principal"
        ]
        
        escolha = inquirer.select(
            message="Como deseja converter?",
            choices=opcoes
        ).execute()

        if escolha == "Selecionar arquivo específico":
            self.converter_arquivo_especifico()
        elif escolha == "Converter todos os CSV de um diretório":
            self.converter_todos_csv()

    def converter_arquivo_especifico(self):
        """Converte um arquivo específico"""
        # Perguntar sobre o diretório
        opcoes_diretorio = [
            "Diretório atual",
            "Escolher outro diretório"
        ]
        
        escolha_diretorio = inquirer.select(
            message="Onde estão os arquivos?",
            choices=opcoes_diretorio
        ).execute()

        if escolha_diretorio == "Diretório atual":
            diretorio = "."
        else:
            diretorio = inquirer.text(
                message="Digite o caminho do diretório:",
                default="."
            ).execute()

        if not os.path.exists(diretorio):
            self.console.print("[red]Diretório não encontrado![/red]")
            return

        # Listar arquivos CSV disponíveis no diretório escolhido
        arquivos_csv = self.listar_arquivos_csv(diretorio)
        
        if not arquivos_csv:
            self.console.print(f"[yellow]Nenhum arquivo CSV encontrado no diretório: {diretorio}[/yellow]")
            return

        # Adicionar opção para digitar caminho manual
        opcoes = arquivos_csv + ["Digitar caminho manual"]
        
        arquivo_escolhido = inquirer.select(
            message="Selecione o arquivo CSV:",
            choices=opcoes
        ).execute()

        if arquivo_escolhido == "Digitar caminho manual":
            arquivo_escolhido = inquirer.text(
                message="Digite o caminho completo do arquivo:"
            ).execute()

        if not os.path.exists(arquivo_escolhido):
            self.console.print("[red]Arquivo não encontrado![/red]")
            return

        # Perguntar sobre delimitador
        delimitador = inquirer.select(
            message="Qual o delimitador do arquivo original?",
            choices=[
                "Auto-detectar",
                "Vírgula (,)",
                "Ponto e vírgula (;)"
            ]
        ).execute()

        delimitador_map = {
            "Auto-detectar": None,
            "Vírgula (,)": ",",
            "Ponto e vírgula (;)": ";"
        }

        self.converter_csv_para_utf8(arquivo_escolhido, delimitador_entrada=delimitador_map[delimitador])

    def converter_todos_csv(self):
        """Converte todos os arquivos CSV do diretório"""
        # Perguntar sobre o diretório
        opcoes_diretorio = [
            "Diretório atual",
            "Escolher outro diretório"
        ]
        
        escolha_diretorio = inquirer.select(
            message="Onde estão os arquivos CSV?",
            choices=opcoes_diretorio
        ).execute()

        if escolha_diretorio == "Diretório atual":
            diretorio = "."
        else:
            diretorio = inquirer.text(
                message="Digite o caminho do diretório:",
                default="."
            ).execute()

        if not os.path.exists(diretorio):
            self.console.print("[red]Diretório não encontrado![/red]")
            return

        # Listar arquivos CSV no diretório escolhido
        arquivos_csv = self.listar_arquivos_csv(diretorio)
        
        if not arquivos_csv:
            self.console.print(f"[yellow]Nenhum arquivo CSV encontrado no diretório: {diretorio}[/yellow]")
            return

        self.console.print(f"[blue]Encontrados {len(arquivos_csv)} arquivos CSV no diretório: {diretorio}[/blue]")
        
        # Mostrar lista dos arquivos encontrados
        self.console.print("[blue]Arquivos encontrados:[/blue]")
        for i, arquivo in enumerate(arquivos_csv, 1):
            nome_arquivo = os.path.basename(arquivo)
            self.console.print(f"  {i}. {nome_arquivo}")
        
        confirmar = inquirer.confirm(
            message="Deseja converter todos estes arquivos?",
            default=False
        ).execute()

        if not confirmar:
            return

        sucessos = 0
        falhas = 0

        for arquivo in track(arquivos_csv, description="Convertendo arquivos..."):
            if self.converter_csv_para_utf8(arquivo):
                sucessos += 1
            else:
                falhas += 1

        self.console.print(f"[green]Conversão concluída![/green]")
        self.console.print(f"[green]Sucessos: {sucessos}[/green]")
        if falhas > 0:
            self.console.print(f"[red]Falhas: {falhas}[/red]")

    def executar(self):
        """Função principal do módulo converter"""
        self.console.print(Panel.fit(
            "[bold blue]Converter Arquivos[/bold blue]\n"
            "[italic]Conversão de CSV para UTF-8[/italic]",
            border_style="blue"
        ))

        opcoes = [
            "Converter CSV para UTF-8",
            "Voltar ao menu principal"
        ]
        
        escolha = inquirer.select(
            message="Selecione uma opção:",
            choices=opcoes
        ).execute()

        if escolha == "Converter CSV para UTF-8":
            self.menu_converter_csv() 