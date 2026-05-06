#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Conversor de TXT para CSV
Converte arquivos .txt em CSV separado por ';'
"""

import os
import pandas as pd
from pathlib import Path
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

class TxtToCsv:
    def __init__(self):
        self.console = Console()

    def executar(self):
        """Função principal do conversor"""
        self.console.print(Panel.fit(
            "[bold green]Conversor TXT para CSV[/bold green]\n"
            "[italic]Converte arquivos .txt em CSV separado por ';'[/italic]",
            border_style="green"
        ))

        # Solicitar caminho da pasta com arquivos .txt
        pasta_origem = inquirer.text(
            message="Digite o caminho da pasta com os arquivos .txt:",
            default="."
        ).execute()

        if not os.path.exists(pasta_origem):
            self.console.print(f"[red]Erro: Pasta '{pasta_origem}' não encontrada![/red]")
            return

        # Solicitar caminho da pasta de destino
        pasta_destino = inquirer.text(
            message="Digite o caminho da pasta onde salvar os arquivos CSV:",
            default="."
        ).execute()

        # Criar pasta de destino se não existir
        os.makedirs(pasta_destino, exist_ok=True)

        # Listar arquivos .txt na pasta de origem
        arquivos_txt = [f for f in os.listdir(pasta_origem) if f.lower().endswith('.txt')]

        if not arquivos_txt:
            self.console.print(f"[yellow]Nenhum arquivo .txt encontrado na pasta '{pasta_origem}'[/yellow]")
            return

        self.console.print(f"[blue]Encontrados {len(arquivos_txt)} arquivos .txt para converter[/blue]")

        # Confirmar conversão
        confirmar = inquirer.confirm(
            message=f"Converter {len(arquivos_txt)} arquivos .txt para CSV?",
            default=True
        ).execute()

        if not confirmar:
            self.console.print("[yellow]Operação cancelada pelo usuário[/yellow]")
            return

        # Converter arquivos
        self.converter_arquivos(pasta_origem, pasta_destino, arquivos_txt)

    def converter_arquivos(self, pasta_origem, pasta_destino, arquivos_txt):
        """Converte todos os arquivos .txt em CSV"""
        sucessos = 0
        erros = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Convertendo arquivos...", total=len(arquivos_txt))

            for arquivo_txt in arquivos_txt:
                try:
                    caminho_txt = os.path.join(pasta_origem, arquivo_txt)
                    nome_base = os.path.splitext(arquivo_txt)[0]
                    caminho_csv = os.path.join(pasta_destino, f"{nome_base}.csv")

                    # Ler arquivo .txt
                    with open(caminho_txt, 'r', encoding='utf-8', errors='ignore') as f:
                        linhas = f.readlines()

                    # Processar linhas e criar DataFrame
                    dados = []
                    for linha in linhas:
                        linha = linha.strip()
                        if linha:  # Ignorar linhas vazias
                            # Dividir por vírgulas e limpar
                            campos = [campo.strip() for campo in linha.split(',') if campo.strip()]
                            if campos:
                                # Adicionar cada CNPJ como uma linha separada
                                for cnpj in campos:
                                    dados.append([cnpj])

                    if dados:
                        # Criar DataFrame com uma única coluna de CNPJs
                        df = pd.DataFrame(dados, columns=['CNPJ'])
                        
                        # Salvar como CSV com separador ';' e sem cabeçalho
                        df.to_csv(caminho_csv, sep=';', index=False, header=False, encoding='utf-8')
                        sucessos += 1
                        
                        progress.update(task, description=f"Convertido: {arquivo_txt}")
                    else:
                        self.console.print(f"[yellow]Arquivo '{arquivo_txt}' está vazio ou não contém dados válidos[/yellow]")
                        erros += 1

                except Exception as e:
                    self.console.print(f"[red]Erro ao converter '{arquivo_txt}': {str(e)}[/red]")
                    erros += 1

                progress.advance(task)

        # Resumo final
        self.console.print(f"\n[bold green]Conversão concluída![/bold green]")
        self.console.print(f"[green]✓ Arquivos convertidos com sucesso: {sucessos}[/green]")
        if erros > 0:
            self.console.print(f"[red]✗ Erros encontrados: {erros}[/red]")
        
        self.console.print(f"[blue]Arquivos CSV salvos em: {pasta_destino}[/blue]")
