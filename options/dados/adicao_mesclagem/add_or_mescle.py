#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de Adição e Mesclagem de Dados
Contém classes e métodos para diferentes tipos de adição e mesclagem de dados em arquivos
"""

import pandas as pd
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
import os
import re
import csv
import unicodedata

class AddOrMescle:
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

    def limpar_aspas_duplas(self, df):
        """Remove todas as aspas dos valores já que usamos ; como separador e não precisamos de aspas"""
        df_limpo = df.copy()
        for coluna in df_limpo.columns:
            if df_limpo[coluna].dtype == 'object':
                df_limpo[coluna] = df_limpo[coluna].astype(str)
                # Remove todas as aspas duplas (ex: ""valor"" -> valor, "valor" -> valor)
                df_limpo[coluna] = df_limpo[coluna].str.replace('""', '', regex=False)
                df_limpo[coluna] = df_limpo[coluna].str.replace('"', '', regex=False)
                # Remove nan como string
                df_limpo[coluna] = df_limpo[coluna].replace('nan', '')
        return df_limpo

    def menu_add_or_mescle(self):
        """Menu principal de opções de adição e mesclagem"""
        return inquirer.select(
            message="Selecione o tipo de operação:",
            choices=[
                Choice("1", name="Unir colunas de dois arquivos pelo CPF"),
                Choice("2", name="Adicionar dados em lote por pasta (com/sem correspondência)"),
                Choice("3", name="Mesclar arquivos CSV de uma pasta em um único arquivo"),
                Choice("4", name="Adicionar coluna personalizada com valor específico"),
                Choice("5", name="Adicionar coluna personalizada em lote por pasta"),
                Choice("6", name="Voltar ao menu principal"),
            ],
        ).execute()

    def formatar_cpf(self, cpf):
        """Formata CPF para o padrão 00000000000"""
        if pd.isna(cpf):
            return None
        cpf = str(cpf)
        # Remove tudo que não for número
        cpf = re.sub(r'\D', '', cpf)
        # Garante que tenha 11 dígitos
        return cpf.zfill(11)

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
        """Permite ao usuário selecionar uma pasta de entrada"""
        return inquirer.filepath(
            message=mensagem,
            filter=lambda x: x.strip(),
        ).execute()

    def carregar_arquivo(self, caminho):
        """Carrega arquivo CSV ou XLSX"""
        if caminho.endswith('.xlsx'):
            return pd.read_excel(caminho)
        else:
            # Tenta detectar o separador lendo a primeira linha
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    primeira_linha = f.readline()
                    if ';' in primeira_linha and primeira_linha.count(';') > primeira_linha.count(','):
                        sep = ';'
                    elif ',' in primeira_linha:
                        sep = ','
                    else:
                        sep = ';'
            except:
                sep = ';'
            
            try:
                # Tenta ler com o separador detectado, garantindo que a primeira linha seja cabeçalho
                df = pd.read_csv(caminho, sep=sep, encoding='utf-8', quoting=csv.QUOTE_MINIMAL, doublequote=True, keep_default_na=False, header=0)
                return df
            except Exception as e:
                # Se falhar, tenta com o outro separador
                outro_sep = ';' if sep == ',' else ','
                try:
                    return pd.read_csv(caminho, sep=outro_sep, encoding='utf-8', quoting=csv.QUOTE_MINIMAL, doublequote=True, keep_default_na=False, header=0)
                except:
                    # Última tentativa sem especificar separador
                    return pd.read_csv(caminho, encoding='utf-8', quoting=csv.QUOTE_MINIMAL, doublequote=True, keep_default_na=False, header=0)

    def carregar_arquivo_pulando_primeira_linha(self, caminho):
        """Carrega CSV ignorando a linha 1 (bugada) e usando a linha 2 como cabeçalho"""
        if caminho.endswith('.xlsx'):
            df = pd.read_excel(caminho, header=1)
            return df
        sep = ';'
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(caminho, 'r', encoding=enc) as f:
                    f.readline()
                    segunda_linha = f.readline()
                sep = ';' if segunda_linha.count(';') > segunda_linha.count(',') else ','
                break
            except Exception:
                continue
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return pd.read_csv(caminho, sep=sep, encoding=enc, quoting=csv.QUOTE_MINIMAL,
                                  doublequote=True, keep_default_na=False, header=1)
            except Exception:
                continue
        outro_sep = ',' if sep == ';' else ';'
        return pd.read_csv(caminho, sep=outro_sep, encoding='utf-8', quoting=csv.QUOTE_MINIMAL,
                          doublequote=True, keep_default_na=False, header=1)

    def salvar_arquivo(self, df, caminho, prefixo, pasta_saida=None):
        """Salva arquivo CSV com prefixo"""
        nome_arquivo = os.path.basename(caminho)
        nome_base = os.path.splitext(nome_arquivo)[0]
        pasta_para_salvar = pasta_saida if pasta_saida else os.path.dirname(caminho)
        caminho_saida = os.path.join(pasta_para_salvar, f"{prefixo}{nome_base}.csv")
        
        while True:
            try:
                # Trata colunas numéricas que devem permanecer como string
                df = self.tratar_colunas_numericas(df)
                df = self.limpar_aspas_duplas(df.copy())
                df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False, quoting=csv.QUOTE_MINIMAL)
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
                    pasta_para_salvar = nova_pasta
                    caminho_saida = os.path.join(pasta_para_salvar, f"{prefixo}{nome_base}.csv")
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Erro inesperado ao salvar arquivo:[/red]\n\n"
                    f"Erro: {str(e)}\n\n"
                    f"[cyan]Por favor, tente escolher uma nova pasta.[/cyan]",
                    title="Erro",
                    border_style="red"
                ))
                
                nova_pasta = self.selecionar_pasta_saida("Selecione uma nova pasta para salvar o arquivo:")
                pasta_para_salvar = nova_pasta
                caminho_saida = os.path.join(pasta_para_salvar, f"{prefixo}{nome_base}.csv")

    def unir_colunas_por_cpf(self):
        """Une colunas de dois arquivos CSV pelo CPF"""
        # Seleciona arquivos
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        arquivo_dados = self.selecionar_arquivo("Selecione o arquivo com dados adicionais:")
        
        # Carrega arquivos
        df_base = self.carregar_arquivo(arquivo_base)
        df_dados = self.carregar_arquivo(arquivo_dados)
        
        # Contagem inicial
        total_linhas_base = len(df_base)
        total_linhas_dados = len(df_dados)
        
        # Seleciona colunas de CPF
        coluna_cpf_base = self.selecionar_coluna(df_base, "Selecione a coluna de CPF do arquivo base:")
        coluna_cpf_dados = self.selecionar_coluna(df_dados, "Selecione a coluna de CPF do arquivo de dados:")
        
        # Formata CPFs
        df_base['cpf_formatado'] = df_base[coluna_cpf_base].apply(self.formatar_cpf)
        df_dados['cpf_formatado'] = df_dados[coluna_cpf_dados].apply(self.formatar_cpf)
        
        # Remove a coluna de CPF do arquivo de dados para evitar duplicação
        colunas_dados = [col for col in df_dados.columns if col != coluna_cpf_dados and col != 'cpf_formatado']
        
        # Realiza o merge
        df_com_corresp = pd.merge(
            df_base,
            df_dados[['cpf_formatado'] + colunas_dados],
            on='cpf_formatado',
            how='inner'
        )
        
        # Identifica CPFs sem correspondência
        cpfs_com_corresp = df_com_corresp['cpf_formatado'].unique()
        df_sem_corresp = df_base[~df_base['cpf_formatado'].isin(cpfs_com_corresp)]
        
        # Remove coluna temporária de CPF formatado
        df_com_corresp = df_com_corresp.drop(columns=['cpf_formatado'])
        df_sem_corresp = df_sem_corresp.drop(columns=['cpf_formatado'])
        
        # Contagem final
        total_linhas_com_corresp = len(df_com_corresp)
        total_linhas_sem_corresp = len(df_sem_corresp)
        
        # Salva arquivos
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos:")
        caminho_com_corresp = self.salvar_arquivo(df_com_corresp, arquivo_base, "comcorresp_", pasta_saida)
        caminho_sem_corresp = self.salvar_arquivo(df_sem_corresp, arquivo_base, "semcorresp_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Arquivo Base:\n"
            f"│  └─ Total de linhas: {total_linhas_base:,}\n"
            f"├─ Arquivo de Dados:\n"
            f"│  └─ Total de linhas: {total_linhas_dados:,}\n"
            f"├─ Resultados:\n"
            f"│  ├─ Total de linhas com correspondência: {total_linhas_com_corresp:,}\n"
            f"│  └─ Total de linhas sem correspondência: {total_linhas_sem_corresp:,}\n\n"
            f"Arquivos salvos como:\n"
            f"├─ Com correspondência: {caminho_com_corresp}\n"
            f"└─ Sem correspondência: {caminho_sem_corresp}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def _normalizar_telefone_discador(self, valor):
        """Apenas dígitos (arquivo discador)."""
        if pd.isna(valor):
            return ''
        return re.sub(r'\D', '', str(valor))

    def _normalizar_telefone_voip(self, valor):
        """Dígitos e remove DDI 55 quando aplicável (arquivo VoIP)."""
        d = self._normalizar_telefone_discador(valor)
        if len(d) >= 12 and d.startswith('55'):
            d = d[2:]
        return d

    def _parse_decimal_flexivel(self, valor):
        """Converte preço/valor para float (aceita vírgula ou ponto decimal)."""
        if pd.isna(valor):
            return float('nan')
        s = str(valor).strip()
        if s == '' or s.lower() in ('nan', 'none'):
            return float('nan')
        s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return float('nan')

    def _formatar_decimal_br(self, valor):
        """Formata número para texto com vírgula decimal (ex.: 0,025)."""
        x = self._parse_decimal_flexivel(valor)
        if x != x:
            return ''
        s = f"{x:.12f}".rstrip('0').rstrip('.')
        if s in ('-0', '-0.'):
            s = '0'
        return s.replace('.', ',')

    def _formatar_inteiro_br(self, valor):
        """Inteiro com separador de milhar em ponto (ex.: 63.416)."""
        if valor is None or (isinstance(valor, float) and valor != valor) or pd.isna(valor):
            return '—'
        try:
            n = int(valor)
        except (TypeError, ValueError):
            return '—'
        return f"{n:,}".replace(',', '.')

    def _formatar_moeda_br(self, valor, casas_decimais=3):
        """Moeda em padrão BR: R$ 72.262,262 (milhar com ponto, centavos com vírgula)."""
        if valor is None:
            return '—'
        try:
            v = float(valor)
        except (TypeError, ValueError):
            return '—'
        if v != v:
            return '—'
        neg = v < 0
        x = abs(v)
        s = f"{x:,.{casas_decimais}f}"
        if '.' in s:
            inteiro, frac = s.split('.', 1)
        else:
            inteiro, frac = s, ''
        inteiro = inteiro.replace(',', '.')
        corpo = f"{inteiro},{frac}" if frac else inteiro
        return ('R$ -' if neg else 'R$ ') + corpo

    def _parse_duracao_segundos(self, valor):
        """Duração em segundos (float; NaN se inválido)."""
        x = self._parse_decimal_flexivel(valor)
        if x != x:
            return float('nan')
        return float(x)

    def _preco_tarifa_por_duracao_segundos(self, valor_duracao):
        """
        Valor cobrado pela duração: R$ 0,05 por minuto; mínimo R$ 0,025 (faixa 1–30 s).
        Para d >= 1 s: max(0,025, (d/60) * 0,05). Sem duração ou < 1 s: 0.
        Ex.: 45 s -> (45/60)*0,05 = 0,0375.
        """
        s = self._parse_duracao_segundos(valor_duracao)
        if s != s or s < 1:
            return 0.0
        proporcional = (s / 60.0) * 0.05
        return max(0.025, proporcional)

    def _formatar_duracao_mm_ww_dd_hhmmss(self, total_segundos):
        """
        Converte soma de segundos para MM:WW:dd:HH:mm:ss (2 dígitos cada).
        MM = meses de 30 dias, WW = semanas de 7 dias, dd = dias restantes.
        Ex.: 8278 s -> 00:00:00:02:17:58
        """
        if total_segundos is None or pd.isna(total_segundos):
            return '—'
        if isinstance(total_segundos, float) and total_segundos != total_segundos:
            return '—'
        try:
            s = int(round(float(total_segundos)))
        except (TypeError, ValueError):
            return '—'
        if s < 0:
            s = 0
        mes_sec = 30 * 86400
        sem_sec = 7 * 86400
        dia_sec = 86400
        meses = s // mes_sec
        s %= mes_sec
        semanas = s // sem_sec
        s %= sem_sec
        dias = s // dia_sec
        s %= dia_sec
        horas = s // 3600
        s %= 3600
        minutos = s // 60
        segundos = s % 60
        return (
            f"{meses:02d}:{semanas:02d}:{dias:02d}:"
            f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        )

    def _fmt_data_hora_br(self, ts):
        """Texto dd/mm/aaaa HH:MM:SS ou vazio."""
        if ts is None or (isinstance(ts, float) and ts != ts):
            return ''
        if pd.isna(ts):
            return ''
        try:
            return pd.Timestamp(ts).strftime('%d/%m/%Y %H:%M:%S')
        except (ValueError, TypeError):
            return ''

    def _montar_relatorio_mesclagem_voip_discador(
        self,
        df1,
        df2,
        pares,
        col_dt1,
        col_price,
        col_dur_voip,
        col_dur_disc,
    ):
        """Texto do relatório: totais de preço, intervalos de data e durações."""
        idx_todas = df1.index.tolist()
        idx_com = set(pares.keys())
        idx_sem = [i for i in idx_todas if i not in idx_com]

        ts_voip = pd.to_datetime(df1[col_dt1], dayfirst=True, errors='coerce')
        preco = df1[col_price].map(self._parse_decimal_flexivel)
        dur_v = df1[col_dur_voip].map(self._parse_duracao_segundos)

        def faixa_datas(indices):
            sub = ts_voip.loc[indices]
            sub = sub.dropna()
            if sub.empty:
                return '—', '—'
            return self._fmt_data_hora_br(sub.min()), self._fmt_data_hora_br(sub.max())

        def soma_preco(indices):
            if not indices:
                return float('nan')
            return preco.loc[indices].sum(min_count=1)

        def soma_dur_voip(indices):
            if not indices:
                return float('nan')
            return dur_v.loc[indices].sum(min_count=1)

        soma_disc_com = float('nan')
        acc_disc = 0.0
        n_disc = 0
        for i1 in idx_com:
            i2 = pares[i1]
            d = self._parse_duracao_segundos(df2.loc[i2, col_dur_disc])
            if d == d:
                acc_disc += d
                n_disc += 1
        if n_disc > 0:
            soma_disc_com = acc_disc

        soma_disc_geral = soma_disc_com  # só linhas emparelhadas têm duração do discador

        inicio_geral, fim_geral = faixa_datas(idx_todas)
        inicio_sem, fim_sem = faixa_datas(idx_sem)
        inicio_com, fim_com = faixa_datas(list(idx_com))

        total_preco_geral = soma_preco(idx_todas)
        total_preco_sem = soma_preco(idx_sem)
        total_preco_com = soma_preco(list(idx_com))

        soma_dur_v_geral = soma_dur_voip(idx_todas)
        soma_dur_v_sem = soma_dur_voip(idx_sem)

        def fmt_num(x):
            return self._formatar_moeda_br(x, 3)

        def fmt_dur(x):
            return self._formatar_duracao_mm_ww_dd_hhmmss(x)

        linhas = [
            'RELATÓRIO — Mesclagem VoIP + discador',
            '(Durações: MM:WW:dd:HH:mm:ss — mes=30d, semana=7d, dd=dias, depois hora:min:seg)',
            '',
            '=== Geral (todas as linhas do arquivo base VoIP) ===',
            f'Total price (soma): {fmt_num(total_preco_geral)}',
            f'Data/hora (VoIP) — início: {inicio_geral} | fim: {fim_geral}',
            f'Soma duração VoIP (MM:WW:dd:HH:mm:ss): {fmt_dur(soma_dur_v_geral)}',
            f'Soma duração discador (MM:WW:dd:HH:mm:ss, só emparelhadas): {fmt_dur(soma_disc_geral)}',
            '',
            '=== Apenas sem correspondência (VoIP sem par no discador) ===',
            f'Total price: {fmt_num(total_preco_sem)}',
            f'Data/hora (VoIP) — início: {inicio_sem} | fim: {fim_sem}',
            f'Soma duração VoIP (MM:WW:dd:HH:mm:ss): {fmt_dur(soma_dur_v_sem)}',
            '',
            '=== Apenas com correspondência (emparelhadas por telefone + horário) ===',
            f'Total price: {fmt_num(total_preco_com)}',
            f'Data/hora (VoIP) — início: {inicio_com} | fim: {fim_com}',
            f'Soma duração discador (MM:WW:dd:HH:mm:ss): {fmt_dur(soma_disc_com)}',
            '',
        ]
        return '\n'.join(linhas)

    def _montar_relatorio_discador_ausente_no_voip(
        self,
        df_disc_slice,
        col_dt2,
        col_dur_disc,
    ):
        """Relatório das linhas do discador cujo telefone normalizado não existe no VoIP."""
        n_lin = len(df_disc_slice)
        linhas = [
            'RELATÓRIO — Discador: números que não aparecem no arquivo VoIP',
            '(Duração: MM:WW:dd:HH:mm:ss — mes=30d, semana=7d, dd=dias, depois hora:min:seg)',
            '',
            f'Total de linhas: {self._formatar_inteiro_br(n_lin)}',
        ]
        if n_lin == 0:
            linhas.append('Telefones únicos (normalizados): 0')
            linhas.append('Data/hora (discador) — início: — | fim: —')
            linhas.append('Linhas com data/hora vazia ou inválida: 0')
            linhas.append('Soma duração discador (MM:WW:dd:HH:mm:ss): —')
            linhas.extend([
                '',
                '=== Tarifa estimada pela duração (discador) ===',
                'Regra: R$ 0,05/min; mínimo R$ 0,025 (1 s a 30 s); acima: max(0,025, (duração_s/60)×0,05).',
                'Linhas com duração >= 1 s (usadas no cálculo): 0',
                'Linhas sem duração ou < 1 s (valor 0): 0',
                'Total estimado a cobrar (soma): —',
            ])
            return '\n'.join(linhas)

        n_unicos = df_disc_slice['_tel_norm_disc'].nunique()
        linhas.append(f'Telefones únicos (normalizados): {self._formatar_inteiro_br(n_unicos)}')

        ts = pd.to_datetime(df_disc_slice[col_dt2], dayfirst=True, errors='coerce')
        n_sem_data = int(ts.isna().sum())
        ts_ok = ts.dropna()
        if ts_ok.empty:
            linhas.append('Data/hora (discador) — início: — | fim: —')
        else:
            linhas.append(
                f'Data/hora (discador) — início: {self._fmt_data_hora_br(ts_ok.min())} | '
                f'fim: {self._fmt_data_hora_br(ts_ok.max())}'
            )
        linhas.append(f'Linhas com data/hora vazia ou inválida: {self._formatar_inteiro_br(n_sem_data)}')

        dur_serie = df_disc_slice[col_dur_disc].map(self._parse_duracao_segundos)
        soma_d = dur_serie.sum(min_count=1)
        linhas.append(
            f'Soma duração discador (MM:WW:dd:HH:mm:ss): '
            f'{self._formatar_duracao_mm_ww_dd_hhmmss(soma_d)}'
        )

        precos = df_disc_slice[col_dur_disc].map(self._preco_tarifa_por_duracao_segundos)
        n_com_dur = int(((dur_serie >= 1) & dur_serie.notna()).sum())
        n_sem_dur_tarifa = n_lin - n_com_dur
        total_tarifa = float(precos.sum())

        linhas.extend([
            '',
            '=== Tarifa estimada pela duração (discador) ===',
            'Regra: R$ 0,05/min; mínimo R$ 0,025 (1 s a 30 s); acima: max(0,025, (duração_s/60)×0,05).',
            'Ex.: 45 s -> (45/60)×0,05 = 0,0375.',
            f'Linhas com duração >= 1 s (usadas no cálculo): {self._formatar_inteiro_br(n_com_dur)}',
            f'Linhas sem duração ou < 1 s (valor 0): {self._formatar_inteiro_br(n_sem_dur_tarifa)}',
            f'Total estimado a cobrar (soma): {self._formatar_moeda_br(total_tarifa, 3)}',
        ])
        return '\n'.join(linhas)

    def _emparelhar_voip_discador(self, df1, df2, col_dt1, col_dt2, tolerancia):
        """
        Por cada telefone normalizado, emparelha linhas 1:1 por menor |t1-t2| dentro da tolerância.
        Retorna dict idx_df1 -> idx_df2 (índices originais do DataFrame).
        """
        t1 = pd.to_datetime(df1[col_dt1], dayfirst=True, errors='coerce')
        t2 = pd.to_datetime(df2[col_dt2], dayfirst=True, errors='coerce')
        tel1 = df1['_tel_norm_voip']
        tel2 = df2['_tel_norm_disc']

        pares = {}
        usados1 = set()
        usados2 = set()

        for tel in tel1.dropna().unique():
            if tel == '':
                continue
            idx1_list = df1.index[tel1 == tel].tolist()
            idx2_list = df2.index[tel2 == tel].tolist()
            if not idx1_list or not idx2_list:
                continue

            candidatos = []
            for i in idx1_list:
                if i in usados1:
                    continue
                ts_i = t1.loc[i]
                if pd.isna(ts_i):
                    continue
                for j in idx2_list:
                    if j in usados2:
                        continue
                    ts_j = t2.loc[j]
                    if pd.isna(ts_j):
                        continue
                    delta = abs(ts_i - ts_j)
                    if delta <= tolerancia:
                        candidatos.append((delta, i, j))

            candidatos.sort(key=lambda x: (x[0], x[1], x[2]))
            for _, i, j in candidatos:
                if i in usados1 or j in usados2:
                    continue
                usados1.add(i)
                usados2.add(j)
                pares[i] = j

        return pares, usados2

    def mesclar_voip_discador_por_telefone_horario(self):
        """
        Mescla arquivo VoIP (1) com discador (2) por telefone + proximidade de data/hora.
        Remove DDI 55 dos telefones do arquivo 1. Colunas homônimas viram _voip / _discador.
        """
        arquivo_voip = self.selecionar_arquivo("Selecione o arquivo 1 (VoIP / base):")
        # VoIP (ex. export MONEY_ANTISPAM): cabeçalho costuma estar na linha 1
        pular_linha_voip = inquirer.select(
            message="Leitura do arquivo VoIP — primeira linha é inválida (cabeçalho na linha 2)?",
            choices=[
                Choice(False, name="Não — cabeçalho na linha 1 (padrão VoIP)"),
                Choice(True, name="Sim — pular primeira linha"),
            ],
        ).execute()
        if pular_linha_voip:
            df1 = self.carregar_arquivo_pulando_primeira_linha(arquivo_voip)
        else:
            df1 = self.carregar_arquivo(arquivo_voip)

        arquivo_disc = self.selecionar_arquivo("Selecione o arquivo 2 (discador):")
        # Mescla discador: muitos arquivos têm lixo na linha 1 e cabeçalho na linha 2
        pular_linha_disc = inquirer.select(
            message="Leitura do arquivo discador — primeira linha é inválida (cabeçalho na linha 2)?",
            choices=[
                Choice(True, name="Sim — pular primeira linha (padrão mescla discador)"),
                Choice(False, name="Não — cabeçalho na linha 1"),
            ],
        ).execute()
        if pular_linha_disc:
            df2 = self.carregar_arquivo_pulando_primeira_linha(arquivo_disc)
        else:
            df2 = self.carregar_arquivo(arquivo_disc)

        if len(df1) == 0:
            self.console.print(Panel("[red]Arquivo VoIP está vazio.[/red]", title="Erro", border_style="red"))
            return
        if len(df2) == 0:
            self.console.print(Panel("[red]Arquivo discador está vazio.[/red]", title="Erro", border_style="red"))
            return

        col_tel1 = self.selecionar_coluna(df1, "Coluna de telefone no arquivo VoIP:")
        col_dt1 = self.selecionar_coluna(df1, "Coluna de data/hora da ligação no arquivo VoIP:")
        col_tel2 = self.selecionar_coluna(df2, "Coluna de telefone no arquivo discador:")
        col_dt2 = self.selecionar_coluna(df2, "Coluna de data/hora da ligação no arquivo discador:")
        col_price = self.selecionar_coluna(df1, "Coluna de preço (Price) no VoIP:")
        col_dur_voip = self.selecionar_coluna(df1, "Coluna de duração em segundos no VoIP (ex.: Duration):")
        col_dur_disc = self.selecionar_coluna(df2, "Coluna de duração no discador (ex.: Duração(Seg)):")

        janela_txt = inquirer.text(
            message="Janela máxima entre horários VoIP e discador (segundos) [padrão 90]:",
            default="90",
        ).execute()
        try:
            janela_seg = int((janela_txt or "90").strip())
            if janela_seg < 0:
                janela_seg = 90
        except ValueError:
            janela_seg = 90
        tolerancia = pd.Timedelta(seconds=janela_seg)

        df1 = df1.copy()
        df2 = df2.copy()
        df1['_tel_norm_voip'] = df1[col_tel1].apply(self._normalizar_telefone_voip)
        df2['_tel_norm_disc'] = df2[col_tel2].apply(self._normalizar_telefone_discador)

        pares, usados_disc = self._emparelhar_voip_discador(
            df1, df2, col_dt1, col_dt2, tolerancia
        )

        # Colunas com mesmo nome nos dois arquivos (exceto telefones usados na chave)
        cols_conflito = set(df1.columns) & set(df2.columns)
        for c in (col_tel1, col_tel2):
            cols_conflito.discard(c)
        cols_conflito.discard('_tel_norm_voip')
        cols_conflito.discard('_tel_norm_disc')

        df_out = df1.drop(columns=['_tel_norm_voip'])
        renomear_voip = {c: f"{c}_voip" for c in cols_conflito}
        df_out = df_out.rename(columns=renomear_voip)

        # Telefone de saída: normalizado (sem 55)
        df_out[col_tel1] = df1.loc[df_out.index, '_tel_norm_voip']

        # Novas colunas vindas do discador
        cols_so_disc = (set(df2.columns) - set(df1.columns)) - {col_tel2, '_tel_norm_disc'}
        novas_disc = [f"{c}_discador" for c in sorted(cols_conflito)]
        novas_disc += sorted(cols_so_disc)
        for nc in novas_disc:
            df_out[nc] = ''

        # Preenche linhas emparelhadas
        for i1, i2 in pares.items():
            row2 = df2.loc[i2]
            for c in cols_conflito:
                df_out.loc[i1, f"{c}_discador"] = row2[c]
            for c in cols_so_disc:
                df_out.loc[i1, c] = row2[c]

        # Preço no CSV com vírgula decimal (ex.: 0,025) para não virar inteiro errado no Excel BR
        nome_preco_out = f"{col_price}_voip" if col_price in cols_conflito else col_price
        if nome_preco_out in df_out.columns:
            df_out[nome_preco_out] = df1.loc[df_out.index, col_price].map(self._formatar_decimal_br)

        total_pares = len(pares)
        total_sem = len(df_out) - total_pares
        total_disc_sem = len(df2) - len(usados_disc)

        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo mesclado:")
        caminho = self.salvar_arquivo(df_out, arquivo_voip, "mesclado_voip_discador_", pasta_saida)

        texto_rel = self._montar_relatorio_mesclagem_voip_discador(
            df1, df2, pares, col_dt1, col_price, col_dur_voip, col_dur_disc
        )
        base_csv, _ = os.path.splitext(caminho)
        caminho_rel = f"{base_csv}_relatorio.txt"
        with open(caminho_rel, 'w', encoding='utf-8') as f_rel:
            f_rel.write(texto_rel)

        # Discador: linhas cujo telefone normalizado não existe em nenhuma linha do VoIP
        tels_voip = set(df1['_tel_norm_voip'].astype(str).str.strip())
        tels_voip.discard('')
        tels_voip.discard('nan')
        tn_disc = df2['_tel_norm_disc'].astype(str).str.strip()
        mask_ausente_voip = (tn_disc != '') & (~tn_disc.isin(tels_voip))
        df_disc_ausente = df2.loc[mask_ausente_voip].copy()

        texto_rel_ausente = self._montar_relatorio_discador_ausente_no_voip(
            df_disc_ausente, col_dt2, col_dur_disc
        )
        df_disc_csv = df_disc_ausente.drop(columns=['_tel_norm_disc'], errors='ignore')
        caminho_disc_ausente = self.salvar_arquivo(
            df_disc_csv, arquivo_disc, "discador_numero_ausente_no_voip_", pasta_saida
        )
        base_aus, _ = os.path.splitext(caminho_disc_ausente)
        caminho_rel_ausente = f"{base_aus}_relatorio.txt"
        with open(caminho_rel_ausente, 'w', encoding='utf-8') as f_ra:
            f_ra.write(texto_rel_ausente)

        mensagem = (
            f"Mesclagem VoIP + discador:\n"
            f"├─ Linhas arquivo VoIP: {len(df_out):,}\n"
            f"├─ Linhas arquivo discador: {len(df2):,}\n"
            f"├─ Emparelhadas (telefone + horário dentro de {janela_seg}s): {total_pares:,}\n"
            f"├─ VoIP sem correspondência: {total_sem:,}\n"
            f"├─ Discador sem uso no pareamento: {total_disc_sem:,}\n"
            f"├─ Discador com número ausente no VoIP: {len(df_disc_ausente):,} linhas\n"
            f"├─ CSV mesclado: {caminho}\n"
            f"├─ Relatório mesclagem: {caminho_rel}\n"
            f"├─ CSV discador (número não está no VoIP): {caminho_disc_ausente}\n"
            f"└─ Relatório discador ausente no VoIP: {caminho_rel_ausente}"
        )
        self.console.print(Panel(mensagem, title="Sucesso", border_style="green"))

    def adicionar_dados_lote(self):
        """Adiciona dados em lote para todos os arquivos CSV de uma pasta"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        
        # Seleciona arquivo com dados adicionais
        arquivo_dados = self.selecionar_arquivo("Selecione o arquivo com dados adicionais:")
        
        # Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos processados:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para processar:[/cyan]\n" + 
            "\n".join([f"• {arquivo}" for arquivo in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))
        
        # Carrega arquivo de dados adicionais
        df_dados = self.carregar_arquivo(arquivo_dados)
        
        # Remove duplicatas do arquivo de dados adicionais
        coluna_cpf_dados = self.selecionar_coluna(df_dados, f"Selecione a coluna de CPF do arquivo de dados adicionais:")
        df_dados['cpf_formatado'] = df_dados[coluna_cpf_dados].apply(self.formatar_cpf)
        df_dados = df_dados.drop_duplicates(subset=['cpf_formatado'], keep='first')
        
        # Remove a coluna de CPF do arquivo de dados para evitar duplicação
        colunas_dados = [col for col in df_dados.columns if col != coluna_cpf_dados and col != 'cpf_formatado']
        
        # Estatísticas gerais
        total_arquivos_processados = 0
        total_linhas_com_corresp = 0
        total_linhas_sem_corresp = 0
        arquivos_com_erro = []
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df_base = self.carregar_arquivo(caminho_arquivo)
                
                # Contagem inicial
                linhas_inicial = len(df_base)
                
                # Seleciona coluna de CPF do arquivo base
                coluna_cpf_base = self.selecionar_coluna(df_base, f"Selecione a coluna de CPF (baseado no arquivo {arquivo}):")
                
                # Verifica se a coluna existe
                if coluna_cpf_base not in df_base.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_cpf_base}' não encontrada")
                    continue
                
                # Formata CPFs do arquivo base
                df_base['cpf_formatado'] = df_base[coluna_cpf_base].apply(self.formatar_cpf)
                
                # Realiza o merge
                df_com_corresp = pd.merge(
                    df_base,
                    df_dados[['cpf_formatado'] + colunas_dados],
                    on='cpf_formatado',
                    how='inner'
                )
                
                # Identifica CPFs sem correspondência
                cpfs_com_corresp = df_com_corresp['cpf_formatado'].unique()
                df_sem_corresp = df_base[~df_base['cpf_formatado'].isin(cpfs_com_corresp)]
                
                # Remove coluna temporária de CPF formatado
                df_com_corresp = df_com_corresp.drop(columns=['cpf_formatado'])
                df_sem_corresp = df_sem_corresp.drop(columns=['cpf_formatado'])
                
                # Contagem final
                linhas_com_corresp = len(df_com_corresp)
                linhas_sem_corresp = len(df_sem_corresp)
                
                total_linhas_com_corresp += linhas_com_corresp
                total_linhas_sem_corresp += linhas_sem_corresp
                
                # Salva arquivos processados
                nome_base = os.path.splitext(arquivo)[0]
                
                # Arquivo com correspondência
                caminho_com = os.path.join(pasta_saida, f"com_{nome_base}.csv")
                df_com_corresp = self.tratar_colunas_numericas(df_com_corresp.copy())
                df_com_corresp = self.limpar_aspas_duplas(df_com_corresp.copy())
                df_com_corresp.to_csv(caminho_com, sep=';', encoding='utf-8', index=False, quoting=csv.QUOTE_MINIMAL)
                
                # Arquivo sem correspondência
                caminho_sem = os.path.join(pasta_saida, f"sem_{nome_base}.csv")
                df_sem_corresp = self.tratar_colunas_numericas(df_sem_corresp.copy())
                df_sem_corresp = self.limpar_aspas_duplas(df_sem_corresp.copy())
                df_sem_corresp.to_csv(caminho_sem, sep=';', encoding='utf-8', index=False, quoting=csv.QUOTE_MINIMAL)
                
                total_arquivos_processados += 1
                
                # Mostra progresso
                self.console.print(f"[green]✓[/green] {arquivo}: {linhas_inicial:,} → com: {linhas_com_corresp:,}, sem: {linhas_sem_corresp:,}")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        # Cria mensagem final detalhada
        mensagem = (
            f"Estatísticas do Processamento em Lote:\n"
            f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
            f"├─ Total de arquivos processados: {total_arquivos_processados:,}\n"
            f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
            f"├─ Total de linhas com correspondência: {total_linhas_com_corresp:,}\n"
            f"└─ Total de linhas sem correspondência: {total_linhas_sem_corresp:,}\n\n"
            f"Pasta de saída: {pasta_saida}\n\n"
            f"[cyan]Arquivos gerados:[/cyan]\n"
            f"• com_[nome_arquivo].csv - CPFs encontrados no arquivo de dados\n"
            f"• sem_[nome_arquivo].csv - CPFs não encontrados no arquivo de dados"
        )
        
        if arquivos_com_erro:
            mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído",
            border_style="green"
        ))

    def mesclar_arquivos_csv(self):
        """Mescla múltiplos arquivos CSV de uma pasta em um único arquivo"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        
        # Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo mesclado:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para mesclar:[/cyan]\n" + 
            "\n".join([f"• {arquivo}" for arquivo in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))
        
        # Coleta todas as colunas únicas de todos os arquivos
        todas_colunas = set()
        colunas_ordenadas = []  # Lista para manter a ordem das colunas
        arquivos_com_erro = []
        total_linhas = 0
        
        # Primeira passagem: identificar todas as colunas únicas mantendo a ordem
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df_temp = self.carregar_arquivo(caminho_arquivo)
                
                # Adiciona colunas na ordem que aparecem no arquivo
                for coluna in df_temp.columns:
                    if coluna not in todas_colunas:
                        todas_colunas.add(coluna)
                        colunas_ordenadas.append(coluna)
                
                total_linhas += len(df_temp)
                self.console.print(f"[blue]📋[/blue] {arquivo}: {len(df_temp.columns)} colunas, {len(df_temp):,} linhas")
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro ao ler: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao ler arquivo")
        
        # Usa a lista ordenada em vez de ordenar alfabeticamente
        todas_colunas = colunas_ordenadas
        
        self.console.print(Panel(
            f"[yellow]Colunas únicas encontradas ({len(todas_colunas)}):[/yellow]\n" + 
            "\n".join([f"• {coluna}" for coluna in todas_colunas]),
            title="Colunas Identificadas",
            border_style="yellow"
        ))
        
        # Lista para armazenar todos os DataFrames processados
        dataframes_mesclados = []
        arquivos_processados = 0
        
        # Segunda passagem: processar cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo(caminho_arquivo)
                
                # Cria um DataFrame com todas as colunas, preenchendo com valores vazios
                df_mesclado = pd.DataFrame(columns=todas_colunas)
                
                # Copia os dados existentes
                for coluna in df.columns:
                    if coluna in todas_colunas:
                        df_mesclado[coluna] = df[coluna]
                
                # Preenche colunas ausentes com valores vazios
                for coluna in todas_colunas:
                    if coluna not in df.columns:
                        df_mesclado[coluna] = ''
                
                dataframes_mesclados.append(df_mesclado)
                arquivos_processados += 1
                
                self.console.print(f"[green]✓[/green] {arquivo}: {len(df):,} linhas processadas")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro ao processar: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        if not dataframes_mesclados:
            self.console.print(Panel(
                "[red]Nenhum arquivo foi processado com sucesso![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        # Concatena todos os DataFrames
        df_final = pd.concat(dataframes_mesclados, ignore_index=True)
        
        # Trata colunas numéricas
        df_final = self.tratar_colunas_numericas(df_final.copy())
        
        # Limpa aspas duplas desnecessárias que podem causar escape duplo
        df_final = self.limpar_aspas_duplas(df_final.copy())
        
        # Salva arquivo mesclado
        nome_arquivo_saida = "arquivo_mesclado.csv"
        caminho_saida = os.path.join(pasta_saida, nome_arquivo_saida)
        
        try:
            df_final.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False, quoting=csv.QUOTE_MINIMAL)
            
            # Cria mensagem final detalhada
            mensagem = (
                f"Estatísticas da Mesclagem:\n"
                f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
                f"├─ Total de arquivos processados: {arquivos_processados:,}\n"
                f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
                f"├─ Total de colunas únicas: {len(todas_colunas):,}\n"
                f"├─ Total de linhas no arquivo final: {len(df_final):,}\n\n"
                f"Arquivo salvo como: {caminho_saida}\n\n"
                f"[cyan]Colunas no arquivo final:[/cyan]\n" + 
                "\n".join([f"• {coluna}" for coluna in todas_colunas])
            )
            
            if arquivos_com_erro:
                mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
            
            self.console.print(Panel(
                mensagem,
                title="Mesclagem Concluída",
                border_style="green"
            ))
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo mesclado:[/red]\n\n"
                f"Erro: {str(e)}\n\n"
                f"[cyan]Verifique as permissões da pasta de destino.[/cyan]",
                title="Erro",
                border_style="red"
                         ))

    def mesclar_arquivos_csv_pulando_primeira_linha(self):
        """Mescla múltiplos arquivos CSV ignorando a linha 1 (bugada) e usando a linha 2 como cabeçalho"""
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo mesclado:")

        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]

        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return

        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para mesclar.[/cyan]\n"
            f"[yellow]Será ignorada a linha 1 de cada arquivo (cabeçalho real na linha 2).[/yellow]\n\n" +
            "\n".join([f"• {a}" for a in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))

        todas_colunas = set()
        colunas_ordenadas = []
        arquivos_com_erro = []
        total_linhas = 0

        for arquivo in arquivos_csv:
            try:
                caminho = os.path.join(pasta_entrada, arquivo)
                df_temp = self.carregar_arquivo_pulando_primeira_linha(caminho)
                for coluna in df_temp.columns:
                    if coluna not in todas_colunas:
                        todas_colunas.add(coluna)
                        colunas_ordenadas.append(coluna)
                total_linhas += len(df_temp)
                self.console.print(f"[blue]📋[/blue] {arquivo}: {len(df_temp.columns)} colunas, {len(df_temp):,} linhas")
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro ao ler: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao ler arquivo")

        todas_colunas = colunas_ordenadas

        dataframes_mesclados = []
        arquivos_processados = 0

        for arquivo in arquivos_csv:
            try:
                caminho = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo_pulando_primeira_linha(caminho)
                df_mesclado = pd.DataFrame(columns=todas_colunas)
                for coluna in df.columns:
                    if coluna in todas_colunas:
                        df_mesclado[coluna] = df[coluna]
                for coluna in todas_colunas:
                    if coluna not in df.columns:
                        df_mesclado[coluna] = ''
                dataframes_mesclados.append(df_mesclado)
                arquivos_processados += 1
                self.console.print(f"[green]✓[/green] {arquivo}: {len(df):,} linhas processadas")
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro ao processar: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")

        if not dataframes_mesclados:
            self.console.print(Panel(
                "[red]Nenhum arquivo foi processado com sucesso![/red]",
                title="Erro",
                border_style="red"
            ))
            return

        df_final = pd.concat(dataframes_mesclados, ignore_index=True)
        df_final = self.tratar_colunas_numericas(df_final.copy())
        df_final = self.limpar_aspas_duplas(df_final.copy())

        nome_saida = "arquivo_mesclado.csv"
        caminho_saida = os.path.join(pasta_saida, nome_saida)

        try:
            df_final.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False, quoting=csv.QUOTE_MINIMAL)
            mensagem = (
                f"Estatísticas da Mesclagem:\n"
                f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
                f"├─ Total de arquivos processados: {arquivos_processados:,}\n"
                f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
                f"├─ Total de colunas únicas: {len(todas_colunas):,}\n"
                f"├─ Total de linhas no arquivo final: {len(df_final):,}\n\n"
                f"Arquivo salvo como: {caminho_saida}\n\n"
                f"[yellow]Linha 1 de cada arquivo foi ignorada (cabeçalho na linha 2).[/yellow]"
            )
            if arquivos_com_erro:
                mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {e}" for e in arquivos_com_erro])
            self.console.print(Panel(mensagem, title="Mesclagem Concluída", border_style="green"))
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo mesclado:[/red]\n\nErro: {str(e)}",
                title="Erro",
                border_style="red"
            ))

    def adicionar_coluna_personalizada(self):
        """Adiciona uma coluna personalizada com valor específico baseado em CPF"""
        # Seleciona arquivo base
        arquivo_base = self.selecionar_arquivo("Selecione o arquivo base:")
        
        # Carrega arquivo
        df = self.carregar_arquivo(arquivo_base)
        
        # Contagem inicial
        total_linhas = len(df)
        
        # Seleciona coluna de CPF
        coluna_cpf = self.selecionar_coluna(df, "Selecione a coluna de CPF:")
        
        # Solicita nome da nova coluna
        nome_coluna = inquirer.text(
            message="Digite o nome da nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Solicita valor a ser adicionado
        valor_coluna = inquirer.text(
            message="Digite o valor/string a ser adicionado na nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Formata CPFs para comparação
        df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
        
        # Adiciona a nova coluna com o valor especificado
        df[nome_coluna] = valor_coluna
        
        # Remove coluna temporária
        df = df.drop(columns=['cpf_formatado'])
        
        # Trata colunas numéricas
        df = self.tratar_colunas_numericas(df.copy())
        
        # Salva arquivo
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar o arquivo:")
        caminho_saida = self.salvar_arquivo(df, arquivo_base, "coluna_adicionada_", pasta_saida)
        
        # Cria mensagem detalhada
        mensagem = (
            f"Estatísticas do Processamento:\n"
            f"├─ Total de linhas processadas: {total_linhas:,}\n"
            f"├─ Nova coluna adicionada: '{nome_coluna}'\n"
            f"├─ Valor adicionado: '{valor_coluna}'\n"
            f"└─ Total de colunas no arquivo final: {len(df.columns):,}\n\n"
            f"Arquivo salvo como: {caminho_saida}"
        )
        
        self.console.print(Panel(
            mensagem,
            title="Sucesso",
            border_style="green"
        ))

    def adicionar_coluna_personalizada_lote(self):
        """Adiciona uma coluna personalizada em lote para todos os arquivos CSV de uma pasta"""
        # Seleciona pasta com arquivos CSV
        pasta_entrada = self.selecionar_pasta_entrada("Selecione a pasta com os arquivos CSV:")
        
        # Seleciona pasta de saída
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos processados:")
        
        # Lista todos os arquivos CSV na pasta
        arquivos_csv = [f for f in os.listdir(pasta_entrada) if f.endswith('.csv')]
        
        if not arquivos_csv:
            self.console.print(Panel(
                "[red]Nenhum arquivo CSV encontrado na pasta selecionada![/red]",
                title="Erro",
                border_style="red"
            ))
            return
        
        self.console.print(Panel(
            f"[cyan]Encontrados {len(arquivos_csv)} arquivos CSV para processar:[/cyan]\n" + 
            "\n".join([f"• {arquivo}" for arquivo in arquivos_csv]),
            title="Arquivos Encontrados",
            border_style="cyan"
        ))
        
        # Solicita nome da nova coluna
        nome_coluna = inquirer.text(
            message="Digite o nome da nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Solicita valor a ser adicionado
        valor_coluna = inquirer.text(
            message="Digite o valor/string a ser adicionado na nova coluna:",
            filter=lambda x: x.strip(),
        ).execute()
        
        # Estatísticas gerais
        total_arquivos_processados = 0
        total_linhas_processadas = 0
        arquivos_com_erro = []
        
        # Processa cada arquivo
        for arquivo in arquivos_csv:
            try:
                caminho_arquivo = os.path.join(pasta_entrada, arquivo)
                df = self.carregar_arquivo(caminho_arquivo)
                
                # Contagem inicial
                linhas_inicial = len(df)
                
                # Seleciona coluna de CPF
                coluna_cpf = self.selecionar_coluna(df, f"Selecione a coluna de CPF (baseado no arquivo {arquivo}):")
                
                # Verifica se a coluna existe
                if coluna_cpf not in df.columns:
                    arquivos_com_erro.append(f"{arquivo} - Coluna '{coluna_cpf}' não encontrada")
                    continue
                
                # Formata CPFs para comparação
                df['cpf_formatado'] = df[coluna_cpf].apply(self.formatar_cpf)
                
                # Adiciona a nova coluna com o valor especificado
                df[nome_coluna] = valor_coluna
                
                # Remove coluna temporária
                df = df.drop(columns=['cpf_formatado'])
                
                # Trata colunas numéricas
                df = self.tratar_colunas_numericas(df.copy())
                
                # Salva arquivo processado
                nome_base = os.path.splitext(arquivo)[0]
                caminho_saida = os.path.join(pasta_saida, f"coluna_adicionada_{nome_base}.csv")
                df = self.limpar_aspas_duplas(df.copy())
                df.to_csv(caminho_saida, sep=';', encoding='utf-8', index=False, quoting=csv.QUOTE_MINIMAL)
                
                total_arquivos_processados += 1
                total_linhas_processadas += linhas_inicial
                
                # Mostra progresso
                self.console.print(f"[green]✓[/green] {arquivo}: {linhas_inicial:,} linhas processadas")
                
            except Exception as e:
                arquivos_com_erro.append(f"{arquivo} - Erro: {str(e)}")
                self.console.print(f"[red]✗[/red] {arquivo}: Erro ao processar")
        
        # Cria mensagem final detalhada
        mensagem = (
            f"Estatísticas do Processamento em Lote:\n"
            f"├─ Total de arquivos encontrados: {len(arquivos_csv):,}\n"
            f"├─ Total de arquivos processados: {total_arquivos_processados:,}\n"
            f"├─ Total de arquivos com erro: {len(arquivos_com_erro):,}\n"
            f"├─ Total de linhas processadas: {total_linhas_processadas:,}\n"
            f"├─ Nova coluna adicionada: '{nome_coluna}'\n"
            f"└─ Valor adicionado: '{valor_coluna}'\n\n"
            f"Pasta de saída: {pasta_saida}"
        )
        
        if arquivos_com_erro:
            mensagem += f"\n\n[red]Arquivos com erro:[/red]\n" + "\n".join([f"• {erro}" for erro in arquivos_com_erro])
        
        self.console.print(Panel(
            mensagem,
            title="Processamento em Lote Concluído",
            border_style="green"
        ))

    def normalizar_razao_social(self, valor):
        """Normaliza razão social para comparação: acentos, pontuação (. - , &), espaços. Compatível com arquivos tipo CLT (; RAZAO SOCIAL) e com_cnpj (CNPJ, RAZAO SOCIAL)."""
        if pd.isna(valor) or valor == '' or str(valor).strip() == '':
            return ''
        s = str(valor).strip().upper()
        s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        s = s.replace('.', '').replace('-', ' ').replace(',', ' ').replace('&', ' ')
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def formatar_cnpj_celula(self, cnpj):
        """Formata CNPJ para string limpa (só números ou como está)"""
        if pd.isna(cnpj) or cnpj == '' or str(cnpj).strip() == '':
            return ''
        return str(cnpj).strip()

    def juntar_por_razao_social(self):
        """Adiciona CNPJ ao arquivo 1 a partir do arquivo 2, usando Razão Social como chave. Arquivo 2 pode ter mesma empresa com vários CNPJs."""
        arquivo1 = self.selecionar_arquivo("Selecione o arquivo com dados da empresa (sem CNPJ preenchido):")
        arquivo2 = self.selecionar_arquivo("Selecione o arquivo com Razão Social e CNPJ:")
        df1 = self.carregar_arquivo(arquivo1)
        df2 = self.carregar_arquivo(arquivo2)
        if df1.empty:
            self.console.print(Panel("[red]Arquivo 1 está vazio![/red]", title="Erro", border_style="red"))
            return
        if df2.empty:
            self.console.print(Panel("[red]Arquivo 2 está vazio![/red]", title="Erro", border_style="red"))
            return
        col_razao_1 = self.selecionar_coluna(df1, "Selecione a coluna de Razão Social no arquivo de dados da empresa:")
        col_razao_2 = self.selecionar_coluna(df2, "Selecione a coluna de Razão Social no arquivo de referência:")
        col_cnpj_2 = self.selecionar_coluna(df2, "Selecione a coluna de CNPJ no arquivo de referência:")
        col_cnpj_saida = 'CNPJ'
        if col_cnpj_saida not in df1.columns:
            df1[col_cnpj_saida] = ''
        razao_para_cnpjs = {}
        for _, row in df2.iterrows():
            razao_norm = self.normalizar_razao_social(row[col_razao_2])
            cnpj_val = self.formatar_cnpj_celula(row[col_cnpj_2])
            if not razao_norm or not cnpj_val:
                continue
            if razao_norm not in razao_para_cnpjs:
                razao_para_cnpjs[razao_norm] = []
            if cnpj_val not in razao_para_cnpjs[razao_norm]:
                razao_para_cnpjs[razao_norm].append(cnpj_val)
        preenchidos = 0
        vazios = 0
        for idx in df1.index:
            razao_norm = self.normalizar_razao_social(df1.at[idx, col_razao_1])
            if not razao_norm:
                vazios += 1
                continue
            cnpjs = razao_para_cnpjs.get(razao_norm, [])
            if cnpjs:
                df1.at[idx, col_cnpj_saida] = '; '.join(cnpjs)
                preenchidos += 1
            else:
                vazios += 1
        pasta_saida = self.selecionar_pasta_saida("Selecione a pasta para salvar os arquivos:")
        col_cnpj_str = df1[col_cnpj_saida].astype(str)
        mask_1_cnpj = col_cnpj_str.str.strip().ne('') & ~col_cnpj_str.str.contains(';', na=False)
        mask_varios_cnpj = col_cnpj_str.str.contains(';', na=False)
        df_1_cnpj = df1[mask_1_cnpj].copy()
        df_varios_raw = df1[mask_varios_cnpj].copy()
        lista_linhas = []
        for idx in df_varios_raw.index:
            row = df_varios_raw.loc[idx].copy()
            cnpjs = [c.strip() for c in str(row[col_cnpj_saida]).split(';') if c.strip()]
            for cnpj in cnpjs:
                row[col_cnpj_saida] = cnpj
                lista_linhas.append(row.copy())
        df_varios_cnpj = pd.DataFrame(lista_linhas, columns=df1.columns) if lista_linhas else pd.DataFrame(columns=df1.columns)
        mask_sem_corresp = col_cnpj_str.str.strip() == ''
        df_sem_corresp = df1[mask_sem_corresp].copy()
        caminho_1 = self.salvar_arquivo(df_1_cnpj, arquivo1, "1_cnpj_", pasta_saida)
        caminho_varios = self.salvar_arquivo(df_varios_cnpj, arquivo1, "varios_cnpj_", pasta_saida)
        caminho_sem = self.salvar_arquivo(df_sem_corresp, arquivo1, "sem_corresp_", pasta_saida)
        mensagem = (
            f"Juntar por Razão Social:\n"
            f"├─ Arquivo dados empresa: {len(df1):,} linhas\n"
            f"├─ Arquivo Razão Social/CNPJ: {len(df2):,} linhas\n"
            f"├─ Linhas com 1 CNPJ: {len(df_1_cnpj):,} → 1_cnpj_...\n"
            f"├─ Empresas com vários CNPJ → {len(df_varios_cnpj):,} linhas (1 por CNPJ) → varios_cnpj_...\n"
            f"├─ Razão social não está no arquivo 2: {len(df_sem_corresp):,} → sem_corresp_...\n"
            f"├─ Arquivo 1 CNPJ: {caminho_1}\n"
            f"├─ Arquivo vários CNPJ: {caminho_varios}\n"
            f"└─ Arquivo sem correspondência: {caminho_sem}"
        )
        self.console.print(Panel(mensagem, title="Sucesso", border_style="green"))

    def executar(self):
        """Executa o menu de adição e mesclagem"""
        while True:
            opcao = self.menu_add_or_mescle()
            
            if opcao == "1":
                self.unir_colunas_por_cpf()
            elif opcao == "2":
                self.adicionar_dados_lote()
            elif opcao == "3":
                self.mesclar_arquivos_csv()
            elif opcao == "4":
                self.adicionar_coluna_personalizada()
            elif opcao == "5":
                self.adicionar_coluna_personalizada_lote()
            else:
                break
