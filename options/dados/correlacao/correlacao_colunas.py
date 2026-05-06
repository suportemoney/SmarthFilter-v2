#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Correlação de Colunas
Permite correlacionar colunas entre um CSV modelo e um CSV de dados
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import os
import glob
from options.utils import (
    carregar_arquivo, salvar_arquivo, selecionar_arquivo, selecionar_pasta,
    converter_numero_para_float, normalizar_valor_numerico
)

class CorrelacaoColunas:
    def __init__(self):
        self.console = Console()
        self.df_modelo = None
        self.df_dados = None
        self.mapeamento_colunas = {}

    def menu_correlacao(self):
        """Menu principal de correlação de colunas"""
        return inquirer.select(
            message="Selecione a operação:",
            choices=[
                Choice("1", name="Correlacionar Colunas"),
                Choice("2", name="Corrigir Totais de Colunas"),
                Choice("3", name="Normalizar Valores"),
                Choice("0", name="Voltar ao menu principal"),
            ],
        ).execute()

    def carregar_csv(self, caminho_arquivo):
        """Carrega um arquivo CSV e retorna o DataFrame"""
        try:
            return carregar_arquivo(caminho_arquivo)
        except Exception as e:
            self.console.print(f"[red]Erro ao carregar arquivo {caminho_arquivo}: {str(e)}[/red]")
            return None

    def exibir_colunas_dataframe(self, df, titulo):
        """Exibe as colunas de um DataFrame em formato de tabela"""
        if df is None or df.empty:
            self.console.print(f"[red]DataFrame vazio para {titulo}[/red]")
            return
        
        table = Table(title=f"Colunas do {titulo}")
        table.add_column("Índice", style="cyan", no_wrap=True)
        table.add_column("Nome da Coluna", style="magenta")
        table.add_column("Tipo", style="green")
        table.add_column("Exemplo", style="yellow")
        
        for i, col in enumerate(df.columns):
            tipo = str(df[col].dtype)
            exemplo = str(df[col].iloc[0]) if not df[col].empty else "N/A"
            if len(exemplo) > 30:
                exemplo = exemplo[:30] + "..."
            
            table.add_row(str(i), col, tipo, exemplo)
        
        self.console.print(table)

    def mapear_colunas(self):
        """Permite ao usuário mapear colunas do modelo para as colunas de dados"""
        self.console.print("\n[bold cyan]Mapeamento de Colunas[/bold cyan]")
        self.console.print("Para cada coluna do modelo, selecione a coluna correspondente nos dados ou deixe vazio")
        
        colunas_modelo = list(self.df_modelo.columns)
        colunas_dados = list(self.df_dados.columns)
        
        # Adicionar opção "Vazio" para cada coluna
        opcoes_colunas = [Choice("", name="(Vazio - não mapear)")] + [Choice(col, name=col) for col in colunas_dados]
        
        for coluna_modelo in colunas_modelo:
            self.console.print(f"\n[bold yellow]Coluna do Modelo: {coluna_modelo}[/bold yellow]")
            
            coluna_mapeada = inquirer.select(
                message=f"Selecione a coluna correspondente nos dados:",
                choices=opcoes_colunas,
            ).execute()
            
            if coluna_mapeada:  # Se não for vazio
                self.mapeamento_colunas[coluna_modelo] = coluna_mapeada
                self.console.print(f"[green]✓[/green] {coluna_modelo} → {coluna_mapeada}")
            else:
                self.console.print(f"[yellow]⚠️[/yellow] {coluna_modelo} → (não mapeada)")

    def gerar_csv_correlacionado(self, pasta_saida):
        """Gera o CSV final com as colunas correlacionadas"""
        try:
            # Criar DataFrame resultado
            df_resultado = pd.DataFrame()
            
            # Adicionar colunas mapeadas
            for coluna_modelo, coluna_dados in self.mapeamento_colunas.items():
                if coluna_dados in self.df_dados.columns:
                    df_resultado[coluna_modelo] = self.df_dados[coluna_dados]
                else:
                    # Se a coluna não existir nos dados, criar com valores vazios
                    df_resultado[coluna_modelo] = ""
            
            # Gerar nome do arquivo de saída
            nome_arquivo = "dados_correlacionados.csv"
            caminho_saida = os.path.join(pasta_saida, nome_arquivo)
            
            # Salvar CSV
            salvar_arquivo(df_resultado, caminho_saida)
            
            return caminho_saida, df_resultado
            
        except Exception as e:
            self.console.print(f"[red]Erro ao gerar CSV correlacionado: {str(e)}[/red]")
            return None, None

    def exibir_relatorio_final(self, caminho_saida, df_resultado):
        """Exibe relatório final da correlação"""
        if df_resultado is None:
            return
        
        total_linhas = len(df_resultado)
        total_colunas = len(df_resultado.columns)
        colunas_mapeadas = len(self.mapeamento_colunas)
        
        mensagem = (
            f"[bold green]Correlação Concluída![/bold green]\n\n"
            f"[cyan]Estatísticas:[/cyan]\n"
            f"├─ Total de linhas processadas: {total_linhas}\n"
            f"├─ Total de colunas no resultado: {total_colunas}\n"
            f"├─ Colunas mapeadas: {colunas_mapeadas}\n"
            f"└─ Arquivo salvo em: {caminho_saida}\n\n"
        )
        
        if self.mapeamento_colunas:
            mensagem += "[bold green]Mapeamentos realizados:[/bold green]\n"
            for i, (modelo, dados) in enumerate(self.mapeamento_colunas.items()):
                prefixo = "└─" if i == len(self.mapeamento_colunas) - 1 else "├─"
                mensagem += f"{prefixo} {modelo} → {dados}\n"
            mensagem += "\n"
        
        # Mostrar preview das primeiras linhas
        if not df_resultado.empty:
            mensagem += "[bold cyan]Preview dos dados (primeiras 3 linhas):[/bold cyan]\n"
            preview = df_resultado.head(3).to_string(index=False)
            mensagem += f"```\n{preview}\n```\n"
        
        self.console.print(Panel(
            mensagem,
            title="Relatório Final",
            border_style="green"
        ))

    def correlacionar_colunas(self):
        """Função principal para correlacionar colunas"""
        
        # 1. Selecionar arquivo modelo
        self.console.print(Panel(
            "[bold cyan]Passo 1: Selecionar CSV Modelo[/bold cyan]\n"
            "Este arquivo define a estrutura das colunas que você quer no resultado final.",
            title="Arquivo Modelo",
            border_style="cyan"
        ))
        
        arquivo_modelo = selecionar_arquivo("Selecione o arquivo CSV MODELO:")
        self.df_modelo = self.carregar_csv(arquivo_modelo)
        
        if self.df_modelo is None:
            return
        
        # 2. Selecionar arquivo de dados
        self.console.print(Panel(
            "[bold cyan]Passo 2: Selecionar CSV de Dados[/bold cyan]\n"
            "Este arquivo contém os dados que serão mapeados para a estrutura do modelo.",
            title="Arquivo de Dados",
            border_style="cyan"
        ))
        
        arquivo_dados = selecionar_arquivo("Selecione o arquivo CSV de DADOS:")
        self.df_dados = self.carregar_csv(arquivo_dados)
        
        if self.df_dados is None:
            return
        
        # 3. Exibir colunas dos dois arquivos
        self.console.print("\n[bold]Visualização das Colunas[/bold]")
        self.exibir_colunas_dataframe(self.df_modelo, "Modelo")
        self.exibir_colunas_dataframe(self.df_dados, "Dados")
        
        # 4. Mapear colunas
        self.mapear_colunas()
        
        if not self.mapeamento_colunas:
            self.console.print("[yellow]Nenhuma coluna foi mapeada. Operação cancelada.[/yellow]")
            return
        
        # 5. Selecionar pasta de saída
        pasta_saida = selecionar_pasta("Selecione a pasta para salvar o arquivo correlacionado:")
        
        # 6. Gerar CSV correlacionado
        self.console.print("\n[cyan]Gerando arquivo correlacionado...[/cyan]")
        caminho_saida, df_resultado = self.gerar_csv_correlacionado(pasta_saida)
        
        if caminho_saida:
            # 7. Exibir relatório final
            self.exibir_relatorio_final(caminho_saida, df_resultado)

    def corrigir_totais_colunas(self):
        """Corrige as colunas de totais nos arquivos CSV"""
        
        # 1. Selecionar pasta com arquivos CSV
        self.console.print(Panel(
            "[bold cyan]Passo 1: Selecionar Pasta[/bold cyan]\n"
            "Selecione a pasta que contém os arquivos CSV com o mesmo cabeçalho.",
            title="Pasta com CSVs",
            border_style="cyan"
        ))
        
        pasta_csv = selecionar_pasta("Selecione a pasta com os arquivos CSV:")
        
        # Buscar arquivos CSV na pasta
        arquivos_csv = glob.glob(os.path.join(pasta_csv, "*.csv"))
        
        if not arquivos_csv:
            self.console.print("[red]Nenhum arquivo CSV encontrado na pasta![/red]")
            return
        
        self.console.print(Panel(
            f"[green]Encontrados {len(arquivos_csv)} arquivos CSV na pasta[/green]",
            title="Arquivos Encontrados",
            border_style="green"
        ))
        
        # 2. Carregar primeiro arquivo para ver as colunas
        df_exemplo = self.carregar_csv(arquivos_csv[0])
        if df_exemplo is None:
            return
        
        colunas = list(df_exemplo.columns)
        
        # 3. Detectar automaticamente as colunas
        self.console.print("\n[bold yellow]Detecção Automática das Colunas[/bold yellow]")
        
        # Buscar colunas automaticamente
        coluna_total_utilizado = self.buscar_coluna_por_padrao(colunas, ["Total_Utilizado", "TOTAL_UTILIZADO"])
        coluna_total_saldo = self.buscar_coluna_por_padrao(colunas, ["Total_Saldo", "TOTAL_SALDO"])
        
        # Buscar colunas de utilizado automaticamente
        colunas_utilizado = self.buscar_colunas_utilizado(colunas)
        
        # Buscar colunas de saldo automaticamente
        colunas_saldo = self.buscar_colunas_saldo(colunas)
        
        # Mostrar detecção automática
        self.console.print(f"[green]✓[/green] Total Utilizado detectado: {coluna_total_utilizado}")
        self.console.print(f"[green]✓[/green] Colunas Utilizado: {', '.join(colunas_utilizado)}")
        self.console.print(f"[green]✓[/green] Total Saldo detectado: {coluna_total_saldo}")
        self.console.print(f"[green]✓[/green] Colunas Saldo: {', '.join(colunas_saldo)}")
        
        # Verificar se encontrou todas as colunas
        if not coluna_total_utilizado or not coluna_total_saldo:
            self.console.print("[red]Erro: Não foi possível detectar automaticamente as colunas de totais![/red]")
            return
        
        if len(colunas_utilizado) == 0 or len(colunas_saldo) == 0:
            self.console.print("[red]Erro: Não foi possível detectar automaticamente as colunas de componentes![/red]")
            return
        
        # 7. Mostrar preview das 3 primeiras linhas
        self.mostrar_preview_conversao(df_exemplo, colunas_utilizado, colunas_saldo)
        
        # 8. Confirmar processamento
        self.console.print(Panel(
            f"[bold cyan]Resumo da Correção:[/bold cyan]\n"
            f"├─ Total Utilizado: {coluna_total_utilizado}\n"
            f"├─ Colunas Utilizado: {', '.join(colunas_utilizado)}\n"
            f"├─ Total Saldo: {coluna_total_saldo}\n"
            f"└─ Colunas Saldo: {', '.join(colunas_saldo)}",
            title="Configuração",
            border_style="cyan"
        ))
        
        continuar = inquirer.confirm(
            message=f"Deseja processar {len(arquivos_csv)} arquivos?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # 8. Processar cada arquivo
        self.console.print("\n[cyan]Processando arquivos...[/cyan]")
        
        arquivos_processados = []
        arquivos_com_erro = []
        
        for i, arquivo_csv in enumerate(arquivos_csv, 1):
            try:
                nome_arquivo = os.path.basename(arquivo_csv)
                self.console.print(f"\n[cyan]Processando {i}/{len(arquivos_csv)}:[/cyan] {nome_arquivo}")
                
                # Carregar arquivo
                df = self.carregar_csv(arquivo_csv)
                if df is None:
                    continue
                
                # Corrigir totais
                df_corrigido = self.recalcular_totais(
                    df, 
                    coluna_total_utilizado, 
                    colunas_utilizado,
                    coluna_total_saldo, 
                    colunas_saldo
                )
                
                # Salvar arquivo corrigido
                salvar_arquivo(df_corrigido, arquivo_csv)
                
                arquivos_processados.append(nome_arquivo)
                self.console.print(f"[green]✓[/green] Arquivo corrigido com sucesso")
                
            except Exception as e:
                self.console.print(f"[red]❌[/red] Erro ao processar {nome_arquivo}: {str(e)}")
                arquivos_com_erro.append(nome_arquivo)
                continue
        
        # 9. Exibir relatório final
        self.exibir_relatorio_correcao_totais(arquivos_processados, arquivos_com_erro, pasta_csv)

    def buscar_coluna_por_padrao(self, colunas, padroes):
        """Busca uma coluna que corresponde a um dos padrões fornecidos"""
        for coluna in colunas:
            for padrao in padroes:
                if padrao.lower() in coluna.lower():
                    return coluna
        return None

    def buscar_colunas_utilizado(self, colunas):
        """Busca automaticamente as colunas de utilizado"""
        colunas_encontradas = []
        
        # Padrões de colunas de utilizado
        padroes_utilizado = [
            "Utilizado_5",
            "Utilizado_Beneficio_5", 
            "Utilizado_35"
        ]
        
        for padrao in padroes_utilizado:
            for coluna in colunas:
                if padrao.lower() in coluna.lower():
                    colunas_encontradas.append(coluna)
                    break
        
        return colunas_encontradas

    def buscar_colunas_saldo(self, colunas):
        """Busca automaticamente as colunas de saldo"""
        colunas_encontradas = []
        
        # Padrões de colunas de saldo
        padroes_saldo = [
            "Saldo_5",
            "Saldo_Beneficio_5",
            "Saldo_35"
        ]
        
        for padrao in padroes_saldo:
            for coluna in colunas:
                if padrao.lower() in coluna.lower():
                    colunas_encontradas.append(coluna)
                    break
        
        return colunas_encontradas

    def mostrar_preview_conversao(self, df, colunas_utilizado, colunas_saldo):
        """Mostra preview da conversão das 3 primeiras linhas"""
        self.console.print(Panel(
            "[bold yellow]Preview da Conversão (3 primeiras linhas)[/bold yellow]",
            title="Preview",
            border_style="yellow"
        ))
        
        # Função de conversão (mesma do processamento)
        def converter_numero(valor):
            valor_convertido = converter_numero_para_float(valor)
            if valor_convertido == 0.0 and str(valor).strip() != '' and str(valor).strip() != '0':
                return "❌ ERRO"
            return valor_convertido
        
        # Mostrar preview para colunas de utilizado
        self.console.print("\n[bold cyan]Colunas Utilizado:[/bold cyan]")
        for col in colunas_utilizado:
            if col in df.columns:
                self.console.print(f"\n[bold]{col}:[/bold]")
                for i in range(min(3, len(df))):
                    valor_original = df[col].iloc[i]
                    valor_convertido = converter_numero(valor_original)
                    self.console.print(f"  Linha {i+1}: {valor_original} → {valor_convertido}")
        
        # Mostrar preview para colunas de saldo
        self.console.print("\n[bold cyan]Colunas Saldo:[/bold cyan]")
        for col in colunas_saldo:
            if col in df.columns:
                self.console.print(f"\n[bold]{col}:[/bold]")
                for i in range(min(3, len(df))):
                    valor_original = df[col].iloc[i]
                    valor_convertido = converter_numero(valor_original)
                    self.console.print(f"  Linha {i+1}: {valor_original} → {valor_convertido}")
        
        # Mostrar soma das linhas para verificação
        self.console.print("\n[bold yellow]Verificação das Somas (3 primeiras linhas):[/bold yellow]")
        for i in range(min(3, len(df))):
            self.console.print(f"\n[bold]Linha {i+1}:[/bold]")
            
            # Calcular soma utilizado
            soma_utilizado = 0.0
            for col in colunas_utilizado:
                if col in df.columns:
                    valor = converter_numero(df[col].iloc[i])
                    if isinstance(valor, (int, float)):
                        soma_utilizado += valor
                    self.console.print(f"  {col}: {df[col].iloc[i]} → {valor}")
            
            # Calcular soma saldo
            soma_saldo = 0.0
            for col in colunas_saldo:
                if col in df.columns:
                    valor = converter_numero(df[col].iloc[i])
                    if isinstance(valor, (int, float)):
                        soma_saldo += valor
                    self.console.print(f"  {col}: {df[col].iloc[i]} → {valor}")
            
            # Mostrar totais calculados (arredondados para 2 casas decimais)
            self.console.print(f"  [bold green]TOTAL_UTILIZADO: {round(soma_utilizado, 2)}[/bold green]")
            self.console.print(f"  [bold green]TOTAL_SALDO: {round(soma_saldo, 2)}[/bold green]")
            
            # Mostrar valores atuais nos arquivos
            if 'Total_Utilizado' in df.columns:
                atual_utilizado = df['Total_Utilizado'].iloc[i]
                self.console.print(f"  [bold red]ATUAL_UTILIZADO: {atual_utilizado}[/bold red]")
            if 'Total_Saldo' in df.columns:
                atual_saldo = df['Total_Saldo'].iloc[i]
                self.console.print(f"  [bold red]ATUAL_SALDO: {atual_saldo}[/bold red]")

    def recalcular_totais(self, df, coluna_total_utilizado, colunas_utilizado, coluna_total_saldo, colunas_saldo):
        """Recalcula os totais das colunas especificadas"""
        df_corrigido = df.copy()
        
        # Converter colunas para numérico usando função utilitária
        def converter_para_numerico(serie):
            return serie.apply(converter_numero_para_float)
        
        # Recalcular total utilizado
        if coluna_total_utilizado in df_corrigido.columns:
            total_util = pd.Series([0.0] * len(df_corrigido), index=df_corrigido.index)
            for col in colunas_utilizado:
                if col in df_corrigido.columns:
                    valores_col = converter_para_numerico(df_corrigido[col])
                    total_util += valores_col
            
            # Validação: totais acima de 100.000 são suspeitos e arredondamento para 2 casas decimais
            total_util = total_util.apply(lambda x: 0.0 if abs(x) > 100000 else round(x, 2))
            
            df_corrigido[coluna_total_utilizado] = total_util
        
        # Recalcular total saldo
        if coluna_total_saldo in df_corrigido.columns:
            total_saldo = pd.Series([0.0] * len(df_corrigido), index=df_corrigido.index)
            for col in colunas_saldo:
                if col in df_corrigido.columns:
                    valores_col = converter_para_numerico(df_corrigido[col])
                    total_saldo += valores_col
            
            # Validação: totais acima de 100.000 são suspeitos e arredondamento para 2 casas decimais
            total_saldo = total_saldo.apply(lambda x: 0.0 if abs(x) > 100000 else round(x, 2))
            
            df_corrigido[coluna_total_saldo] = total_saldo
        
        return df_corrigido

    def normalizar_valores(self):
        """Normaliza valores numéricos para formato padronizado"""
        self.console.print(Panel(
            "[bold cyan]Normalizar Valores[/bold cyan]\n"
            "Esta opção padroniza todos os valores numéricos para o formato '000,00' ou '0000,00'",
            title="Normalização",
            border_style="cyan"
        ))
        
        # 1. Selecionar pasta
        pasta_csv = selecionar_pasta("Selecione a pasta com os arquivos CSV para normalizar:")
        if not pasta_csv:
            return
        
        # 2. Encontrar arquivos CSV
        arquivos_csv = [f for f in os.listdir(pasta_csv) if f.endswith('.csv')]
        if not arquivos_csv:
            self.console.print("[red]Nenhum arquivo CSV encontrado na pasta![/red]")
            return
        
        # 3. Carregar primeiro arquivo para ver estrutura
        primeiro_arquivo = os.path.join(pasta_csv, arquivos_csv[0])
        df_exemplo = self.carregar_csv(primeiro_arquivo)
        
        if df_exemplo is None:
            return
        
        # 4. Detectar colunas numéricas automaticamente
        colunas_numericas = self.detectar_colunas_numericas(df_exemplo)
        
        if not colunas_numericas:
            self.console.print("[red]Nenhuma coluna numérica detectada![/red]")
            return
        
        # 5. Mostrar preview da normalização
        self.mostrar_preview_normalizacao(df_exemplo, colunas_numericas)
        
        # 6. Confirmar processamento
        self.console.print(Panel(
            f"[bold cyan]Resumo da Normalização:[/bold cyan]\n"
            f"├─ Total de arquivos: {len(arquivos_csv)}\n"
            f"├─ Colunas a normalizar: {', '.join(colunas_numericas)}\n"
            f"└─ Formato final: '000,00' ou '0000,00'",
            title="Configuração",
            border_style="cyan"
        ))
        
        continuar = inquirer.confirm(
            message=f"Deseja processar {len(arquivos_csv)} arquivos?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # 7. Processar arquivos
        arquivos_processados = []
        arquivos_com_erro = []
        
        self.console.print("\n[bold cyan]Processando arquivos...[/bold cyan]")
        
        for i, arquivo in enumerate(arquivos_csv, 1):
            try:
                self.console.print(f"Processando {i}/{len(arquivos_csv)}: {arquivo}")
                
                caminho_arquivo = os.path.join(pasta_csv, arquivo)
                df = self.carregar_csv(caminho_arquivo)
                
                if df is not None:
                    df_normalizado = self.normalizar_dataframe(df, colunas_numericas)
                    salvar_arquivo(df_normalizado, caminho_arquivo)
                    arquivos_processados.append(arquivo)
                    self.console.print(f"✓ Arquivo normalizado com sucesso")
                else:
                    arquivos_com_erro.append(arquivo)
                    
            except Exception as e:
                arquivos_com_erro.append(arquivo)
                self.console.print(f"❌ Erro ao processar {arquivo}: {str(e)}")
        
        # 8. Exibir relatório final
        self.exibir_relatorio_normalizacao(arquivos_processados, arquivos_com_erro, pasta_csv)

    def detectar_colunas_numericas(self, df):
        """Detecta colunas específicas para normalização"""
        # Colunas específicas que devem ser normalizadas
        colunas_especificas = [
            "Renda_Bruta",
            "Bruta_5", 
            "Utilizado_5",
            "Saldo_5",
            "Bruta_Beneficio_5",
            "Utilizado_Beneficio_5", 
            "Saldo_Beneficio_5",
            "Bruta_35",
            "Utilizado_35",
            "Saldo_35",
            "Total_Utilizado",
            "Total_Saldo"
        ]
        
        # Verificar quais colunas existem no DataFrame
        colunas_encontradas = []
        for coluna in colunas_especificas:
            if coluna in df.columns:
                colunas_encontradas.append(coluna)
        
        return colunas_encontradas

    def mostrar_preview_normalizacao(self, df, colunas_numericas):
        """Mostra preview da normalização das 3 primeiras linhas"""
        self.console.print(Panel(
            "[bold yellow]Preview da Normalização (3 primeiras linhas)[/bold yellow]",
            title="Preview",
            border_style="yellow"
        ))
        
        # Função de normalização usando utilitário
        def normalizar_valor(valor):
            return normalizar_valor_numerico(valor)
        
        # Mostrar preview para cada coluna numérica
        for col in colunas_numericas:
            if col in df.columns:
                self.console.print(f"\n[bold cyan]{col}:[/bold cyan]")
                for i in range(min(3, len(df))):
                    valor_original = df[col].iloc[i]
                    valor_normalizado = normalizar_valor(valor_original)
                    self.console.print(f"  Linha {i+1}: {valor_original} → {valor_normalizado}")

    def normalizar_dataframe(self, df, colunas_numericas):
        """Normaliza um DataFrame aplicando formatação padronizada"""
        df_normalizado = df.copy()
        
        # Aplicar normalização nas colunas numéricas usando função utilitária
        for col in colunas_numericas:
            if col in df_normalizado.columns:
                df_normalizado[col] = df_normalizado[col].apply(normalizar_valor_numerico)
        
        return df_normalizado

    def exibir_relatorio_normalizacao(self, arquivos_processados, arquivos_com_erro, pasta_csv):
        """Exibe relatório final da normalização"""
        total_arquivos = len(arquivos_processados) + len(arquivos_com_erro)
        taxa_sucesso = (len(arquivos_processados) / total_arquivos * 100) if total_arquivos > 0 else 0
        
        self.console.print(Panel(
            f"[bold green]Normalização Concluída![/bold green]\n\n"
            f"[bold cyan]Estatísticas:[/bold cyan]\n"
            f"├─ Total de arquivos encontrados: {total_arquivos}\n"
            f"├─ Arquivos processados com sucesso: {len(arquivos_processados)}\n"
            f"├─ Arquivos com erro: {len(arquivos_com_erro)}\n"
            f"└─ Taxa de sucesso: {taxa_sucesso:.1f}%\n\n"
            f"[bold cyan]Pasta processada:[/bold cyan]\n{pasta_csv}\n\n"
            f"[bold cyan]Arquivos Normalizados:[/bold cyan]\n" + 
            "\n".join([f"├─ {arquivo}" for arquivo in arquivos_processados]) + "\n\n"
            f"[bold cyan]Normalizações aplicadas:[/bold cyan]\n"
            f"├─ Padronizou formato numérico para '000,00'\n"
            f"├─ Manteve 2 casas decimais\n"
            f"├─ Usou vírgula como separador decimal\n"
            f"└─ Sem separador de milhares\n\n"
            f"💡 [bold yellow]Dica:[/bold yellow] Os arquivos foram normalizados diretamente na pasta original!",
            title="Relatório Final - Normalização",
            border_style="green"
        ))

    def exibir_relatorio_correcao_totais(self, arquivos_processados, arquivos_com_erro, pasta_csv):
        """Exibe relatório final da correção de totais"""
        
        total_arquivos = len(arquivos_processados) + len(arquivos_com_erro)
        total_processados = len(arquivos_processados)
        total_erros = len(arquivos_com_erro)
        
        # Calcular taxa de sucesso evitando divisão por zero
        taxa_sucesso = (total_processados/total_arquivos*100) if total_arquivos > 0 else 0.0
        
        mensagem = (
            f"[bold green]Correção de Totais Concluída![/bold green]\n\n"
            f"[cyan]Estatísticas:[/cyan]\n"
            f"├─ Total de arquivos encontrados: {total_arquivos}\n"
            f"├─ Arquivos processados com sucesso: {total_processados}\n"
            f"├─ Arquivos com erro: {total_erros}\n"
            f"└─ Taxa de sucesso: {taxa_sucesso:.1f}%\n\n"
            f"[cyan]Pasta processada:[/cyan] {pasta_csv}\n\n"
        )
        
        if arquivos_processados:
            mensagem += "[bold green]Arquivos Corrigidos:[/bold green]\n"
            for i, arquivo in enumerate(arquivos_processados):
                prefixo = "└─" if i == len(arquivos_processados) - 1 else "├─"
                mensagem += f"{prefixo} {arquivo}\n"
            mensagem += "\n"
        
        if arquivos_com_erro:
            mensagem += "[bold red]Arquivos com Erro:[/bold red]\n"
            for i, arquivo in enumerate(arquivos_com_erro):
                prefixo = "└─" if i == len(arquivos_com_erro) - 1 else "├─"
                mensagem += f"{prefixo} {arquivo}\n"
            mensagem += "\n"
        
        mensagem += (
            "[bold]Correções aplicadas:[/bold]\n"
            f"├─ Recalculou coluna TOTAL_UTILIZADO\n"
            f"├─ Recalculou coluna TOTAL_SALDO\n"
            f"├─ Tratou valores com vírgula como separador decimal\n"
            f"└─ Substituiu valores inválidos por 0\n\n"
            f"[bold blue]💡 Dica:[/bold blue] Os arquivos foram corrigidos diretamente na pasta original!"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Relatório Final - Correção de Totais",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de correlação de colunas"""
        while True:
            opcao = self.menu_correlacao()
            
            if opcao == "1":
                self.correlacionar_colunas()
            elif opcao == "2":
                self.corrigir_totais_colunas()
            elif opcao == "3":
                self.normalizar_valores()
            else:
                break
