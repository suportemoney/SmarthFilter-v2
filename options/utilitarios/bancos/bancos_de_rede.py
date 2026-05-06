#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para Gerar Lista de Bancos de Rede
Gera um CSV com código e nome dos bancos de rede (com agências físicas)
a partir da API oficial de agências do Banco Central do Brasil.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, Tuple, List
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from InquirerPy import inquirer
from options.utils import selecionar_pasta

BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Informes_Agencias/"
    "versao/v1/odata/Agencias"
)

# Lista de estados brasileiros (UF)
ESTADOS_BRASIL = [
    ("AC", "Acre"),
    ("AL", "Alagoas"),
    ("AP", "Amapá"),
    ("AM", "Amazonas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"),
    ("GO", "Goiás"),
    ("MA", "Maranhão"),
    ("MT", "Mato Grosso"),
    ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"),
    ("PA", "Pará"),
    ("PB", "Paraíba"),
    ("PR", "Paraná"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RJ", "Rio de Janeiro"),
    ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"),
    ("RO", "Rondônia"),
    ("RR", "Roraima"),
    ("SC", "Santa Catarina"),
    ("SP", "São Paulo"),
    ("SE", "Sergipe"),
    ("TO", "Tocantins"),
]


class BancosDeRede:
    def __init__(self):
        self.console = Console()

    def _fetch_agencias(self, top: int = 1000, max_retries: int = 3, uf_filtro: str = None):
        """
        Faz paginação na API de agências do Bacen e devolve um gerador
        com os registros (cada item é um dict).
        
        Args:
            top: Número de registros por página
            max_retries: Número máximo de tentativas em caso de erro
            uf_filtro: UF (estado) para filtrar (ex: "SP", "RJ"). None para todos os estados.
        """
        skip = 0
        total_items = 0
        
        while True:
            params = {
                "$top": top,
                "$skip": skip,
                "$format": "json",
            }
            
            # Nota: A API do Banco Central não suporta filtro OData por UF diretamente
            # O filtro será feito no lado do cliente após receber os dados
            
            # Tentar com retry
            items = []
            resp = None
            data = None
            
            for tentativa in range(max_retries):
                try:
                    # Timeout maior para API do Banco Central que pode ser lenta
                    # (connect timeout, read timeout)
                    resp = requests.get(BASE_URL, params=params, timeout=(15, 90))
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get("value", [])
                    break  # Sucesso, sair do loop de retry
                except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
                    if tentativa < max_retries - 1:
                        self.console.print(f"[yellow]⚠️ Tentativa {tentativa + 1}/{max_retries} falhou (timeout). Tentando novamente...[/yellow]")
                        import time
                        time.sleep(2)  # Aguarda 2 segundos antes de tentar novamente
                        continue
                    else:
                        # Última tentativa falhou
                        self.console.print(f"[red]❌ Timeout após {max_retries} tentativas[/red]")
                        self.console.print(f"[yellow]A API do Banco Central está demorando muito para responder.[/yellow]")
                        return  # Retorna vazio do gerador
                except requests.RequestException as e:
                    if tentativa < max_retries - 1:
                        self.console.print(f"[yellow]⚠️ Tentativa {tentativa + 1}/{max_retries} falhou. Tentando novamente...[/yellow]")
                        import time
                        time.sleep(2)
                        continue
                    else:
                        # Última tentativa falhou
                        self.console.print(f"[red]❌ Erro após {max_retries} tentativas: {str(e)}[/red]")
                        return  # Retorna vazio do gerador
            
            # Processar items retornados
            if not items:
                if skip == 0:
                    # Primeira requisição não retornou nada - pode ser problema na API
                    self.console.print(f"[yellow]⚠️ API retornou vazio na primeira requisição[/yellow]")
                    if resp:
                        self.console.print(f"[dim]URL: {resp.url}[/dim]")
                        self.console.print(f"[dim]Status: {resp.status_code}[/dim]")
                    if data:
                        self.console.print(f"[dim]Resposta: {str(data)[:200]}...[/dim]")
                break
            
            total_items += len(items)
            for item in items:
                yield item
            
            # Se voltou menos que o limite, acabou a paginação
            if len(items) < top:
                break
            
            skip += top

    def _extract_codigo_nome(self, ag: dict) -> Tuple[str, str]:
        """
        Tenta extrair o código de compensação do banco e o nome da instituição
        a partir do registro da agência.
        """
        # Códigos de compensação / número do banco
        # Tentar diferentes variações de nomes de campos (API pode mudar)
        codigo_candidates = [
            "CodigoCompe",
            "Codigo_Compe",
            "CodigoCompensacao",
            "Numero_Codigo",
            "NumeroBanco",
            "Numero_Banco",
            "Codigo",
            "codigo",
            "CODIGO_COMPE",
        ]
        
        nome_candidates = [
            "NomeIf",  # Nome da Instituição Financeira (campo real da API)
            "NomeInstituicao",
            "Nome_Instituicao",
            "NomeExtenso",
            "Nome_Extenso",
            "NomeReduzido",
            "Nome_Reduzido",
            "Instituicao",
            "instituicao",
            "Nome",
            "nome",
            "NOME_INSTITUICAO",
        ]
        
        codigo = None
        for field in codigo_candidates:
            if field in ag:
                valor = ag[field]
                # Aceita qualquer valor não None e não vazio (mesmo que seja 0)
                if valor is not None and str(valor).strip():
                    codigo = str(valor).strip()
                    break
        
        nome = None
        for field in nome_candidates:
            if field in ag:
                valor = ag[field]
                # Aceita qualquer valor não None e não vazio
                if valor is not None and str(valor).strip():
                    nome = str(valor).strip()
                    break
        
        return codigo or "", nome or ""

    def listar_bancos_de_rede(self, progress=None, progress_task=None, uf_filtro: str = None) -> List[Tuple[str, str]]:
        """
        Retorna uma lista de tuplas (codigo_banco, nome_banco) contendo
        apenas bancos que possuem ao menos uma agência física na base do Bacen.
        A deduplicação é feita por código do banco.
        
        Args:
            progress: Objeto Progress do Rich (opcional)
            progress_task: Task ID do progresso (opcional)
            uf_filtro: UF (estado) para filtrar (ex: "SP", "RJ"). None para todos os estados.
        """
        mensagem_inicio = "[bold cyan]Conectando à API do Banco Central do Brasil...[/bold cyan]\n"
        if uf_filtro:
            nome_estado = next((nome for sigla, nome in ESTADOS_BRASIL if sigla == uf_filtro.upper()), uf_filtro)
            mensagem_inicio += f"[dim]Buscando dados de agências bancárias no estado: {nome_estado} ({uf_filtro.upper()})[/dim]\n"
            mensagem_inicio += f"[yellow]⚠️ Nota: Filtrando no lado do cliente (pode demorar mais)[/yellow]"
        else:
            mensagem_inicio += "[dim]Buscando dados de agências bancárias[/dim]"
        
        self.console.print(Panel(
            mensagem_inicio,
            title="Iniciando",
            border_style="cyan"
        ))
        
        bancos: Dict[str, str] = {}
        total_processado = 0
        total_sem_codigo = 0
        total_sem_nome = 0
        total_codigo_invalido = 0
        exemplo_agencia = None
        
        # Debug: identificar campo de UF no primeiro registro
        primeiro_registro_verificado = False
        
        for agencia in self._fetch_agencias(uf_filtro=uf_filtro):
            # Filtrar por UF no lado do cliente (a API não suporta filtro OData por UF)
            if uf_filtro:
                # Debug: verificar campos de UF no primeiro registro
                if not primeiro_registro_verificado:
                    campos_uf = [k for k in agencia.keys() if 'uf' in k.lower() or 'estado' in k.lower() or 'Uf' in k or 'Municipio' in k]
                    if campos_uf:
                        self.console.print(f"[dim]🔍 Campos de UF encontrados: {campos_uf}[/dim]")
                        for campo in campos_uf[:3]:  # Mostrar apenas os 3 primeiros
                            self.console.print(f"[dim]  {campo}: {agencia.get(campo, 'N/A')}[/dim]")
                    primeiro_registro_verificado = True
                
                # Tentar diferentes nomes de campos para UF
                uf_agencia = None
                for campo_uf in ["Uf", "UF", "uf", "Estado", "estado", "EstadoSigla", "Estado_Sigla", "MunicipioUf", "Municipio_Uf"]:
                    if campo_uf in agencia:
                        valor_uf = agencia[campo_uf]
                        if valor_uf is not None:
                            uf_agencia = str(valor_uf).strip().upper()
                            # Se o campo contém mais informações (ex: "Porto Alegre/RS"), extrair apenas a UF
                            if "/" in uf_agencia:
                                uf_agencia = uf_agencia.split("/")[-1].strip()
                            break
                
                # Se não encontrou o campo ou não corresponde ao filtro, pular
                if not uf_agencia or uf_agencia != uf_filtro.upper():
                    continue
            
            total_processado += 1
            
            # Guarda primeiro exemplo para debug
            if exemplo_agencia is None:
                exemplo_agencia = agencia
            
            if progress and progress_task:
                progress.update(
                    progress_task,
                    description=f"[cyan]Processando agências... ({total_processado} processadas)[/cyan]"
                )
            
            codigo, nome = self._extract_codigo_nome(agencia)
            
            # Debug: verificar se os campos existem no dict (apenas se não estiver filtrando)
            if total_processado == 1 and not uf_filtro:
                self.console.print(f"[dim]🔍 Debug - Primeiro registro:[/dim]")
                self.console.print(f"[dim]Campos disponíveis: {list(agencia.keys())[:15]}...[/dim]")
                self.console.print(f"[dim]CodigoCompe: {agencia.get('CodigoCompe', 'NÃO ENCONTRADO')}[/dim]")
                self.console.print(f"[dim]NomeIf: {agencia.get('NomeIf', 'NÃO ENCONTRADO')}[/dim]")
                # Verificar campos relacionados a UF/estado
                campos_uf = [k for k in agencia.keys() if 'uf' in k.lower() or 'estado' in k.lower() or 'Uf' in k]
                if campos_uf:
                    self.console.print(f"[dim]Campos de UF encontrados: {campos_uf}[/dim]")
                    for campo in campos_uf:
                        self.console.print(f"[dim]{campo}: {agencia.get(campo, 'N/A')}[/dim]")
                self.console.print(f"[dim]Extraído - código: '{codigo}', nome: '{nome}'[/dim]")
            
            # Ignora registros sem código ou nome
            if not codigo:
                total_sem_codigo += 1
                continue
            
            if not nome:
                total_sem_nome += 1
                continue
            
            # Alguns registros podem ter códigos "000" ou coisas não úteis
            if not codigo.isdigit():
                total_codigo_invalido += 1
                continue
            
            # Salva o primeiro nome encontrado para aquele código
            bancos.setdefault(codigo, nome)
        
        # Debug: mostrar estatísticas se não encontrou bancos
        if not bancos and total_processado > 0:
            self.console.print(Panel(
                f"[yellow]⚠️ Processamento concluído mas nenhum banco válido encontrado[/yellow]\n\n"
                f"[cyan]Estatísticas:[/cyan]\n"
                f"├─ Agências processadas: {total_processado:,}\n"
                f"├─ Sem código: {total_sem_codigo:,}\n"
                f"├─ Sem nome: {total_sem_nome:,}\n"
                f"└─ Código inválido: {total_codigo_invalido:,}\n\n"
                f"[dim]Exemplo de registro recebido:[/dim]\n"
                f"{str(exemplo_agencia)[:300] if exemplo_agencia else 'N/A'}...",
                title="Debug",
                border_style="yellow"
            ))
        elif total_processado == 0:
            self.console.print(Panel(
                "[red]❌ Nenhuma agência foi retornada pela API[/red]\n"
                "[yellow]Possíveis causas:[/yellow]\n"
                "• API do Banco Central temporariamente indisponível\n"
                "• Problema de conexão com a internet\n"
                "• Mudança na estrutura da API",
                title="Erro",
                border_style="red"
            ))
        
        # Retorna ordenado pelo código do banco
        return sorted(bancos.items(), key=lambda x: int(x[0]))

    def gerar_csv_bancos_de_rede(self, caminho_saida: str | Path, uf_filtro: str = None) -> Path:
        """
        Gera um arquivo CSV com cabeçalho:
            codigo_banco,nome_banco
        E retorna o Path para o arquivo criado.
        
        Args:
            caminho_saida: Caminho onde salvar o arquivo CSV
            uf_filtro: UF (estado) para filtrar (ex: "SP", "RJ"). None para todos os estados.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress_task = progress.add_task("[cyan]Buscando dados da API...[/cyan]", total=None)
            
            bancos = self.listar_bancos_de_rede(progress=progress, progress_task=progress_task, uf_filtro=uf_filtro)
        
        if not bancos:
            self.console.print(Panel(
                "[red]Nenhum banco foi encontrado![/red]\n"
                "[yellow]Verifique sua conexão com a internet ou tente novamente mais tarde.[/yellow]",
                title="Erro",
                border_style="red"
            ))
            return None
        
        caminho = Path(caminho_saida).resolve()
        
        try:
            with caminho.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["codigo_banco", "nome_banco"])
                writer.writerows(bancos)
            
            return caminho
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]Erro ao salvar arquivo:[/red]\n{str(e)}",
                title="Erro",
                border_style="red"
            ))
            return None

    def executar(self):
        """Função principal do módulo"""
        self.console.print(Panel.fit(
            "[bold blue]Gerar Lista de Bancos de Rede[/bold blue]\n"
            "[italic]Lista bancos com agências físicas do Banco Central[/italic]",
            border_style="blue"
        ))
        
        # Perguntar se deseja filtrar por estado
        self.console.print()
        filtrar_estado = inquirer.confirm(
            message="Deseja filtrar por estado (UF)?",
            default=False
        ).execute()
        
        uf_filtro = None
        if filtrar_estado:
            # Criar lista de opções de estados
            opcoes_estados = [f"{sigla} - {nome}" for sigla, nome in ESTADOS_BRASIL]
            opcoes_estados.append("← Voltar (sem filtro)")
            
            estado_selecionado = inquirer.select(
                message="Selecione o estado:",
                choices=opcoes_estados,
                default=None
            ).execute()
            
            if estado_selecionado and estado_selecionado != "← Voltar (sem filtro)":
                # Extrair a sigla (primeiros 2 caracteres)
                uf_filtro = estado_selecionado.split(" - ")[0].strip()
            else:
                uf_filtro = None
        
        # Selecionar pasta de saída
        pasta_saida = selecionar_pasta("Selecione a pasta para salvar o arquivo CSV:")
        
        if not pasta_saida:
            self.console.print("[yellow]Operação cancelada.[/yellow]")
            return
        
        # Nome do arquivo
        nome_arquivo = inquirer.text(
            message="Digite o nome do arquivo (sem extensão):",
            default="bancos_de_rede",
            filter=lambda x: x.strip() if x else "bancos_de_rede"
        ).execute()
        
        caminho_saida = Path(pasta_saida) / f"{nome_arquivo}.csv"
        
        # Gerar CSV
        arquivo_gerado = self.gerar_csv_bancos_de_rede(caminho_saida, uf_filtro=uf_filtro)
        
        if arquivo_gerado:
            # Contar bancos do arquivo gerado
            try:
                with arquivo_gerado.open("r", encoding="utf-8") as f:
                    reader = csv.reader(f, delimiter=';')
                    next(reader)  # Pula cabeçalho
                    total_bancos = sum(1 for _ in reader)
            except:
                total_bancos = 0
            
            mensagem_estatisticas = f"[bold green]CSV gerado com sucesso![/bold green]\n\n"
            mensagem_estatisticas += f"[cyan]Estatísticas:[/cyan]\n"
            mensagem_estatisticas += f"├─ Total de bancos encontrados: {total_bancos:,}\n"
            if uf_filtro:
                nome_estado = next((nome for sigla, nome in ESTADOS_BRASIL if sigla == uf_filtro.upper()), uf_filtro)
                mensagem_estatisticas += f"├─ Estado filtrado: {nome_estado} ({uf_filtro.upper()})\n"
            mensagem_estatisticas += f"├─ Arquivo gerado: {arquivo_gerado.name}\n"
            mensagem_estatisticas += f"└─ Localização: {arquivo_gerado}\n\n"
            mensagem_estatisticas += f"[dim]Fonte: API do Banco Central do Brasil[/dim]"
            
            self.console.print(Panel(
                mensagem_estatisticas,
                title="Sucesso",
                border_style="green"
            ))


if __name__ == "__main__":
    app = BancosDeRede()
    app.executar()

