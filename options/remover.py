#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Remoção de Dados
Contém classes e métodos para diferentes tipos de remoção de dados em arquivos
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
import os
import re

class Remover:
    def __init__(self):
        self.console = Console()

    def menu_remover(self):
        """Menu principal de opções de remoção"""
        return inquirer.select(
            message="Selecione o tipo de remoção:",
            choices=[
                Choice("1", name="Remover duplicatas de CPFs"),
                Choice("2", name="Remover CPFs da Blacklist"),
                Choice("3", name="Remover Números da Blacklist"),
                Choice("4", name="Voltar ao menu principal"),
            ],
        ).execute()

    def formatar_cpf(self, cpf):
        """Formata CPF para o padrão 00000000000"""
        if pd.isna(cpf):
            return None
        cpf = str(cpf)
        # Remove tudo que não for número
        cpf = re.sub(r'\D', '', cpf)
        # Garante que tenha 11 dígitos
        return cpf.zfill(11)

    def selecionar_coluna(self, df, mensagem):
        """Permite ao usuário selecionar uma coluna do DataFrame"""
        colunas = list(df.columns)
        return inquirer.select(
            message=mensagem,
            choices=colunas,
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

    def salvar_arquivo(self, df, caminho, prefixo, pasta_saida=None):
        """Salva arquivo CSV com prefixo"""
        nome_arquivo = os.path.basename(caminho)
        nome_base = os.path.splitext(nome_arquivo)[0]
        pasta_para_salvar = pasta_saida if pasta_saida else os.path.dirname(caminho)
        caminho_saida = os.path.join(pasta_para_salvar, f"{prefixo}{nome_base}.csv")
        
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
                    pasta_para_salvar = nova_pasta
                    caminho_saida = os.path.join(pasta_para_salvar, f"{prefixo}{nome_base}.csv")
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro inesperado ao salvar arquivo:[/red]\n\n"
                    f"Erro: {str(e)}\n\n"
                    f"[cyan]Por favor, tente escolher uma nova pasta.[/cyan]",
                    title="Erro",
                    border_style="red"
                ))
                
                nova_pasta = self.selecionar_pasta_saida("Selecione uma nova pasta para salvar o arquivo:")
                pasta_para_salvar = nova_pasta
                caminho_saida = os.path.join(pasta_para_salvar, f"{prefixo}{nome_base}.csv")

    def remover_duplicatas_cpf(self):
        """Remove duplicatas de CPFs"""
        arquivo = self.selecionar_arquivo("Selecione o arquivo com CPFs:")
        df = self.carregar_arquivo(arquivo)
        
        # Contagem inicial
        total_linhas_inicial = len(df)
        
        coluna_cpf = self.selecionar_coluna(df, "Selecione a coluna de CPF:")
        
        # Formata CPFs
        df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
        
        # Contagem de CPFs únicos
        total_cpfs_unicos = df['cpf_formatado'].nunique()
        
        # Remove duplicatas mantendo a primeira ocorrência
        df_sem_duplicatas = df.drop_duplicates(subset=['cpf_formatado'], keep='first')
        df_sem_duplicatas = df_sem_duplicatas.drop(columns=['cpf_formatado'])
        
        # Contagem final
        total_linhas_final = len(df_sem_duplicatas)
        total_duplicatas = total_linhas_inicial - total_linhas_final
        
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        caminho_saida = self.salvar_arquivo(df_sem_duplicatas, arquivo, "filter_cpf_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Total de linhas no arquivo original: {total_linhas_inicial:,}\n"
            f"├─ Total de CPFs únicos encontrados: {total_cpfs_unicos:,}\n"
            f"├─ Total de duplicatas removidas: {total_duplicatas:,}\n"
            f"└─ Total de linhas no arquivo final: {total_linhas_final:,}\n\n"
            f"Arquivo salvo como: {caminho_saida}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def remover_cpfs_blacklist(self):
        """Remove CPFs que estão na blacklist"""
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        arquivo_blacklist = self.selecionar_arquivo("Selecione o arquivo blacklist:")
        
        df_base = self.carregar_arquivo(arquivo_base)
        df_blacklist = self.carregar_arquivo(arquivo_blacklist)
        
        # Contagem inicial
        total_linhas_base = len(df_base)
        total_linhas_blacklist = len(df_blacklist)
        
        coluna_cpf_base = self.selecionar_coluna(df_base, "Selecione a coluna de CPF do arquivo base:")
        coluna_cpf_blacklist = self.selecionar_coluna(df_blacklist, "Selecione a coluna de CPF da blacklist:")
        
        # Formata CPFs
        df_base['cpf_formatado'] = df_base[coluna_cpf_base].apply(self.formatar_cpf)
        df_blacklist['cpf_formatado'] = df_blacklist[coluna_cpf_blacklist].apply(self.formatar_cpf)
        
        # Remove CPFs da blacklist
        df_whitelist = df_base[~df_base['cpf_formatado'].isin(df_blacklist['cpf_formatado'])]
        df_blacklist_result = df_base[df_base['cpf_formatado'].isin(df_blacklist['cpf_formatado'])]
        
        # Remove coluna temporária
        df_whitelist = df_whitelist.drop(columns=['cpf_formatado'])
        df_blacklist_result = df_blacklist_result.drop(columns=['cpf_formatado'])
        
        # Contagem final
        total_linhas_whitelist = len(df_whitelist)
        total_linhas_blacklist_result = len(df_blacklist_result)
        
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos:")
        caminho_whitelist = self.salvar_arquivo(df_whitelist, arquivo_base, "whitelist_", pasta_saida)
        caminho_blacklist = self.salvar_arquivo(df_blacklist_result, arquivo_base, "blacklist_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Arquivo Blacklist:\n"
            f"│  └─ Total de linhas: {total_linhas_blacklist:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Total de linhas na Whitelist: {total_linhas_whitelist:,}\n"
            f"│  └─ Total de linhas na Blacklist: {total_linhas_blacklist_result:,}\n\n"
            f"Arquivos salvos como:\n"
            f"├─ Whitelist: {caminho_whitelist}\n"
            f"└─ Blacklist: {caminho_blacklist}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def remover_numeros_blacklist(self):
        """Remove números da blacklist por CPF"""
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        arquivo_blacklist = self.selecionar_arquivo("Selecione o arquivo blacklist:")
        
        df_base = self.carregar_arquivo(arquivo_base)
        df_blacklist = self.carregar_arquivo(arquivo_blacklist)
        
        # Contagem inicial
        total_linhas_base = len(df_base)
        total_linhas_blacklist = len(df_blacklist)
        
        coluna_cpf_base = self.selecionar_coluna(df_base, "Selecione a coluna de CPF do arquivo base:")
        coluna_numero_base = self.selecionar_coluna(df_base, "Selecione a coluna de número do arquivo base:")
        coluna_cpf_blacklist = self.selecionar_coluna(df_blacklist, "Selecione a coluna de CPF da blacklist:")
        coluna_numero_blacklist = self.selecionar_coluna(df_blacklist, "Selecione a coluna de número da blacklist:")
        
        # Formata CPFs
        df_base['cpf_formatado'] = df_base[coluna_cpf_base].apply(self.formatar_cpf)
        df_blacklist['cpf_formatado'] = df_blacklist[coluna_cpf_blacklist].apply(self.formatar_cpf)
        
        # Cria uma cópia do DataFrame base
        df_resultado = df_base.copy()
        
        # Contador de números substituídos
        total_substituidos = 0
        
        # Para cada linha na blacklist
        for _, row in df_blacklist.iterrows():
            # Encontra todas as linhas no arquivo base com o mesmo CPF
            mask = df_resultado['cpf_formatado'] == row['cpf_formatado']
            # Se o número também for igual, substitui por '-'
            mask_numero = df_resultado[coluna_numero_base] == row[coluna_numero_blacklist]
            total_substituidos += mask_numero.sum()
            df_resultado.loc[mask & mask_numero, coluna_numero_base] = '-'
        
        # Remove coluna temporária
        df_resultado = df_resultado.drop(columns=['cpf_formatado'])
        
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        caminho_saida = self.salvar_arquivo(df_resultado, arquivo_base, "blacklist_num_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Arquivo Blacklist:\n"
            f"│  └─ Total de linhas: {total_linhas_blacklist:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Total de números substituídos: {total_substituidos:,}\n"
            f"│  └─ Total de linhas no arquivo final: {len(df_resultado):,}\n\n"
            f"Arquivo salvo como: {caminho_saida}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de remoção"""
        while True:
            opcao = self.menu_remover()
            
            if opcao == "1":
                self.remover_duplicatas_cpf()
            elif opcao == "2":
                self.remover_cpfs_blacklist()
            elif opcao == "3":
                self.remover_numeros_blacklist()
            else:
                break
