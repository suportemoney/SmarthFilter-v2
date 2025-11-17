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

    def menu_add_or_mescle(self):
        """Menu principal de opções de adição e mesclagem"""
        return inquirer.select(
            message="Selecione o tipo de operação:",
            choices=[
                Choice("1", name="Unir colunas de dois arquivos pelo CPF"),
                Choice("2", name="Adicionar dados em lote por pasta (com/sem correspondência)"),
                Choice("3", name="Mesclar arquivos CSV de uma pasta em um único arquivo"),
                Choice("4", name="Adicionar coluna personalizada com valor específico"),
                Choice("5", name="Adicionar coluna personalizada em lote por pasta"),
                Choice("6", name="Voltar ao menu principal"),
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

    def selecionar_pasta_entrada(self, mensagem):
        """Permite ao usuário selecionar uma pasta de entrada"""
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
                # Trata colunas numéricas que devem permanecer como string
                df = self.tratar_colunas_numericas(df)
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
        caminho_com_corresp = self.salvar_arquivo(df_com_corresp, arquivo_base, "comcorresp_", pasta_saida)
        caminho_sem_corresp = self.salvar_arquivo(df_sem_corresp, arquivo_base, "semcorresp_", pasta_saida)
        
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

    def adicionar_dados_lote(self):
        """Adiciona dados em lote para todos os arquivos CSV de uma pasta"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        
        # Seleciona arquivo com dados adicionais
        arquivo_dados = self.selecionar_arquivo("Selecione o arquivo com dados adicionais:")
        
        # Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos processados:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para processar:[/cyan]\n" + 
            "\n".join([f"• {arquivo}" for arquivo in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))
        
        # Carrega arquivo de dados adicionais
        df_dados = self.carregar_arquivo(arquivo_dados)
        
        # Remove duplicatas do arquivo de dados adicionais
        coluna_cpf_dados = self.selecionar_coluna(df_dados, f"Selecione a coluna de CPF do arquivo de dados adicionais:")
        df_dados['cpf_formatado'] = df_dados[coluna_cpf_dados].apply(self.formatar_cpf)
        df_dados = df_dados.drop_duplicates(subset=['cpf_formatado'], keep='first')
        
        # Remove a coluna de CPF do arquivo de dados para evitar duplicação
        colunas_dados = [col for col in df_dados.columns if col != coluna_cpf_dados and col != 'cpf_formatado']
        
        # Estatísticas gerais
        total_arquivos_processados = 0
        total_linhas_com_corresp = 0
        total_linhas_sem_corresp = 0
        arquivos_com_erro = []
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df_base = self.carregar_arquivo(caminho_arquivo)
                
                # Contagem inicial
                linhas_inicial = len(df_base)
                
                # Seleciona coluna de CPF do arquivo base
                coluna_cpf_base = self.selecionar_coluna(df_base, f"Selecione a coluna de CPF (baseado no arquivo {arquivo}):")
                
                # Verifica se a coluna existe
                if coluna_cpf_base not in df_base.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_cpf_base}' não encontrada")
                    continue
                
                # Formata CPFs do arquivo base
                df_base['cpf_formatado'] = df_base[coluna_cpf_base].apply(self.formatar_cpf)
                
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
                linhas_com_corresp = len(df_com_corresp)
                linhas_sem_corresp = len(df_sem_corresp)
                
                total_linhas_com_corresp += linhas_com_corresp
                total_linhas_sem_corresp += linhas_sem_corresp
                
                # Salva arquivos processados
                nome_base = os.path.splitext(arquivo)[0]
                
                # Arquivo com correspondência
                caminho_com = os.path.join(pasta_saida, f"com_{nome_base}.csv")
                df_com_corresp = self.tratar_colunas_numericas(df_com_corresp.copy())
                df_com_corresp.to_csv(caminho_com, sep=';', encoding='utf-8', index=False)
                
                # Arquivo sem correspondência
                caminho_sem = os.path.join(pasta_saida, f"sem_{nome_base}.csv")
                df_sem_corresp = self.tratar_colunas_numericas(df_sem_corresp.copy())
                df_sem_corresp.to_csv(caminho_sem, sep=';', encoding='utf-8', index=False)
                
                total_arquivos_processados += 1
                
                # Mostra progresso
                self.console.print(f"[green]✓[/green] {arquivo}: {linhas_inicial:,} → com: {linhas_com_corresp:,}, sem: {linhas_sem_corresp:,}")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        # Cria mensagem final detalhada
        mensagem = (
            f"Estatísticas do Processamento em Lote:\n"
            f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
            f"├─ Total de arquivos processados: {total_arquivos_processados:,}\n"
            f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
            f"├─ Total de linhas com correspondência: {total_linhas_com_corresp:,}\n"
            f"└─ Total de linhas sem correspondência: {total_linhas_sem_corresp:,}\n\n"
            f"Pasta de saída: {pasta_saida}\n\n"
            f"[cyan]Arquivos gerados:[/cyan]\n"
            f"• com_[nome_arquivo].csv - CPFs encontrados no arquivo de dados\n"
            f"• sem_[nome_arquivo].csv - CPFs não encontrados no arquivo de dados"
        )
        
        if arquivos_com_erro:
            mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído",
            border_style="green"
        ))

    def mesclar_arquivos_csv(self):
        """Mescla múltiplos arquivos CSV de uma pasta em um único arquivo"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        
        # Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo mesclado:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para mesclar:[/cyan]\n" + 
            "\n".join([f"• {arquivo}" for arquivo in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))
        
        # Coleta todas as colunas únicas de todos os arquivos
        todas_colunas = set()
        colunas_ordenadas = []  # Lista para manter a ordem das colunas
        arquivos_com_erro = []
        total_linhas = 0
        
        # Primeira passagem: identificar todas as colunas únicas mantendo a ordem
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df_temp = self.carregar_arquivo(caminho_arquivo)
                
                # Adiciona colunas na ordem que aparecem no arquivo
                for coluna in df_temp.columns:
                    if coluna not in todas_colunas:
                        todas_colunas.add(coluna)
                        colunas_ordenadas.append(coluna)
                
                total_linhas += len(df_temp)
                self.console.print(f"[blue]📋[/blue] {arquivo}: {len(df_temp.columns)} colunas, {len(df_temp):,} linhas")
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro ao ler: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao ler arquivo")
        
        # Usa a lista ordenada em vez de ordenar alfabeticamente
        todas_colunas = colunas_ordenadas
        
        self.console.print(Panel(
            f"[yellow]Colunas únicas encontradas ({len(todas_colunas)}):[/yellow]\n" + 
            "\n".join([f"• {coluna}" for coluna in todas_colunas]),
            title="Colunas Identificadas",
            border_style="yellow"
        ))
        
        # Lista para armazenar todos os DataFrames processados
        dataframes_mesclados = []
        arquivos_processados = 0
        
        # Segunda passagem: processar cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo(caminho_arquivo)
                
                # Cria um DataFrame com todas as colunas, preenchendo com valores vazios
                df_mesclado = pd.DataFrame(columns=todas_colunas)
                
                # Copia os dados existentes
                for coluna in df.columns:
                    if coluna in todas_colunas:
                        df_mesclado[coluna] = df[coluna]
                
                # Preenche colunas ausentes com valores vazios
                for coluna in todas_colunas:
                    if coluna not in df.columns:
                        df_mesclado[coluna] = ''
                
                dataframes_mesclados.append(df_mesclado)
                arquivos_processados += 1
                
                self.console.print(f"[green]✓[/green] {arquivo}: {len(df):,} linhas processadas")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro ao processar: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        if not dataframes_mesclados:
            self.console.print(Panel(
                "[red]Nenhum arquivo foi processado com sucesso![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Concatena todos os DataFrames
        df_final = pd.concat(dataframes_mesclados, ignore_index=True)
        
        # Trata colunas numéricas
        df_final = self.tratar_colunas_numericas(df_final.copy())
        
        # Salva arquivo mesclado
        nome_arquivo_saida = "arquivo_mesclado.csv"
        caminho_saida = os.path.join(pasta_saida, nome_arquivo_saida)
        
        try:
            df_final.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            # Cria mensagem final detalhada
            mensagem = (
                f"Estatísticas da Mesclagem:\n"
                f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
                f"├─ Total de arquivos processados: {arquivos_processados:,}\n"
                f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
                f"├─ Total de colunas únicas: {len(todas_colunas):,}\n"
                f"├─ Total de linhas no arquivo final: {len(df_final):,}\n\n"
                f"Arquivo salvo como: {caminho_saida}\n\n"
                f"[cyan]Colunas no arquivo final:[/cyan]\n" + 
                "\n".join([f"• {coluna}" for coluna in todas_colunas])
            )
            
            if arquivos_com_erro:
                mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
            
            self.console.print(Panel(
                mensagem,
                title="Mesclagem Concluída",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo mesclado:[/red]\n\n"
                f"Erro: {str(e)}\n\n"
                f"[cyan]Verifique as permissões da pasta de destino.[/cyan]",
                title="Erro",
                border_style="red"
                         ))

    def adicionar_coluna_personalizada(self):
        """Adiciona uma coluna personalizada com valor específico baseado em CPF"""
        # Seleciona arquivo base
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        
        # Carrega arquivo
        df = self.carregar_arquivo(arquivo_base)
        
        # Contagem inicial
        total_linhas = len(df)
        
        # Seleciona coluna de CPF
        coluna_cpf = self.selecionar_coluna(df, "Selecione a coluna de CPF:")
        
        # Solicita nome da nova coluna
        nome_coluna = inquirer.text(
            message="Digite o nome da nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Solicita valor a ser adicionado
        valor_coluna = inquirer.text(
            message="Digite o valor/string a ser adicionado na nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Formata CPFs para comparação
        df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
        
        # Adiciona a nova coluna com o valor especificado
        df[nome_coluna] = valor_coluna
        
        # Remove coluna temporária
        df = df.drop(columns=['cpf_formatado'])
        
        # Trata colunas numéricas
        df = self.tratar_colunas_numericas(df.copy())
        
        # Salva arquivo
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        caminho_saida = self.salvar_arquivo(df, arquivo_base, "coluna_adicionada_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Total de linhas processadas: {total_linhas:,}\n"
            f"├─ Nova coluna adicionada: '{nome_coluna}'\n"
            f"├─ Valor adicionado: '{valor_coluna}'\n"
            f"└─ Total de colunas no arquivo final: {len(df.columns):,}\n\n"
            f"Arquivo salvo como: {caminho_saida}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def adicionar_coluna_personalizada_lote(self):
        """Adiciona uma coluna personalizada em lote para todos os arquivos CSV de uma pasta"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        
        # Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos processados:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para processar:[/cyan]\n" + 
            "\n".join([f"• {arquivo}" for arquivo in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))
        
        # Solicita nome da nova coluna
        nome_coluna = inquirer.text(
            message="Digite o nome da nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Solicita valor a ser adicionado
        valor_coluna = inquirer.text(
            message="Digite o valor/string a ser adicionado na nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Estatísticas gerais
        total_arquivos_processados = 0
        total_linhas_processadas = 0
        arquivos_com_erro = []
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo(caminho_arquivo)
                
                # Contagem inicial
                linhas_inicial = len(df)
                
                # Seleciona coluna de CPF
                coluna_cpf = self.selecionar_coluna(df, f"Selecione a coluna de CPF (baseado no arquivo {arquivo}):")
                
                # Verifica se a coluna existe
                if coluna_cpf not in df.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_cpf}' não encontrada")
                    continue
                
                # Formata CPFs para comparação
                df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
                
                # Adiciona a nova coluna com o valor especificado
                df[nome_coluna] = valor_coluna
                
                # Remove coluna temporária
                df = df.drop(columns=['cpf_formatado'])
                
                # Trata colunas numéricas
                df = self.tratar_colunas_numericas(df.copy())
                
                # Salva arquivo processado
                nome_base = os.path.splitext(arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"coluna_adicionada_{nome_base}.csv")
                df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                
                total_arquivos_processados += 1
                total_linhas_processadas += linhas_inicial
                
                # Mostra progresso
                self.console.print(f"[green]✓[/green] {arquivo}: {linhas_inicial:,} linhas processadas")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        # Cria mensagem final detalhada
        mensagem = (
            f"Estatísticas do Processamento em Lote:\n"
            f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
            f"├─ Total de arquivos processados: {total_arquivos_processados:,}\n"
            f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
            f"├─ Total de linhas processadas: {total_linhas_processadas:,}\n"
            f"├─ Nova coluna adicionada: '{nome_coluna}'\n"
            f"└─ Valor adicionado: '{valor_coluna}'\n\n"
            f"Pasta de saída: {pasta_saida}"
        )
        
        if arquivos_com_erro:
            mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de adição e mesclagem"""
        while True:
            opcao = self.menu_add_or_mescle()
            
            if opcao == "1":
                self.unir_colunas_por_cpf()
            elif opcao == "2":
                self.adicionar_dados_lote()
            elif opcao == "3":
                self.mesclar_arquivos_csv()
            elif opcao == "4":
                self.adicionar_coluna_personalizada()
            elif opcao == "5":
                self.adicionar_coluna_personalizada_lote()
            else:
                break
