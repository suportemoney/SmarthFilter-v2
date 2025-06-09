#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Filtros
Contém classes e métodos para diferentes tipos de filtros e divisões de arquivos
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
import os
import math

class Filters:
    def __init__(self):
        self.console = Console()

    def menu_filters(self):
        """Menu principal de opções de filtros"""
        return inquirer.select(
            message="Selecione o tipo de filtro:",
            choices=[
                Choice("1", name="Dividir arquivo em partes"),
                Choice("2", name="Voltar ao menu principal"),
            ],
        ).execute()

    def selecionar_arquivo(self, mensagem):
        """Permite ao usuário selecionar um arquivo"""
        return inquirer.filepath(
            message=mensagem,
            validate=lambda x: x.endswith(('.xlsx', '.csv')),
            filter=lambda x: x.strip(),
        ).execute()

    def selecionar_pasta_saida(self, mensagem):
        """Permite ao usuário selecionar uma pasta para salvar"""
        return inquirer.filepath(
            message=mensagem,
            filter=lambda x: x.strip(),
        ).execute()

    def carregar_arquivo(self, caminho):
        """Carrega arquivo CSV ou XLSX"""
        if caminho.endswith('.xlsx'):
            return pd.read_excel(caminho)
        else:
            try:
                return pd.read_csv(caminho, sep=';', encoding='utf-8')
            except:
                return pd.read_csv(caminho, sep=',', encoding='utf-8')

    def salvar_arquivo(self, df, caminho, prefixo, indice, pasta_saida):
        """Salva arquivo CSV com prefixo e índice"""
        nome_arquivo = os.path.basename(caminho)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{indice}_{nome_base}.csv")
        
        while True:
            try:
                df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                return caminho_saida
            except PermissionError:
                self.console.print(Panel(
                    f"[red]Erro de Permissão![/red]\n\n"
                    f"Não foi possível salvar o arquivo:\n"
                    f"{caminho_saida}\n\n"
                    f"[yellow]Possíveis causas:[/yellow]\n"
                    f"• O arquivo está aberto no Excel ou outro programa\n"
                    f"• Sem permissão de escrita na pasta\n"
                    f"• Arquivo protegido contra escrita\n\n"
                    f"[cyan]Por favor:[/cyan]\n"
                    f"1. Feche todos os arquivos relacionados\n"
                    f"2. Verifique as permissões da pasta\n"
                    f"3. Tente novamente",
                    title="Erro de Permissão",
                    border_style="red"
                ))
                
                # Pergunta se quer tentar novamente ou escolher nova pasta
                opcao = inquirer.select(
                    message="O que deseja fazer?",
                    choices=[
                        Choice("1", name="Tentar salvar novamente no mesmo local"),
                        Choice("2", name="Escolher nova pasta para salvar"),
                    ],
                ).execute()
                
                if opcao == "2":
                    nova_pasta = self.selecionar_pasta_saida("Selecione uma nova pasta para salvar o arquivo:")
                    pasta_saida = nova_pasta
                    caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{indice}_{nome_base}.csv")
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro inesperado ao salvar arquivo:[/red]\n\n"
                    f"Erro: {str(e)}\n\n"
                    f"[cyan]Por favor, tente escolher uma nova pasta.[/cyan]",
                    title="Erro",
                    border_style="red"
                ))
                
                nova_pasta = self.selecionar_pasta_saida("Selecione uma nova pasta para salvar o arquivo:")
                pasta_saida = nova_pasta
                caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{indice}_{nome_base}.csv")

    def dividir_arquivo(self):
        """Divide um arquivo em partes de tamanho específico"""
        # Seleciona arquivo
        arquivo = self.selecionar_arquivo("Selecione o arquivo para dividir:")
        
        # Carrega arquivo
        df = self.carregar_arquivo(arquivo)
        total_linhas = len(df)
        
        # Seleciona tamanho das partes
        tamanho_parte = inquirer.select(
            message="Selecione o tamanho de cada parte:",
            choices=[
                Choice(5000, name="5.000 linhas"),
                Choice(10000, name="10.000 linhas"),
                Choice(30000, name="30.000 linhas"),
                Choice(100000, name="100.000 linhas"),
            ],
        ).execute()
        
        # Calcula número de partes
        num_partes = math.ceil(total_linhas / tamanho_parte)
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos:")
        
        # Divide e salva as partes
        arquivos_salvos = []
        for i in range(num_partes):
            inicio = i * tamanho_parte
            fim = min((i + 1) * tamanho_parte, total_linhas)
            df_parte = df.iloc[inicio:fim]
            
            caminho_saida = self.salvar_arquivo(
                df_parte, 
                arquivo, 
                f"{tamanho_parte//1000}k", 
                i + 1,
                pasta_saida
            )
            arquivos_salvos.append(caminho_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Original:\n"
            f"│  └─ Total de linhas: {total_linhas:,}\n"
            f"├─ Configuração:\n"
            f"│  └─ Tamanho de cada parte: {tamanho_parte:,} linhas\n"
            f"├─ Resultados:\n"
            f"│  ├─ Total de partes geradas: {num_partes}\n"
            f"│  └─ Tamanho da última parte: {len(df.iloc[(num_partes-1)*tamanho_parte:]):,} linhas\n\n"
            f"Arquivos salvos como:\n"
        )
        
        # Adiciona lista de arquivos salvos
        for i, caminho in enumerate(arquivos_salvos, 1):
            prefixo = "└─" if i == len(arquivos_salvos) else "├─"
            mensagem += f"{prefixo} Parte {i}: {caminho}\n"
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de filtros"""
        while True:
            opcao = self.menu_filters()
            
            if opcao == "1":
                self.dividir_arquivo()
            else:
                break
