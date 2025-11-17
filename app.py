#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SmartFiler2 - Processador de Arquivos

REGRAS DO SISTEMA:
1. Menu dinâmico usando InquirerPy para melhor experiência do usuário
2. Interface rica usando biblioteca rich para melhor visualização
3. Suporte para arquivos XLSX e CSV
4. CSV aceita delimitadores ',' e ';'
5. Todos os arquivos de saída são salvos em CSV UTF-8 com delimitador ';'

Dependências:
- inquirerpy
- rich
- pandas
- openpyxl
- selenium
- beautifulsoup4
- requests
"""

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from options.remover import Remover
from options.add_or_mescle import AddOrMescle
from options.filters import Filters
from options.banco_nomes import BancoNomes
from options.converter import Converter
from options.web_downloader import WebDownloader
from options.extrator_cnpj import ExtratorCNPJ
from options.txt_to_csv import TxtToCsv
from options.juntar_csv_cnpj import JuntarCsvCnpj
from options.moves_copys import MovesCopys
from options.correlacao_colunas import CorrelacaoColunas

class SmartFiler:
    def __init__(self):
        self.console = Console()
        self.remover = Remover()
        self.add_or_mescle = AddOrMescle()
        self.filters = Filters()
        self.banco_nomes = BancoNomes()
        self.converter = Converter()
        self.web_downloader = WebDownloader()
        self.extrator_cnpj = ExtratorCNPJ()
        self.txt_to_csv = TxtToCsv()
        self.juntar_csv_cnpj = JuntarCsvCnpj()
        self.moves_copys = MovesCopys()
        self.correlacao_colunas = CorrelacaoColunas()

    def menu_principal(self):
        """Cria o menu principal dinâmico usando InquirerPy"""
        return inquirer.select(
            message="Selecione uma opção:",
            choices=[
                Choice("1", name="Remover Dados"),
                Choice("2", name="Filtrar Dados"),
                Choice("3", name="Adicionar/Mesclar Dados"),
                Choice("4", name="Adicionar Nomes de Bancos"),
                Choice("5", name="Converter Arquivos"),
                Choice("6", name="Baixar Arquivos de Sites"),
                Choice("7", name="Extrair CNPJs"),
                Choice("8", name="Converter TXT para CSV"),
                Choice("9", name="Juntar CSV através da coluna CNPJ"),
                Choice("10", name="Moves && Copys"),
                Choice("11", name="Correlacionar Colunas"),
                Choice("12", name="Sair"),
            ],
        ).execute()

    def menu_conversao_arquivos(self):
        """Menu de conversão de arquivos"""
        return inquirer.select(
            message="Selecione uma operação de conversão:",
            choices=[
                Choice("1", name="Converter Arquivos"),
                Choice("2", name="Voltar ao menu principal"),
            ],
        ).execute()

    def menu_download_arquivos(self):
        """Menu de download de arquivos"""
        return inquirer.select(
            message="Selecione uma operação de download:",
            choices=[
                Choice("1", name="Baixar Arquivos de Sites"),
                Choice("2", name="Voltar ao menu principal"),
            ],
        ).execute()

    def executar(self):
        """Função principal do programa"""
        self.console.print(Panel.fit(
            "[bold blue]SmartFiler2[/bold blue]\n"
            "[italic]Processador de Arquivos[/italic]",
            border_style="blue"
        ))

        while True:
            opcao = self.menu_principal()
            
            if opcao == "1":
                self.remover.executar()
            elif opcao == "2":
                self.filters.executar()
            elif opcao == "3":
                self.add_or_mescle.executar()
            elif opcao == "4":
                self.banco_nomes.executar()
            elif opcao == "5":
                self.converter.executar()
            elif opcao == "6":
                self.web_downloader.executar()
            elif opcao == "7":
                self.extrator_cnpj.executar()
            elif opcao == "8":
                self.txt_to_csv.executar()
            elif opcao == "9":
                self.juntar_csv_cnpj.executar()
            elif opcao == "10":
                self.moves_copys.executar()
            elif opcao == "11":
                self.correlacao_colunas.executar()
            else:
                self.console.print("[red]Saindo do programa...[/red]")
                break

if __name__ == "__main__":
    app = SmartFiler()
    app.executar()