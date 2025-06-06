#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Adição e Mesclagem de Dados
Contém classes e métodos para diferentes tipos de adição e mesclagem de dados em arquivos
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
import os
import re

class AddOrMescle:
    def __init__(self):
        self.console = Console()

    def menu_add_or_mescle(self):
        """Menu principal de opções de adição e mesclagem"""
        return inquirer.select(
            message="Selecione o tipo de operação:",
            choices=[
                Choice("1", name="Unir colunas de dois arquivos pelo CPF"),
                Choice("2", name="Voltar ao menu principal"),
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

    def salvar_arquivo(self, df, caminho, prefixo):
        """Salva arquivo CSV com prefixo"""
        nome_arquivo = os.path.basename(caminho)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(os.path.dirname(caminho), f"{prefixo}{nome_base}.csv")
        df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
        return caminho_saida

    def unir_colunas_por_cpf(self):
        """Une colunas de dois arquivos CSV pelo CPF"""
        # Seleciona arquivos
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        arquivo_dados = self.selecionar_arquivo("Selecione o arquivo com dados adicionais:")
        
        # Carrega arquivos
        df_base = self.carregar_arquivo(arquivo_base)
        df_dados = self.carregar_arquivo(arquivo_dados)
        
        # Contagem inicial
        total_linhas_base = len(df_base)
        total_linhas_dados = len(df_dados)
        
        # Seleciona colunas de CPF
        coluna_cpf_base = self.selecionar_coluna(df_base, "Selecione a coluna de CPF do arquivo base:")
        coluna_cpf_dados = self.selecionar_coluna(df_dados, "Selecione a coluna de CPF do arquivo de dados:")
        
        # Formata CPFs
        df_base['cpf_formatado'] = df_base[coluna_cpf_base].apply(self.formatar_cpf)
        df_dados['cpf_formatado'] = df_dados[coluna_cpf_dados].apply(self.formatar_cpf)
        
        # Remove a coluna de CPF do arquivo de dados para evitar duplicação
        colunas_dados = [col for col in df_dados.columns if col != coluna_cpf_dados and col != 'cpf_formatado']
        
        # Realiza o merge
        df_com_corresp = pd.merge(
            df_base,
            df_dados[['cpf_formatado'] + colunas_dados],
            on='cpf_formatado',
            how='inner'
        )
        
        # Identifica CPFs sem correspondência
        cpfs_com_corresp = df_com_corresp['cpf_formatado'].unique()
        df_sem_corresp = df_base[~df_base['cpf_formatado'].isin(cpfs_com_corresp)]
        
        # Remove coluna temporária de CPF formatado
        df_com_corresp = df_com_corresp.drop(columns=['cpf_formatado'])
        df_sem_corresp = df_sem_corresp.drop(columns=['cpf_formatado'])
        
        # Contagem final
        total_linhas_com_corresp = len(df_com_corresp)
        total_linhas_sem_corresp = len(df_sem_corresp)
        
        # Salva arquivos
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos:")
        caminho_com_corresp = self.salvar_arquivo(df_com_corresp, arquivo_base, "comcorresp_")
        caminho_sem_corresp = self.salvar_arquivo(df_sem_corresp, arquivo_base, "semcorresp_")
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Arquivo de Dados:\n"
            f"│  └─ Total de linhas: {total_linhas_dados:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Total de linhas com correspondência: {total_linhas_com_corresp:,}\n"
            f"│  └─ Total de linhas sem correspondência: {total_linhas_sem_corresp:,}\n\n"
            f"Arquivos salvos como:\n"
            f"├─ Com correspondência: {caminho_com_corresp}\n"
            f"└─ Sem correspondência: {caminho_sem_corresp}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de adição e mesclagem"""
        while True:
            opcao = self.menu_add_or_mescle()
            
            if opcao == "1":
                self.unir_colunas_por_cpf()
            else:
                break
