#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Juntar CSV através da coluna CNPJ
Junta arquivos CSV usando CNPJ como chave, criando subpasta 'Cdata' com dados enriquecidos
"""

import os
import pandas as pd
import re
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import chardet

class JuntarCsvCnpj:
    def __init__(self):
        self.console = Console()

    def normalize_cnpj(self, cnpj):
        """Normaliza CNPJ removendo caracteres especiais e mantendo apenas números"""
        if pd.isna(cnpj) or cnpj == '':
            return None
        
        # Converte para string e remove caracteres especiais
        cnpj_str = str(cnpj).strip()
        cnpj_limpo = re.sub(r'[^\d]', '', cnpj_str)
        
        # Verifica se tem 14 dígitos (CNPJ válido)
        if len(cnpj_limpo) == 14:
            return cnpj_limpo
        return None

    def executar(self):
        """Função principal do juntador de CSV"""
        self.console.print(Panel.fit(
            "[bold green]Juntar CSV através da coluna CNPJ[/bold green]\n"
            "[italic]Junta arquivos CSV usando CNPJ como chave de relacionamento[/italic]",
            border_style="green"
        ))

        # Solicitar pasta com arquivos CSV que contêm CNPJs
        pasta_csv_cnpj = inquirer.text(
            message="Digite o caminho da pasta com os arquivos CSV que contêm CNPJs:",
            default="."
        ).execute()

        if not os.path.exists(pasta_csv_cnpj):
            self.console.print(f"[red]Erro: Pasta '{pasta_csv_cnpj}' não encontrada![/red]")
            return

        # Solicitar arquivo CSV com dados de cada CNPJ
        arquivo_dados_cnpj = inquirer.text(
            message="Digite o caminho do arquivo CSV com dados de cada CNPJ:",
            default="."
        ).execute()

        if not os.path.exists(arquivo_dados_cnpj):
            self.console.print(f"[red]Erro: Arquivo '{arquivo_dados_cnpj}' não encontrado![/red]")
            return

        # Listar arquivos CSV na pasta de origem
        arquivos_csv = [f for f in os.listdir(pasta_csv_cnpj) if f.lower().endswith('.csv')]

        if not arquivos_csv:
            self.console.print(f"[yellow]Nenhum arquivo CSV encontrado na pasta '{pasta_csv_cnpj}'[/yellow]")
            return

        self.console.print(f"[blue]Encontrados {len(arquivos_csv)} arquivos CSV para processar[/blue]")

        # Confirmar processamento
        confirmar = inquirer.confirm(
            message=f"Processar {len(arquivos_csv)} arquivos CSV?",
            default=True
        ).execute()

        if not confirmar:
            self.console.print("[yellow]Operação cancelada pelo usuário[/yellow]")
            return

        # Processar arquivos
        self.processar_arquivos(pasta_csv_cnpj, arquivo_dados_cnpj, arquivos_csv)

    def processar_arquivos(self, pasta_csv_cnpj, arquivo_dados_cnpj, arquivos_csv):
        """Processa todos os arquivos CSV"""
        sucessos = 0
        erros = 0

        # Criar pasta Cdata
        pasta_cdata = os.path.join(pasta_csv_cnpj, 'Cdata')
        os.makedirs(pasta_cdata, exist_ok=True)

        # Carregar arquivo de dados de CNPJ
        try:
            self.console.print(f"[blue]Carregando arquivo de dados: {arquivo_dados_cnpj}[/blue]")
            
            # Detectar encoding e delimitador
            encoding = self.detectar_encoding(arquivo_dados_cnpj)
            delimitador = self.detectar_delimitador(arquivo_dados_cnpj)
            
            df_dados = pd.read_csv(arquivo_dados_cnpj, encoding=encoding, delimiter=delimitador)
            
            # Identificar coluna CNPJ
            coluna_cnpj_dados = self.identificar_coluna_cnpj(df_dados)
            if not coluna_cnpj_dados:
                return
            
            # Normalizar CNPJs no arquivo de dados
            df_dados[f'{coluna_cnpj_dados}_normalizado'] = df_dados[coluna_cnpj_dados].apply(self.normalize_cnpj)
            
            # Remover linhas com CNPJs inválidos
            df_dados = df_dados.dropna(subset=[f'{coluna_cnpj_dados}_normalizado'])
            
            self.console.print(f"[green]Arquivo de dados carregado: {len(df_dados)} registros válidos[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Erro ao carregar arquivo de dados: {str(e)}[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Processando arquivos...", total=len(arquivos_csv))

            for arquivo_csv in arquivos_csv:
                try:
                    caminho_csv = os.path.join(pasta_csv_cnpj, arquivo_csv)
                    nome_base = os.path.splitext(arquivo_csv)[0]
                    caminho_saida = os.path.join(pasta_cdata, f"{nome_base}.csv")

                    # Carregar arquivo CSV (sem cabeçalho, apenas uma coluna de CNPJ)
                    encoding = self.detectar_encoding(caminho_csv)
                    delimitador = self.detectar_delimitador(caminho_csv)
                    
                    # Ler arquivo sem cabeçalho e com nome de coluna personalizado
                    df_arquivo = pd.read_csv(caminho_csv, encoding=encoding, delimiter=delimitador, header=None, names=['CNPJ'])
                    
                    # Normalizar CNPJs no arquivo
                    df_arquivo['CNPJ_normalizado'] = df_arquivo['CNPJ'].apply(self.normalize_cnpj)
                    
                    # Remover linhas com CNPJs inválidos
                    df_arquivo = df_arquivo.dropna(subset=['CNPJ_normalizado'])
                    
                    # Fazer merge com dados de CNPJ
                    df_resultado = pd.merge(
                        df_arquivo,
                        df_dados,
                        left_on='CNPJ_normalizado',
                        right_on=f'{coluna_cnpj_dados}_normalizado',
                        how='left'
                    )

                    # Remover colunas de CNPJ normalizado (não são mais necessárias)
                    colunas_para_remover = ['CNPJ_normalizado', f'{coluna_cnpj_dados}_normalizado']
                    for col in colunas_para_remover:
                        if col in df_resultado.columns:
                            df_resultado = df_resultado.drop(columns=[col])

                    # Salvar arquivo resultante com encoding correto
                    df_resultado.to_csv(caminho_saida, sep=';', index=False, encoding='utf-8-sig')
                    
                    sucessos += 1
                    progress.update(task, description=f"Processado: {arquivo_csv}")

                except Exception as e:
                    self.console.print(f"[red]Erro ao processar '{arquivo_csv}': {str(e)}[/red]")
                    erros += 1

                progress.advance(task)

        # Resumo final
        self.console.print(f"\n[bold green]Processamento concluído![/bold green]")
        self.console.print(f"[green]✓ Arquivos processados com sucesso: {sucessos}[/green]")
        if erros > 0:
            self.console.print(f"[red]✗ Erros encontrados: {erros}[/red]")
        
        self.console.print(f"[blue]Arquivos processados salvos em: {pasta_cdata}[/blue]")

    def detectar_encoding(self, arquivo_path):
        """Detecta a codificação do arquivo"""
        try:
            with open(arquivo_path, 'rb') as arquivo:
                resultado = chardet.detect(arquivo.read())
                encoding_detectado = resultado['encoding']
                
                # Se detectou encoding, usar ele
                if encoding_detectado:
                    self.console.print(f"[blue]Encoding detectado: {encoding_detectado}[/blue]")
                    return encoding_detectado
                else:
                    # Se não detectou, tentar encodings comuns
                    encodings_teste = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                    for enc in encodings_teste:
                        try:
                            with open(arquivo_path, 'r', encoding=enc) as f:
                                f.read()
                            self.console.print(f"[blue]Encoding testado com sucesso: {enc}[/blue]")
                            return enc
                        except:
                            continue
                    
                    # Se nada funcionar, usar utf-8
                    self.console.print(f"[yellow]Não foi possível detectar encoding, usando UTF-8[/yellow]")
                    return 'utf-8'
                    
        except Exception as e:
            self.console.print(f"[red]Erro ao detectar encoding: {e}[/red]")
            return 'utf-8'

    def detectar_delimitador(self, arquivo_path):
        """Detecta o delimitador do arquivo CSV"""
        try:
            with open(arquivo_path, 'r', encoding='utf-8', errors='ignore') as arquivo:
                primeira_linha = arquivo.readline()
                if ';' in primeira_linha:
                    return ';'
                elif ',' in primeira_linha:
                    return ','
                else:
                    return ';'
        except Exception:
            return ';'

    def identificar_coluna_cnpj(self, df):
        """Identifica a coluna que contém CNPJs"""
        colunas_cnpj = []
        
        for coluna in df.columns:
            coluna_lower = coluna.lower()
            if 'cnpj' in coluna_lower or 'cpf' in coluna_lower:
                colunas_cnpj.append(coluna)
        
        if len(colunas_cnpj) == 1:
            return colunas_cnpj[0]
        elif len(colunas_cnpj) > 1:
            # Se houver múltiplas colunas, deixar o usuário escolher
            coluna_selecionada = inquirer.select(
                message="Múltiplas colunas CNPJ encontradas. Selecione a principal:",
                choices=colunas_cnpj
            ).execute()
            return coluna_selecionada
        else:
            # Se não encontrar, mostrar todas as colunas para seleção
            self.console.print("[yellow]Nenhuma coluna CNPJ encontrada automaticamente.[/yellow]")
            self.console.print(f"[blue]Colunas disponíveis: {list(df.columns)}[/blue]")
            
            coluna_selecionada = inquirer.select(
                message="Selecione a coluna que contém os CNPJs:",
                choices=list(df.columns)
            ).execute()
            return coluna_selecionada
