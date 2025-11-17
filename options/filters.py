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

class Filters:
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

    def menu_filters(self):
        """Menu principal de opções de filtros"""
        return inquirer.select(
            message="Selecione o tipo de filtro:",
            choices=[
                Choice("1", name="Dividir arquivo em partes"),
                Choice("2", name="Blacklist por CPF - Arquivos por Pasta"),
                Choice("3", name="Repartir por coluna"),
                Choice("4", name="Remover linhas com valores vazios/zero (arquivo único)"),
                Choice("5", name="Remover linhas com valores vazios/zero (processamento em lote)"),
                Choice("6", name="Adicionar coluna de idade baseada na data de nascimento"),
                Choice("7", name="Voltar ao menu principal"),
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

    def carregar_arquivo(self, caminho):
        """Carrega arquivo CSV ou XLSX"""
        if caminho.endswith('.xlsx'):
            return pd.read_excel(caminho)
        else:
            try:
                return pd.read_csv(caminho, sep=';', encoding='utf-8')
            except:
                try:
                    return pd.read_csv(caminho, sep=',', encoding='utf-8')
                except:
                    try:
                        return pd.read_csv(caminho, sep=';', encoding='latin-1')
                    except:
                        return pd.read_csv(caminho, sep=',', encoding='latin-1')

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
                Choice(150000, name="150.000 linhas"),
                Choice(200000, name="200.000 linhas"),
                Choice(250000, name="250.000 linhas"),
                Choice(300000, name="300.000 linhas"),
                Choice(500000, name="500.000 linhas"),
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

    def executar(self):
        """Executa o menu de filtros"""
        while True:
            opcao = self.menu_filters()
            
            if opcao == "1":
                self.dividir_arquivo()
            elif opcao == "2":
                self.blacklist_cpf_pasta()
            elif opcao == "3":
                self.repartir_por_coluna()
            elif opcao == "4":
                self.remover_linhas_vazias_arquivo_unico()
            elif opcao == "5":
                self.remover_linhas_vazias_em_lote()
            elif opcao == "6":
                self.adicionar_coluna_idade()
            else:
                break
