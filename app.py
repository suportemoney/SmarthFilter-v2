#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SmartFiler2 - Processador de Arquivos
Sistema hierárquico: Categorias -> SubCategorias -> Opções -> Programa

REGRAS DO SISTEMA:
1. Menu dinâmico hierárquico usando InquirerPy
2. Interface rica usando biblioteca rich
3. Suporte para arquivos XLSX e CSV
4. CSV aceita delimitadores ',' e ';'
5. Todos os arquivos de saída são salvos em CSV UTF-8 com delimitador ';'
"""

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from options.estrutura_categorias import (
    ESTRUTURA_SISTEMA, listar_categorias, listar_subcategorias, 
    listar_opcoes, obter_opcao_por_id
)

# Imports dinâmicos dos módulos
from options.dados.remocao.remover import Remover
from options.dados.filtragem.filters import Filters
from options.dados.adicao_mesclagem.add_or_mescle import AddOrMescle
from options.dados.correlacao.correlacao_colunas import CorrelacaoColunas
from options.conversao.formatos.converter import Converter
from options.conversao.formatos.txt_to_csv import TxtToCsv
from options.conversao.extracao.extrator_cnpj import ExtratorCNPJ
from options.conversao.extracao.juntar_csv_cnpj import JuntarCsvCnpj
from options.download.web.web_downloader import WebDownloader
from options.utilitarios.arquivos.moves_copys import MovesCopys
from options.utilitarios.bancos.banco_nomes import BancoNomes
from options.utilitarios.bancos.bancos_de_rede import BancosDeRede


class SmartFiler:
    def __init__(self):
        self.console = Console()
        
        # Inicializar instâncias dos módulos
        self.remover = Remover()
        self.filters = Filters()
        self.add_or_mescle = AddOrMescle()
        self.correlacao_colunas = CorrelacaoColunas()
        self.converter = Converter()
        self.txt_to_csv = TxtToCsv()
        self.extrator_cnpj = ExtratorCNPJ()
        self.juntar_csv_cnpj = JuntarCsvCnpj()
        self.web_downloader = WebDownloader()
        self.moves_copys = MovesCopys()
        self.banco_nomes = BancoNomes()
        self.bancos_de_rede = BancosDeRede()
        
        # Mapeamento de módulos para instâncias (usando último componente do caminho)
        self.modulos = {
            'remover': self.remover,
            'filters': self.filters,
            'add_or_mescle': self.add_or_mescle,
            'correlacao_colunas': self.correlacao_colunas,
            'converter': self.converter,
            'txt_to_csv': self.txt_to_csv,
            'extrator_cnpj': self.extrator_cnpj,
            'juntar_csv_cnpj': self.juntar_csv_cnpj,
            'web_downloader': self.web_downloader,
            'moves_copys': self.moves_copys,
            'banco_nomes': self.banco_nomes,
            'bancos_de_rede': self.bancos_de_rede,
        }

    def exibir_arvore_sistema(self):
        """Exibe a árvore hierárquica do sistema"""
        tree = Tree("📊 SmartFiler2 - Sistema de Processamento de Arquivos")
        
        for categoria in ESTRUTURA_SISTEMA.values():
            categoria_node = tree.add(f"{categoria.icone} [bold cyan]{categoria.nome}[/bold cyan]")
            categoria_node.add(f"[dim]{categoria.descricao}[/dim]")
            
            for subcategoria in categoria.subcategorias:
                subcat_node = categoria_node.add(f"  └─ [yellow]{subcategoria.nome}[/yellow]")
                subcat_node.add(f"    [dim]{subcategoria.descricao}[/dim]")
                
                for opcao in subcategoria.opcoes[:3]:  # Mostra apenas as 3 primeiras
                    subcat_node.add(f"      • {opcao.nome}")
                if len(subcategoria.opcoes) > 3:
                    subcat_node.add(f"      ... e mais {len(subcategoria.opcoes) - 3} opções")
        
        self.console.print(tree)

    def menu_principal(self):
        """Menu principal - seleção de categoria"""
        self.console.print("\n[bold cyan]Selecione uma categoria:[/bold cyan]")
        return inquirer.select(
            message="",
            choices=listar_categorias() + [Choice("sair", name="🚪 Sair")],
        ).execute()

    def menu_subcategoria(self, categoria_id: str):
        """Menu de subcategorias"""
        categoria = ESTRUTURA_SISTEMA.get(categoria_id)
        if not categoria:
            return None
        
        self.console.print(Panel(
            f"[bold cyan]{categoria.nome}[/bold cyan]\n"
            f"[dim]{categoria.descricao}[/dim]",
            title="Categoria",
            border_style="cyan"
        ))
        
        subcategorias = listar_subcategorias(categoria_id)
        subcategorias.append(Choice("voltar", name="  ← Voltar"))
        
        self.console.print("\n[bold yellow]Selecione uma subcategoria:[/bold yellow]")
        return inquirer.select(
            message="",
            choices=subcategorias,
        ).execute()

    def menu_opcoes(self, categoria_id: str, subcategoria_id: str):
        """Menu de opções/programas"""
        categoria = ESTRUTURA_SISTEMA.get(categoria_id)
        subcategoria = None
        
        if categoria:
            for subcat in categoria.subcategorias:
                if subcat.id == subcategoria_id:
                    subcategoria = subcat
                    break
        
        if not subcategoria:
            return None
        
        self.console.print(Panel(
            f"[bold yellow]{subcategoria.nome}[/bold yellow]\n"
            f"[dim]{subcategoria.descricao}[/dim]",
            title="Subcategoria",
            border_style="yellow"
        ))
        
        opcoes = listar_opcoes(categoria_id, subcategoria_id)
        opcoes.append(Choice("voltar", name="    ← Voltar"))
        
        self.console.print("\n[bold green]Selecione uma opção:[/bold green]")
        return inquirer.select(
            message="",
            choices=opcoes,
        ).execute()

    def executar_opcao(self, categoria_id: str, subcategoria_id: str, opcao_id: str):
        """Executa a opção selecionada"""
        opcao = obter_opcao_por_id(categoria_id, subcategoria_id, opcao_id)
        
        if not opcao:
            self.console.print("[red]Opção não encontrada![/red]")
            return
        
        self.console.print(Panel(
            f"[bold green]{opcao.nome}[/bold green]\n"
            f"[dim]{opcao.descricao}[/dim]",
            title="Executando",
            border_style="green"
        ))
        
        # Extrair módulo e método do caminho
        # Formato: dados.remocao.remover.Remover.remover_duplicatas_cpf
        partes_modulo = opcao.modulo.split('.')
        nome_classe_arquivo = partes_modulo[-2]  # Nome do arquivo (ex: remover, filters)
        nome_metodo = partes_modulo[-1]  # Nome do método
        
        # Mapear nome do arquivo para instância
        # Remove sufixos comuns e normaliza
        nome_classe_normalizado = nome_classe_arquivo.replace('_', '').lower()
        modulo = None
        
        # Buscar no mapeamento
        for key, instance in self.modulos.items():
            if key.replace('_', '').lower() == nome_classe_normalizado:
                modulo = instance
                break
        
        if not modulo:
            # Tentar buscar pelo nome exato
            modulo = self.modulos.get(nome_classe_arquivo)
        
        if not modulo:
            self.console.print(f"[red]Módulo '{nome_classe_arquivo}' não encontrado![/red]")
            self.console.print(f"[yellow]Módulos disponíveis: {list(self.modulos.keys())}[/yellow]")
            return
        
        # Executar método
        try:
            if hasattr(modulo, nome_metodo):
                metodo = getattr(modulo, nome_metodo)
                if callable(metodo):
                    metodo()
                else:
                    self.console.print(f"[red]'{nome_metodo}' não é um método executável![/red]")
            else:
                # Se o método não existe, pode ser que precise chamar executar() do módulo
                if hasattr(modulo, 'executar'):
                    modulo.executar()
                else:
                    self.console.print(f"[red]Método '{nome_metodo}' não encontrado no módulo![/red]")
        except Exception as e:
            self.console.print(f"[red]Erro ao executar: {str(e)}[/red]")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def executar(self):
        """Função principal do programa com navegação hierárquica"""
        self.console.print(Panel.fit(
            "[bold blue]SmartFiler2[/bold blue]\n"
            "[italic]Sistema Hierárquico de Processamento de Arquivos[/italic]",
            border_style="blue"
        ))
        
        # Mostrar estrutura do sistema na primeira vez
        mostrar_arvore = inquirer.confirm(
            message="Deseja ver a estrutura completa do sistema?",
            default=True
        ).execute()
        
        if mostrar_arvore:
            self.exibir_arvore_sistema()
            input("\n[dim]Pressione Enter para continuar...[/dim]")
        
        # Navegação hierárquica
        while True:
            # Nível 1: Categoria
            categoria_id = self.menu_principal()
            
            if categoria_id == "sair":
                self.console.print("[red]Saindo do programa...[/red]")
                break
            
            # Nível 2: Subcategoria
            while True:
                subcategoria_id = self.menu_subcategoria(categoria_id)
                
                if subcategoria_id == "voltar" or subcategoria_id is None:
                    break
                
                # Nível 3: Opção/Programa
                while True:
                    opcao_id = self.menu_opcoes(categoria_id, subcategoria_id)
                    
                    if opcao_id == "voltar" or opcao_id is None:
                        break
                    
                    # Executar programa
                    self.executar_opcao(categoria_id, subcategoria_id, opcao_id)
                    
                    # Perguntar se quer continuar nesta subcategoria
                    continuar = inquirer.confirm(
                        message="Deseja executar outra opção nesta subcategoria?",
                        default=False
                    ).execute()
                    
                    if not continuar:
                        break


if __name__ == "__main__":
    app = SmartFiler()
    app.executar()
