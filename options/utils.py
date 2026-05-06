#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Utilitários Compartilhados
Contém funções comuns usadas por todos os módulos do sistema
"""

import pandas as pd
import chardet
import re
import os
from pathlib import Path
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console


def tratar_colunas_numericas(df):
    """Trata colunas numéricas que devem permanecer como string (telefones, CPFs, códigos)"""
    df_tratado = df.copy()
    
    # Palavras-chave para identificar colunas que devem ser string
    keywords_string = [
        'telefone', 'fone', 'phone', 'celular', 'mobile',
        'cpf', 'cnpj', 'rg', 'cep', 'codigo', 'code',
        'numero', 'num', 'id', 'identificador'
    ]
    
    for coluna in df_tratado.columns:
        coluna_lower = coluna.lower()
        
        # Verifica se a coluna contém alguma das palavras-chave
        if any(keyword in coluna_lower for keyword in keywords_string):
            # Converte para string e remove .0 e 'nan'
            df_tratado[coluna] = df_tratado[coluna].astype(str)
            df_tratado[coluna] = df_tratado[coluna].replace(['nan', 'None', 'NULL'], '')
            df_tratado[coluna] = df_tratado[coluna].str.replace('.0', '', regex=False)
    
    return df_tratado


def formatar_cpf(cpf):
    """Formata CPF para o padrão 00000000000"""
    if pd.isna(cpf):
        return None
    cpf = str(cpf)
    # Remove tudo que não for número
    cpf = re.sub(r'\D', '', cpf)
    # Garante que tenha 11 dígitos
    return cpf.zfill(11)


def formatar_numero_celular(numero):
    """Formata número de celular removendo caracteres especiais"""
    if pd.isna(numero):
        return None
    numero = str(numero)
    # Remove tudo que não for número
    numero = re.sub(r'\D', '', numero)
    return numero


def detectar_encoding(arquivo_path, amostra_bytes=10000):
    """Detecta a codificação do arquivo usando chardet"""
    try:
        with open(arquivo_path, 'rb') as arquivo:
            amostra = arquivo.read(amostra_bytes)
            resultado = chardet.detect(amostra)
            encoding_detectado = resultado.get('encoding')
            
            if encoding_detectado:
                # Normaliza alguns encodings comuns
                encoding_map = {
                    'ISO-8859-1': 'latin-1',
                    'Windows-1252': 'cp1252',
                    'ascii': 'utf-8'
                }
                return encoding_map.get(encoding_detectado, encoding_detectado)
            
            # Se não detectou, tentar encodings comuns
            encodings_teste = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            for enc in encodings_teste:
                try:
                    with open(arquivo_path, 'r', encoding=enc) as f:
                        f.read(1000)
                    return enc
                except:
                    continue
            
            return 'utf-8'
            
    except Exception as e:
        return 'utf-8'


def detectar_delimitador(arquivo_path, encoding='utf-8'):
    """Detecta o delimitador do arquivo CSV"""
    try:
        with open(arquivo_path, 'r', encoding=encoding) as arquivo:
            primeira_linha = arquivo.readline()
            
            # Conta ocorrências de cada delimitador comum
            delimitadores = {
                ';': primeira_linha.count(';'),
                ',': primeira_linha.count(','),
                '\t': primeira_linha.count('\t')
            }
            
            # Retorna o delimitador com mais ocorrências
            delimitador = max(delimitadores, key=delimitadores.get)
            
            # Se nenhum delimitador foi encontrado, usa vírgula como padrão
            if delimitadores[delimitador] == 0:
                return ','
            
            return delimitador
    except:
        return ';'


def carregar_arquivo(caminho, encoding=None, delimitador=None):
    """Carrega arquivo CSV ou XLSX com detecção automática de encoding e delimitador"""
    if caminho.endswith('.xlsx'):
        try:
            return pd.read_excel(caminho)
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo XLSX: {str(e)}")
    
    # Para CSV, detecta encoding e delimitador se não fornecidos
    if encoding is None:
        encoding = detectar_encoding(caminho)
    
    if delimitador is None:
        delimitador = detectar_delimitador(caminho, encoding)
    
    # Tenta diferentes combinações de encoding e delimitador
    tentativas = [
        (encoding, delimitador),
        (encoding, ';'),
        (encoding, ','),
        ('utf-8', delimitador),
        ('utf-8', ';'),
        ('utf-8', ','),
        ('latin-1', delimitador),
        ('latin-1', ';'),
        ('latin-1', ',')
    ]
    
    for enc, sep in tentativas:
        try:
            df = pd.read_csv(caminho, encoding=enc, sep=sep, low_memory=False)
            if len(df.columns) > 1:  # Se encontrou mais de uma coluna, provavelmente é o correto
                return df
        except:
            continue
    
    # Última tentativa com pandas auto-detection
    try:
        return pd.read_csv(caminho, encoding='utf-8', sep=';', low_memory=False)
    except:
        return pd.read_csv(caminho, encoding='latin-1', sep=',', low_memory=False)


def salvar_arquivo(df, caminho_saida, tratar_numericas=True):
    """Salva arquivo CSV com tratamento padrão"""
    try:
        if tratar_numericas:
            df = tratar_colunas_numericas(df.copy())
        
        # Garante que o diretório existe
        diretorio = os.path.dirname(caminho_saida)
        if diretorio:  # Se não for vazio
            os.makedirs(diretorio, exist_ok=True)
        
        df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False)
        return caminho_saida
    except PermissionError:
        raise PermissionError(f"Não foi possível salvar o arquivo. Verifique se está aberto em outro programa: {caminho_saida}")
    except Exception as e:
        raise Exception(f"Erro ao salvar arquivo: {str(e)}")


def selecionar_arquivo(mensagem, validar_extensao=True):
    """Permite ao usuário selecionar um arquivo"""
    if validar_extensao:
        return inquirer.filepath(
            message=mensagem,
            validate=lambda x: x.endswith(('.xlsx', '.csv')),
            filter=lambda x: x.strip(),
        ).execute()
    else:
        return inquirer.filepath(
            message=mensagem,
            filter=lambda x: x.strip(),
        ).execute()


def selecionar_pasta(mensagem, apenas_diretorios=True):
    """Permite ao usuário selecionar uma pasta"""
    return inquirer.filepath(
        message=mensagem,
        only_directories=apenas_diretorios,
        filter=lambda x: x.strip(),
    ).execute()


def selecionar_coluna(df, mensagem):
    """Permite ao usuário selecionar uma coluna do DataFrame"""
    colunas = list(df.columns)
    return inquirer.select(
        message=mensagem,
        choices=colunas,
    ).execute()


def converter_numero_para_float(valor):
    """Converte string numérica para float, tratando vírgula como separador decimal"""
    if pd.isna(valor) or valor == '' or str(valor).strip() == '':
        return 0.0
    
    valor_str = str(valor).strip()
    
    # Se tem vírgula, ponto é separador de milhares
    if ',' in valor_str:
        valor_sem_pontos = valor_str.replace('.', '')
        valor_final = valor_sem_pontos.replace(',', '.')
    else:
        # Se não tem vírgula, pode ter ponto como decimal
        valor_final = valor_str
    
    try:
        valor_convertido = float(valor_final)
        # Validação: valores acima de 100.000 são suspeitos
        if abs(valor_convertido) > 100000:
            return 0.0
        return valor_convertido
    except:
        return 0.0


def normalizar_valor_numerico(valor):
    """Normaliza valor numérico para formato padronizado '000,00'"""
    if pd.isna(valor) or valor == '' or str(valor).strip() == '':
        return "0,00"
    
    valor_str = str(valor).strip()
    
    try:
        # Converter para float primeiro
        if ',' in valor_str:
            valor_sem_pontos = valor_str.replace('.', '')
            valor_final = valor_sem_pontos.replace(',', '.')
        else:
            valor_final = valor_str
        
        valor_float = float(valor_final)
        
        # Formatar com 2 casas decimais e vírgula como separador decimal
        return f"{valor_float:.2f}".replace('.', ',')
        
    except:
        return valor_str  # Se não conseguir converter, mantém original

