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
import ftfy

class BancoNomes:
    def __init__(self):
        self.console = Console()

    def corrigir_encoding_texto(self, texto):
        """Corrige problemas de encoding em texto usando ftfy"""
        if pd.isna(texto) or texto == '':
            return texto
        
        try:
            # Converte para string se não for
            texto_str = str(texto)
            
            # Usa ftfy para corrigir encoding automaticamente
            texto_corrigido = ftfy.fix_text(texto_str)
            
            return texto_corrigido
        except Exception as e:
            # Se der erro, retorna o texto original
            return texto

    def corrigir_encoding_dataframe(self, df):
        """Corrige problemas de encoding em todas as colunas de texto do DataFrame"""
        try:
            # Lista de colunas que podem conter texto com problemas de encoding
            colunas_texto = [
                'nome_banco', 'nome_completo_banco', 'Banco', 'name', 'fullName',
                'fonte_informacao', 'Site', 'site'
            ]
            
            # Corrige apenas as colunas que existem no DataFrame
            colunas_para_corrigir = [col for col in colunas_texto if col in df.columns]
            
            for coluna in colunas_para_corrigir:
                if df[coluna].dtype == 'object':  # Apenas colunas de texto
                    df[coluna] = df[coluna].apply(self.corrigir_encoding_texto)
            
            return df
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Erro ao corrigir encoding: {str(e)}")
            return df

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
                # Converte para string e remove .0 desnecessários apenas para valores inteiros
                df[coluna] = df[coluna].astype(str).apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)
                # Remove 'nan' strings e substitui por vazio
                df[coluna] = df[coluna].replace('nan', '', regex=False)
            else:
                # Para colunas numéricas, converte pontos por vírgulas (formato brasileiro)
                df[coluna] = df[coluna].astype(str).str.replace('.', ',', regex=False)
                # Remove 'nan' strings e substitui por vazio
                df[coluna] = df[coluna].replace('nan', '', regex=False)
        
        return df

    def menu_banco_nomes(self):
        """Menu principal de opções de adição de nomes de bancos"""
        return inquirer.select(
            message="Selecione o tipo de operação:",
            choices=[
                Choice("1", name="Adicionar nomes de bancos por código (usando arquivo)"),
                Choice("2", name="Adicionar nomes de bancos por código (usando BrasilAPI)"),
                Choice("3", name="Adicionar nomes de bancos por código (BrasilAPI + arquivo como fallback)"),
                Choice("4", name="Processar múltiplos arquivos em lote (BrasilAPI + arquivo como fallback)"),
                Choice("5", name="Voltar ao menu principal"),
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

    def selecionar_pasta_entrada(self, mensagem):
        """Permite ao usuário selecionar uma pasta com arquivos CSV"""
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
                # Trata colunas numéricas que devem permanecer como string
                df = self.tratar_colunas_numericas(df.copy())
                
                # Corrige problemas de encoding antes de salvar
                df = self.corrigir_encoding_dataframe(df.copy())
                
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
                    'nome': self.corrigir_encoding_texto(data.get('name', '')),
                    'nome_completo': self.corrigir_encoding_texto(data.get('fullName', '')),
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
                            resultados[codigo] = {
                                **resultado,
                                'fonte': 'BRASIL_API'
                            }
                        
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
        
        # Corrige encoding dos nomes dos bancos
        dict_bancos_corrigido = {}
        for codigo, nome in dict_bancos.items():
            dict_bancos_corrigido[codigo] = self.corrigir_encoding_texto(nome)
        
        # Adiciona coluna nome_banco no arquivo base
        df_base['nome_banco'] = df_base['codigo_banco_formatado'].map(dict_bancos_corrigido)
        
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
                            'nome': self.corrigir_encoding_texto(dict_bancos_csv[codigo]),
                            'nome_completo': self.corrigir_encoding_texto(dict_bancos_csv[codigo]),  # Usar o mesmo nome
                            'ispb': '',  # CSV não tem ISPB
                            'site': self.corrigir_encoding_texto(dict_sites_csv.get(codigo, '')),
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

    def processar_arquivos_em_lote(self):
        """Processa múltiplos arquivos CSV em lote adicionando nomes de bancos"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV para processar:")
        
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
        
        # Pergunta sobre o modo de processamento
        modo_processamento = inquirer.select(
            message="Selecione o modo de processamento:",
            choices=[
                Choice("1", name="Apenas BrasilAPI (mais rápido, menos cobertura)"),
                Choice("2", name="BrasilAPI + CSV local (mais lento, máxima cobertura)"),
            ],
        ).execute()
        
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
        total_linhas_com_nome = 0
        
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
                
                # Tenta identificar coluna de código do banco automaticamente
                coluna_codigo = self.identificar_coluna_codigo_banco(df)
                
                if not coluna_codigo:
                    self.console.print(f"[red]❌ Não foi possível identificar coluna de código do banco em: {nome_arquivo}[/red]")
                    arquivos_com_erro += 1
                    continue
                
                # Formata códigos para consistência
                df['codigo_banco_formatado'] = df[coluna_codigo].apply(self.formatar_codigo_banco)
                
                # Obtém códigos únicos
                codigos_unicos = df['codigo_banco_formatado'].dropna().unique().tolist()
                
                if not codigos_unicos:
                    self.console.print(f"[yellow]⚠️  Nenhum código de banco válido encontrado em: {nome_arquivo}[/yellow]")
                    arquivos_com_erro += 1
                    continue
                
                # Consulta bancos baseado no modo selecionado
                if modo_processamento == "1":
                    # Apenas BrasilAPI
                    resultados_combinados = self.consultar_bancos_em_lote(codigos_unicos)
                else:
                    # BrasilAPI + CSV como fallback
                    resultados_combinados = self.consultar_bancos_em_lote(codigos_unicos)
                    
                    # Para códigos não encontrados na API, consulta no CSV local
                    codigos_nao_encontrados = [cod for cod in codigos_unicos if cod not in resultados_combinados]
                    
                    if codigos_nao_encontrados:
                        resultados_csv = self.consultar_bancos_csv_local(codigos_nao_encontrados)
                        resultados_combinados.update(resultados_csv)
                
                # Adiciona informações dos bancos no DataFrame
                df['nome_banco'] = df['codigo_banco_formatado'].map(
                    lambda x: resultados_combinados.get(x, {}).get('nome', '') if x in resultados_combinados else ''
                )
                df['nome_completo_banco'] = df['codigo_banco_formatado'].map(
                    lambda x: resultados_combinados.get(x, {}).get('nome_completo', '') if x in resultados_combinados else ''
                )
                df['ispb'] = df['codigo_banco_formatado'].map(
                    lambda x: resultados_combinados.get(x, {}).get('ispb', '') if x in resultados_combinados else ''
                )
                df['fonte_informacao'] = df['codigo_banco_formatado'].map(
                    lambda x: resultados_combinados.get(x, {}).get('fonte', '') if x in resultados_combinados else ''
                )
                
                # Remove coluna temporária
                df_resultado = df.drop(columns=['codigo_banco_formatado'])
                
                # Salva arquivo processado
                nome_base = os.path.splitext(nome_arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"lote_bancos_{nome_base}.csv")
                
                try:
                    # Trata colunas numéricas que devem permanecer como string
                    df_resultado = self.tratar_colunas_numericas(df_resultado.copy())
                    
                    df_resultado.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
                    
                    # Estatísticas do arquivo
                    linhas_com_nome = df_resultado['nome_banco'].str.len().gt(0).sum()
                    linhas_sem_nome = total_linhas - linhas_com_nome
                    codigos_encontrados = len(resultados_combinados)
                    
                    estatisticas_arquivo = {
                        'arquivo': nome_arquivo,
                        'total_linhas': total_linhas,
                        'linhas_com_nome': linhas_com_nome,
                        'linhas_sem_nome': linhas_sem_nome,
                        'codigos_encontrados': codigos_encontrados,
                        'codigos_unicos': len(codigos_unicos),
                        'cobertura': (linhas_com_nome / total_linhas * 100) if total_linhas > 0 else 0
                    }
                    
                    estatisticas_arquivos.append(estatisticas_arquivo)
                    
                    # Atualiza contadores gerais
                    arquivos_processados += 1
                    total_linhas_processadas += total_linhas
                    total_linhas_com_nome += linhas_com_nome
                    
                    self.console.print(f"[green]✅ Processado: {nome_arquivo} ({linhas_com_nome}/{total_linhas} linhas com nome)[/green]")
                    
                except Exception as e:
                    self.console.print(f"[red]❌ Erro ao salvar {nome_arquivo}: {str(e)}[/red]")
                    arquivos_com_erro += 1
                
            except Exception as e:
                self.console.print(f"[red]❌ Erro ao processar {nome_arquivo}: {str(e)}[/red]")
                arquivos_com_erro += 1
        
        # Exibe relatório final
        self.exibir_relatorio_lote(
            total_arquivos, arquivos_processados, arquivos_com_erro,
            total_linhas_processadas, total_linhas_com_nome,
            estatisticas_arquivos, pasta_saida, modo_processamento
        )

    def identificar_coluna_codigo_banco(self, df):
        """Tenta identificar automaticamente a coluna de código do banco"""
        colunas = list(df.columns)
        
        # Palavras-chave que podem indicar coluna de código do banco (em ordem de prioridade)
        keywords_prioritarias = ['codigo_banco', 'codigo_comp', 'codigo_compe', 'banco_codigo', 'bank_code', 'comp', 'compe']
        keywords_secundarias = ['banco', 'codigo', 'code', 'bank', 'instituicao', 'inst', 'numero', 'num']
        
        # Primeira tentativa: palavras-chave prioritárias
        for coluna in colunas:
            coluna_lower = coluna.lower().replace(' ', '_').replace('-', '_')
            for keyword in keywords_prioritarias:
                if keyword in coluna_lower:
                    self.console.print(f"[cyan]🔍 Coluna identificada por palavra-chave prioritária: {coluna}[/cyan]")
                    return coluna
        
        # Segunda tentativa: palavras-chave secundárias
        for coluna in colunas:
            coluna_lower = coluna.lower().replace(' ', '_').replace('-', '_')
            for keyword in keywords_secundarias:
                if keyword in coluna_lower:
                    self.console.print(f"[cyan]🔍 Coluna identificada por palavra-chave secundária: {coluna}[/cyan]")
                    return coluna
        
        # Terceira tentativa: análise do padrão dos dados
        for coluna in colunas:
            try:
                valores = df[coluna].dropna().astype(str)
                if len(valores) > 0:
                    # Verifica se pelo menos 60% dos valores são números de 3 dígitos
                    numeros_3_digitos = valores.str.match(r'^\d{3}$').sum()
                    if numeros_3_digitos / len(valores) >= 0.6:
                        self.console.print(f"[cyan]🔍 Coluna identificada por padrão de dados (3 dígitos): {coluna}[/cyan]")
                        return coluna
                    
                    # Verifica se pelo menos 50% dos valores são números de 1-4 dígitos
                    numeros_1_4_digitos = valores.str.match(r'^\d{1,4}$').sum()
                    if numeros_1_4_digitos / len(valores) >= 0.5:
                        self.console.print(f"[cyan]🔍 Coluna identificada por padrão de dados (1-4 dígitos): {coluna}[/cyan]")
                        return coluna
            except:
                continue
        
        # Se não conseguir identificar automaticamente, pergunta ao usuário
        self.console.print(f"[yellow]⚠️  Não foi possível identificar automaticamente a coluna de código do banco.[/yellow]")
        return inquirer.select(
            message="Selecione a coluna que contém o código do banco:",
            choices=colunas,
        ).execute()

    def consultar_bancos_csv_local(self, codigos):
        """Consulta códigos de bancos no arquivo CSV local"""
        resultados = {}
        
        try:
            # Carrega arquivo de bancos CSV padrão
            df_bancos_csv = pd.read_csv("COD_BANCOS.csv", sep=';', encoding='utf-8')
            
            # Formata códigos do CSV para consistência
            df_bancos_csv['codigo_banco_formatado'] = df_bancos_csv['Código COMPE'].apply(self.formatar_codigo_banco)
            
            # Cria dicionário de códigos para nomes do CSV
            dict_bancos_csv = df_bancos_csv.set_index('codigo_banco_formatado')['Banco'].to_dict()
            dict_sites_csv = df_bancos_csv.set_index('codigo_banco_formatado')['Site'].to_dict()
            
            # Busca códigos
            for codigo in codigos:
                if codigo in dict_bancos_csv:
                    resultados[codigo] = {
                        'nome': self.corrigir_encoding_texto(dict_bancos_csv[codigo]),
                        'nome_completo': self.corrigir_encoding_texto(dict_bancos_csv[codigo]),
                        'ispb': '',
                        'site': self.corrigir_encoding_texto(dict_sites_csv.get(codigo, '')),
                        'fonte': 'CSV_LOCAL'
                    }
            
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Erro ao carregar COD_BANCOS.csv: {str(e)}")
        
        return resultados

    def exibir_relatorio_lote(self, total_arquivos, arquivos_processados, arquivos_com_erro,
                             total_linhas_processadas, total_linhas_com_nome,
                             estatisticas_arquivos, pasta_saida, modo_processamento=None):
        """Exibe relatório detalhado do processamento em lote"""
        
        # Calcula estatísticas gerais
        cobertura_geral = (total_linhas_com_nome / total_linhas_processadas * 100) if total_linhas_processadas > 0 else 0
        taxa_sucesso = (arquivos_processados / total_arquivos * 100) if total_arquivos > 0 else 0
        
        # Ordena estatísticas por cobertura (melhor para pior)
        estatisticas_ordenadas = sorted(estatisticas_arquivos, key=lambda x: x['cobertura'], reverse=True)
        
        # Cria mensagem do relatório
        modo_texto = "Apenas BrasilAPI" if modo_processamento == "1" else "BrasilAPI + CSV local"
        
        mensagem = (
            f"[bold cyan]RELATÓRIO DE PROCESSAMENTO EM LOTE[/bold cyan]\n\n"
            f"[bold]Configuração:[/bold]\n"
            f"└─ Modo de processamento: {modo_texto}\n\n"
            f"[bold]Resumo Geral:[/bold]\n"
            f"├─ Total de arquivos encontrados: {total_arquivos:,}\n"
            f"├─ Arquivos processados com sucesso: {arquivos_processados:,}\n"
            f"├─ Arquivos com erro: {arquivos_com_erro:,}\n"
            f"├─ Taxa de sucesso: {taxa_sucesso:.1f}%\n\n"
            f"[bold]Estatísticas de Dados:[/bold]\n"
            f"├─ Total de linhas processadas: {total_linhas_processadas:,}\n"
            f"├─ Linhas com nome de banco adicionado: {total_linhas_com_nome:,}\n"
            f"├─ Linhas sem nome de banco: {total_linhas_processadas - total_linhas_com_nome:,}\n"
            f"└─ Cobertura geral: {cobertura_geral:.1f}%\n\n"
            f"[bold]Pasta de saída:[/bold]\n"
            f"└─ {pasta_saida}\n\n"
        )
        
        # Adiciona detalhes dos arquivos (top 10 melhores e piores)
        if estatisticas_ordenadas:
            mensagem += "[bold green]Top 10 - Melhor Cobertura:[/bold green]\n"
            for i, stats in enumerate(estatisticas_ordenadas[:10], 1):
                mensagem += (
                    f"{i:2d}. {stats['arquivo']:<30} "
                    f"{stats['linhas_com_nome']:>6}/{stats['total_linhas']:<6} "
                    f"({stats['cobertura']:>5.1f}%)\n"
                )
            
            if len(estatisticas_ordenadas) > 10:
                mensagem += f"... e mais {len(estatisticas_ordenadas) - 10} arquivos\n"
            
            mensagem += "\n"
            
            # Adiciona piores coberturas se houver
            piores = estatisticas_ordenadas[-10:] if len(estatisticas_ordenadas) > 10 else estatisticas_ordenadas
            if piores and piores[0]['cobertura'] < 100:
                mensagem += "[bold red]Arquivos com Baixa Cobertura:[/bold red]\n"
                for i, stats in enumerate(piores, 1):
                    mensagem += (
                        f"{i:2d}. {stats['arquivo']:<30} "
                        f"{stats['linhas_com_nome']:>6}/{stats['total_linhas']:<6} "
                        f"({stats['cobertura']:>5.1f}%)\n"
                    )
                mensagem += "\n"
        
        # Adiciona informações sobre colunas adicionadas
        mensagem += (
            "[bold]Colunas adicionadas em cada arquivo:[/bold]\n"
            f"├─ nome_banco: Nome do banco\n"
            f"├─ nome_completo_banco: Nome completo do banco\n"
            f"├─ ispb: Código ISPB do banco (apenas da API)\n"
            f"└─ fonte_informacao: Fonte dos dados (BRASIL_API ou CSV_LOCAL)\n\n"
            f"[bold blue]💡 Dica:[/bold blue] Arquivos com prefixo 'lote_bancos_' foram processados com sucesso!"
        )
        
        # Salva relatório detalhado em CSV
        if estatisticas_arquivos:
            try:
                df_relatorio = pd.DataFrame(estatisticas_arquivos)
                relatorio_path = os.path.join(pasta_saida, "relatorio_processamento_lote.csv")
                # Trata colunas numéricas que devem permanecer como string
                df_relatorio = self.tratar_colunas_numericas(df_relatorio.copy())
                
                df_relatorio.to_csv(relatorio_path, sep=';', encoding='utf-8', index=False)
                mensagem += f"\n\n[bold green]📊 Relatório detalhado salvo:[/bold green]\n└─ {relatorio_path}"
            except Exception as e:
                mensagem += f"\n\n[bold red]❌ Erro ao salvar relatório: {str(e)}[/bold red]"
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído",
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
            elif opcao == "4":
                self.processar_arquivos_em_lote()
            else:
                break 