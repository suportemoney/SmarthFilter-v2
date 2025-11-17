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

    def tratar_colunas_numericas(self, df):
        """Trata colunas numéricas que devem permanecer como string (telefones, CPFs, etc.)"""
        # Lista de padrões de colunas que devem permanecer como string
        padroes_string = [
            'telefone', 'fone', 'phone', 'celular', 'mobile',
            'cpf', 'cnpj', 'rg', 'cep', 'codigo', 'code',
            'numero', 'num', 'id', 'identificador'
        ]
        
        for coluna in df.columns:
            coluna_lower = coluna.lower()
            
            # Verifica se a coluna deve ser tratada como string
            deve_ser_string = any(padrao in coluna_lower for padrao in padroes_string)
            
            if deve_ser_string:
                # Converte para string e remove .0 desnecessários
                df[coluna] = df[coluna].astype(str).str.replace('.0', '', regex=False)
                # Remove 'nan' strings e substitui por vazio
                df[coluna] = df[coluna].replace('nan', '', regex=False)
        
        return df

    def menu_remover(self):
        """Menu principal de opções de remoção"""
        return inquirer.select(
            message="Selecione o tipo de remoção:",
            choices=[
                Choice("1", name="Remover duplicatas de CPFs"),
                Choice("2", name="Remover duplicatas de CPFs em lote por pasta"),
                Choice("3", name="Remover duplicatas de CPFs em lote por pasta (manter maior valor)"),
                Choice("4", name="Remover CPFs da Blacklist"),
                Choice("5", name="Remover Números da Blacklist"),
                Choice("6", name="Remover em lote (por pasta) números da blacklist"),
                Choice("7", name="Remover linhas por números de celular da blacklist"),
                Choice("8", name="Voltar ao menu principal"),
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

    def formatar_numero_celular(self, numero):
        """Formata número de celular removendo caracteres especiais"""
        if pd.isna(numero):
            return None
        numero = str(numero)
        # Remove tudo que não for número
        numero = re.sub(r'\D', '', numero)
        return numero

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
                df = self.tratar_colunas_numericas(df.copy())
                
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

    def remover_duplicatas_cpf_lote(self):
        """Remove duplicatas de CPFs em todos os arquivos CSV de uma pasta"""
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
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
        
        # Pergunta qual coluna de CPF usar (assumindo que todos os arquivos têm a mesma estrutura)
        primeiro_arquivo = os.path.join(pasta_entrada, arquivos_csv[0])
        df_exemplo = self.carregar_arquivo(primeiro_arquivo)
        coluna_cpf = self.selecionar_coluna(df_exemplo, f"Selecione a coluna de CPF (baseado no arquivo {arquivos_csv[0]}):")
        
        # Estatísticas gerais
        total_arquivos_processados = 0
        total_linhas_inicial = 0
        total_linhas_final = 0
        total_duplicatas_removidas = 0
        arquivos_com_erro = []
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo(caminho_arquivo)
                
                # Contagem inicial
                linhas_inicial = len(df)
                total_linhas_inicial += linhas_inicial
                
                # Verifica se a coluna existe
                if coluna_cpf not in df.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_cpf}' não encontrada")
                    continue
                
                # Formata CPFs
                df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
                
                # Remove duplicatas mantendo a primeira ocorrência
                df_sem_duplicatas = df.drop_duplicates(subset=['cpf_formatado'], keep='first')
                df_sem_duplicatas = df_sem_duplicatas.drop(columns=['cpf_formatado'])
                
                # Contagem final
                linhas_final = len(df_sem_duplicatas)
                duplicatas_removidas = linhas_inicial - linhas_final
                
                total_linhas_final += linhas_final
                total_duplicatas_removidas += duplicatas_removidas
                
                # Salva arquivo processado
                nome_base = os.path.splitext(arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"filter_cpf_{nome_base}.csv")
                
                # Trata colunas numéricas que devem permanecer como string
                df_sem_duplicatas = self.tratar_colunas_numericas(df_sem_duplicatas.copy())
                
                df_sem_duplicatas.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                total_arquivos_processados += 1
                
                # Mostra progresso
                self.console.print(f"[green]✓[/green] {arquivo}: {linhas_inicial:,} → {linhas_final:,} linhas (-{duplicatas_removidas:,} duplicatas)")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        # Cria mensagem final detalhada
        mensagem = (
            f"Estatísticas do Processamento em Lote:\n"
            f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
            f"├─ Total de arquivos processados: {total_arquivos_processados:,}\n"
            f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
            f"├─ Total de linhas processadas: {total_linhas_inicial:,}\n"
            f"├─ Total de duplicatas removidas: {total_duplicatas_removidas:,}\n"
            f"└─ Total de linhas finais: {total_linhas_final:,}\n\n"
            f"Pasta de saída: {pasta_saida}"
        )
        
        if arquivos_com_erro:
            mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído",
            border_style="green"
        ))

    def remover_duplicatas_cpf_lote_maior_valor(self):
        """Remove duplicatas de CPFs em todos os arquivos CSV de uma pasta, mantendo o registro com maior valor"""
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
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
        
        # Pergunta qual coluna de CPF usar (assumindo que todos os arquivos têm a mesma estrutura)
        primeiro_arquivo = os.path.join(pasta_entrada, arquivos_csv[0])
        df_exemplo = self.carregar_arquivo(primeiro_arquivo)
        coluna_cpf = self.selecionar_coluna(df_exemplo, f"Selecione a coluna de CPF (baseado no arquivo {arquivos_csv[0]}):")
        coluna_valor = self.selecionar_coluna(df_exemplo, f"Selecione a coluna de valor (ex: Valor_Parcela) (baseado no arquivo {arquivos_csv[0]}):")
        
        # Estatísticas gerais
        total_arquivos_processados = 0
        total_linhas_inicial = 0
        total_linhas_final = 0
        total_duplicatas_removidas = 0
        arquivos_com_erro = []
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo(caminho_arquivo)
                
                # Contagem inicial
                linhas_inicial = len(df)
                total_linhas_inicial += linhas_inicial
                
                # Verifica se as colunas existem
                if coluna_cpf not in df.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_cpf}' não encontrada")
                    continue
                
                if coluna_valor not in df.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_valor}' não encontrada")
                    continue
                
                # Formata CPFs
                df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
                
                # Converte coluna de valor para numérico, tratando valores inválidos
                df['valor_numerico'] = pd.to_numeric(df[coluna_valor], errors='coerce').fillna(0)
                
                # Remove duplicatas mantendo o registro com maior valor
                df_sem_duplicatas = df.loc[df.groupby('cpf_formatado')['valor_numerico'].idxmax()]
                df_sem_duplicatas = df_sem_duplicatas.drop(columns=['cpf_formatado', 'valor_numerico'])
                
                # Contagem final
                linhas_final = len(df_sem_duplicatas)
                duplicatas_removidas = linhas_inicial - linhas_final
                
                total_linhas_final += linhas_final
                total_duplicatas_removidas += duplicatas_removidas
                
                # Salva arquivo processado
                nome_base = os.path.splitext(arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"filter_cpf_maior_valor_{nome_base}.csv")
                
                # Trata colunas numéricas que devem permanecer como string
                df_sem_duplicatas = self.tratar_colunas_numericas(df_sem_duplicatas.copy())
                
                df_sem_duplicatas.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                total_arquivos_processados += 1
                
                # Mostra progresso
                self.console.print(f"[green]✓[/green] {arquivo}: {linhas_inicial:,} → {linhas_final:,} linhas (-{duplicatas_removidas:,} duplicatas)")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        # Cria mensagem final detalhada
        mensagem = (
            f"Estatísticas do Processamento em Lote (Maior Valor):\n"
            f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
            f"├─ Total de arquivos processados: {total_arquivos_processados:,}\n"
            f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
            f"├─ Total de linhas processadas: {total_linhas_inicial:,}\n"
            f"├─ Total de duplicatas removidas: {total_duplicatas_removidas:,}\n"
            f"└─ Total de linhas finais: {total_linhas_final:,}\n\n"
            f"Pasta de saída: {pasta_saida}"
        )
        
        if arquivos_com_erro:
            mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído (Maior Valor)",
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

    def remover_numeros_blacklist_lote(self):
        """Remove números da blacklist em lote por pasta"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV para processar:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = []
        for arquivo in os.listdir(pasta_entrada):
            if arquivo.lower().endswith('.csv'):
                arquivos_csv.append(os.path.join(pasta_entrada, arquivo))
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]\n\n"
                f"Pasta: {pasta_entrada}\n\n"
                "[cyan]Certifique-se de que a pasta contém arquivos .csv[/cyan]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Seleciona arquivo blacklist
        arquivo_blacklist = self.selecionar_arquivo("Selecione o arquivo blacklist (arquivo único com coluna 'numero'):")
        
        # Carrega arquivo blacklist
        df_blacklist = self.carregar_arquivo(arquivo_blacklist)
        total_linhas_blacklist = len(df_blacklist)
        
        # Seleciona coluna de número na blacklist
        coluna_numero_blacklist = self.selecionar_coluna(df_blacklist, "Selecione a coluna 'numero' da blacklist:")
        
        # Cria conjunto de números da blacklist para busca rápida
        numeros_blacklist = set(df_blacklist[coluna_numero_blacklist].astype(str).str.strip())
        
        self.console.print(Panel(
            f"[cyan]Processamento em Lote - Remoção de Números da Blacklist[/cyan]\n\n"
            f"Pasta de entrada: {pasta_entrada}\n"
            f"Total de arquivos CSV encontrados: {len(arquivos_csv):,}\n"
            f"Arquivo blacklist: {os.path.basename(arquivo_blacklist)}\n"
            f"Total de números na blacklist: {total_linhas_blacklist:,}\n\n"
            f"[yellow]Arquivos que serão processados:[/yellow]\n" + 
            "\n".join([f"• {os.path.basename(arquivo)}" for arquivo in arquivos_csv[:10]]) +
            (f"\n... e mais {len(arquivos_csv) - 10} arquivos" if len(arquivos_csv) > 10 else ""),
            title="Iniciando Processamento",
            border_style="blue"
        ))
        
        # Pergunta sobre o modo de seleção de coluna
        modo_selecao = inquirer.select(
            message="Como deseja selecionar as colunas de número?",
            choices=[
                Choice("1", name="Selecionar manualmente para cada arquivo (mais preciso)"),
                Choice("2", name="Identificação automática (mais rápido, pode errar)"),
            ],
        ).execute()
        
        # Confirma se quer continuar
        confirmacao = inquirer.confirm(
            message="Deseja continuar com o processamento em lote?",
            default=True
        ).execute()
        
        if not confirmacao:
            self.console.print("[yellow]Processamento cancelado pelo usuário.[/yellow]")
            return
        
        # Seleciona pasta para salvar os arquivos processados
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos processados:")
        
        # Estatísticas gerais
        total_arquivos = len(arquivos_csv)
        arquivos_processados = 0
        arquivos_com_erro = 0
        total_linhas_processadas = 0
        total_linhas_removidas = 0
        total_numeros_removidos = 0
        
        # Lista para armazenar estatísticas de cada arquivo
        estatisticas_arquivos = []
        
        # Processa cada arquivo
        for i, arquivo_csv in enumerate(arquivos_csv, 1):
            nome_arquivo = os.path.basename(arquivo_csv)
            
            self.console.print(f"[cyan]Processando arquivo {i}/{total_arquivos}: {nome_arquivo}[/cyan]")
            
            try:
                # Carrega arquivo
                df = self.carregar_arquivo(arquivo_csv)
                total_linhas = len(df)
                
                if total_linhas == 0:
                    self.console.print(f"[yellow]⚠️  Arquivo vazio: {nome_arquivo}[/yellow]")
                    arquivos_com_erro += 1
                    continue
                
                # Seleciona coluna de número baseado no modo escolhido
                if modo_selecao == "1":
                    # Modo manual - pergunta para cada arquivo
                    coluna_numero = self.selecionar_coluna(df, f"Selecione a coluna de número no arquivo {nome_arquivo}:")
                else:
                    # Modo automático - tenta identificar automaticamente
                    coluna_numero = self.identificar_coluna_numero(df)
                    
                    if not coluna_numero:
                        self.console.print(f"[red]❌ Não foi possível identificar coluna de número em: {nome_arquivo}[/red]")
                        arquivos_com_erro += 1
                        continue
                
                # Contagem inicial
                total_linhas_processadas += total_linhas
                
                # Remove linhas que contêm números da blacklist
                df_original = df.copy()
                df_filtrado = df[~df[coluna_numero].astype(str).str.strip().isin(numeros_blacklist)]
                
                # Contagem final
                linhas_removidas = total_linhas - len(df_filtrado)
                total_linhas_removidas += linhas_removidas
                
                # Conta números únicos removidos
                numeros_removidos = set(df_original[coluna_numero].astype(str).str.strip()) - set(df_filtrado[coluna_numero].astype(str).str.strip())
                total_numeros_removidos += len(numeros_removidos)
                
                # Salva arquivo processado
                nome_base = os.path.splitext(nome_arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"blacklist_lote_{nome_base}.csv")
                
                try:
                    # Trata colunas numéricas que devem permanecer como string
                    df_filtrado = self.tratar_colunas_numericas(df_filtrado.copy())
                    
                    df_filtrado.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                    
                    # Estatísticas do arquivo
                    estatisticas_arquivo = {
                        'arquivo': nome_arquivo,
                        'total_linhas': total_linhas,
                        'linhas_removidas': linhas_removidas,
                        'linhas_finais': len(df_filtrado),
                        'numeros_removidos': len(numeros_removidos),
                        'taxa_remocao': (linhas_removidas / total_linhas * 100) if total_linhas > 0 else 0
                    }
                    
                    estatisticas_arquivos.append(estatisticas_arquivo)
                    
                    # Atualiza contadores gerais
                    arquivos_processados += 1
                    
                    self.console.print(f"[green]✅ Processado: {nome_arquivo} ({linhas_removidas}/{total_linhas} linhas removidas)[/green]")
                    
                except Exception as e:
                    self.console.print(f"[red]❌ Erro ao salvar {nome_arquivo}: {str(e)}[/red]")
                    arquivos_com_erro += 1
                
            except Exception as e:
                self.console.print(f"[red]❌ Erro ao processar {nome_arquivo}: {str(e)}[/red]")
                arquivos_com_erro += 1
        
        # Exibe relatório final
        self.exibir_relatorio_blacklist_lote(
            total_arquivos, arquivos_processados, arquivos_com_erro,
            total_linhas_processadas, total_linhas_removidas, total_numeros_removidos,
            estatisticas_arquivos, pasta_saida
        )

    def identificar_coluna_numero(self, df):
        """Tenta identificar automaticamente a coluna de número"""
        colunas = list(df.columns)
        
        # Palavras-chave que podem indicar coluna de número (em ordem de prioridade)
        keywords_prioritarias = ['telefone', 'fone', 'phone', 'celular', 'mobile', 'numero', 'num', 'number']
        keywords_secundarias = ['id', 'codigo', 'code']
        
        # Primeira tentativa: palavras-chave prioritárias
        for coluna in colunas:
            coluna_lower = coluna.lower().replace(' ', '_').replace('-', '_')
            for keyword in keywords_prioritarias:
                if keyword in coluna_lower:
                    # Verifica se a coluna realmente contém números (telefones, etc.)
                    if self.verificar_se_coluna_contem_numeros(df[coluna]):
                        self.console.print(f"[cyan]🔍 Coluna identificada por palavra-chave prioritária: {coluna}[/cyan]")
                        return coluna
        
        # Segunda tentativa: palavras-chave secundárias
        for coluna in colunas:
            coluna_lower = coluna.lower().replace(' ', '_').replace('-', '_')
            for keyword in keywords_secundarias:
                if keyword in coluna_lower:
                    # Verifica se a coluna realmente contém números
                    if self.verificar_se_coluna_contem_numeros(df[coluna]):
                        self.console.print(f"[cyan]🔍 Coluna identificada por palavra-chave secundária: {coluna}[/cyan]")
                        return coluna
        
        # Terceira tentativa: análise do padrão dos dados
        for coluna in colunas:
            if self.verificar_se_coluna_contem_numeros(df[coluna]):
                self.console.print(f"[cyan]🔍 Coluna identificada por padrão de dados: {coluna}[/cyan]")
                return coluna
        
        # Se não conseguir identificar automaticamente, retorna None
        return None

    def verificar_se_coluna_contem_numeros(self, serie):
        """Verifica se uma coluna contém números (telefones, etc.)"""
        try:
            # Pega uma amostra dos valores não nulos
            valores = serie.dropna().astype(str).str.strip()
            if len(valores) == 0:
                return False
            
            # Verifica se pelo menos 70% dos valores são números ou contêm números
            valores_com_numeros = 0
            for valor in valores.head(100):  # Verifica apenas os primeiros 100 valores
                # Remove caracteres especiais e verifica se sobra número
                valor_limpo = str(valor).replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
                if valor_limpo.isdigit() and len(valor_limpo) >= 8:  # Telefones têm pelo menos 8 dígitos
                    valores_com_numeros += 1
            
            # Se pelo menos 70% dos valores são números válidos
            return (valores_com_numeros / min(len(valores), 100)) >= 0.7
            
        except:
            return False

    def exibir_relatorio_blacklist_lote(self, total_arquivos, arquivos_processados, arquivos_com_erro,
                                       total_linhas_processadas, total_linhas_removidas, total_numeros_removidos,
                                       estatisticas_arquivos, pasta_saida):
        """Exibe relatório detalhado do processamento em lote da blacklist"""
        
        # Calcula estatísticas gerais
        taxa_remocao_geral = (total_linhas_removidas / total_linhas_processadas * 100) if total_linhas_processadas > 0 else 0
        taxa_sucesso = (arquivos_processados / total_arquivos * 100) if total_arquivos > 0 else 0
        
        # Ordena estatísticas por taxa de remoção (maior para menor)
        estatisticas_ordenadas = sorted(estatisticas_arquivos, key=lambda x: x['taxa_remocao'], reverse=True)
        
        # Cria mensagem do relatório
        mensagem = (
            f"[bold cyan]RELATÓRIO DE PROCESSAMENTO EM LOTE - BLACKLIST[/bold cyan]\n\n"
            f"[bold]Resumo Geral:[/bold]\n"
            f"├─ Total de arquivos encontrados: {total_arquivos:,}\n"
            f"├─ Arquivos processados com sucesso: {arquivos_processados:,}\n"
            f"├─ Arquivos com erro: {arquivos_com_erro:,}\n"
            f"├─ Taxa de sucesso: {taxa_sucesso:.1f}%\n\n"
            f"[bold]Estatísticas de Dados:[/bold]\n"
            f"├─ Total de linhas processadas: {total_linhas_processadas:,}\n"
            f"├─ Total de linhas removidas: {total_linhas_removidas:,}\n"
            f"├─ Total de números únicos removidos: {total_numeros_removidos:,}\n"
            f"├─ Linhas finais: {total_linhas_processadas - total_linhas_removidas:,}\n"
            f"└─ Taxa de remoção geral: {taxa_remocao_geral:.1f}%\n\n"
            f"[bold]Pasta de saída:[/bold]\n"
            f"└─ {pasta_saida}\n\n"
        )
        
        # Adiciona detalhes dos arquivos (top 10 com maior remoção)
        if estatisticas_ordenadas:
            mensagem += "[bold green]Top 10 - Maior Taxa de Remoção:[/bold green]\n"
            for i, stats in enumerate(estatisticas_ordenadas[:10], 1):
                mensagem += (
                    f"{i:2d}. {stats['arquivo']:<30} "
                    f"{stats['linhas_removidas']:>6}/{stats['total_linhas']:<6} "
                    f"({stats['taxa_remocao']:>5.1f}%) - {stats['numeros_removidos']} números únicos\n"
                )
            
            if len(estatisticas_ordenadas) > 10:
                mensagem += f"... e mais {len(estatisticas_ordenadas) - 10} arquivos\n"
            
            mensagem += "\n"
        
        # Adiciona informações sobre arquivos processados
        mensagem += (
            "[bold]Arquivos processados:[/bold]\n"
            f"├─ Prefixo: 'blacklist_lote_'\n"
            f"├─ Formato: CSV UTF-8 com delimitador ';'\n"
            f"└─ Conteúdo: Apenas linhas que NÃO contêm números da blacklist\n\n"
            f"[bold blue]💡 Dica:[/bold blue] Arquivos com prefixo 'blacklist_lote_' foram processados com sucesso!"
        )
        
        # Salva relatório detalhado em CSV
        if estatisticas_arquivos:
            try:
                df_relatorio = pd.DataFrame(estatisticas_arquivos)
                relatorio_path = os.path.join(pasta_saida, "relatorio_blacklist_lote.csv")
                # Trata colunas numéricas que devem permanecer como string
                df_relatorio = self.tratar_colunas_numericas(df_relatorio.copy())
                
                df_relatorio.to_csv(relatorio_path, sep=';', encoding='utf-8', index=False)
                mensagem += f"\n\n[bold green]📊 Relatório detalhado salvo:[/bold green]\n└─ {relatorio_path}"
            except Exception as e:
                mensagem += f"\n\n[bold red]❌ Erro ao salvar relatório: {str(e)}[/bold red]"
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote - Blacklist Concluído",
            border_style="green"
        ))

    def remover_celulares_blacklist(self):
        """Remove linhas do arquivo base que têm números de celular presentes na blacklist"""
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        arquivo_blacklist = self.selecionar_arquivo("Selecione o arquivo blacklist_numeros:")
        
        df_base = self.carregar_arquivo(arquivo_base)
        df_blacklist = self.carregar_arquivo(arquivo_blacklist)
        
        # Contagem inicial
        total_linhas_base = len(df_base)
        total_linhas_blacklist = len(df_blacklist)
        
        coluna_celular_base = self.selecionar_coluna(df_base, "Selecione a coluna de celular do arquivo base:")
        coluna_celular_blacklist = self.selecionar_coluna(df_blacklist, "Selecione a coluna de celular do arquivo blacklist_numeros:")
        
        # Formata números de celular
        df_base['celular_formatado'] = df_base[coluna_celular_base].apply(self.formatar_numero_celular)
        df_blacklist['celular_formatado'] = df_blacklist[coluna_celular_blacklist].apply(self.formatar_numero_celular)
        
        # Remove valores None e cria conjunto de números da blacklist
        numeros_blacklist = set(df_blacklist['celular_formatado'].dropna())
        
        # Remove linhas que têm números presentes na blacklist
        mask_remover = df_base['celular_formatado'].isin(numeros_blacklist)
        df_resultado = df_base[~mask_remover]
        df_removidos = df_base[mask_remover]
        
        # Remove coluna temporária
        df_resultado = df_resultado.drop(columns=['celular_formatado'])
        df_removidos = df_removidos.drop(columns=['celular_formatado'])
        
        # Contagem final
        total_linhas_resultado = len(df_resultado)
        total_linhas_removidas = len(df_removidos)
        
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        caminho_saida = self.salvar_arquivo(df_resultado, arquivo_base, "sem_blacklist_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Arquivo Blacklist:\n"
            f"│  └─ Total de linhas: {total_linhas_blacklist:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Total de linhas removidas: {total_linhas_removidas:,}\n"
            f"│  └─ Total de linhas no arquivo final: {total_linhas_resultado:,}\n\n"
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
                self.remover_duplicatas_cpf_lote()
            elif opcao == "3":
                self.remover_duplicatas_cpf_lote_maior_valor()
            elif opcao == "4":
                self.remover_cpfs_blacklist()
            elif opcao == "5":
                self.remover_numeros_blacklist()
            elif opcao == "6":
                self.remover_numeros_blacklist_lote()
            elif opcao == "7":
                self.remover_celulares_blacklist()
            else:
                break
