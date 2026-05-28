#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para conversão de arquivos CSV
"""

import os
import pandas as pd
import chardet
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, track
from rich.table import Table
from pathlib import Path
from options.utils import (
    carregar_arquivo,
    salvar_arquivo,
    selecionar_arquivo,
    selecionar_pasta,
    selecionar_colunas,
    aplicar_formato_excel_colunas,
    formatar_valor_excel,
)

class Converter:
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

    def detectar_encoding(self, arquivo_path):
        """Detecta a codificação do arquivo"""
        try:
            with open(arquivo_path, 'rb') as arquivo:
                resultado = chardet.detect(arquivo.read())
                return resultado['encoding']
        except Exception as e:
            self.console.print(f"[red]Erro ao detectar encoding: {e}[/red]")
            return None

    def converter_csv_para_utf8(self, arquivo_entrada, arquivo_saida=None, delimitador_entrada=None):
        """Converte arquivo CSV para UTF-8"""
        try:
            # Detectar encoding original
            encoding_original = self.detectar_encoding(arquivo_entrada)
            if not encoding_original:
                self.console.print(f"[red]Não foi possível detectar o encoding de {arquivo_entrada}[/red]")
                return False

            self.console.print(f"[blue]Encoding detectado: {encoding_original}[/blue]")

            # Tentar detectar delimitador se não foi fornecido
            if not delimitador_entrada:
                with open(arquivo_entrada, 'r', encoding=encoding_original) as arquivo:
                    primeira_linha = arquivo.readline()
                    if ';' in primeira_linha:
                        delimitador_entrada = ';'
                    elif ',' in primeira_linha:
                        delimitador_entrada = ','
                    else:
                        delimitador_entrada = ','

            self.console.print(f"[blue]Delimitador detectado: '{delimitador_entrada}'[/blue]")

            # Ler arquivo com encoding original
            df = pd.read_csv(arquivo_entrada, encoding=encoding_original, delimiter=delimitador_entrada)

            # Definir arquivo de saída se não foi fornecido
            if not arquivo_saida:
                nome_base = Path(arquivo_entrada).stem
                diretorio = Path(arquivo_entrada).parent
                arquivo_saida = diretorio / f"{nome_base}_utf8.csv"

            # Trata colunas numéricas que devem permanecer como string
            df = self.tratar_colunas_numericas(df)
            
            # Salvar em UTF-8 com delimitador ';'
            df.to_csv(arquivo_saida, encoding='utf-8', sep=';', index=False)

            self.console.print(f"[green]Arquivo convertido com sucesso![/green]")
            self.console.print(f"[green]Arquivo de saída: {arquivo_saida}[/green]")
            self.console.print(f"[green]Total de linhas: {len(df)}[/green]")
            
            return True

        except Exception as e:
            self.console.print(f"[red]Erro durante a conversão: {e}[/red]")
            return False

    def listar_arquivos_csv(self, diretorio="."):
        """Lista arquivos CSV no diretório"""
        try:
            arquivos_csv = []
            for arquivo in Path(diretorio).glob("*.csv"):
                if arquivo.is_file():
                    arquivos_csv.append(str(arquivo))
            return arquivos_csv
        except Exception as e:
            self.console.print(f"[red]Erro ao listar arquivos: {e}[/red]")
            return []

    def menu_converter_csv(self):
        """Menu para conversão de CSV"""
        opcoes = [
            "Selecionar arquivo específico",
            "Converter todos os CSV de um diretório",
            "Voltar ao menu principal"
        ]
        
        escolha = inquirer.select(
            message="Como deseja converter?",
            choices=opcoes
        ).execute()

        if escolha == "Selecionar arquivo específico":
            self.converter_arquivo_especifico()
        elif escolha == "Converter todos os CSV de um diretório":
            self.converter_todos_csv()

    def converter_arquivo_especifico(self):
        """Converte um arquivo específico"""
        # Perguntar sobre o diretório
        opcoes_diretorio = [
            "Diretório atual",
            "Escolher outro diretório"
        ]
        
        escolha_diretorio = inquirer.select(
            message="Onde estão os arquivos?",
            choices=opcoes_diretorio
        ).execute()

        if escolha_diretorio == "Diretório atual":
            diretorio = "."
        else:
            diretorio = inquirer.text(
                message="Digite o caminho do diretório:",
                default="."
            ).execute()

        if not os.path.exists(diretorio):
            self.console.print("[red]Diretório não encontrado![/red]")
            return

        # Listar arquivos CSV disponíveis no diretório escolhido
        arquivos_csv = self.listar_arquivos_csv(diretorio)
        
        if not arquivos_csv:
            self.console.print(f"[yellow]Nenhum arquivo CSV encontrado no diretório: {diretorio}[/yellow]")
            return

        # Adicionar opção para digitar caminho manual
        opcoes = arquivos_csv + ["Digitar caminho manual"]
        
        arquivo_escolhido = inquirer.select(
            message="Selecione o arquivo CSV:",
            choices=opcoes
        ).execute()

        if arquivo_escolhido == "Digitar caminho manual":
            arquivo_escolhido = inquirer.text(
                message="Digite o caminho completo do arquivo:"
            ).execute()

        if not os.path.exists(arquivo_escolhido):
            self.console.print("[red]Arquivo não encontrado![/red]")
            return

        # Perguntar sobre delimitador
        delimitador = inquirer.select(
            message="Qual o delimitador do arquivo original?",
            choices=[
                "Auto-detectar",
                "Vírgula (,)",
                "Ponto e vírgula (;)"
            ]
        ).execute()

        delimitador_map = {
            "Auto-detectar": None,
            "Vírgula (,)": ",",
            "Ponto e vírgula (;)": ";"
        }

        self.converter_csv_para_utf8(arquivo_escolhido, delimitador_entrada=delimitador_map[delimitador])

    def converter_todos_csv(self):
        """Converte todos os arquivos CSV do diretório"""
        # Perguntar sobre o diretório
        opcoes_diretorio = [
            "Diretório atual",
            "Escolher outro diretório"
        ]
        
        escolha_diretorio = inquirer.select(
            message="Onde estão os arquivos CSV?",
            choices=opcoes_diretorio
        ).execute()

        if escolha_diretorio == "Diretório atual":
            diretorio = "."
        else:
            diretorio = inquirer.text(
                message="Digite o caminho do diretório:",
                default="."
            ).execute()

        if not os.path.exists(diretorio):
            self.console.print("[red]Diretório não encontrado![/red]")
            return

        # Listar arquivos CSV no diretório escolhido
        arquivos_csv = self.listar_arquivos_csv(diretorio)
        
        if not arquivos_csv:
            self.console.print(f"[yellow]Nenhum arquivo CSV encontrado no diretório: {diretorio}[/yellow]")
            return

        self.console.print(f"[blue]Encontrados {len(arquivos_csv)} arquivos CSV no diretório: {diretorio}[/blue]")
        
        # Mostrar lista dos arquivos encontrados
        self.console.print("[blue]Arquivos encontrados:[/blue]")
        for i, arquivo in enumerate(arquivos_csv, 1):
            nome_arquivo = os.path.basename(arquivo)
            self.console.print(f"  {i}. {nome_arquivo}")
        
        confirmar = inquirer.confirm(
            message="Deseja converter todos estes arquivos?",
            default=False
        ).execute()

        if not confirmar:
            return

        sucessos = 0
        falhas = 0

        for arquivo in track(arquivos_csv, description="Convertendo arquivos..."):
            if self.converter_csv_para_utf8(arquivo):
                sucessos += 1
            else:
                falhas += 1

        self.console.print(f"[green]Conversão concluída![/green]")
        self.console.print(f"[green]Sucessos: {sucessos}[/green]")
        if falhas > 0:
            self.console.print(f"[red]Falhas: {falhas}[/red]")

    def _mostrar_preview_excel(self, df, colunas):
        """Exibe preview da formatação Excel nas colunas selecionadas"""
        self.console.print(Panel(
            "[bold yellow]Preview da formatação (até 5 linhas)[/bold yellow]",
            title="Preview",
            border_style="yellow",
        ))

        for col in colunas:
            if col not in df.columns:
                continue
            self.console.print(f"\n[bold cyan]{col}:[/bold cyan]")
            for i in range(min(5, len(df))):
                original = df[col].iloc[i]
                formatado = formatar_valor_excel(original)
                self.console.print(f"  Linha {i + 1}: {original} → {formatado or '(vazio)'}")

    def _salvar_com_retry_permissao(self, df, caminho_saida, pasta_saida_atual):
        """Salva arquivo com retry em caso de PermissionError"""
        while True:
            try:
                salvar_arquivo(df, caminho_saida, tratar_numericas=False)
                return caminho_saida, pasta_saida_atual
            except PermissionError:
                self.console.print(Panel(
                    f"[red]Erro de Permissão![/red]\n\n"
                    f"Não foi possível salvar:\n{caminho_saida}\n\n"
                    f"[yellow]Possíveis causas:[/yellow]\n"
                    f"• Arquivo aberto no Excel\n"
                    f"• Sem permissão de escrita na pasta",
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
                    pasta_saida_atual = selecionar_pasta(
                        "Selecione a nova pasta para salvar os arquivos:"
                    )
                    nome_arquivo = os.path.basename(caminho_saida)
                    caminho_saida = os.path.join(pasta_saida_atual, nome_arquivo)

    def formatar_colunas_numeros_excel(self):
        """Formata colunas numéricas selecionadas para padrão Excel (arquivo único)"""
        self.console.print(Panel(
            "[bold cyan]Formatar Colunas Numéricas (Excel)[/bold cyan]\n"
            "Converte valores BR (1.456,00 / 123,45) para formato Excel "
            "(1456.00 / 123.45) — ponto decimal, sem milhar, 2 casas.",
            title="Formatação Excel",
            border_style="cyan",
        ))

        arquivo = selecionar_arquivo("Selecione o arquivo (CSV ou XLSX):")
        if not arquivo:
            return

        try:
            df = carregar_arquivo(arquivo)
            if len(df) == 0:
                self.console.print(Panel("[red]O arquivo está vazio![/red]", border_style="red"))
                return
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao carregar arquivo:[/red]\n\n{e}",
                border_style="red",
            ))
            return

        colunas = selecionar_colunas(df, "Selecione as colunas numéricas para formatar:")
        if not colunas:
            self.console.print("[yellow]Nenhuma coluna selecionada.[/yellow]")
            return

        self._mostrar_preview_excel(df, colunas)

        if not inquirer.confirm(
            message="Deseja aplicar a formatação e salvar o arquivo?",
            default=True,
        ).execute():
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return

        pasta_saida = selecionar_pasta("Selecione a pasta para salvar o arquivo final:")
        if not pasta_saida:
            return

        df_formatado = aplicar_formato_excel_colunas(df, colunas)
        nome_base = os.path.splitext(os.path.basename(arquivo))[0]
        caminho_saida = os.path.join(pasta_saida, f"excel_num_{nome_base}.csv")

        try:
            caminho_final, _ = self._salvar_com_retry_permissao(
                df_formatado, caminho_saida, pasta_saida
            )
            self.console.print(Panel(
                f"[green]Arquivo salvo com sucesso![/green]\n\n"
                f"Colunas formatadas: {', '.join(colunas)}\n"
                f"Arquivo: {caminho_final}\n"
                f"Total de linhas: {len(df_formatado):,}",
                title="Concluído",
                border_style="green",
            ))
        except Exception as e:
            self.console.print(Panel(f"[red]Erro ao salvar:[/red]\n\n{e}", border_style="red"))

    def formatar_colunas_numeros_excel_lote(self):
        """Formata colunas numéricas em lote (pasta de arquivos)"""
        self.console.print(Panel(
            "[bold cyan]Formatar Colunas Numéricas (Excel) em Lote[/bold cyan]\n"
            "Processa todos os CSV/XLSX de uma pasta com as mesmas colunas selecionadas.",
            title="Formatação Excel em Lote",
            border_style="cyan",
        ))

        pasta_entrada = selecionar_pasta("Selecione a pasta com os arquivos de entrada:")
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
            df_exemplo = carregar_arquivo(arquivos[0])
        except Exception as e:
            self.console.print(Panel(f"[red]Erro ao carregar primeiro arquivo:[/red]\n\n{e}", border_style="red"))
            return

        colunas = selecionar_colunas(
            df_exemplo,
            f"Selecione as colunas (base: {os.path.basename(arquivos[0])}):",
        )
        if not colunas:
            self.console.print("[yellow]Nenhuma coluna selecionada.[/yellow]")
            return

        self._mostrar_preview_excel(df_exemplo, colunas)

        self.console.print(Panel(
            f"Pasta entrada: {pasta_entrada}\n"
            f"Arquivos encontrados: {len(arquivos)}\n"
            f"Colunas: {', '.join(colunas)}\n"
            f"Formato saída: 0000.00 (ponto decimal, 2 casas)",
            title="Resumo",
            border_style="blue",
        ))

        if not inquirer.confirm(
            message=f"Processar {len(arquivos)} arquivo(s)?",
            default=True,
        ).execute():
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return

        pasta_saida = selecionar_pasta("Selecione a pasta para salvar os arquivos finais:")
        if not pasta_saida:
            return

        processados = []
        erros = []
        avisos_colunas = []

        self.console.print("\n[bold cyan]Processando arquivos...[/bold cyan]")

        for i, caminho_arquivo in enumerate(arquivos, 1):
            nome = os.path.basename(caminho_arquivo)
            self.console.print(f"[blue]{i}/{len(arquivos)}: {nome}[/blue]")
            try:
                df = carregar_arquivo(caminho_arquivo)
                colunas_presentes = [c for c in colunas if c in df.columns]
                colunas_ausentes = [c for c in colunas if c not in df.columns]

                if colunas_ausentes:
                    avisos_colunas.append(
                        f"{nome}: colunas ausentes — {', '.join(colunas_ausentes)}"
                    )

                if not colunas_presentes:
                    erros.append(f"{nome}: nenhuma coluna selecionada encontrada")
                    continue

                df_formatado = aplicar_formato_excel_colunas(df, colunas_presentes)
                nome_base = os.path.splitext(nome)[0]
                caminho_saida = os.path.join(pasta_saida, f"excel_num_{nome_base}.csv")
                caminho_final, pasta_saida = self._salvar_com_retry_permissao(
                    df_formatado, caminho_saida, pasta_saida
                )
                processados.append(nome)
                self.console.print(f"  [green]✓ Salvo: {caminho_final}[/green]")
            except Exception as e:
                erros.append(f"{nome}: {e}")
                self.console.print(f"  [red]✗ Erro: {e}[/red]")

        tabela = Table(title="Resultado do Lote")
        tabela.add_column("Métrica", style="cyan")
        tabela.add_column("Valor", style="green")
        tabela.add_row("Processados", str(len(processados)))
        tabela.add_row("Erros", str(len(erros)))
        tabela.add_row("Pasta saída", pasta_saida)
        self.console.print(tabela)

        if avisos_colunas:
            self.console.print(Panel(
                "\n".join(avisos_colunas[:20]) +
                (f"\n... e mais {len(avisos_colunas) - 20}" if len(avisos_colunas) > 20 else ""),
                title="Avisos de colunas",
                border_style="yellow",
            ))

        if erros:
            self.console.print(Panel(
                "\n".join(erros[:20]),
                title="Erros",
                border_style="red",
            ))

    def executar(self):
        """Função principal do módulo converter"""
        self.console.print(Panel.fit(
            "[bold blue]Converter Arquivos[/bold blue]\n"
            "[italic]Conversão de CSV para UTF-8[/italic]",
            border_style="blue"
        ))

        opcoes = [
            "Converter CSV para UTF-8",
            "Voltar ao menu principal"
        ]
        
        escolha = inquirer.select(
            message="Selecione uma opção:",
            choices=opcoes
        ).execute()

        if escolha == "Converter CSV para UTF-8":
            self.menu_converter_csv() 