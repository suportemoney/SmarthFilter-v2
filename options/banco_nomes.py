#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Adição de Nomes de Bancos
Contém classes e métodos para adicionar nomes de bancos com base nos códigos bancários
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class BancoNomes:
    def __init__(self):
        self.console = Console()

    def menu_banco_nomes(self):
        """Menu principal de opções de adição de nomes de bancos"""
        return inquirer.select(
            message="Selecione o tipo de operação:",
            choices=[
                Choice("1", name="Adicionar nomes de bancos por código (usando arquivo)"),
                Choice("2", name="Adicionar nomes de bancos por código (usando BrasilAPI)"),
                Choice("3", name="Adicionar nomes de bancos por código (BrasilAPI + arquivo como fallback)"),
                Choice("4", name="Voltar ao menu principal"),
            ],
        ).execute()

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

    def carregar_arquivo(self, caminho):
        """Carrega arquivo CSV ou XLSX"""
        if caminho.endswith('.xlsx'):
            return pd.read_excel(caminho)
        else:
            try:
                return pd.read_csv(caminho, sep=';', encoding='utf-8')
            except:
                return pd.read_csv(caminho, sep=',', encoding='utf-8')

    def salvar_arquivo(self, df, arquivo_base, pasta_saida, prefixo="codbank"):
        """Salva arquivo CSV com prefixo personalizado"""
        nome_arquivo = os.path.basename(arquivo_base)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{nome_base}.csv")
        
        while True:
            try:
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
                    caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{nome_base}.csv")
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
                caminho_saida = os.path.join(pasta_saida, f"{prefixo}_{nome_base}.csv")

    def formatar_codigo_banco(self, codigo):
        """Formata código do banco para consistência"""
        if pd.isna(codigo):
            return None
        # Converte para string, remove espaços e converte de volta para int para padronizar
        codigo_str = str(codigo).strip()
        try:
            # Remove pontos decimais desnecessários (ex: "626.0" vira "626")
            if '.' in codigo_str:
                codigo_str = str(int(float(codigo_str)))
            return codigo_str
        except (ValueError, TypeError):
            return codigo_str

    def consultar_banco_api(self, codigo):
        """Consulta informações do banco na BrasilAPI"""
        try:
            codigo_formatado = self.formatar_codigo_banco(codigo)
            if not codigo_formatado:
                return None
            
            url = f"https://brasilapi.com.br/api/banks/v1/{codigo_formatado}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'nome': data.get('name', ''),
                    'nome_completo': data.get('fullName', ''),
                    'ispb': data.get('ispb', '')
                }
            elif response.status_code == 404:
                return None  # Banco não encontrado
            else:
                return None  # Erro na consulta
        except Exception as e:
            return None  # Erro na requisição

    def consultar_bancos_em_lote(self, codigos_unicos):
        """Consulta múltiplos bancos usando threads para melhor performance"""
        resultados = {}
        total_codigos = len(codigos_unicos)
        
        with self.console.status(f"[cyan]Consultando {total_codigos} códigos de bancos na BrasilAPI...") as status:
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Submete todas as consultas
                future_to_codigo = {
                    executor.submit(self.consultar_banco_api, codigo): codigo 
                    for codigo in codigos_unicos if codigo is not None
                }
                
                # Processa resultados conforme completam
                for i, future in enumerate(as_completed(future_to_codigo)):
                    codigo = future_to_codigo[future]
                    try:
                        resultado = future.result()
                        if resultado:
                            resultados[codigo] = resultado
                        
                        # Atualiza status
                        status.update(f"[cyan]Consultando bancos... {i+1}/{len(future_to_codigo)} concluídos")
                        
                        # Pequena pausa para não sobrecarregar a API
                        time.sleep(0.1)
                        
                    except Exception as e:
                        self.console.print(f"[yellow]Erro ao consultar código {codigo}: {str(e)}")
        
        return resultados

    def adicionar_nomes_bancos_api(self):
        """Adiciona nomes de bancos usando a BrasilAPI"""
        # Seleciona arquivo base
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        
        # Carrega arquivo base
        df_base = self.carregar_arquivo(arquivo_base)
        total_linhas_base = len(df_base)
        
        # Seleciona coluna de código banco no arquivo base
        coluna_codigo_base = self.selecionar_coluna(
            df_base, 
            "Selecione a coluna de código do banco no arquivo base:"
        )
        
        # Formata códigos para consistência
        df_base['codigo_banco_formatado'] = df_base[coluna_codigo_base].apply(self.formatar_codigo_banco)
        
        # Obtém códigos únicos (excluindo valores nulos)
        codigos_unicos = df_base['codigo_banco_formatado'].dropna().unique().tolist()
        total_codigos_unicos = len(codigos_unicos)
        
        self.console.print(Panel(
            f"[cyan]Iniciando consulta na BrasilAPI[/cyan]\n\n"
            f"Total de linhas no arquivo: {total_linhas_base:,}\n"
            f"Códigos únicos de bancos a consultar: {total_codigos_unicos:,}\n\n"
            f"[yellow]Aguarde... Esta operação pode levar alguns minutos.[/yellow]",
            title="Consulta API",
            border_style="blue"
        ))
        
        # Consulta bancos na API
        resultados_api = self.consultar_bancos_em_lote(codigos_unicos)
        
        # Adiciona informações dos bancos no DataFrame
        df_base['nome_banco'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_api.get(x, {}).get('nome', '') if x in resultados_api else ''
        )
        df_base['nome_completo_banco'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_api.get(x, {}).get('nome_completo', '') if x in resultados_api else ''
        )
        df_base['ispb'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_api.get(x, {}).get('ispb', '') if x in resultados_api else ''
        )
        
        # Conta linhas que tiveram nome adicionado
        linhas_com_nome = df_base['nome_banco'].str.len().gt(0).sum()
        linhas_sem_nome = total_linhas_base - linhas_com_nome
        codigos_encontrados = len(resultados_api)
        codigos_nao_encontrados = total_codigos_unicos - codigos_encontrados
        
        # Remove coluna temporária de código formatado
        df_resultado = df_base.drop(columns=['codigo_banco_formatado'])
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo final:")
        
        # Salva arquivo final
        caminho_final = self.salvar_arquivo(df_resultado, arquivo_base, pasta_saida, "api_bancos")
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas da Consulta API:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Consulta na BrasilAPI:\n"
            f"│  ├─ Códigos únicos consultados: {total_codigos_unicos:,}\n"
            f"│  ├─ Códigos encontrados na API: {codigos_encontrados:,}\n"
            f"│  └─ Códigos não encontrados na API: {codigos_nao_encontrados:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Linhas com informações de banco adicionadas: {linhas_com_nome:,}\n"
            f"│  └─ Linhas sem informações de banco: {linhas_sem_nome:,}\n\n"
            f"[green]Colunas adicionadas:[/green]\n"
            f"├─ nome_banco: Nome do banco\n"
            f"├─ nome_completo_banco: Nome completo do banco\n"
            f"└─ ispb: Código ISPB do banco\n\n"
            f"Arquivo salvo como:\n"
            f"└─ {caminho_final}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Consulta API Concluída",
            border_style="green"
        ))

    def adicionar_nomes_bancos(self):
        """Adiciona nomes de bancos com base nos códigos bancários usando arquivo"""
        # Seleciona arquivo base
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        
        # Carrega arquivo base
        df_base = self.carregar_arquivo(arquivo_base)
        total_linhas_base = len(df_base)
        
        # Seleciona coluna de código banco no arquivo base
        coluna_codigo_base = self.selecionar_coluna(
            df_base, 
            "Selecione a coluna de código do banco no arquivo base:"
        )
        
        # Seleciona arquivo com tabela de códigos de bancos
        arquivo_bancos = self.selecionar_arquivo("Selecione o arquivo CSV com tabela de códigos de bancos:")
        
        # Carrega arquivo de bancos
        df_bancos = self.carregar_arquivo(arquivo_bancos)
        total_linhas_bancos = len(df_bancos)
        
        # Seleciona coluna de código banco no arquivo de bancos
        coluna_codigo_bancos = self.selecionar_coluna(
            df_bancos, 
            "Selecione a coluna de código do banco no arquivo de bancos:"
        )
        
        # Seleciona coluna de nome banco no arquivo de bancos
        coluna_nome_bancos = self.selecionar_coluna(
            df_bancos, 
            "Selecione a coluna de nome do banco no arquivo de bancos:"
        )
        
        # Formata códigos para consistência
        df_base['codigo_banco_formatado'] = df_base[coluna_codigo_base].apply(self.formatar_codigo_banco)
        df_bancos['codigo_banco_formatado'] = df_bancos[coluna_codigo_bancos].apply(self.formatar_codigo_banco)
        
        # Cria dicionário de códigos para nomes
        dict_bancos = df_bancos.set_index('codigo_banco_formatado')[coluna_nome_bancos].to_dict()
        
        # Adiciona coluna nome_banco no arquivo base
        df_base['nome_banco'] = df_base['codigo_banco_formatado'].map(dict_bancos)
        
        # Conta linhas que tiveram nome adicionado
        linhas_com_nome = df_base['nome_banco'].notna().sum()
        linhas_sem_nome = df_base['nome_banco'].isna().sum()
        
        # Remove coluna temporária de código formatado
        df_resultado = df_base.drop(columns=['codigo_banco_formatado'])
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo final:")
        
        # Salva arquivo final
        caminho_final = self.salvar_arquivo(df_resultado, arquivo_base, pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Arquivo de Bancos:\n"
            f"│  └─ Total de linhas: {total_linhas_bancos:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Linhas com nome de banco adicionado: {linhas_com_nome:,}\n"
            f"│  └─ Linhas que não encontraram código do banco: {linhas_sem_nome:,}\n\n"
            f"Arquivo salvo como:\n"
            f"└─ {caminho_final}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def adicionar_nomes_bancos_hibrido(self):
        """Adiciona nomes de bancos usando BrasilAPI + arquivo CSV como fallback"""
        # Seleciona arquivo base
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        
        # Carrega arquivo base
        df_base = self.carregar_arquivo(arquivo_base)
        total_linhas_base = len(df_base)
        
        # Seleciona coluna de código banco no arquivo base
        coluna_codigo_base = self.selecionar_coluna(
            df_base, 
            "Selecione a coluna de código do banco no arquivo base:"
        )
        
        # Formata códigos para consistência
        df_base['codigo_banco_formatado'] = df_base[coluna_codigo_base].apply(self.formatar_codigo_banco)
        
        # Obtém códigos únicos (excluindo valores nulos)
        codigos_unicos = df_base['codigo_banco_formatado'].dropna().unique().tolist()
        total_codigos_unicos = len(codigos_unicos)
        
        self.console.print(Panel(
            f"[cyan]Iniciando consulta híbrida (BrasilAPI + CSV local)[/cyan]\n\n"
            f"Total de linhas no arquivo: {total_linhas_base:,}\n"
            f"Códigos únicos de bancos a consultar: {total_codigos_unicos:,}\n\n"
            f"[yellow]Fase 1: Consultando BrasilAPI...[/yellow]\n"
            f"[yellow]Fase 2: Consultando arquivo CSV para códigos não encontrados...[/yellow]",
            title="Consulta Híbrida",
            border_style="blue"
        ))
        
        # FASE 1: Consulta bancos na API
        resultados_api = self.consultar_bancos_em_lote(codigos_unicos)
        codigos_encontrados_api = set(resultados_api.keys())
        codigos_nao_encontrados_api = [cod for cod in codigos_unicos if cod not in codigos_encontrados_api]
        
        self.console.print(f"[green]✅ Fase 1 concluída: {len(resultados_api)} bancos encontrados na API")
        
        # FASE 2: Para códigos não encontrados na API, consulta no arquivo CSV
        resultados_csv = {}
        if codigos_nao_encontrados_api:
            self.console.print(f"[cyan]🔍 Fase 2: Consultando {len(codigos_nao_encontrados_api)} códigos no arquivo CSV...")
            
            # Carrega arquivo de bancos CSV padrão
            try:
                df_bancos_csv = pd.read_csv("COD_BANCOS.csv", sep=';', encoding='utf-8')
                
                # Formata códigos do CSV para consistência
                df_bancos_csv['codigo_banco_formatado'] = df_bancos_csv['Código COMPE'].apply(self.formatar_codigo_banco)
                
                # Cria dicionário de códigos para nomes do CSV
                dict_bancos_csv = df_bancos_csv.set_index('codigo_banco_formatado')['Banco'].to_dict()
                dict_sites_csv = df_bancos_csv.set_index('codigo_banco_formatado')['Site'].to_dict()
                
                # Busca códigos não encontrados na API
                for codigo in codigos_nao_encontrados_api:
                    if codigo in dict_bancos_csv:
                        resultados_csv[codigo] = {
                            'nome': dict_bancos_csv[codigo],
                            'nome_completo': dict_bancos_csv[codigo],  # Usar o mesmo nome
                            'ispb': '',  # CSV não tem ISPB
                            'site': dict_sites_csv.get(codigo, ''),
                            'fonte': 'CSV_LOCAL'
                        }
                
                self.console.print(f"[green]✅ Fase 2 concluída: {len(resultados_csv)} bancos adicionais encontrados no CSV")
                
            except Exception as e:
                self.console.print(f"[red]❌ Erro ao carregar COD_BANCOS.csv: {str(e)}")
                self.console.print(f"[yellow]⚠️  Continuando apenas com dados da API...")
        
        # Combina resultados da API e CSV
        resultados_combinados = {}
        
        # Adiciona resultados da API
        for codigo, dados in resultados_api.items():
            resultados_combinados[codigo] = {
                **dados,
                'fonte': 'BRASIL_API'
            }
        
        # Adiciona resultados do CSV
        for codigo, dados in resultados_csv.items():
            resultados_combinados[codigo] = dados
        
        # Adiciona informações dos bancos no DataFrame
        df_base['nome_banco'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_combinados.get(x, {}).get('nome', '') if x in resultados_combinados else ''
        )
        df_base['nome_completo_banco'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_combinados.get(x, {}).get('nome_completo', '') if x in resultados_combinados else ''
        )
        df_base['ispb'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_combinados.get(x, {}).get('ispb', '') if x in resultados_combinados else ''
        )
        df_base['fonte_informacao'] = df_base['codigo_banco_formatado'].map(
            lambda x: resultados_combinados.get(x, {}).get('fonte', '') if x in resultados_combinados else ''
        )
        
        # Conta estatísticas
        linhas_com_nome = df_base['nome_banco'].str.len().gt(0).sum()
        linhas_sem_nome = total_linhas_base - linhas_com_nome
        
        # Estatísticas por fonte
        linhas_api = (df_base['fonte_informacao'] == 'BRASIL_API').sum()
        linhas_csv = (df_base['fonte_informacao'] == 'CSV_LOCAL').sum()
        
        codigos_encontrados_api = len(resultados_api)
        codigos_encontrados_csv = len(resultados_csv)
        codigos_nao_encontrados = len(codigos_unicos) - len(resultados_combinados)
        
        # Remove colunas temporárias
        df_resultado = df_base.drop(columns=['codigo_banco_formatado'])
        
        # Seleciona pasta para salvar
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo final:")
        
        # Salva arquivo final
        caminho_final = self.salvar_arquivo(df_resultado, arquivo_base, pasta_saida, "hibrido_bancos")
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas da Consulta Híbrida:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Consulta Híbrida:\n"
            f"│  ├─ Códigos únicos consultados: {total_codigos_unicos:,}\n"
            f"│  ├─ Encontrados na BrasilAPI: {codigos_encontrados_api:,}\n"
            f"│  ├─ Encontrados no CSV local: {codigos_encontrados_csv:,}\n"
            f"│  ├─ Total encontrados: {len(resultados_combinados):,}\n"
            f"│  └─ Códigos não encontrados em nenhuma fonte: {codigos_nao_encontrados:,}\n"
            f"├─ Resultados por Fonte:\n"
            f"│  ├─ Linhas com dados da BrasilAPI: {linhas_api:,}\n"
            f"│  ├─ Linhas com dados do CSV local: {linhas_csv:,}\n"
            f"│  └─ Linhas sem informações de banco: {linhas_sem_nome:,}\n\n"
            f"[green]Colunas adicionadas:[/green]\n"
            f"├─ nome_banco: Nome do banco\n"
            f"├─ nome_completo_banco: Nome completo do banco\n"
            f"├─ ispb: Código ISPB do banco (apenas da API)\n"
            f"└─ fonte_informacao: Fonte dos dados (BRASIL_API ou CSV_LOCAL)\n\n"
            f"[blue]💡 Cobertura máxima alcançada:[/blue]\n"
            f"├─ {((len(resultados_combinados)/total_codigos_unicos)*100):.1f}% dos códigos únicos foram encontrados\n"
            f"├─ {((linhas_com_nome/total_linhas_base)*100):.1f}% das linhas receberam informações de banco\n"
            f"└─ Combinação de fontes garantiu a máxima cobertura possível\n\n"
            f"Arquivo salvo como:\n"
            f"└─ {caminho_final}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Consulta Híbrida Concluída",
            border_style="green"
        ))

    def executar(self):
        """Executa o menu de adição de nomes de bancos"""
        while True:
            opcao = self.menu_banco_nomes()
            
            if opcao == "1":
                self.adicionar_nomes_bancos()
            elif opcao == "2":
                self.adicionar_nomes_bancos_api()
            elif opcao == "3":
                self.adicionar_nomes_bancos_hibrido()
            else:
                break 