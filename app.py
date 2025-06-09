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
"""

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from options.remover import Remover
from options.add_or_mescle import AddOrMescle
from options.filters import Filters
from options.banco_nomes import BancoNomes

class SmartFiler:
    def __init__(self):
        self.console = Console()
        self.remover = Remover()
        self.add_or_mescle = AddOrMescle()
        self.filters = Filters()
        self.banco_nomes = BancoNomes()

    def menu_principal(self):
        """Cria o menu principal dinâmico usando InquirerPy"""
        return inquirer.select(
            message="Selecione uma opção:",
            choices=[
                Choice("1", name="Remover Dados"),
                Choice("2", name="Filtrar Dados"),
                Choice("3", name="Adicionar/Mesclar Dados"),
                Choice("4", name="Adicionar Nomes de Bancos"),
                Choice("5", name="Sair"),
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
            else:
                self.console.print("[red]Saindo do programa...[/red]")
                break

if __name__ == "__main__":
    app = SmartFiler()
    app.executar()
