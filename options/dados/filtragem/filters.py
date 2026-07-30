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
import glob
import csv
import re
from options.utils import (
    selecionar_colunas,
    extrair_colunas_com_cabecalho_alfabetico,
    gerar_nomes_colunas_alfabeticas,
)

class Filters:
    def __init__(self):
        self.console = Console()

    def tratar_colunas_numericas(self, df):
        """Trata colunas numéricas que devem permanecer como string (telefones, CPFs, etc.)"""
        # Substring: nomes longos o suficiente para não colidir (ex.: 'id' em 'idade')
        padroes_substring = [
            'telefone', 'fone', 'phone', 'celular', 'mobile',
            'cpf', 'cnpj', 'rg', 'cep', 'codigo',
            'numero', 'identificador'
        ]
        # Padrões curtos: só como palavra inteira (evita 'id' em 'idade', 'num' em 'numero' já coberto acima)
        padroes_palavra = ['id', 'num', 'code']

        for coluna in df.columns:
            coluna_lower = coluna.lower()

            # Verifica se a coluna deve ser tratada como string
            deve_ser_string = any(padrao in coluna_lower for padrao in padroes_substring)
            if not deve_ser_string:
                deve_ser_string = any(
                    re.search(rf'(^|_){re.escape(padrao)}(_|$)', coluna_lower)
                    or coluna_lower == padrao
                    for padrao in padroes_palavra
                )

            if deve_ser_string:
                # Converte para string e remove .0 desnecessários
                df[coluna] = df[coluna].astype(str).str.replace('.0', '', regex=False)
                # Remove 'nan' strings e substitui por vazio
                df[coluna] = df[coluna].replace('nan', '', regex=False)

        return df

    def menu_filters(self):
        """Menu principal de opções de filtros"""
        return inquirer.select(
            message="Selecione o tipo de filtro:",
            choices=[
                Choice("1", name="Dividir arquivo em partes"),
                Choice("2", name="Blacklist por CPF - Arquivos por Pasta"),
                Choice("3", name="Whitelist por CPF - Arquivos por Pasta"),
                Choice("4", name="Filtrar arquivo por CPF (Arquivo 1 x Arquivo 2)"),
                Choice("5", name="Repartir por coluna"),
                Choice("6", name="Remover linhas com valores vazios/zero (arquivo único)"),
                Choice("7", name="Remover linhas com valores vazios/zero (processamento em lote)"),
                Choice("8", name="Adicionar coluna de idade baseada na data de nascimento"),
                Choice("9", name="Voltar ao menu principal"),
            ],
        ).execute()

    def selecionar_arquivo(self, mensagem):
        """Permite ao usuário selecionar um arquivo"""
        return inquirer.filepath(
            message=mensagem,
            validate=lambda x: x.endswith(('.xlsx', '.csv')),
            filter=lambda x: x.strip(),
        ).execute()

    def selecionar_pasta(self, mensagem):
        """Permite ao usuário selecionar uma pasta"""
        return inquirer.filepath(
            message=mensagem,
            only_directories=True,
            filter=lambda x: x.strip(),
        ).execute()

    def selecionar_pasta_saida(self, mensagem):
        """Permite ao usuário selecionar uma pasta para salvar"""
        return inquirer.filepath(
            message=mensagem,
            filter=lambda x: x.strip(),
        ).execute()

    def carregar_arquivo(self, caminho, dtype=None):
        """Carrega arquivo CSV ou XLSX. dtype=str força todas as colunas como string (evita perder zeros em CNPJ etc.)."""
        if caminho.endswith('.xlsx'):
            return pd.read_excel(caminho)
        else:
            kw = dict(quoting=csv.QUOTE_MINIMAL, doublequote=True, keep_default_na=False, header=0, on_bad_lines='warn')
            if dtype is not None:
                kw['dtype'] = dtype
            melhor_df = None
            melhor_num_colunas = 0
            for sep in [';', ',']:
                for encoding in ['utf-8', 'latin-1']:
                    try:
                        df = pd.read_csv(caminho, sep=sep, encoding=encoding, **kw)
                        num_colunas = len(df.columns)
                        if num_colunas > melhor_num_colunas:
                            melhor_df = df
                            melhor_num_colunas = num_colunas
                            if num_colunas > 1:
                                return melhor_df
                    except:
                        continue
            if melhor_df is not None:
                return melhor_df
            try:
                return pd.read_csv(caminho, encoding='utf-8', **kw)
            except:
                return pd.read_csv(caminho, encoding='latin-1', **kw)

    def carregar_csv_blacklist(self, caminho):
        """Carrega arquivo CSV de blacklist com diferentes encodings"""
        try:
            return pd.read_csv(caminho, encoding='utf-8')
        except:
            try:
                return pd.read_csv(caminho, encoding='latin-1')
            except:
                try:
                    return pd.read_csv(caminho, sep=';', encoding='utf-8')
                except:
                    return pd.read_csv(caminho, sep=';', encoding='latin-1')

    def salvar_arquivo(self, df, caminho, prefixo, indice, pasta_saida):
        """Salva arquivo CSV com prefixo e índice"""
        nome_arquivo = os.path.basename(caminho)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{indice}_{nome_base}.csv")
        
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

    def salvar_arquivo_blacklist(self, df, nome_original, tipo, pasta_saida):
        """Salva arquivo whitelist ou blacklist"""
        nome_base = os.path.splitext(nome_original)[0]
        caminho_saida = os.path.join(pasta_saida, f"{tipo}_{nome_base}.csv")
        
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
                    caminho_saida = os.path.join(pasta_saida, f"{tipo}_{nome_base}.csv")
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
                caminho_saida = os.path.join(pasta_saida, f"{tipo}_{nome_base}.csv")

    def salvar_arquivo_repartido(self, df, nome_original, valor_coluna, pasta_saida):
        """Salva arquivo repartido por valor da coluna"""
        nome_base = os.path.splitext(nome_original)[0]
        # Limpar o valor da coluna para usar como nome de arquivo
        valor_limpo = str(valor_coluna).lower().strip().replace(' ', '_').replace('/', '_').replace('\\', '_')
        caminho_saida = os.path.join(pasta_saida, f"{valor_limpo}_{nome_base}.csv")
        
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
                    caminho_saida = os.path.join(pasta_saida, f"{valor_limpo}_{nome_base}.csv")
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
                caminho_saida = os.path.join(pasta_saida, f"{valor_limpo}_{nome_base}.csv")

    def repartir_por_coluna(self):
        """Repartir arquivo CSV por valores únicos de uma coluna"""
        
        # 1. Receber o caminho de 1 arquivo CSV
        arquivo = inquirer.filepath(
            message="Selecione o arquivo CSV para repartir:",
            validate=lambda x: x.endswith('.csv'),
            filter=lambda x: x.strip(),
        ).execute()
        
        # Carregar o arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            self.console.print(Panel(
                f"[green]Arquivo carregado com sucesso![/green]\n"
                f"Total de registros: {len(df):,}\n"
                f"Total de colunas: {len(df.columns)}",
                title="Arquivo Carregado",
                border_style="green"
            ))
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\n"
                f"Erro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # 2. Pedir para selecionar uma coluna
        if df.empty:
            self.console.print(Panel(
                "[red]O arquivo está vazio![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Criar lista de escolhas com as colunas
        choices_colunas = []
        for i, coluna in enumerate(df.columns):
            # Mostrar alguns valores únicos da coluna como exemplo
            valores_unicos = df[coluna].dropna().unique()[:5]
            exemplo = ", ".join([str(v) for v in valores_unicos])
            if len(valores_unicos) > 5:
                exemplo += "..."
            
            choices_colunas.append(
                Choice(coluna, name=f"{coluna} (ex: {exemplo})")
            )
        
        coluna_selecionada = inquirer.select(
            message="Selecione a coluna para repartir o arquivo:",
            choices=choices_colunas,
        ).execute()
        
        # Verificar valores únicos da coluna selecionada
        valores_unicos = df[coluna_selecionada].dropna().unique()
        total_valores = len(valores_unicos)
        
        if total_valores == 0:
            self.console.print(Panel(
                f"[red]A coluna '{coluna_selecionada}' não possui valores válidos![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Mostrar informações sobre a repartição
        self.console.print(Panel(
            f"[cyan]Informações da Repartição:[/cyan]\n"
            f"├─ Coluna selecionada: {coluna_selecionada}\n"
            f"├─ Valores únicos encontrados: {total_valores}\n"
            f"└─ Arquivos que serão gerados: {total_valores}\n\n"
            f"[yellow]Valores únicos:[/yellow]\n" +
            "\n".join([f"• {valor}" for valor in sorted(valores_unicos)]),
            title="Prévia da Repartição",
            border_style="cyan"
        ))
        
        # Confirmar se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e gerar {total_valores} arquivos?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # 3. Receber caminho da pasta para salvar
        pasta_saida = self.selecionar_pasta("Selecione a pasta para salvar os arquivos repartidos:")
        
        # 4. Processar e salvar os arquivos por valor da coluna
        self.console.print("\n[cyan]Repartindo arquivo...[/cyan]")
        
        arquivos_salvos = []
        estatisticas = []
        nome_arquivo_original = os.path.basename(arquivo)
        
        for valor in valores_unicos:
            try:
                # Filtrar dados para este valor
                df_filtrado = df[df[coluna_selecionada] == valor].copy()
                
                if len(df_filtrado) == 0:
                    continue
                
                # Salvar arquivo
                arquivo_salvo = self.salvar_arquivo_repartido(
                    df_filtrado, nome_arquivo_original, valor, pasta_saida
                )
                
                arquivos_salvos.append(arquivo_salvo)
                estatisticas.append({
                    'valor': valor,
                    'registros': len(df_filtrado),
                    'arquivo': os.path.basename(arquivo_salvo)
                })
                
                self.console.print(f"[green]✓[/green] {valor}: {len(df_filtrado):,} registros")
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro ao processar valor '{valor}':[/red]\n\nErro: {str(e)}",
                    title="Erro",
                    border_style="red"
                ))
                continue
        
        # Mostrar relatório final
        if estatisticas:
            total_registros_processados = sum([stat['registros'] for stat in estatisticas])
            
            mensagem_final = (
                f"[bold green]Repartição Concluída![/bold green]\n\n"
                f"[cyan]Estatísticas Gerais:[/cyan]\n"
                f"├─ Arquivo original: {nome_arquivo_original}\n"
                f"├─ Coluna usada: {coluna_selecionada}\n"
                f"├─ Total de registros processados: {total_registros_processados:,}\n"
                f"├─ Valores únicos processados: {len(estatisticas)}\n"
                f"└─ Arquivos gerados: {len(arquivos_salvos)}\n\n"
                f"[cyan]Detalhes por valor:[/cyan]\n"
            )
            
            for i, stat in enumerate(estatisticas):
                prefixo = "└─" if i == len(estatisticas) - 1 else "├─"
                mensagem_final += (
                    f"{prefixo} {stat['valor']}: {stat['registros']:,} registros\n"
                    f"   └─ Arquivo: {stat['arquivo']}\n"
                )
            
            self.console.print(Panel(
                mensagem_final,
                title="Relatório Final",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                "[red]Nenhum arquivo foi gerado![/red]",
                title="Erro",
                border_style="red"
            ))

    def blacklist_cpf_pasta(self):
        """Processa blacklist de CPF por pasta de arquivos"""
        
        # 1. Perguntar tipo de arquivo
        tipo_arquivo = inquirer.select(
            message="Qual o tipo dos arquivos dentro da pasta?",
            choices=[
                Choice("csv", name="CSV"),
                Choice("xlsx", name="XLSX"),
            ],
        ).execute()
        
        # 2. Pedir caminho da pasta de dados
        pasta_dados = self.selecionar_pasta("Selecione a pasta com os arquivos de dados:")
        
        # Buscar arquivos na pasta
        if tipo_arquivo == "csv":
            arquivos_dados = glob.glob(os.path.join(pasta_dados, "*.csv"))
        else:
            arquivos_dados = glob.glob(os.path.join(pasta_dados, "*.xlsx"))
        
        if not arquivos_dados:
            self.console.print(Panel(
                f"[red]Nenhum arquivo {tipo_arquivo.upper()} encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[green]Encontrados {len(arquivos_dados)} arquivos {tipo_arquivo.upper()}[/green]",
            title="Arquivos Encontrados",
            border_style="green"
        ))
        
        # 3. Confirmar se todos têm coluna CPF
        tem_cpf = inquirer.confirm(
            message="Todos os arquivos têm a coluna com cabeçalho 'CPF'?",
            default=True,
        ).execute()
        
        if not tem_cpf:
            self.console.print(Panel(
                "[red]Todos os arquivos devem ter a coluna 'CPF' para continuar![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # 4. Verificar e confirmar colunas CPF
        arquivos_verificados = []
        for arquivo in arquivos_dados:
            try:
                df = self.carregar_arquivo(arquivo)
                
                if 'CPF' not in df.columns:
                    self.console.print(Panel(
                        f"[red]Arquivo sem coluna 'CPF':[/red]\n{os.path.basename(arquivo)}",
                        title="Erro",
                        border_style="red"
                    ))
                    return
                
                # Mostrar exemplo da segunda linha
                if len(df) > 0:
                    valor_exemplo = df['CPF'].iloc[0] if len(df) > 0 else "N/A"
                    self.console.print(f"[cyan]Arquivo:[/cyan] {os.path.basename(arquivo)}")
                    self.console.print(f"[cyan]Exemplo CPF (primeira linha):[/cyan] {valor_exemplo}")
                    
                    confirmar = inquirer.confirm(
                        message=f"Confirma que esta é a coluna correta de CPF para o arquivo {os.path.basename(arquivo)}?",
                        default=True,
                    ).execute()
                    
                    if not confirmar:
                        self.console.print(Panel(
                            "[red]Processamento cancelado pelo usuário![/red]",
                            title="Cancelado",
                            border_style="red"
                        ))
                        return
                
                arquivos_verificados.append(arquivo)
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro ao carregar arquivo:[/red]\n{os.path.basename(arquivo)}\n\nErro: {str(e)}",
                    title="Erro",
                    border_style="red"
                ))
                return
        
        # 5. Pedir pasta dos arquivos de blacklist
        pasta_blacklist = self.selecionar_pasta("Selecione a pasta com os arquivos de blacklist (apenas CSV com coluna CPF):")
        
        # Buscar arquivos CSV de blacklist
        arquivos_blacklist = glob.glob(os.path.join(pasta_blacklist, "*.csv"))
        
        if not arquivos_blacklist:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta de blacklist![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # 6. Informar sobre requisitos dos arquivos de blacklist
        self.console.print(Panel(
            "[yellow]ATENÇÃO:[/yellow]\n"
            "• Todos os arquivos de blacklist devem ser CSV\n"
            "• Devem ter uma coluna com cabeçalho 'CPF' ou 'identifier'\n"
            "• O sistema reconhece tanto UTF-8 quanto outros encodings",
            title="Requisitos dos Arquivos de Blacklist",
            border_style="yellow"
        ))
        
        # 7. Carregar e unir arquivos de blacklist
        self.console.print("[cyan]Carregando arquivos de blacklist...[/cyan]")
        
        cpfs_blacklist = set()
        for arquivo_bl in arquivos_blacklist:
            try:
                df_bl = self.carregar_csv_blacklist(arquivo_bl)
                
                # Verificar se tem coluna CPF ou identifier
                coluna_cpf = None
                if 'CPF' in df_bl.columns:
                    coluna_cpf = 'CPF'
                elif 'identifier' in df_bl.columns:
                    coluna_cpf = 'identifier'
                else:
                    self.console.print(Panel(
                        f"[red]Arquivo de blacklist sem coluna 'CPF' ou 'identifier':[/red]\n{os.path.basename(arquivo_bl)}",
                        title="Erro",
                        border_style="red"
                    ))
                    return
                
                # Adicionar CPFs ao set (remove duplicatas automaticamente)
                cpfs_arquivo = df_bl[coluna_cpf].dropna().astype(str).str.strip()
                cpfs_blacklist.update(cpfs_arquivo)
                
                self.console.print(f"[green]✓[/green] {os.path.basename(arquivo_bl)} - {len(cpfs_arquivo)} CPFs (coluna: {coluna_cpf})")
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro ao carregar arquivo de blacklist:[/red]\n{os.path.basename(arquivo_bl)}\n\nErro: {str(e)}",
                    title="Erro",
                    border_style="red"
                ))
                return
        
        # 8. Remover duplicatas (já feito pelo set)
        total_cpfs_blacklist = len(cpfs_blacklist)
        self.console.print(Panel(
            f"[green]Total de CPFs únicos na blacklist: {total_cpfs_blacklist:,}[/green]",
            title="Blacklist Carregada",
            border_style="green"
        ))
        
        # 11. Criar pastas blacklist e whitelist automaticamente na pasta dos arquivos
        pasta_blacklist = os.path.join(pasta_dados, "blacklist")
        pasta_whitelist = os.path.join(pasta_dados, "whitelist")
        
        # Criar as pastas se não existirem
        os.makedirs(pasta_blacklist, exist_ok=True)
        os.makedirs(pasta_whitelist, exist_ok=True)
        
        self.console.print(Panel(
            f"[green]Pastas criadas automaticamente:[/green]\n"
            f"├─ Blacklist: {pasta_blacklist}\n"
            f"└─ Whitelist: {pasta_whitelist}",
            title="Pastas Criadas",
            border_style="green"
        ))
        
        pasta_saida = pasta_dados  # Usa a pasta dos dados como base
        
        # 9. Processar cada arquivo da pasta de dados
        self.console.print("\n[cyan]Processando arquivos...[/cyan]")
        
        arquivos_salvos = []
        estatisticas = []
        
        for arquivo in arquivos_verificados:
            try:
                nome_arquivo = os.path.basename(arquivo)
                self.console.print(f"\n[cyan]Processando:[/cyan] {nome_arquivo}")
                
                df = self.carregar_arquivo(arquivo)
                
                # Converter CPF para string e limpar
                df['CPF'] = df['CPF'].astype(str).str.strip()
                
                # Separar whitelist e blacklist
                df_blacklist = df[df['CPF'].isin(cpfs_blacklist)].copy()
                df_whitelist = df[~df['CPF'].isin(cpfs_blacklist)].copy()
                
                # 10. Salvar arquivos whitelist e blacklist nas pastas específicas
                arquivo_whitelist = self.salvar_arquivo_blacklist(
                    df_whitelist, nome_arquivo, "whitelist", pasta_whitelist
                )
                arquivo_blacklist = self.salvar_arquivo_blacklist(
                    df_blacklist, nome_arquivo, "blacklist", pasta_blacklist
                )
                
                arquivos_salvos.extend([arquivo_whitelist, arquivo_blacklist])
                
                # Guardar estatísticas
                estatisticas.append({
                    'arquivo': nome_arquivo,
                    'total': len(df),
                    'whitelist': len(df_whitelist),
                    'blacklist': len(df_blacklist)
                })
                
                self.console.print(f"[green]✓[/green] Whitelist: {len(df_whitelist):,} registros")
                self.console.print(f"[green]✓[/green] Blacklist: {len(df_blacklist):,} registros")
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro ao processar arquivo:[/red]\n{nome_arquivo}\n\nErro: {str(e)}",
                    title="Erro",
                    border_style="red"
                ))
                continue
        
        # Mostrar relatório final
        mensagem_final = (
            f"[bold green]Processamento Concluído![/bold green]\n\n"
            f"[cyan]Estatísticas Gerais:[/cyan]\n"
            f"├─ Arquivos processados: {len(estatisticas)}\n"
            f"├─ CPFs únicos na blacklist: {total_cpfs_blacklist:,}\n"
            f"└─ Total de arquivos gerados: {len(arquivos_salvos)}\n\n"
            f"[cyan]Localização dos arquivos:[/cyan]\n"
            f"├─ Pasta Blacklist: {pasta_blacklist}\n"
            f"└─ Pasta Whitelist: {pasta_whitelist}\n\n"
            f"[cyan]Detalhes por arquivo:[/cyan]\n"
        )
        
        for i, stat in enumerate(estatisticas):
            prefixo = "└─" if i == len(estatisticas) - 1 else "├─"
            mensagem_final += (
                f"{prefixo} {stat['arquivo']}:\n"
                f"   ├─ Total: {stat['total']:,}\n"
                f"   ├─ Whitelist: {stat['whitelist']:,}\n"
                f"   └─ Blacklist: {stat['blacklist']:,}\n"
            )
        
        self.console.print(Panel(
            mensagem_final,
            title="Relatório Final",
            border_style="green"
        ))

    def whitelist_cpf_pasta(self):
        """Processa whitelist de CPF por pasta de arquivos (Pasta 1 vs Pasta 2)"""
        
        # 1. Pedir caminho da pasta 1 (arquivos de dados a serem filtrados)
        pasta_1 = self.selecionar_pasta("Selecione a pasta 1 (arquivos de dados a serem filtrados):")
        
        # Buscar arquivos na pasta 1 (suporta CSV e XLSX)
        arquivos_pasta1 = glob.glob(os.path.join(pasta_1, "*.csv")) + glob.glob(os.path.join(pasta_1, "*.xlsx"))
        
        if not arquivos_pasta1:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV ou XLSX encontrado na pasta 1![/red]",
                title="Erro",
                border_style="red"
            ))
            return
            
        self.console.print(Panel(
            f"[green]Encontrados {len(arquivos_pasta1)} arquivos na pasta 1[/green]",
            title="Arquivos Pasta 1",
            border_style="green"
        ))
        
        # 2. Pedir caminho da pasta 2 (arquivos com CPFs de referência)
        pasta_2 = self.selecionar_pasta("Selecione a pasta 2 (arquivos com CPFs de referência):")
        
        # Buscar arquivos na pasta 2 (suporta CSV e XLSX)
        arquivos_pasta2 = glob.glob(os.path.join(pasta_2, "*.csv")) + glob.glob(os.path.join(pasta_2, "*.xlsx"))
        
        if not arquivos_pasta2:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV ou XLSX encontrado na pasta 2![/red]",
                title="Erro",
                border_style="red"
            ))
            return
            
        self.console.print(Panel(
            f"[green]Encontrados {len(arquivos_pasta2)} arquivos na pasta 2[/green]",
            title="Arquivos Pasta 2",
            border_style="green"
        ))
        
        # 3. Perguntar qual coluna dos arquivos da pasta 1 é a de CPF
        try:
            df_exemplo1 = self.carregar_arquivo(arquivos_pasta1[0])
            coluna_cpf_pasta1 = self.selecionar_coluna(
                df_exemplo1,
                "Selecione a coluna que contém os CPFs na pasta 1:"
            )
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao ler o primeiro arquivo da pasta 1:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
            
        # 4. Perguntar qual coluna dos arquivos da pasta 2 é a de CPF
        try:
            df_exemplo2 = self.carregar_arquivo(arquivos_pasta2[0])
            coluna_cpf_pasta2 = self.selecionar_coluna(
                df_exemplo2,
                "Selecione a coluna que contém os CPFs na pasta 2:"
            )
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao ler o primeiro arquivo da pasta 2:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
            
        # 5. Pedir caminho da pasta de saída
        pasta_salvar = self.selecionar_pasta_saida("Selecione a pasta onde deseja salvar as pastas 'whitelist' e 'blacklist':")
        
        # Criar subpastas whitelist e blacklist
        pasta_whitelist = os.path.join(pasta_salvar, "whitelist")
        pasta_blacklist = os.path.join(pasta_salvar, "blacklist")
        os.makedirs(pasta_whitelist, exist_ok=True)
        os.makedirs(pasta_blacklist, exist_ok=True)
        
        self.console.print(Panel(
            f"[green]Pastas de saída configuradas:[/green]\n"
            f"├─ Whitelist: {pasta_whitelist}\n"
            f"└─ Blacklist: {pasta_blacklist}",
            title="Pastas de Saída",
            border_style="green"
        ))
        
        # Função local para normalizar CPF
        def normalizar_cpf(cpf):
            if pd.isna(cpf) or cpf == '' or str(cpf).strip() == '':
                return ''
            try:
                cpf_str = str(cpf).strip()
                # Remove todos os caracteres não numéricos
                cpf_limpo = re.sub(r'\D', '', cpf_str)
                if not cpf_limpo:
                    return ''
                # Preenche com zeros à esquerda até 11 dígitos
                cpf_formatado = cpf_limpo.zfill(11)
                # Pega apenas os 11 primeiros dígitos
                return cpf_formatado[:11]
            except:
                return ''
                
        # 6. Carregar e normalizar todos os CPFs da pasta 2
        self.console.print("[cyan]Carregando e normalizando CPFs de referência da pasta 2...[/cyan]")
        cpfs_referencia = set()
        
        for arquivo in arquivos_pasta2:
            try:
                df_p2 = self.carregar_arquivo(arquivo)
                if coluna_cpf_pasta2 not in df_p2.columns:
                    self.console.print(f"[yellow]Aviso: O arquivo {os.path.basename(arquivo)} não possui a coluna '{coluna_cpf_pasta2}'. Ignorando...[/yellow]")
                    continue
                
                # Normaliza os CPFs e adiciona ao set
                cpfs_p2 = df_p2[coluna_cpf_pasta2].apply(normalizar_cpf)
                cpfs_p2 = cpfs_p2[cpfs_p2 != ''].tolist()
                cpfs_referencia.update(cpfs_p2)
                self.console.print(f"[green]✓[/green] {os.path.basename(arquivo)} - {len(cpfs_p2):,} CPFs carregados")
            except Exception as e:
                self.console.print(f"[red]Erro ao processar arquivo {os.path.basename(arquivo)}: {str(e)}[/red]")
                
        total_cpfs_referencia = len(cpfs_referencia)
        self.console.print(Panel(
            f"[green]Total de CPFs de referência únicos carregados: {total_cpfs_referencia:,}[/green]",
            title="Referência Carregada",
            border_style="green"
        ))
        
        # 7. Processar cada arquivo da pasta 1
        self.console.print("\n[cyan]Processando arquivos da pasta 1...[/cyan]")
        
        arquivos_salvos = []
        estatisticas = []
        
        for arquivo in arquivos_pasta1:
            try:
                nome_arquivo = os.path.basename(arquivo)
                self.console.print(f"\n[cyan]Processando:[/cyan] {nome_arquivo}")
                
                df = self.carregar_arquivo(arquivo)
                
                if coluna_cpf_pasta1 not in df.columns:
                    self.console.print(Panel(
                        f"[red]Arquivo sem coluna '{coluna_cpf_pasta1}':[/red]\n{nome_arquivo}",
                        title="Erro",
                        border_style="red"
                    ))
                    continue
                
                # Normalizar CPFs temporariamente para a comparação
                cpfs_normalizados = df[coluna_cpf_pasta1].apply(normalizar_cpf)
                
                # Separar whitelist e blacklist
                # Se o CPF normalizado está no set de referência, vai para whitelist. Senão, blacklist.
                mask_whitelist = cpfs_normalizados.isin(cpfs_referencia)
                df_whitelist = df[mask_whitelist].copy()
                df_blacklist = df[~mask_whitelist].copy()
                
                # Salvar arquivos whitelist e blacklist nas pastas específicas
                arquivo_whitelist = self.salvar_arquivo_blacklist(
                    df_whitelist, nome_arquivo, "whitelist", pasta_whitelist
                )
                arquivo_blacklist = self.salvar_arquivo_blacklist(
                    df_blacklist, nome_arquivo, "blacklist", pasta_blacklist
                )
                
                arquivos_salvos.extend([arquivo_whitelist, arquivo_blacklist])
                
                # Guardar estatísticas
                estatisticas.append({
                    'arquivo': nome_arquivo,
                    'total': len(df),
                    'whitelist': len(df_whitelist),
                    'blacklist': len(df_blacklist)
                })
                
                self.console.print(f"[green]✓[/green] Whitelist (presente na pasta 2): {len(df_whitelist):,} registros")
                self.console.print(f"[green]✓[/green] Blacklist (não presente na pasta 2): {len(df_blacklist):,} registros")
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro ao processar arquivo:[/red]\n{nome_arquivo}\n\nErro: {str(e)}",
                    title="Erro",
                    border_style="red"
                ))
                continue
                
        # 8. Mostrar relatório final
        mensagem_final = (
            f"[bold green]Processamento Concluído![/bold green]\n\n"
            f"[cyan]Estatísticas Gerais:[/cyan]\n"
            f"├─ Arquivos processados: {len(estatisticas)}\n"
            f"├─ CPFs de referência (pasta 2): {total_cpfs_referencia:,}\n"
            f"└─ Total de arquivos gerados: {len(arquivos_salvos)}\n\n"
            f"[cyan]Localização dos arquivos:[/cyan]\n"
            f"├─ Pasta Whitelist: {pasta_whitelist}\n"
            f"└─ Pasta Blacklist: {pasta_blacklist}\n\n"
            f"[cyan]Detalhes por arquivo:[/cyan]\n"
        )
        
        for i, stat in enumerate(estatisticas):
            prefixo = "└─" if i == len(estatisticas) - 1 else "├─"
            mensagem_final += (
                f"{prefixo} {stat['arquivo']}:\n"
                f"   ├─ Total: {stat['total']:,}\n"
                f"   ├─ Whitelist: {stat['whitelist']:,}\n"
                f"   └─ Blacklist: {stat['blacklist']:,}\n"
            )
            
        self.console.print(Panel(
            mensagem_final,
            title="Relatório Final",
            border_style="green"
        ))

    def filtrar_arquivo_por_cpf(self):
        """Filtra o arquivo 1 por CPF com base na lista de CPFs do arquivo 2.
        Gera dois arquivos na pasta escolhida:
        - linhas do arquivo 1 cujo CPF aparece no arquivo 2
        - linhas do arquivo 1 cujo CPF não aparece no arquivo 2
        """
        # 1. Seleciona arquivo 1 (dados a filtrar)
        arquivo_1 = self.selecionar_arquivo("Selecione o arquivo 1 (dados a filtrar):")
        try:
            df1 = self.carregar_arquivo(arquivo_1)
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar o arquivo 1:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return

        if len(df1) == 0:
            self.console.print(Panel(
                "[red]O arquivo 1 está vazio![/red]",
                title="Erro",
                border_style="red"
            ))
            return

        self.console.print(Panel(
            f"[green]Arquivo 1 carregado![/green]\n"
            f"Registros: {len(df1):,} | Colunas: {len(df1.columns)}",
            title="Arquivo 1",
            border_style="green"
        ))

        coluna_cpf_1 = self.selecionar_coluna(
            df1,
            "Selecione a coluna de CPF do arquivo 1:"
        )

        # 2. Seleciona arquivo 2 (lista de CPFs de referência)
        arquivo_2 = self.selecionar_arquivo("Selecione o arquivo 2 (lista de CPFs):")
        try:
            df2 = self.carregar_arquivo(arquivo_2)
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar o arquivo 2:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return

        if len(df2) == 0:
            self.console.print(Panel(
                "[red]O arquivo 2 está vazio![/red]",
                title="Erro",
                border_style="red"
            ))
            return

        self.console.print(Panel(
            f"[green]Arquivo 2 carregado![/green]\n"
            f"Registros: {len(df2):,} | Colunas: {len(df2.columns)}",
            title="Arquivo 2",
            border_style="green"
        ))

        coluna_cpf_2 = self.selecionar_coluna(
            df2,
            "Selecione a coluna de CPF do arquivo 2:"
        )

        # 3. Pasta de saída (antes do processamento, para já poder salvar)
        pasta_saida = self.selecionar_pasta_saida(
            "Selecione a pasta onde deseja salvar os dois arquivos:"
        )
        os.makedirs(pasta_saida, exist_ok=True)

        # Normaliza CPF (só dígitos, 11 posições)
        def normalizar_cpf(cpf):
            if pd.isna(cpf) or cpf == '' or str(cpf).strip() == '':
                return ''
            try:
                cpf_limpo = re.sub(r'\D', '', str(cpf).strip())
                if not cpf_limpo:
                    return ''
                return cpf_limpo.zfill(11)[:11]
            except Exception:
                return ''

        # 4. Monta set de CPFs do arquivo 2
        self.console.print("[cyan]Normalizando CPFs do arquivo 2...[/cyan]")
        cpfs_arquivo2 = set(
            cpf for cpf in df2[coluna_cpf_2].apply(normalizar_cpf).tolist() if cpf
        )
        self.console.print(Panel(
            f"[green]CPFs únicos no arquivo 2: {len(cpfs_arquivo2):,}[/green]",
            title="Lista de Referência",
            border_style="green"
        ))

        # 5. Filtra arquivo 1
        self.console.print("[cyan]Filtrando arquivo 1...[/cyan]")
        cpfs_norm_1 = df1[coluna_cpf_1].apply(normalizar_cpf)
        mask_presente = cpfs_norm_1.isin(cpfs_arquivo2)

        df_presente = df1[mask_presente].copy()
        df_ausente = df1[~mask_presente].copy()

        nome_original = os.path.basename(arquivo_1)
        caminho_presente = self.salvar_arquivo_blacklist(
            df_presente, nome_original, "presente_arquivo2", pasta_saida
        )
        caminho_ausente = self.salvar_arquivo_blacklist(
            df_ausente, nome_original, "ausente_arquivo2", pasta_saida
        )

        self.console.print(Panel(
            f"[bold green]Processamento concluído![/bold green]\n\n"
            f"[cyan]Estatísticas:[/cyan]\n"
            f"├─ Total arquivo 1: {len(df1):,}\n"
            f"├─ Presentes no arquivo 2: {len(df_presente):,}\n"
            f"├─ Ausentes no arquivo 2: {len(df_ausente):,}\n"
            f"└─ CPFs únicos no arquivo 2: {len(cpfs_arquivo2):,}\n\n"
            f"[cyan]Arquivos gerados:[/cyan]\n"
            f"├─ {caminho_presente}\n"
            f"└─ {caminho_ausente}",
            title="Relatório Final",
            border_style="green"
        ))

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
                Choice(15000, name="15.000 linhas"),
                Choice(20000, name="20.000 linhas"),
                Choice(30000, name="30.000 linhas"),
                Choice(50000, name="50.000 linhas"),
                Choice(80000, name="80.000 linhas"),
                Choice(100000, name="100.000 linhas"),
                Choice(150000, name="150.000 linhas"),
                Choice(200000, name="200.000 linhas"),
                Choice(300000, name="300.000 linhas"),
                Choice(500000, name="500.000 linhas"),
                Choice(1000000, name="1.000.000 linhas"),
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

    def selecionar_coluna(self, df, mensagem):
        """Permite ao usuário selecionar uma coluna do DataFrame"""
        colunas = list(df.columns)
        return inquirer.select(
            message=mensagem,
            choices=colunas,
        ).execute()

    def remover_linhas_vazias_arquivo_unico(self):
        """Remove linhas onde uma coluna específica está vazia, com valor 0 ou .0"""
        # Seleciona arquivo
        arquivo = self.selecionar_arquivo("Selecione o arquivo para processar:")
        
        # Carrega arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas_original = len(df)
            
            if total_linhas_original == 0:
                self.console.print(Panel(
                    "[red]O arquivo está vazio![/red]",
                    title="Erro",
                    border_style="red"
                ))
                return
                
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Mostra informações do arquivo
        self.console.print(Panel(
            f"[green]Arquivo carregado com sucesso![/green]\n"
            f"Total de registros: {total_linhas_original:,}\n"
            f"Total de colunas: {len(df.columns)}",
            title="Arquivo Carregado",
            border_style="green"
        ))
        
        # Seleciona coluna para filtrar
        coluna_selecionada = self.selecionar_coluna(
            df, 
            "Selecione a coluna para verificar valores vazios/zero:"
        )
        
        # Mostra estatísticas da coluna antes do filtro
        valores_vazios = df[coluna_selecionada].isna().sum()
        valores_zero = (df[coluna_selecionada] == 0).sum()
        valores_ponto_zero = (df[coluna_selecionada] == 0.0).sum()
        valores_string_vazia = (df[coluna_selecionada] == '').sum()
        
        total_linhas_para_remover = valores_vazios + valores_zero + valores_ponto_zero + valores_string_vazia
        
        self.console.print(Panel(
            f"[cyan]Estatísticas da coluna '{coluna_selecionada}':[/cyan]\n"
            f"├─ Valores vazios (NaN): {valores_vazios:,}\n"
            f"├─ Valores zero (0): {valores_zero:,}\n"
            f"├─ Valores ponto zero (0.0): {valores_ponto_zero:,}\n"
            f"├─ Strings vazias (''): {valores_string_vazia:,}\n"
            f"└─ Total de linhas que serão removidas: {total_linhas_para_remover:,}\n\n"
            f"[yellow]Linhas que permanecerão: {total_linhas_original - total_linhas_para_remover:,}[/yellow]",
            title="Análise da Coluna",
            border_style="cyan"
        ))
        
        # Confirma se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e remover {total_linhas_para_remover:,} linhas?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # Aplica o filtro
        df_filtrado = df[
            (df[coluna_selecionada].notna()) &  # Remove NaN
            (df[coluna_selecionada] != 0) &     # Remove 0
            (df[coluna_selecionada] != 0.0) &   # Remove 0.0
            (df[coluna_selecionada] != '')      # Remove strings vazias
        ].copy()
        
        total_linhas_final = len(df_filtrado)
        linhas_removidas = total_linhas_original - total_linhas_final
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo filtrado:")
        
        # Salva arquivo filtrado
        nome_arquivo = os.path.basename(arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"filtrado_vazios_{nome_base}.csv")
        
        try:
            # Trata colunas numéricas que devem permanecer como string
            df_filtrado = self.tratar_colunas_numericas(df_filtrado)
            
            df_filtrado.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            # Cria mensagem de sucesso
            mensagem = (
                f"[bold green]Filtro aplicado com sucesso![/bold green]\n\n"
                f"[cyan]Estatísticas do Processamento:[/cyan]\n"
                f"├─ Arquivo original: {nome_arquivo}\n"
                f"├─ Coluna filtrada: {coluna_selecionada}\n"
                f"├─ Linhas originais: {total_linhas_original:,}\n"
                f"├─ Linhas removidas: {linhas_removidas:,}\n"
                f"├─ Linhas mantidas: {total_linhas_final:,}\n"
                f"└─ Taxa de redução: {(linhas_removidas/total_linhas_original*100):.1f}%\n\n"
                f"[green]Arquivo salvo como:[/green]\n"
                f"└─ {caminho_saida}"
            )
            
            self.console.print(Panel(
                mensagem,
                title="Filtro Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def remover_linhas_vazias_em_lote(self):
        """Remove linhas com valores vazios/zero em múltiplos arquivos"""
        # Seleciona pasta com arquivos
        pasta_entrada = self.selecionar_pasta("Selecione a pasta com os arquivos para processar:")
        
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
        
        self.console.print(Panel(
            f"[cyan]Processamento em Lote[/cyan]\n\n"
            f"Pasta selecionada: {pasta_entrada}\n"
            f"Total de arquivos CSV encontrados: {len(arquivos_csv):,}\n\n"
            f"[yellow]Arquivos que serão processados:[/yellow]\n" + 
            "\n".join([f"• {os.path.basename(arquivo)}" for arquivo in arquivos_csv[:10]]) +
            (f"\n... e mais {len(arquivos_csv) - 10} arquivos" if len(arquivos_csv) > 10 else ""),
            title="Iniciando Processamento",
            border_style="blue"
        ))
        
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
        total_linhas_mantidas = 0
        total_linhas_removidas = 0
        
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
                
                # Tenta identificar coluna automaticamente ou pergunta ao usuário
                coluna_selecionada = self.identificar_coluna_para_filtro(df, nome_arquivo)
                
                if not coluna_selecionada:
                    self.console.print(f"[red]❌ Não foi possível identificar coluna para filtrar em: {nome_arquivo}[/red]")
                    arquivos_com_erro += 1
                    continue
                
                # Aplica o filtro
                df_filtrado = df[
                    (df[coluna_selecionada].notna()) &  # Remove NaN
                    (df[coluna_selecionada] != 0) &     # Remove 0
                    (df[coluna_selecionada] != 0.0) &   # Remove 0.0
                    (df[coluna_selecionada] != '')      # Remove strings vazias
                ].copy()
                
                linhas_mantidas = len(df_filtrado)
                linhas_removidas = total_linhas - linhas_mantidas
                
                # Salva arquivo processado
                nome_base = os.path.splitext(nome_arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"lote_filtrado_{nome_base}.csv")
                
                try:
                    # Trata colunas numéricas que devem permanecer como string
                    df_filtrado = self.tratar_colunas_numericas(df_filtrado)
                    
                    df_filtrado.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                    
                    # Estatísticas do arquivo
                    estatisticas_arquivo = {
                        'arquivo': nome_arquivo,
                        'coluna_filtrada': coluna_selecionada,
                        'total_linhas': total_linhas,
                        'linhas_mantidas': linhas_mantidas,
                        'linhas_removidas': linhas_removidas,
                        'taxa_reducao': (linhas_removidas / total_linhas * 100) if total_linhas > 0 else 0
                    }
                    
                    estatisticas_arquivos.append(estatisticas_arquivo)
                    
                    # Atualiza contadores gerais
                    arquivos_processados += 1
                    total_linhas_processadas += total_linhas
                    total_linhas_mantidas += linhas_mantidas
                    total_linhas_removidas += linhas_removidas
                    
                    self.console.print(f"[green]✅ Processado: {nome_arquivo} ({linhas_mantidas}/{total_linhas} linhas mantidas)[/green]")
                    
                except Exception as e:
                    self.console.print(f"[red]❌ Erro ao salvar {nome_arquivo}: {str(e)}[/red]")
                    arquivos_com_erro += 1
                
            except Exception as e:
                self.console.print(f"[red]❌ Erro ao processar {nome_arquivo}: {str(e)}[/red]")
                arquivos_com_erro += 1
        
        # Exibe relatório final
        self.exibir_relatorio_filtro_lote(
            total_arquivos, arquivos_processados, arquivos_com_erro,
            total_linhas_processadas, total_linhas_mantidas, total_linhas_removidas,
            estatisticas_arquivos, pasta_saida
        )

    def identificar_coluna_para_filtro(self, df, nome_arquivo):
        """Tenta identificar automaticamente a coluna para filtrar ou pergunta ao usuário"""
        colunas = list(df.columns)
        
        # Se só tem uma coluna, usa ela
        if len(colunas) == 1:
            self.console.print(f"[cyan]🔍 Coluna única identificada: {colunas[0]}[/cyan]")
            return colunas[0]
        
        # Se tem múltiplas colunas, pergunta ao usuário
        self.console.print(f"[yellow]⚠️  Arquivo {nome_arquivo} tem múltiplas colunas. Selecione a coluna para filtrar:[/yellow]")
        return self.selecionar_coluna(df, "Selecione a coluna para verificar valores vazios/zero:")

    def exibir_relatorio_filtro_lote(self, total_arquivos, arquivos_processados, arquivos_com_erro,
                                    total_linhas_processadas, total_linhas_mantidas, total_linhas_removidas,
                                    estatisticas_arquivos, pasta_saida):
        """Exibe relatório detalhado do processamento em lote"""
        
        # Calcula estatísticas gerais
        taxa_reducao_geral = (total_linhas_removidas / total_linhas_processadas * 100) if total_linhas_processadas > 0 else 0
        taxa_sucesso = (arquivos_processados / total_arquivos * 100) if total_arquivos > 0 else 0
        
        # Ordena estatísticas por taxa de redução (maior para menor)
        estatisticas_ordenadas = sorted(estatisticas_arquivos, key=lambda x: x['taxa_reducao'], reverse=True)
        
        # Cria mensagem do relatório
        mensagem = (
            f"[bold cyan]RELATÓRIO DE FILTRO EM LOTE[/bold cyan]\n\n"
            f"[bold]Resumo Geral:[/bold]\n"
            f"├─ Total de arquivos encontrados: {total_arquivos:,}\n"
            f"├─ Arquivos processados com sucesso: {arquivos_processados:,}\n"
            f"├─ Arquivos com erro: {arquivos_com_erro:,}\n"
            f"├─ Taxa de sucesso: {taxa_sucesso:.1f}%\n\n"
            f"[bold]Estatísticas de Dados:[/bold]\n"
            f"├─ Total de linhas processadas: {total_linhas_processadas:,}\n"
            f"├─ Linhas mantidas: {total_linhas_mantidas:,}\n"
            f"├─ Linhas removidas: {total_linhas_removidas:,}\n"
            f"└─ Taxa de redução geral: {taxa_reducao_geral:.1f}%\n\n"
            f"[bold]Pasta de saída:[/bold]\n"
            f"└─ {pasta_saida}\n\n"
        )
        
        # Adiciona detalhes dos arquivos (top 10 com maior redução)
        if estatisticas_ordenadas:
            mensagem += "[bold green]Top 10 - Maior Redução:[/bold green]\n"
            for i, stats in enumerate(estatisticas_ordenadas[:10], 1):
                mensagem += (
                    f"{i:2d}. {stats['arquivo']:<30} "
                    f"{stats['linhas_mantidas']:>6}/{stats['total_linhas']:<6} "
                    f"({stats['taxa_reducao']:>5.1f}%)\n"
                )
            
            if len(estatisticas_ordenadas) > 10:
                mensagem += f"... e mais {len(estatisticas_ordenadas) - 10} arquivos\n"
            
            mensagem += "\n"
            
            # Adiciona arquivos com menor redução se houver
            menores = estatisticas_ordenadas[-10:] if len(estatisticas_ordenadas) > 10 else estatisticas_ordenadas
            if menores and menores[-1]['taxa_reducao'] > 0:
                mensagem += "[bold blue]Arquivos com Menor Redução:[/bold blue]\n"
                for i, stats in enumerate(menores, 1):
                    mensagem += (
                        f"{i:2d}. {stats['arquivo']:<30} "
                        f"{stats['linhas_mantidas']:>6}/{stats['total_linhas']:<6} "
                        f"({stats['taxa_reducao']:>5.1f}%)\n"
                    )
                mensagem += "\n"
        
        # Adiciona informações sobre o filtro aplicado
        mensagem += (
            "[bold]Filtro aplicado:[/bold]\n"
            f"├─ Remove valores NaN (vazios)\n"
            f"├─ Remove valores 0\n"
            f"├─ Remove valores 0.0\n"
            f"└─ Remove strings vazias ('')\n\n"
            f"[bold blue]💡 Dica:[/bold blue] Arquivos com prefixo 'lote_filtrado_' foram processados com sucesso!"
        )
        
        # Salva relatório detalhado em CSV
        if estatisticas_arquivos:
            try:
                df_relatorio = pd.DataFrame(estatisticas_arquivos)
                relatorio_path = os.path.join(pasta_saida, "relatorio_filtro_lote.csv")
                df_relatorio.to_csv(relatorio_path, sep=';', encoding='utf-8', index=False)
                mensagem += f"\n\n[bold green]📊 Relatório detalhado salvo:[/bold green]\n└─ {relatorio_path}"
            except Exception as e:
                mensagem += f"\n\n[bold red]❌ Erro ao salvar relatório: {str(e)}[/bold red]"
        
        self.console.print(Panel(
            mensagem,
            title="Filtro em Lote Concluído",
            border_style="green"
        ))

    def calcular_idade(self, data_nascimento):
        """Calcula idade baseada na data de nascimento"""
        from datetime import datetime, date
        
        try:
            # Tenta diferentes formatos de data
            formatos_data = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%Y/%m/%d',
                '%d/%m/%y', '%d-%m-%y', '%y-%m-%d', '%y/%m/%d',
                '%d/%m/%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S',
                '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S'
            ]
            
            data_obj = None
            for formato in formatos_data:
                try:
                    data_obj = datetime.strptime(str(data_nascimento), formato)
                    break
                except:
                    continue
            
            if data_obj is None:
                return None
            
            hoje = date.today()
            idade = hoje.year - data_obj.year - ((hoje.month, hoje.day) < (data_obj.month, data_obj.day))
            return idade
            
        except:
            return None

    def adicionar_coluna_idade(self):
        """Adiciona coluna de idade baseada na data de nascimento"""
        # Seleciona arquivo
        arquivo = self.selecionar_arquivo("Selecione o arquivo CSV para processar:")
        
        # Carrega arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas_original = len(df)
            
            if total_linhas_original == 0:
                self.console.print(Panel(
                    "[red]O arquivo está vazio![/red]",
                    title="Erro",
                    border_style="red"
                ))
                return
                
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Mostra informações do arquivo
        self.console.print(Panel(
            f"[green]Arquivo carregado com sucesso![/green]\n"
            f"Total de registros: {total_linhas_original:,}\n"
            f"Total de colunas: {len(df.columns)}",
            title="Arquivo Carregado",
            border_style="green"
        ))
        
        # Seleciona coluna de data de nascimento
        coluna_data = self.selecionar_coluna(
            df, 
            "Selecione a coluna que contém a data de nascimento:"
        )
        
        # Mostra alguns exemplos da coluna selecionada
        exemplos = df[coluna_data].dropna().head(5).tolist()
        self.console.print(Panel(
            f"[cyan]Exemplos de datas na coluna '{coluna_data}':[/cyan]\n" +
            "\n".join([f"• {exemplo}" for exemplo in exemplos]),
            title="Exemplos de Datas",
            border_style="cyan"
        ))
        
        # Confirma se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e adicionar a coluna de idade baseada na coluna '{coluna_data}'?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # Calcula idade para cada linha
        self.console.print("[cyan]Calculando idades...[/cyan]")
        df['idade'] = df[coluna_data].apply(self.calcular_idade)
        
        # Estatísticas das idades calculadas
        idades_validas = df['idade'].notna().sum()
        idades_invalidas = df['idade'].isna().sum()
        
        if idades_validas > 0:
            idade_min = df['idade'].min()
            idade_max = df['idade'].max()
            idade_media = df['idade'].mean()
            
            self.console.print(Panel(
                f"[green]Idades calculadas com sucesso![/green]\n"
                f"├─ Idades válidas: {idades_validas:,}\n"
                f"├─ Idades inválidas: {idades_invalidas:,}\n"
                f"├─ Idade mínima: {idade_min:.0f} anos\n"
                f"├─ Idade máxima: {idade_max:.0f} anos\n"
                f"└─ Idade média: {idade_media:.1f} anos",
                title="Estatísticas das Idades",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                f"[red]Nenhuma idade válida foi calculada![/red]\n"
                f"Verifique se o formato das datas está correto.",
                title="Erro no Cálculo",
                border_style="red"
            ))
            return
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo com idade:")
        
        # Salva arquivo com idade
        nome_arquivo = os.path.basename(arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"com_idade_{nome_base}.csv")
        
        try:
            # Trata colunas numéricas que devem permanecer como string
            df = self.tratar_colunas_numericas(df.copy())
            
            df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Arquivo original: {nome_arquivo}\n"
                f"├─ Arquivo processado: com_idade_{nome_base}.csv\n"
                f"├─ Total de registros: {total_linhas_original:,}\n"
                f"├─ Idades calculadas: {idades_validas:,}\n"
                f"└─ Local: {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def formatar_coluna_data(self):
        """Formata e normaliza coluna de data para dd/MM/AAAA"""
        # Seleciona arquivo
        arquivo = self.selecionar_arquivo("Selecione o arquivo CSV para processar:")
        
        # Carrega arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas_original = len(df)
            
            if total_linhas_original == 0:
                self.console.print(Panel(
                    "[red]O arquivo está vazio![/red]",
                    title="Erro",
                    border_style="red"
                ))
                return
                
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Mostra informações do arquivo
        self.console.print(Panel(
            f"[green]Arquivo carregado com sucesso![/green]\n"
            f"Total de registros: {total_linhas_original:,}\n"
            f"Total de colunas: {len(df.columns)}",
            title="Arquivo Carregado",
            border_style="green"
        ))
        
        # Seleciona coluna de data
        coluna_data = self.selecionar_coluna(
            df, 
            "Selecione a coluna que contém a data:"
        )
        
        # Mostra alguns exemplos da coluna selecionada
        exemplos = df[coluna_data].dropna().head(5).tolist()
        self.console.print(Panel(
            f"[cyan]Exemplos de datas na coluna '{coluna_data}':[/cyan]\n" +
            "\n".join([f"• {str(exemplo)}" for exemplo in exemplos]),
            title="Exemplos de Datas",
            border_style="cyan"
        ))
        
        # Confirma se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e formatar a coluna '{coluna_data}' para dd/MM/AAAA?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # Formata datas
        self.console.print("[cyan]Formatando datas...[/cyan]")
        
        def formatar_data_para_dd_mm_aaaa(valor):
            """Formata data para dd/MM/AAAA"""
            if pd.isna(valor) or valor == '' or str(valor).strip() == '':
                return ''
            
            try:
                valor_str = str(valor).strip()
                
                # Tenta diferentes formatos de entrada
                formatos_entrada = [
                    '%Y-%m-%d %H:%M:%S',  # 1952-08-17 00:00:00
                    '%Y-%m-%d',          # 1952-08-17
                    '%d/%m/%Y',          # 17/08/1952
                    '%d/%m/%Y %H:%M:%S', # 17/08/1952 00:00:00
                    '%d-%m-%Y',          # 17-08-1952
                    '%Y/%m/%d',          # 1952/08/17
                ]
                
                # Tenta converter usando pandas to_datetime primeiro
                try:
                    data = pd.to_datetime(valor_str, errors='coerce')
                    if pd.notna(data):
                        return data.strftime('%d/%m/%Y')
                except:
                    pass
                
                # Tenta cada formato manualmente
                from datetime import datetime
                for formato in formatos_entrada:
                    try:
                        data = datetime.strptime(valor_str, formato)
                        return data.strftime('%d/%m/%Y')
                    except:
                        continue
                
                # Se não conseguir converter, retorna o valor original
                return valor_str
                
            except Exception as e:
                return str(valor)
        
        # Aplica formatação
        df[coluna_data] = df[coluna_data].apply(formatar_data_para_dd_mm_aaaa)
        
        # Estatísticas da formatação
        datas_formatadas = df[coluna_data].notna().sum()
        datas_vazias = df[coluna_data].isna().sum()
        
        # Mostra alguns exemplos após formatação
        exemplos_formatados = df[coluna_data].dropna().head(5).tolist()
        self.console.print(Panel(
            f"[green]Datas formatadas com sucesso![/green]\n"
            f"├─ Datas formatadas: {datas_formatadas:,}\n"
            f"├─ Datas vazias: {datas_vazias:,}\n\n"
            f"[cyan]Exemplos após formatação:[/cyan]\n" +
            "\n".join([f"• {exemplo}" for exemplo in exemplos_formatados]),
            title="Formatação Concluída",
            border_style="green"
        ))
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo formatado:")
        
        # Salva arquivo formatado
        nome_arquivo = os.path.basename(arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"formatado_{nome_base}.csv")
        
        try:
            # Trata colunas numéricas que devem permanecer como string
            df = self.tratar_colunas_numericas(df.copy())
            
            df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Arquivo original: {nome_arquivo}\n"
                f"├─ Arquivo processado: formatado_{nome_base}.csv\n"
                f"├─ Total de registros: {total_linhas_original:,}\n"
                f"├─ Datas formatadas: {datas_formatadas:,}\n"
                f"└─ Local: {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def calcular_idade_data(self):
        """Calcula idade com base na data de nascimento e adiciona coluna 'idade'"""
        from datetime import date
        
        # Seleciona arquivo
        arquivo = self.selecionar_arquivo("Selecione o arquivo CSV para processar:")
        
        # Carrega arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas_original = len(df)
            
            if total_linhas_original == 0:
                self.console.print(Panel(
                    "[red]O arquivo está vazio![/red]",
                    title="Erro",
                    border_style="red"
                ))
                return
                
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Mostra informações do arquivo
        self.console.print(Panel(
            f"[green]Arquivo carregado com sucesso![/green]\n"
            f"Total de registros: {total_linhas_original:,}\n"
            f"Total de colunas: {len(df.columns)}",
            title="Arquivo Carregado",
            border_style="green"
        ))
        
        # Seleciona coluna de data de nascimento
        coluna_data = self.selecionar_coluna(
            df, 
            "Selecione a coluna que contém a data de nascimento:"
        )
        
        # Mostra alguns exemplos da coluna selecionada
        exemplos = df[coluna_data].dropna().head(5).tolist()
        self.console.print(Panel(
            f"[cyan]Exemplos de datas na coluna '{coluna_data}':[/cyan]\n" +
            "\n".join([f"• {str(exemplo)}" for exemplo in exemplos]),
            title="Exemplos de Datas",
            border_style="cyan"
        ))
        
        # Confirma se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e calcular idade baseada na coluna '{coluna_data}'?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # Calcula idade
        self.console.print("[cyan]Calculando idades...[/cyan]")
        
        def calcular_idade_hoje(data_nascimento):
            """Calcula idade a partir da data de nascimento"""
            if pd.isna(data_nascimento) or data_nascimento == '' or str(data_nascimento).strip() == '':
                return None
            
            try:
                # Tenta converter usando pandas to_datetime (mais robusto)
                data_obj = pd.to_datetime(data_nascimento, errors='coerce', dayfirst=True)
                
                if pd.isna(data_obj):
                    return None
                
                # Calcula idade
                hoje = date.today()
                idade = hoje.year - data_obj.year - ((hoje.month, hoje.day) < (data_obj.month, data_obj.day))
                
                # Verifica se a idade é válida (entre 0 e 150 anos)
                if 0 <= idade <= 150:
                    return int(idade)
                else:
                    return None
                    
            except Exception as e:
                return None
        
        # Aplica cálculo de idade
        df['idade'] = df[coluna_data].apply(calcular_idade_hoje)
        
        # Estatísticas das idades calculadas
        idades_validas = df['idade'].notna().sum()
        idades_invalidas = df['idade'].isna().sum()
        
        if idades_validas > 0:
            idade_min = int(df['idade'].min())
            idade_max = int(df['idade'].max())
            idade_media = float(df['idade'].mean())
            
            self.console.print(Panel(
                f"[green]Idades calculadas com sucesso![/green]\n"
                f"├─ Idades válidas: {idades_validas:,}\n"
                f"├─ Idades inválidas: {idades_invalidas:,}\n"
                f"├─ Idade mínima: {idade_min} anos\n"
                f"├─ Idade máxima: {idade_max} anos\n"
                f"└─ Idade média: {idade_media:.1f} anos",
                title="Estatísticas das Idades",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                f"[red]Nenhuma idade válida foi calculada![/red]\n"
                f"Verifique se o formato das datas está correto.",
                title="Erro no Cálculo",
                border_style="red"
            ))
            return
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo com idade:")
        
        # Salva arquivo com idade
        nome_arquivo = os.path.basename(arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"com_idade_{nome_base}.csv")
        
        try:
            # Trata colunas numéricas que devem permanecer como string
            df = self.tratar_colunas_numericas(df.copy())
            
            # Garante que a coluna idade seja inteira
            df['idade'] = df['idade'].astype('Int64')  # Int64 permite NaN
            
            df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Arquivo original: {nome_arquivo}\n"
                f"├─ Arquivo processado: com_idade_{nome_base}.csv\n"
                f"├─ Total de registros: {total_linhas_original:,}\n"
                f"├─ Idades calculadas: {idades_validas:,}\n"
                f"├─ Idades inválidas: {idades_invalidas:,}\n"
                f"└─ Local: {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def atualizar_idade_data_nascimento(self):
        """Usa a coluna de data de nascimento (ex.: NASC) para recalcular e atualizar a coluna de idade."""
        from datetime import date

        arquivo = self.selecionar_arquivo("Selecione o arquivo CSV para processar:")
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas = len(df)
            if total_linhas == 0:
                self.console.print(Panel("[red]O arquivo está vazio![/red]", title="Erro", border_style="red"))
                return
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return

        colunas_lower = {c.strip().lower(): c for c in df.columns}
        nomes_data = ('nasc', 'data_nascimento', 'data nascimento', 'datanascimento')
        coluna_data = None
        for nome in nomes_data:
            if nome in colunas_lower:
                coluna_data = colunas_lower[nome]
                break
        if coluna_data is None:
            coluna_data = self.selecionar_coluna(
                df, "Selecione a coluna de data de nascimento (ex.: NASC):"
            )

        coluna_idade = None
        for c in df.columns:
            if c.strip().lower() in ('idade',):
                coluna_idade = c
                break
        if coluna_idade is None:
            coluna_idade = 'IDADE'

        def calcular_idade_hoje(data_nascimento):
            if pd.isna(data_nascimento) or data_nascimento == '' or str(data_nascimento).strip() == '':
                return None
            try:
                data_obj = pd.to_datetime(data_nascimento, errors='coerce', dayfirst=True)
                if pd.isna(data_obj):
                    return None
                hoje = date.today()
                idade = hoje.year - data_obj.year - ((hoje.month, hoje.day) < (data_obj.month, data_obj.day))
                if 0 <= idade <= 150:
                    return int(idade)
                return None
            except Exception:
                return None

        self.console.print("[cyan]Calculando e atualizando idades...[/cyan]")
        df[coluna_idade] = df[coluna_data].apply(calcular_idade_hoje)

        idades_validas = df[coluna_idade].notna().sum()
        idades_invalidas = df[coluna_idade].isna().sum()

        if idades_validas > 0:
            idade_min = int(df[coluna_idade].min())
            idade_max = int(df[coluna_idade].max())
            idade_media = float(df[coluna_idade].mean())
            self.console.print(Panel(
                f"[green]Idades atualizadas com sucesso![/green]\n"
                f"├─ Coluna data: {coluna_data}\n"
                f"├─ Coluna idade: {coluna_idade}\n"
                f"├─ Idades válidas: {idades_validas:,}\n"
                f"├─ Idades inválidas: {idades_invalidas:,}\n"
                f"├─ Idade mínima: {idade_min} anos\n"
                f"├─ Idade máxima: {idade_max} anos\n"
                f"└─ Idade média: {idade_media:.1f} anos",
                title="Estatísticas",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                "[red]Nenhuma idade válida calculada. Verifique o formato das datas.[/red]",
                title="Erro no Cálculo",
                border_style="red"
            ))
            return

        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        nome_arquivo = os.path.basename(arquivo)
        caminho_saida = os.path.join(pasta_saida, nome_arquivo)

        try:
            # Garante idades inválidas como NA e cast Int64 antes do tratamento de strings
            df[coluna_idade] = pd.to_numeric(df[coluna_idade], errors='coerce').astype('Int64')
            df = self.tratar_colunas_numericas(df.copy())
            # Reaplica Int64 na coluna de idade (tratar pode ter tocado outras colunas)
            df[coluna_idade] = pd.to_numeric(df[coluna_idade], errors='coerce').astype('Int64')
            df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Registros: {total_linhas:,}\n"
                f"└─ {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def formatar_coluna_cpf(self):
        """Formata e normaliza coluna de CPF preenchendo zeros à esquerda até 11 dígitos"""
        # Seleciona arquivo
        arquivo = self.selecionar_arquivo("Selecione o arquivo CSV para processar:")
        
        # Carrega arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas_original = len(df)
            
            if total_linhas_original == 0:
                self.console.print(Panel(
                    "[red]O arquivo está vazio![/red]",
                    title="Erro",
                    border_style="red"
                ))
                return
                
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Mostra informações do arquivo
        self.console.print(Panel(
            f"[green]Arquivo carregado com sucesso![/green]\n"
            f"Total de registros: {total_linhas_original:,}\n"
            f"Total de colunas: {len(df.columns)}",
            title="Arquivo Carregado",
            border_style="green"
        ))
        
        # Seleciona coluna de CPF
        coluna_cpf = self.selecionar_coluna(
            df, 
            "Selecione a coluna que contém os CPFs:"
        )
        
        # Mostra alguns exemplos da coluna selecionada
        exemplos = df[coluna_cpf].dropna().head(5).tolist()
        self.console.print(Panel(
            f"[cyan]Exemplos de CPFs na coluna '{coluna_cpf}' (antes):[/cyan]\n" +
            "\n".join([f"• {str(exemplo)}" for exemplo in exemplos]),
            title="Exemplos de CPFs",
            border_style="cyan"
        ))
        
        # Confirma se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e formatar a coluna '{coluna_cpf}' preenchendo zeros à esquerda?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # Formata CPFs
        self.console.print("[cyan]Formatando CPFs...[/cyan]")
        
        def formatar_cpf_normalizado(cpf):
            """Formata CPF removendo caracteres especiais e preenchendo zeros à esquerda"""
            if pd.isna(cpf) or cpf == '' or str(cpf).strip() == '':
                return ''
            
            try:
                # Converte para string e remove espaços
                cpf_str = str(cpf).strip()
                
                # Remove todos os caracteres não numéricos (pontos, traços, espaços, etc)
                cpf_limpo = re.sub(r'\D', '', cpf_str)
                
                # Se estiver vazio após limpeza, retorna vazio
                if not cpf_limpo:
                    return ''
                
                # Preenche com zeros à esquerda até ter 11 dígitos
                cpf_formatado = cpf_limpo.zfill(11)
                
                # Se tiver mais de 11 dígitos, pega apenas os 11 primeiros
                if len(cpf_formatado) > 11:
                    cpf_formatado = cpf_formatado[:11]
                
                return cpf_formatado
                
            except Exception as e:
                return str(cpf)
        
        # Aplica formatação
        df[coluna_cpf] = df[coluna_cpf].apply(formatar_cpf_normalizado)
        
        # Estatísticas da formatação
        cpfs_formatados = df[coluna_cpf].notna().sum()
        cpfs_vazios = (df[coluna_cpf] == '').sum()
        
        # Mostra alguns exemplos após formatação
        exemplos_formatados = df[coluna_cpf].dropna().head(5).tolist()
        exemplos_formatados = [cpf for cpf in exemplos_formatados if cpf != '']
        
        self.console.print(Panel(
            f"[green]CPFs formatados com sucesso![/green]\n"
            f"├─ CPFs formatados: {cpfs_formatados:,}\n"
            f"├─ CPFs vazios: {cpfs_vazios:,}\n\n"
            f"[cyan]Exemplos após formatação:[/cyan]\n" +
            "\n".join([f"• {cpf}" for cpf in exemplos_formatados[:5]]),
            title="Formatação Concluída",
            border_style="green"
        ))
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo formatado:")
        
        # Salva arquivo formatado
        nome_arquivo = os.path.basename(arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"cpf_formatado_{nome_base}.csv")
        
        try:
            # Trata colunas numéricas que devem permanecer como string
            df = self.tratar_colunas_numericas(df.copy())
            
            df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Arquivo original: {nome_arquivo}\n"
                f"├─ Arquivo processado: cpf_formatado_{nome_base}.csv\n"
                f"├─ Total de registros: {total_linhas_original:,}\n"
                f"├─ CPFs formatados: {cpfs_formatados:,}\n"
                f"└─ Local: {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def formatar_coluna_cnpj(self):
        """Normaliza a coluna de CNPJ para o padrão 00.000.000/0000-00."""
        arquivo = self.selecionar_arquivo("Selecione o arquivo com a coluna de CNPJ das empresas:")
        try:
            df = self.carregar_arquivo(arquivo, dtype=str)
            total_linhas_original = len(df)
            if total_linhas_original == 0:
                self.console.print(Panel("[red]O arquivo está vazio![/red]", title="Erro", border_style="red"))
                return
        except Exception as e:
            self.console.print(Panel(f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}", title="Erro", border_style="red"))
            return
        self.console.print(Panel(
            f"[green]Arquivo carregado com sucesso![/green]\n"
            f"Total de registros: {total_linhas_original:,}\n"
            f"Total de colunas: {len(df.columns)}",
            title="Arquivo Carregado",
            border_style="green"
        ))
        coluna_cnpj = self.selecionar_coluna(df, "Selecione a coluna de CNPJ das empresas:")
        exemplos = df[coluna_cnpj].dropna().head(5).tolist()
        self.console.print(Panel(
            f"[cyan]Exemplos de CNPJs na coluna '{coluna_cnpj}' (antes):[/cyan]\n" +
            "\n".join([f"• {str(ex)}" for ex in exemplos]),
            title="Exemplos de CNPJs",
            border_style="cyan"
        ))
        continuar = inquirer.confirm(
            message=f"Deseja continuar e formatar a coluna '{coluna_cnpj}' para 00.000.000/0000-00?",
            default=True,
        ).execute()
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        _fullwidth = '０１２３４５６７８９'
        _ascii_dig = '0123456789'
        def formatar_cnpj_mascara(valor):
            if pd.isna(valor) or valor == '' or str(valor).strip() == '':
                return ''
            if str(valor).strip().lower() == 'nan':
                return ''
            if isinstance(valor, (int, float)):
                raw = format(valor, '.0f')
            else:
                raw = str(valor).strip()
            for fw, ac in zip(_fullwidth, _ascii_dig):
                raw = raw.replace(fw, ac)
            conteudo = ''.join(c for c in raw if c in _ascii_dig)
            if not conteudo:
                return ''
            s = conteudo.zfill(14)[:14]
            return f"{s[0:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:14]}"
        self.console.print("[cyan]Formatando CNPJs...[/cyan]")
        df[coluna_cnpj] = df[coluna_cnpj].astype(str).apply(formatar_cnpj_mascara)
        cnpjs_formatados = (df[coluna_cnpj] != '').sum()
        cnpjs_vazios = (df[coluna_cnpj] == '').sum()
        exemplos_depois = df[coluna_cnpj][df[coluna_cnpj] != ''].head(5).tolist()
        self.console.print(Panel(
            f"[green]CNPJs formatados com sucesso![/green]\n"
            f"├─ CNPJs formatados: {cnpjs_formatados:,}\n"
            f"├─ CNPJs vazios: {cnpjs_vazios:,}\n\n"
            f"[cyan]Exemplos após formatação:[/cyan]\n" +
            "\n".join([f"• {c}" for c in exemplos_depois]),
            title="Formatação Concluída",
            border_style="green"
        ))
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo final:")
        nome_arquivo = os.path.basename(arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"cnpj_formatado_{nome_base}.csv")
        try:
            df = df.copy()
            df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Arquivo original: {nome_arquivo}\n"
                f"├─ Arquivo processado: cnpj_formatado_{nome_base}.csv\n"
                f"├─ Total de registros: {total_linhas_original:,}\n"
                f"├─ CNPJs formatados: {cnpjs_formatados:,}\n"
                f"└─ Local: {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
        except Exception as e:
            self.console.print(Panel(f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}", title="Erro", border_style="red"))

    def formatar_coluna_price_voip(self):
        """
        Formata a coluna Price do CSV VoIP com vírgula decimal e 3 casas (ex.: 0,025)
        para facilitar cálculos no Excel em locale BR.
        """
        arquivo = self.selecionar_arquivo("Selecione o arquivo VoIP (CSV ou XLSX):")
        try:
            df = self.carregar_arquivo(arquivo)
            if len(df) == 0:
                self.console.print(Panel("[red]O arquivo está vazio![/red]", title="Erro", border_style="red"))
                return
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red",
            ))
            return

        coluna_price = self.selecionar_coluna(df, "Selecione a coluna de preço (Price):")

        def parse_decimal(valor):
            if pd.isna(valor):
                return float('nan')
            s = str(valor).strip()
            if s == '' or s.lower() in ('nan', 'none'):
                return float('nan')
            s = s.replace(',', '.')
            try:
                return float(s)
            except ValueError:
                return float('nan')

        def formatar_tres_casas(valor):
            x = parse_decimal(valor)
            if x != x:
                return ''
            return f"{x:.3f}".replace('.', ',')

        df = df.copy()
        df[coluna_price] = df[coluna_price].map(formatar_tres_casas)

        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        nome_base = os.path.splitext(os.path.basename(arquivo))[0]
        caminho_saida = os.path.join(pasta_saida, f"price_formatado_{nome_base}.csv")
        try:
            df.to_csv(
                caminho_saida,
                sep=';',
                encoding='utf-8',
                index=False,
                quoting=csv.QUOTE_MINIMAL,
            )
            n_ok = (df[coluna_price] != '').sum()
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n"
                f"├─ Coluna: {coluna_price} (3 casas decimais, vírgula)\n"
                f"├─ Linhas com preço preenchido: {n_ok:,}\n"
                f"└─ {caminho_saida}",
                title="Concluído",
                border_style="green",
            ))
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar:[/red]\n\n{str(e)}",
                title="Erro",
                border_style="red",
            ))

    def _voip_resumo_datas_para_painel(self, ts):
        """
        Retorna texto: dia mín/máx (calendário), hora mín/máx apenas no último dia,
        e intervalo datetime completo. ts = Series datetime com NaT possíveis.
        """
        if not isinstance(ts, pd.Series):
            ts = pd.Series(ts, dtype='datetime64[ns]')
        ts_ok = ts.dropna()
        if ts_ok.empty:
            return (
                "Dia mínimo: —\n"
                "Dia máximo: —\n"
                "No último dia com dados — hora mínima: — | hora máxima: —\n"
                "Intervalo completo (data e hora): — | —"
            )
        dia_min = ts_ok.min().strftime('%d/%m/%Y')
        dia_max = ts_ok.max().strftime('%d/%m/%Y')
        t_norm = ts_ok.dt.normalize()
        ultimo_dia = t_norm.max()
        no_ultimo = ts_ok[t_norm == ultimo_dia]
        hora_min_ud = no_ultimo.min().strftime('%H:%M:%S')
        hora_max_ud = no_ultimo.max().strftime('%H:%M:%S')
        ini_c = ts_ok.min().strftime('%d/%m/%Y %H:%M:%S')
        fim_c = ts_ok.max().strftime('%d/%m/%Y %H:%M:%S')
        return (
            f"Dia mínimo (primeiro dia com registro): {dia_min}\n"
            f"Dia máximo (último dia com registro): {dia_max}\n"
            f"No último dia ({dia_max}) — hora mínima: {hora_min_ud} | hora máxima: {hora_max_ud}\n"
            f"Intervalo completo (data e hora): início {ini_c} | fim {fim_c}"
        )

    def exportar_voip_price_formatado_com_relatorio(self):
        """
        Lê apenas o arquivo VoIP, grava CSV com Price em vírgula (3 casas) e TXT com
        totais de ligações, soma do Price e faixa de data/hora.
        Permite ver resumo de datas e filtrar por intervalo de dias.
        """
        from options.dados.adicao_mesclagem.add_or_mescle import AddOrMescle

        arquivo = self.selecionar_arquivo("Selecione o arquivo VoIP (CSV ou XLSX):")
        pular_linha = inquirer.select(
            message="A primeira linha do arquivo é inválida (cabeçalho na linha 2)?",
            choices=[
                Choice(False, name="Não — cabeçalho na linha 1"),
                Choice(True, name="Sim — pular primeira linha"),
            ],
        ).execute()
        carregador = AddOrMescle()
        try:
            if pular_linha:
                df = carregador.carregar_arquivo_pulando_primeira_linha(arquivo)
            else:
                df = carregador.carregar_arquivo(arquivo)
            if len(df) == 0:
                self.console.print(Panel("[red]O arquivo está vazio![/red]", title="Erro", border_style="red"))
                return
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red",
            ))
            return

        coluna_price = self.selecionar_coluna(df, "Selecione a coluna de preço (Price):")
        coluna_data = self.selecionar_coluna(
            df, "Selecione a coluna de data e hora da ligação (ex.: Start Time, Data & Hora):"
        )
        fmt_data_arquivo = inquirer.select(
            message="Formato da data/hora nessa coluna no arquivo VoIP:",
            choices=[
                Choice("us", name="Americano — MM/dd/YYYY (ex.: export MONEY_ANTISPAM)"),
                Choice("br", name="Brasileiro — dd/mm/aaaa"),
            ],
        ).execute()
        dayfirst_voip = fmt_data_arquivo == "br"
        legenda_fmt = (
            "interpretação da coluna: formato US (MM/dd/YYYY)"
            if fmt_data_arquivo == "us"
            else "interpretação da coluna: formato BR (dd/mm/aaaa)"
        )

        ts_full = pd.to_datetime(df[coluna_data], dayfirst=dayfirst_voip, errors='coerce')
        texto_resumo = self._voip_resumo_datas_para_painel(ts_full)
        self.console.print(Panel(
            f"[cyan]{texto_resumo}[/cyan]",
            title="Resumo de datas no arquivo completo",
            border_style="cyan",
        ))

        modo = inquirer.select(
            message="Como deseja exportar?",
            choices=[
                Choice("todos", name="Usar todos os registros"),
                Choice("filtrar", name="Filtrar por intervalo de datas (apenas dias escolhidos)"),
            ],
        ).execute()

        sufixo_arquivo = ""
        linha_filtro_rel = ""
        if modo == "filtrar":
            di = inquirer.text(
                message="Data inicial (dd/mm/aaaa):",
                default="",
            ).execute()
            df_txt = inquirer.text(
                message="Data final (dd/mm/aaaa), inclusiva:",
                default="",
            ).execute()
            try:
                d_ini = pd.to_datetime((di or "").strip(), dayfirst=True)
                d_fim = pd.to_datetime((df_txt or "").strip(), dayfirst=True)
            except Exception:
                self.console.print(Panel(
                    "[red]Datas inválidas. Use dd/mm/aaaa.[/red]",
                    title="Erro",
                    border_style="red",
                ))
                return
            if d_ini > d_fim:
                d_ini, d_fim = d_fim, d_ini
                self.console.print("[yellow]Datas invertidas — ajustado para inicial ≤ final.[/yellow]")
            # Apenas comparação de data (calendário)
            td = ts_full.dt.date
            d_ini_d = d_ini.date()
            d_fim_d = d_fim.date()
            mask = (td >= d_ini_d) & (td <= d_fim_d)
            df = df.loc[mask].copy()
            if len(df) == 0:
                self.console.print(Panel(
                    "[red]Nenhum registro no intervalo informado.[/red]",
                    title="Erro",
                    border_style="red",
                ))
                return
            sufixo_arquivo = (
                f"_de_{d_ini_d.strftime('%d%m%Y')}_ate_{d_fim_d.strftime('%d%m%Y')}"
            )
            linha_filtro_rel = (
                f'Filtro de datas aplicado: {d_ini_d.strftime("%d/%m/%Y")} a '
                f'{d_fim_d.strftime("%d/%m/%Y")} (inclusivo)'
            )

        def parse_decimal(valor):
            if pd.isna(valor):
                return float('nan')
            s = str(valor).strip()
            if s == '' or s.lower() in ('nan', 'none'):
                return float('nan')
            s = s.replace(',', '.')
            try:
                return float(s)
            except ValueError:
                return float('nan')

        preco_num = df[coluna_price].map(parse_decimal)
        n_linhas = len(df)
        n_com_valor = int(preco_num.notna().sum())
        n_cobradas_pos = int((preco_num > 0).sum())
        total_price = preco_num.sum(min_count=1)

        ts = pd.to_datetime(df[coluna_data], dayfirst=dayfirst_voip, errors='coerce')
        n_sem_data = int(ts.isna().sum())
        ts_ok = ts.dropna()
        if ts_ok.empty:
            inicio = fim = '—'
        else:
            inicio = ts_ok.min().strftime('%d/%m/%Y %H:%M:%S')
            fim = ts_ok.max().strftime('%d/%m/%Y %H:%M:%S')

        texto_resumo_export = self._voip_resumo_datas_para_painel(ts)

        def formatar_tres_casas(valor):
            x = parse_decimal(valor)
            if x != x:
                return ''
            return f"{x:.3f}".replace('.', ',')

        df_out = df.copy()
        df_out[coluna_price] = df_out[coluna_price].map(formatar_tres_casas)

        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o CSV e o relatório:")
        nome_base = os.path.splitext(os.path.basename(arquivo))[0]
        nome_arq = f"voip_price_formatado_{nome_base}{sufixo_arquivo}"
        caminho_csv = os.path.join(pasta_saida, f"{nome_arq}.csv")
        caminho_txt = os.path.join(pasta_saida, f"{nome_arq}_relatorio.txt")

        moeda = carregador._formatar_moeda_br
        inteiro = carregador._formatar_inteiro_br

        linhas_txt = [
            'RELATÓRIO — VoIP (coluna Price)',
            legenda_fmt,
            '',
        ]
        if linha_filtro_rel:
            linhas_txt.append(linha_filtro_rel)
            linhas_txt.append('')
        linhas_txt.extend([
            '--- Dados exportados (resumo de datas) ---',
            texto_resumo_export,
            '',
            f'Total de ligações (linhas exportadas): {inteiro(n_linhas)}',
            f'Ligações com preço numérico informado: {inteiro(n_com_valor)}',
            f'Ligações com valor cobrado (Price > 0): {inteiro(n_cobradas_pos)}',
            f'Valor total cobrado (soma Price): {moeda(total_price, 3)}',
            f'Intervalo de data e hora (detalhe): início {inicio} | fim {fim}',
            f'Linhas com data/hora vazia ou inválida: {inteiro(n_sem_data)}',
            '',
            f'Arquivo CSV gerado: {nome_arq}.csv',
        ])
        texto = '\n'.join(linhas_txt)

        try:
            df_out.to_csv(
                caminho_csv,
                sep=';',
                encoding='utf-8',
                index=False,
                quoting=csv.QUOTE_MINIMAL,
            )
            with open(caminho_txt, 'w', encoding='utf-8') as f:
                f.write(texto)
            self.console.print(Panel(
                f"[green]Concluído![/green]\n"
                f"├─ CSV: {caminho_csv}\n"
                f"└─ Relatório: {caminho_txt}",
                title="Sucesso",
                border_style="green",
            ))
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar:[/red]\n\n{str(e)}",
                title="Erro",
                border_style="red",
            ))

    def executar(self):
        """Executa o menu de filtros"""
        while True:
            opcao = self.menu_filters()
            
            if opcao == "1":
                self.dividir_arquivo()
            elif opcao == "2":
                self.blacklist_cpf_pasta()
            elif opcao == "3":
                self.whitelist_cpf_pasta()
            elif opcao == "4":
                self.filtrar_arquivo_por_cpf()
            elif opcao == "5":
                self.repartir_por_coluna()
            elif opcao == "6":
                self.remover_linhas_vazias_arquivo_unico()
            elif opcao == "7":
                self.remover_linhas_vazias_em_lote()
            elif opcao == "8":
                self.adicionar_coluna_idade()
            else:
                break

    def organizar_base_inss(self):
        """
        Organiza uma base INSS no formato padrão:
        CEL1, Nome, CPF, NASC, IDADE, Municipio, UF, Codigo_Banco, nome_banco,
        Valor_Parcela, Prazo, Parcelas_Paga, Parcelas_Restante, Emprestimo_Ativos,
        Beneficio, Valor_Beneficio, Margem_Disponivel, Margem_RMC, Margem_RCC.
        
        1. Recebe caminho do arquivo base (CSV)
        2. Recebe pasta de saída para salvar o arquivo organizado
        """
        # 1. Seleciona o arquivo base
        arquivo = self.selecionar_arquivo("Selecione o arquivo base INSS (CSV):")
        
        # 2. Carrega o arquivo
        try:
            df = self.carregar_arquivo(arquivo)
            total_linhas = len(df)
            
            if total_linhas == 0:
                self.console.print(Panel(
                    "[red]O arquivo está vazio![/red]",
                    title="Erro",
                    border_style="red"
                ))
                return
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))
            return
        
        # 3. Garante a existência da coluna 'nome_banco'
        if 'nome_banco' not in df.columns:
            df['nome_banco'] = ''
        
        # 4. Define as colunas finais e verifica se todas existem
        colunas_finais = [
            "CEL1",
            "Nome",
            "CPF",
            "NASC",
            "IDADE",
            "Municipio",
            "UF",
            "Codigo_Banco",
            "nome_banco",
            "Valor_Parcela",
            "Prazo",
            "Parcelas_Paga",
            "Parcelas_Restante",
            "Emprestimo_Ativos",
            "Beneficio",
            "Valor_Beneficio",
            "Margem_Disponivel",
            "Margem_RMC",
            "Margem_RCC",
        ]
        
        colunas_faltantes = [c for c in colunas_finais if c not in df.columns]
        if colunas_faltantes:
            self.console.print(Panel(
                "[red]Não foi possível organizar a base INSS.[/red]\n\n"
                "[yellow]Colunas necessárias não encontradas:[/yellow]\n"
                + "\n".join(f"• {c}" for c in colunas_faltantes)
                + "\n\n[cyan]Verifique se o arquivo base está no layout esperado.[/cyan]",
                title="Colunas Ausentes",
                border_style="red"
            ))
            return
        
        # 5. Cria DataFrame apenas com as colunas no formato final
        df_saida = df[colunas_finais].copy()
        
        # 6. Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo organizado:")
        
        # Usa o mesmo nome do arquivo original
        nome_arquivo = os.path.basename(arquivo)
        caminho_saida = os.path.join(pasta_saida, nome_arquivo)
        
        # 7. Trata colunas numéricas e salva
        try:
            df_saida = self.tratar_colunas_numericas(df_saida.copy())
            df_saida.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
            
            self.console.print(Panel(
                f"[green]Base INSS organizada com sucesso![/green]\n\n"
                f"[cyan]Resumo:[/cyan]\n"
                f"├─ Registros: {total_linhas:,}\n"
                f"├─ Colunas de saída: {len(colunas_finais)}\n"
                f"└─ Arquivo salvo em:\n   {caminho_saida}",
                title="Processamento Concluído",
                border_style="green"
            ))
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo organizado:[/red]\n\nErro: {str(e)}",
                title="Erro ao Salvar",
                border_style="red"
            ))

    def _salvar_arquivo_colunas_selecionadas(self, df, caminho_original, pasta_saida):
        """Salva CSV com colunas filtradas na pasta de saída"""
        nome_arquivo = os.path.basename(caminho_original)
        caminho_saida = os.path.join(pasta_saida, nome_arquivo)

        while True:
            try:
                df = self.tratar_colunas_numericas(df.copy())
                df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                return caminho_saida
            except PermissionError:
                self.console.print(Panel(
                    f"[red]Erro de Permissão![/red]\n\n"
                    f"Não foi possível salvar o arquivo:\n{caminho_saida}\n\n"
                    f"[cyan]Feche o arquivo se estiver aberto e tente novamente.[/cyan]",
                    title="Erro de Permissão",
                    border_style="red",
                ))
                opcao = inquirer.select(
                    message="O que deseja fazer?",
                    choices=[
                        Choice("1", name="Tentar salvar novamente no mesmo local"),
                        Choice("2", name="Escolher nova pasta para salvar"),
                    ],
                ).execute()
                if opcao == "2":
                    pasta_saida = self.selecionar_pasta_saida(
                        "Selecione uma nova pasta para salvar o arquivo:"
                    )
                    caminho_saida = os.path.join(pasta_saida, nome_arquivo)
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro ao salvar arquivo:[/red]\n\nErro: {str(e)}",
                    title="Erro",
                    border_style="red",
                ))
                pasta_saida = self.selecionar_pasta_saida(
                    "Selecione uma nova pasta para salvar o arquivo:"
                )
                caminho_saida = os.path.join(pasta_saida, nome_arquivo)

    def manter_colunas_selecionadas(self):
        """Mantém apenas colunas escolhidas pelo cabeçalho e renomeia para A, B, C..."""
        self.console.print(Panel(
            "[bold cyan]Manter Apenas Colunas Selecionadas[/bold cyan]\n"
            "Selecione os cabeçalhos que deseja manter. As demais colunas serão removidas.\n"
            "Os cabeçalhos de saída serão renomeados sequencialmente (A, B, C...).",
            title="Extrair Colunas",
            border_style="cyan",
        ))

        arquivo = self.selecionar_arquivo("Selecione o arquivo (CSV ou XLSX):")
        if not arquivo:
            return

        try:
            df = self.carregar_arquivo(arquivo)
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\n{e}",
                title="Erro",
                border_style="red",
            ))
            return

        if len(df.columns) == 0:
            self.console.print("[red]Nenhuma coluna encontrada no arquivo![/red]")
            return

        colunas_escolhidas = selecionar_colunas(
            df,
            "Selecione as colunas (cabeçalhos) que deseja manter:",
        )
        if not colunas_escolhidas:
            self.console.print("[yellow]Nenhuma coluna selecionada.[/yellow]")
            return

        try:
            df_saida = extrair_colunas_com_cabecalho_alfabetico(df, colunas_escolhidas)
        except ValueError as e:
            self.console.print(Panel(f"[red]{e}[/red]", border_style="red"))
            return

        mapeamento = "\n".join(
            f"  • {orig} → {novo}"
            for orig, novo in zip(
                [c for c in df.columns if c in set(colunas_escolhidas)],
                list(df_saida.columns),
            )
        )

        self.console.print(Panel(
            f"Arquivo: {os.path.basename(arquivo)}\n"
            f"Linhas: {len(df):,}\n"
            f"Colunas de saída: {len(df_saida.columns)}\n\n"
            f"[cyan]Mapeamento de cabeçalhos:[/cyan]\n{mapeamento}",
            title="Resumo",
            border_style="blue",
        ))

        if not inquirer.confirm(message="Processar e salvar?", default=True).execute():
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return

        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        if not pasta_saida:
            return

        caminho_saida = self._salvar_arquivo_colunas_selecionadas(df_saida, arquivo, pasta_saida)

        self.console.print(Panel(
            f"[green]Arquivo gerado com sucesso![/green]\n\n"
            f"Cabeçalhos finais: {', '.join(df_saida.columns)}\n"
            f"Salvo em:\n{caminho_saida}",
            title="Concluído",
            border_style="green",
        ))

    def manter_colunas_selecionadas_lote(self):
        """Mantém colunas selecionadas em lote (mesmos cabeçalhos em todos os arquivos)"""
        self.console.print(Panel(
            "[bold cyan]Manter Colunas Selecionadas (Lote)[/bold cyan]\n"
            "Usa o primeiro arquivo da pasta para escolher os cabeçalhos.\n"
            "Aplica a mesma seleção em todos os CSV/XLSX da pasta.",
            title="Extrair Colunas em Lote",
            border_style="cyan",
        ))

        pasta_entrada = self.selecionar_pasta("Selecione a pasta com os arquivos de entrada:")
        if not pasta_entrada:
            return

        extensoes = ('.csv', '.xlsx')
        arquivos = sorted([
            os.path.join(pasta_entrada, f)
            for f in os.listdir(pasta_entrada)
            if f.lower().endswith(extensoes)
        ])

        if not arquivos:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV ou XLSX encontrado na pasta![/red]",
                border_style="red",
            ))
            return

        try:
            df_exemplo = self.carregar_arquivo(arquivos[0])
        except Exception as e:
            self.console.print(Panel(f"[red]Erro ao carregar primeiro arquivo:[/red]\n\n{e}", border_style="red"))
            return

        colunas_escolhidas = selecionar_colunas(
            df_exemplo,
            f"Selecione as colunas (base: {os.path.basename(arquivos[0])}):",
        )
        if not colunas_escolhidas:
            self.console.print("[yellow]Nenhuma coluna selecionada.[/yellow]")
            return

        nomes_saida = gerar_nomes_colunas_alfabeticas(len(colunas_escolhidas))
        self.console.print(Panel(
            f"Pasta entrada: {pasta_entrada}\n"
            f"Arquivos: {len(arquivos)}\n"
            f"Colunas mantidas: {', '.join(colunas_escolhidas)}\n"
            f"Cabeçalhos de saída: {', '.join(nomes_saida)}",
            title="Resumo",
            border_style="blue",
        ))

        if not inquirer.confirm(
            message=f"Processar {len(arquivos)} arquivo(s)?",
            default=True,
        ).execute():
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return

        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos:")
        if not pasta_saida:
            return

        processados = []
        erros = []
        avisos = []

        self.console.print("\n[bold cyan]Processando arquivos...[/bold cyan]")

        for i, caminho in enumerate(arquivos, 1):
            nome = os.path.basename(caminho)
            self.console.print(f"[blue]{i}/{len(arquivos)}: {nome}[/blue]")
            try:
                df = self.carregar_arquivo(caminho)
                colunas_ausentes = [c for c in colunas_escolhidas if c not in df.columns]
                if colunas_ausentes:
                    avisos.append(f"{nome}: colunas ausentes — {', '.join(colunas_ausentes)}")
                df_saida = extrair_colunas_com_cabecalho_alfabetico(df, colunas_escolhidas)
                caminho_salvo = self._salvar_arquivo_colunas_selecionadas(
                    df_saida, caminho, pasta_saida
                )
                processados.append(caminho_salvo)
            except Exception as e:
                erros.append(f"{nome}: {e}")

        mensagem = f"[green]Processados com sucesso: {len(processados)}[/green]\n"
        if avisos:
            mensagem += f"\n[yellow]Avisos ({len(avisos)}):[/yellow]\n" + "\n".join(f"• {a}" for a in avisos)
        if erros:
            mensagem += f"\n[red]Erros ({len(erros)}):[/red]\n" + "\n".join(f"• {e}" for e in erros)

        self.console.print(Panel(mensagem, title="Lote Concluído", border_style="green" if not erros else "yellow"))

    def extrair_identifier_como_cpf(self):
        """Extrai a coluna 'identifier' dos CSVs de uma pasta, renomeia para CPF e salva na subpasta CPFs"""
        self.console.print(Panel(
            "[bold cyan]Extrair CPF da Coluna Identifier[/bold cyan]\n"
            "Processa todos os arquivos .csv de uma pasta.\n"
            "Extrai apenas a coluna com cabeçalho 'identifier', renomeia para 'CPF'\n"
            "e salva os arquivos na subpasta [bold]CPFs[/bold] dentro da pasta enviada.",
            title="Extrair Identifier como CPF",
            border_style="cyan",
        ))

        pasta_entrada = self.selecionar_pasta("Selecione a pasta com os arquivos CSV:")
        if not pasta_entrada:
            return

        arquivos = sorted([
            os.path.join(pasta_entrada, f)
            for f in os.listdir(pasta_entrada)
            if f.lower().endswith('.csv') and os.path.isfile(os.path.join(pasta_entrada, f))
        ])

        if not arquivos:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta![/red]",
                border_style="red",
            ))
            return

        pasta_saida = os.path.join(pasta_entrada, "CPFs")
        os.makedirs(pasta_saida, exist_ok=True)

        self.console.print(Panel(
            f"Pasta de entrada: {pasta_entrada}\n"
            f"Pasta de saída: {pasta_saida}\n"
            f"Arquivos encontrados: {len(arquivos)}",
            title="Resumo",
            border_style="blue",
        ))

        if not inquirer.confirm(
            message=f"Processar {len(arquivos)} arquivo(s)?",
            default=True,
        ).execute():
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return

        processados = []
        erros = []

        self.console.print("\n[bold cyan]Processando arquivos...[/bold cyan]")

        for i, caminho in enumerate(arquivos, 1):
            nome = os.path.basename(caminho)
            self.console.print(f"[blue]{i}/{len(arquivos)}: {nome}[/blue]")
            try:
                df = self.carregar_arquivo(caminho)
                if 'identifier' not in df.columns:
                    erros.append(f"{nome}: coluna 'identifier' não encontrada")
                    continue

                df_saida = df[['identifier']].copy()
                df_saida.columns = ['CPF']
                caminho_salvo = self._salvar_arquivo_colunas_selecionadas(
                    df_saida, caminho, pasta_saida
                )
                processados.append(caminho_salvo)
            except Exception as e:
                erros.append(f"{nome}: {e}")

        mensagem = (
            f"[green]Processados com sucesso: {len(processados)}[/green]\n"
            f"Pasta de saída: {pasta_saida}"
        )
        if erros:
            mensagem += f"\n\n[red]Erros ({len(erros)}):[/red]\n" + "\n".join(f"• {e}" for e in erros)

        self.console.print(Panel(
            mensagem,
            title="Concluído",
            border_style="green" if not erros else "yellow",
        ))
