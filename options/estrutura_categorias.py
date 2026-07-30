#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Estrutura Hierárquica do Sistema
Define categorias, subcategorias e opções do sistema
"""

from dataclasses import dataclass
from typing import List, Optional, Callable
from InquirerPy.base.control import Choice


@dataclass
class OpcaoPrograma:
    """Representa uma opção de programa específica"""
    id: str
    nome: str
    descricao: str
    executar: Callable
    modulo: str  # Nome do módulo/classe


@dataclass
class SubCategoria:
    """Representa uma subcategoria dentro de uma categoria"""
    id: str
    nome: str
    descricao: str
    opcoes: List[OpcaoPrograma]


@dataclass
class Categoria:
    """Representa uma categoria principal do sistema"""
    id: str
    nome: str
    descricao: str
    subcategorias: List[SubCategoria]
    icone: str = "📁"


# Estrutura completa do sistema
ESTRUTURA_SISTEMA = {
    "dados": Categoria(
        id="dados",
        nome="📊 Dados",
        descricao="Manipulação e processamento de dados",
        subcategorias=[
            SubCategoria(
                id="remocao",
                nome="Remoção",
                descricao="Remover dados, duplicatas e blacklists",
                opcoes=[
                    OpcaoPrograma(
                        id="remover_duplicatas_cpf",
                        nome="Remover Duplicatas de CPF",
                        descricao="Remove CPFs duplicados mantendo a primeira ocorrência",
                        executar=None,  # Será preenchido dinamicamente
                        modulo="dados.remocao.remover.Remover.remover_duplicatas_cpf"
                    ),
                    OpcaoPrograma(
                        id="remover_duplicatas_cpf_lote",
                        nome="Remover Duplicatas de CPF em Lote",
                        descricao="Remove duplicatas de CPF em múltiplos arquivos de uma pasta",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.remover_duplicatas_cpf_lote"
                    ),
                    OpcaoPrograma(
                        id="remover_duplicatas_cpf_maior_valor",
                        nome="Remover Duplicatas CPF (Manter Maior Valor)",
                        descricao="Remove duplicatas mantendo o registro com maior valor",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.remover_duplicatas_cpf_lote_maior_valor"
                    ),
                    OpcaoPrograma(
                        id="remover_cpfs_blacklist",
                        nome="Remover CPFs da Blacklist",
                        descricao="Remove CPFs que estão em uma lista de blacklist",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.remover_cpfs_blacklist"
                    ),
                    OpcaoPrograma(
                        id="remover_numeros_blacklist",
                        nome="Remover Números da Blacklist",
                        descricao="Remove números específicos da blacklist",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.remover_numeros_blacklist"
                    ),
                    OpcaoPrograma(
                        id="remover_numeros_blacklist_lote",
                        nome="Remover Números Blacklist em Lote",
                        descricao="Remove números da blacklist em múltiplos arquivos",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.remover_numeros_blacklist_lote"
                    ),
                    OpcaoPrograma(
                        id="remover_celulares_blacklist",
                        nome="Remover Celulares da Blacklist",
                        descricao="Remove linhas com números de celular na blacklist",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.remover_celulares_blacklist"
                    ),
                    OpcaoPrograma(
                        id="filtrar_cnpj",
                        nome="Filtrar CNPJ",
                        descricao="Remove do arquivo 1 as linhas cujo CNPJ está no arquivo 2 (dois arquivos, colunas e pasta de saída)",
                        executar=None,
                        modulo="dados.remocao.remover.Remover.filtrar_cnpj"
                    ),
                ]
            ),
            SubCategoria(
                id="filtragem",
                nome="Filtragem",
                descricao="Filtrar e dividir arquivos",
                opcoes=[
                    OpcaoPrograma(
                        id="dividir_arquivo",
                        nome="Dividir Arquivo em Partes",
                        descricao="Divide um arquivo grande em partes menores",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.dividir_arquivo"
                    ),
                    OpcaoPrograma(
                        id="blacklist_cpf_pasta",
                        nome="Blacklist por CPF (Arquivos por Pasta)",
                        descricao="Separa arquivos em whitelist e blacklist por CPF",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.blacklist_cpf_pasta"
                    ),
                    OpcaoPrograma(
                        id="whitelist_cpf_pasta",
                        nome="Whitelist por CPF (Arquivos por Pasta)",
                        descricao="Verifica os CPFs da pasta 1 que aparecem na pasta 2; se aparecer vai para whitelist, se não, para blacklist",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.whitelist_cpf_pasta"
                    ),
                    OpcaoPrograma(
                        id="filtrar_arquivo_por_cpf",
                        nome="Filtrar Arquivo por CPF (Arquivo 1 x Arquivo 2)",
                        descricao="Separa o arquivo 1 em dois: CPFs que aparecem no arquivo 2 e CPFs que não aparecem",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.filtrar_arquivo_por_cpf"
                    ),
                    OpcaoPrograma(
                        id="repartir_por_coluna",
                        nome="Repartir por Coluna",
                        descricao="Divide arquivo em múltiplos arquivos baseado em valores de uma coluna",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.repartir_por_coluna"
                    ),
                    OpcaoPrograma(
                        id="remover_linhas_vazias",
                        nome="Remover Linhas Vazias/Zero",
                        descricao="Remove linhas com valores vazios ou zero",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.remover_linhas_vazias_arquivo_unico"
                    ),
                    OpcaoPrograma(
                        id="remover_linhas_vazias_lote",
                        nome="Remover Linhas Vazias em Lote",
                        descricao="Remove linhas vazias em múltiplos arquivos",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.remover_linhas_vazias_em_lote"
                    ),
                    OpcaoPrograma(
                        id="adicionar_idade",
                        nome="Adicionar Coluna de Idade",
                        descricao="Calcula e adiciona coluna de idade baseada em data de nascimento",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.adicionar_coluna_idade"
                    ),
                    OpcaoPrograma(
                        id="formatar_coluna_data",
                        nome="Formatar Coluna de Data",
                        descricao="Formata e normaliza coluna de data para dd/MM/AAAA",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.formatar_coluna_data"
                    ),
                    OpcaoPrograma(
                        id="calcular_idade_data",
                        nome="Calcular Idade a partir de Data",
                        descricao="Calcula idade com base na data de nascimento e adiciona coluna 'idade'",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.calcular_idade_data"
                    ),
                    OpcaoPrograma(
                        id="atualizar_idade_data_nascimento",
                        nome="Atualizar idade a partir de data de nascimento",
                        descricao="Usa a coluna de data de nascimento (ex.: NASC) para recalcular e atualizar a coluna de idade",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.atualizar_idade_data_nascimento"
                    ),
                    OpcaoPrograma(
                        id="formatar_coluna_cpf",
                        nome="Formatar e Normalizar Coluna de CPF",
                        descricao="Formata CPFs preenchendo zeros à esquerda até 11 dígitos",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.formatar_coluna_cpf"
                    ),
                    OpcaoPrograma(
                        id="formatar_coluna_cnpj",
                        nome="Formatar e Normalizar Coluna de CNPJ",
                        descricao="Normaliza a coluna de CNPJ para o padrão 00.000.000/0000-00 (arquivo, coluna e pasta de saída)",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.formatar_coluna_cnpj"
                    ),
                    OpcaoPrograma(
                        id="formatar_coluna_price_voip",
                        nome="Formatar coluna Price (VoIP) para Excel",
                        descricao="Lê CSV/XLSX VoIP, formata Price com vírgula e 3 casas decimais (ex.: 0,025) e salva CSV na pasta escolhida",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.formatar_coluna_price_voip"
                    ),
                    OpcaoPrograma(
                        id="exportar_voip_price_formatado_com_relatorio",
                        nome="VoIP: Price formatado + relatório (TXT)",
                        descricao="Só o VoIP: escolhe se a data é US (MM/dd) ou BR (dd/mm); resumo e filtro por dias; CSV Price (3 casas) e TXT com totais e faixa",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.exportar_voip_price_formatado_com_relatorio"
                    ),
                    OpcaoPrograma(
                        id="organizar_base_inss",
                        nome="Organizar Base INSS (colunas padrão)",
                        descricao="Reorganiza colunas da base INSS e cria a coluna 'nome_banco'",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.organizar_base_inss"
                    ),
                    OpcaoPrograma(
                        id="manter_colunas_selecionadas",
                        nome="Manter Apenas Colunas Selecionadas",
                        descricao="Remove colunas não escolhidas e renomeia cabeçalhos para A, B, C... (ex.: A e G viram A e B)",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.manter_colunas_selecionadas"
                    ),
                    OpcaoPrograma(
                        id="manter_colunas_selecionadas_lote",
                        nome="Manter Colunas Selecionadas (Lote)",
                        descricao="Mesma extração de colunas por cabeçalho em todos os CSV/XLSX de uma pasta",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.manter_colunas_selecionadas_lote"
                    ),
                    OpcaoPrograma(
                        id="extrair_identifier_como_cpf",
                        nome="Extrair CPF da Coluna Identifier",
                        descricao="Extrai a coluna 'identifier' dos CSVs de uma pasta, renomeia para CPF e salva na subpasta CPFs",
                        executar=None,
                        modulo="dados.filtragem.filters.Filters.extrair_identifier_como_cpf"
                    ),
                ]
            ),
            SubCategoria(
                id="adicao_mesclagem",
                nome="Adição e Mesclagem",
                descricao="Adicionar e mesclar dados de arquivos",
                opcoes=[
                    OpcaoPrograma(
                        id="unir_colunas_por_cpf",
                        nome="Unir Colunas por CPF",
                        descricao="Une colunas de dois arquivos usando CPF como chave",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.unir_colunas_por_cpf"
                    ),
                    OpcaoPrograma(
                        id="mesclar_voip_discador_telefone_horario",
                        nome="Mesclar VoIP + discador (telefone e horário)",
                        descricao="Une VoIP ao discador por telefone e horário; CSV mesclado + relatório TXT; CSV do discador com números que não existem no VoIP + relatório TXT dessas linhas",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.mesclar_voip_discador_por_telefone_horario"
                    ),
                    OpcaoPrograma(
                        id="adicionar_dados_lote",
                        nome="Adicionar Dados em Lote",
                        descricao="Adiciona dados de um arquivo em múltiplos arquivos",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.adicionar_dados_lote"
                    ),
                    OpcaoPrograma(
                        id="mesclar_arquivos_csv",
                        nome="Mesclar Arquivos CSV",
                        descricao="Combina múltiplos arquivos CSV em um único arquivo",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.mesclar_arquivos_csv"
                    ),
                    OpcaoPrograma(
                        id="mesclar_arquivos_csv_pulando_primeira_linha",
                        nome="Mesclar Arquivos CSV (ignorar linha 1)",
                        descricao="Mescla CSVs ignorando a linha 1 bugada (cabeçalho na linha 2)",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.mesclar_arquivos_csv_pulando_primeira_linha"
                    ),
                    OpcaoPrograma(
                        id="adicionar_coluna_personalizada",
                        nome="Adicionar Coluna Personalizada",
                        descricao="Adiciona uma coluna com valor específico",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.adicionar_coluna_personalizada"
                    ),
                    OpcaoPrograma(
                        id="adicionar_coluna_personalizada_lote",
                        nome="Adicionar Coluna Personalizada em Lote",
                        descricao="Adiciona coluna personalizada em múltiplos arquivos",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.adicionar_coluna_personalizada_lote"
                    ),
                    OpcaoPrograma(
                        id="juntar_por_razao_social",
                        nome="Juntar por Razão Social",
                        descricao="Adiciona CNPJ ao arquivo de dados da empresa usando arquivo Razão Social + CNPJ (mesma empresa pode ter vários CNPJs)",
                        executar=None,
                        modulo="dados.adicao_mesclagem.add_or_mescle.AddOrMescle.juntar_por_razao_social"
                    ),
                ]
            ),
            SubCategoria(
                id="correlacao",
                nome="Correlação",
                descricao="Correlacionar e normalizar colunas",
                opcoes=[
                    OpcaoPrograma(
                        id="correlacionar_colunas",
                        nome="Correlacionar Colunas",
                        descricao="Mapeia colunas entre arquivo modelo e arquivo de dados",
                        executar=None,
                        modulo="dados.correlacao.correlacao_colunas.CorrelacaoColunas.correlacionar_colunas"
                    ),
                    OpcaoPrograma(
                        id="corrigir_totais_colunas",
                        nome="Corrigir Totais de Colunas",
                        descricao="Recalcula totais de colunas numéricas",
                        executar=None,
                        modulo="dados.correlacao.correlacao_colunas.CorrelacaoColunas.corrigir_totais_colunas"
                    ),
                    OpcaoPrograma(
                        id="normalizar_valores",
                        nome="Normalizar Valores",
                        descricao="Normaliza valores numéricos para formato padronizado",
                        executar=None,
                        modulo="dados.correlacao.correlacao_colunas.CorrelacaoColunas.normalizar_valores"
                    ),
                ]
            ),
        ]
    ),
    "conversao": Categoria(
        id="conversao",
        nome="🔄 Conversão",
        descricao="Conversão de formatos e extração de dados",
        subcategorias=[
            SubCategoria(
                id="formatos",
                nome="Formatos",
                descricao="Converter entre diferentes formatos de arquivo",
                opcoes=[
                    OpcaoPrograma(
                        id="converter_csv_utf8",
                        nome="Converter CSV para UTF-8",
                        descricao="Converte arquivos CSV para encoding UTF-8",
                        executar=None,
                        modulo="conversao.formatos.converter.Converter.converter_csv_para_utf8"
                    ),
                    OpcaoPrograma(
                        id="converter_txt_csv",
                        nome="Converter TXT para CSV",
                        descricao="Converte arquivos de texto para formato CSV",
                        executar=None,
                        modulo="conversao.formatos.txt_to_csv.TxtToCsv.executar"
                    ),
                    OpcaoPrograma(
                        id="formatar_colunas_excel",
                        nome="Formatar Colunas Numéricas (Excel)",
                        descricao="Formata colunas selecionadas para padrão Excel (123.45, sem milhar)",
                        executar=None,
                        modulo="conversao.formatos.converter.Converter.formatar_colunas_numeros_excel"
                    ),
                    OpcaoPrograma(
                        id="formatar_colunas_excel_lote",
                        nome="Formatar Colunas Numéricas (Excel) em Lote",
                        descricao="Formata colunas numéricas em todos os CSV/XLSX de uma pasta",
                        executar=None,
                        modulo="conversao.formatos.converter.Converter.formatar_colunas_numeros_excel_lote"
                    ),
                ]
            ),
            SubCategoria(
                id="extracao",
                nome="Extração",
                descricao="Extrair dados específicos de arquivos",
                opcoes=[
                    OpcaoPrograma(
                        id="extrair_cnpj",
                        nome="Extrair CNPJs",
                        descricao="Extrai CNPJs de uma coluna específica",
                        executar=None,
                        modulo="conversao.extracao.extrator_cnpj.ExtratorCNPJ.executar"
                    ),
                    OpcaoPrograma(
                        id="juntar_csv_cnpj",
                        nome="Juntar CSV por CNPJ",
                        descricao="Une arquivos CSV usando CNPJ como chave",
                        executar=None,
                        modulo="conversao.extracao.juntar_csv_cnpj.JuntarCsvCnpj.executar"
                    ),
                ]
            ),
        ]
    ),
    "download": Categoria(
        id="download",
        nome="⬇️ Download",
        descricao="Download de arquivos da web",
        subcategorias=[
            SubCategoria(
                id="web",
                nome="Web",
                descricao="Download de arquivos de sites",
                opcoes=[
                    OpcaoPrograma(
                        id="download_sequencial",
                        nome="Download Sequencial Inteligente",
                        descricao="Baixa arquivos sequencialmente de forma inteligente",
                        executar=None,
                        modulo="download.web.web_downloader.WebDownloader.baixar_todos_automaticamente"
                    ),
                    OpcaoPrograma(
                        id="download_multiprocessamento",
                        nome="Download Multiprocessamento",
                        descricao="Baixa arquivos em paralelo (rápido)",
                        executar=None,
                        modulo="download.web.web_downloader.WebDownloader.baixar_todos_multiprocessamento"
                    ),
                    OpcaoPrograma(
                        id="download_link_especifico",
                        nome="Download de Link Específico",
                        descricao="Baixa arquivo de um link específico",
                        executar=None,
                        modulo="download.web.web_downloader.WebDownloader.baixar_link_especifico"
                    ),
                    OpcaoPrograma(
                        id="navegar_especifico",
                        nome="Navegar e Baixar Específicos",
                        descricao="Navega e baixa arquivos específicos",
                        executar=None,
                        modulo="download.web.web_downloader.WebDownloader.navegar_especifico"
                    ),
                ]
            ),
        ]
    ),
    "utilitarios": Categoria(
        id="utilitarios",
        nome="🛠️ Utilitários",
        descricao="Ferramentas auxiliares e utilitários",
        subcategorias=[
            SubCategoria(
                id="arquivos",
                nome="Arquivos",
                descricao="Operações com arquivos e pastas",
                opcoes=[
                    OpcaoPrograma(
                        id="moves_copys",
                        nome="Mover e Copiar Arquivos",
                        descricao="Move e copia arquivos entre pastas",
                        executar=None,
                        modulo="utilitarios.arquivos.moves_copys.MovesCopys.executar"
                    ),
                ]
            ),
            SubCategoria(
                id="bancos",
                nome="Bancos",
                descricao="Operações relacionadas a bancos",
                opcoes=[
                    OpcaoPrograma(
                        id="adicionar_nomes_bancos",
                        nome="Adicionar Nomes de Bancos",
                        descricao="Adiciona nomes de bancos baseado em códigos",
                        executar=None,
                        modulo="utilitarios.bancos.banco_nomes.BancoNomes.executar"
                    ),
                    OpcaoPrograma(
                        id="gerar_lista_bancos_rede",
                        nome="Gerar Lista de Bancos de Rede",
                        descricao="Gera CSV com bancos que possuem agências físicas (API Banco Central)",
                        executar=None,
                        modulo="utilitarios.bancos.bancos_de_rede.BancosDeRede.executar"
                    ),
                ]
            ),
        ]
    ),
}


def obter_categoria_por_id(categoria_id: str) -> Optional[Categoria]:
    """Retorna uma categoria pelo ID"""
    return ESTRUTURA_SISTEMA.get(categoria_id)


def obter_subcategoria_por_id(categoria_id: str, subcategoria_id: str) -> Optional[SubCategoria]:
    """Retorna uma subcategoria pelo ID"""
    categoria = obter_categoria_por_id(categoria_id)
    if categoria:
        for subcat in categoria.subcategorias:
            if subcat.id == subcategoria_id:
                return subcat
    return None


def obter_opcao_por_id(categoria_id: str, subcategoria_id: str, opcao_id: str) -> Optional[OpcaoPrograma]:
    """Retorna uma opção pelo ID"""
    subcategoria = obter_subcategoria_por_id(categoria_id, subcategoria_id)
    if subcategoria:
        for opcao in subcategoria.opcoes:
            if opcao.id == opcao_id:
                return opcao
    return None


def listar_categorias() -> List[Choice]:
    """Retorna lista de categorias para menu"""
    return [
        Choice(cat.id, name=f"{cat.icone} {cat.nome}")
        for cat in ESTRUTURA_SISTEMA.values()
    ]


def listar_subcategorias(categoria_id: str) -> List[Choice]:
    """Retorna lista de subcategorias para menu"""
    categoria = obter_categoria_por_id(categoria_id)
    if categoria:
        return [
            Choice(subcat.id, name=f"  └─ {subcat.nome}")
            for subcat in categoria.subcategorias
        ]
    return []


def listar_opcoes(categoria_id: str, subcategoria_id: str) -> List[Choice]:
    """Retorna lista de opções para menu"""
    subcategoria = obter_subcategoria_por_id(categoria_id, subcategoria_id)
    if subcategoria:
        return [
            Choice(opcao.id, name=f"    └─ {opcao.nome}")
            for opcao in subcategoria.opcoes
        ]
    return []

