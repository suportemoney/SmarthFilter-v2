#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Moves && Copys
Contém classes e métodos para mover e copiar arquivos com renomeação automática
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
import os
import shutil
import glob
import re

class MovesCopys:
    def __init__(self):
        self.console = Console()

    def menu_moves_copys(self):
        """Menu principal de opções de moves e copys"""
        return inquirer.select(
            message="Selecione a operação:",
            choices=[
                Choice("1", name="Mover Base CSV"),
                Choice("2", name="Voltar ao menu principal"),
            ],
        ).execute()

    def selecionar_pasta(self, mensagem):
        """Permite ao usuário selecionar uma pasta"""
        return inquirer.filepath(
            message=mensagem,
            only_directories=True,
            filter=lambda x: x.strip(),
        ).execute()

    def mover_base_csv(self):
        """Move arquivos CSV de uma pasta para outra com renomeação automática"""
        
        # 1. Selecionar pasta origem (onde estão os CSV)
        pasta_origem = self.selecionar_pasta("Selecione a pasta de ORIGEM (onde estão os arquivos CSV):")
        
        # Buscar arquivos CSV na pasta origem
        arquivos_csv = glob.glob(os.path.join(pasta_origem, "*.csv"))
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta de origem![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[green]Encontrados {len(arquivos_csv)} arquivos CSV na pasta de origem[/green]",
            title="Arquivos Encontrados",
            border_style="green"
        ))
        
        # 2. Selecionar pasta destino (para onde copiar)
        pasta_destino = self.selecionar_pasta("Selecione a pasta de DESTINO (para onde copiar os arquivos):")
        
        # 3. Mostrar arquivos que serão processados
        self.console.print(Panel(
            f"[cyan]Arquivos que serão processados:[/cyan]\n" +
            "\n".join([f"• {os.path.basename(arquivo)}" for arquivo in arquivos_csv[:10]]) +
            (f"\n... e mais {len(arquivos_csv) - 10} arquivos" if len(arquivos_csv) > 10 else ""),
            title="Prévia dos Arquivos",
            border_style="cyan"
        ))
        
        # 4. Confirmar se quer continuar
        continuar = inquirer.confirm(
            message=f"Deseja continuar e processar {len(arquivos_csv)} arquivos?",
            default=True,
        ).execute()
        
        if not continuar:
            self.console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # 5. Processar cada arquivo
        self.console.print("\n[cyan]Processando arquivos...[/cyan]")
        
        arquivos_processados = []
        arquivos_com_erro = []
        
        for i, arquivo_csv in enumerate(arquivos_csv, 1):
            try:
                nome_arquivo = os.path.basename(arquivo_csv)
                self.console.print(f"\n[cyan]Processando {i}/{len(arquivos_csv)}:[/cyan] {nome_arquivo}")
                
                # Gerar novo nome do arquivo
                novo_nome = self.gerar_novo_nome(nome_arquivo)
                
                if novo_nome:
                    # Caminho completo do arquivo de destino
                    caminho_destino = os.path.join(pasta_destino, novo_nome)
                    
                    # Copiar arquivo
                    shutil.copy2(arquivo_csv, caminho_destino)
                    
                    arquivos_processados.append({
                        'arquivo_original': nome_arquivo,
                        'arquivo_novo': novo_nome,
                        'caminho_destino': caminho_destino
                    })
                    
                    self.console.print(f"[green]✓[/green] Copiado como: {novo_nome}")
                else:
                    self.console.print(f"[yellow]⚠️[/yellow] Arquivo ignorado (não segue o padrão esperado)")
                
            except Exception as e:
                self.console.print(f"[red]❌[/red] Erro ao processar {nome_arquivo}: {str(e)}")
                arquivos_com_erro.append(nome_arquivo)
                continue
        
        # 6. Mostrar relatório final
        self.exibir_relatorio_final(arquivos_processados, arquivos_com_erro, pasta_origem, pasta_destino)

    def gerar_novo_nome(self, nome_arquivo):
        """Gera novo nome para o arquivo seguindo as regras especificadas"""
        
        # Padrão 1: whitelist_NOME_NUMERO.csv (padrão original)
        padrao_whitelist = r'^whitelist_(.+?)_(\d+)\.csv$'
        match_whitelist = re.match(padrao_whitelist, nome_arquivo)
        
        if match_whitelist:
            # Extrair partes do nome
            parte_meio = match_whitelist.group(1)  # Parte do meio (ex: NV_INSS_POA_0508)
            numero_atual = int(match_whitelist.group(2))  # Número atual (ex: 2)
            
            # Aumentar o número
            novo_numero = numero_atual + 1
            
            # Gerar novo nome
            novo_nome = f"{parte_meio}_{novo_numero}.csv"
            
            return novo_nome
        
        # Padrão 2: NOME_NUMERO.csv (sem prefixo whitelist)
        # Exemplo: 10k_1_NV_NOVOSIAPE_2309_0.csv -> 10k_1_NV_NOVOSIAPE_2309_1.csv
        padrao_simples = r'^(.+?)_(\d+)\.csv$'
        match_simples = re.match(padrao_simples, nome_arquivo)
        
        if match_simples:
            # Extrair partes do nome
            parte_meio = match_simples.group(1)  # Parte do meio (ex: 10k_1_NV_NOVOSIAPE_2309)
            numero_atual = int(match_simples.group(2))  # Número atual (ex: 0)
            
            # Aumentar o número
            novo_numero = numero_atual + 1
            
            # Gerar novo nome
            novo_nome = f"{parte_meio}_{novo_numero}.csv"
            
            return novo_nome
        
        # Se não seguir nenhum padrão, retorna None (arquivo será ignorado)
        return None

    def exibir_relatorio_final(self, arquivos_processados, arquivos_com_erro, pasta_origem, pasta_destino):
        """Exibe relatório final do processamento"""
        
        total_arquivos = len(arquivos_processados) + len(arquivos_com_erro)
        total_processados = len(arquivos_processados)
        total_erros = len(arquivos_com_erro)
        
        # Calcular taxa de sucesso evitando divisão por zero
        taxa_sucesso = (total_processados/total_arquivos*100) if total_arquivos > 0 else 0.0
        
        mensagem = (
            f"[bold green]Processamento Concluído![/bold green]\n\n"
            f"[cyan]Estatísticas Gerais:[/cyan]\n"
            f"├─ Total de arquivos encontrados: {total_arquivos}\n"
            f"├─ Arquivos processados com sucesso: {total_processados}\n"
            f"├─ Arquivos com erro: {total_erros}\n"
            f"└─ Taxa de sucesso: {taxa_sucesso:.1f}%\n\n"
            f"[cyan]Localização:[/cyan]\n"
            f"├─ Pasta origem: {pasta_origem}\n"
            f"└─ Pasta destino: {pasta_destino}\n\n"
        )
        
        if arquivos_processados:
            mensagem += "[bold green]Arquivos Processados:[/bold green]\n"
            for i, arquivo in enumerate(arquivos_processados):
                prefixo = "└─" if i == len(arquivos_processados) - 1 else "├─"
                mensagem += (
                    f"{prefixo} {arquivo['arquivo_original']}\n"
                    f"   └─ → {arquivo['arquivo_novo']}\n"
                )
            mensagem += "\n"
        
        if arquivos_com_erro:
            mensagem += "[bold red]Arquivos com Erro:[/bold red]\n"
            for i, arquivo in enumerate(arquivos_com_erro):
                prefixo = "└─" if i == len(arquivos_com_erro) - 1 else "├─"
                mensagem += f"{prefixo} {arquivo}\n"
            mensagem += "\n"
        
        mensagem += (
            "[bold]Regras aplicadas:[/bold]\n"
            f"├─ Padrão 1: whitelist_NOME_NUMERO.csv → NOME_NUMERO+1.csv\n"
            f"├─ Padrão 2: NOME_NUMERO.csv → NOME_NUMERO+1.csv\n"
            f"├─ Aumenta número final (_0 → _1, _1 → _2, _2 → _3, etc.)\n"
            f"└─ Mantém extensão .csv\n\n"
            f"[bold blue]💡 Dica:[/bold blue] Arquivos que seguem os padrões 'whitelist_NOME_NUMERO.csv' ou 'NOME_NUMERO.csv' são processados!"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Relatório Final",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de moves e copys"""
        while True:
            opcao = self.menu_moves_copys()
            
            if opcao == "1":
                self.mover_base_csv()
            else:
                break
