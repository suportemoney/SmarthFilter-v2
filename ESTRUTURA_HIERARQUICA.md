# Estrutura Hierárquica do SmartFiler2

## Sistema Organizado: Categorias → SubCategorias → Opções → Programa

### 📊 Dados
Manipulação e processamento de dados

#### Remoção
- Remover Duplicatas de CPF
- Remover Duplicatas de CPF em Lote
- Remover Duplicatas CPF (Manter Maior Valor)
- Remover CPFs da Blacklist
- Remover Números da Blacklist
- Remover Números Blacklist em Lote
- Remover Celulares da Blacklist

#### Filtragem
- Dividir Arquivo em Partes
- Blacklist por CPF (Arquivos por Pasta)
- Repartir por Coluna
- Remover Linhas Vazias/Zero
- Remover Linhas Vazias em Lote
- Adicionar Coluna de Idade

#### Adição e Mesclagem
- Unir Colunas por CPF
- Adicionar Dados em Lote
- Mesclar Arquivos CSV
- Adicionar Coluna Personalizada
- Adicionar Coluna Personalizada em Lote

#### Correlação
- Correlacionar Colunas
- Corrigir Totais de Colunas
- Normalizar Valores

### 🔄 Conversão
Conversão de formatos e extração de dados

#### Formatos
- Converter CSV para UTF-8
- Converter TXT para CSV

#### Extração
- Extrair CNPJs
- Juntar CSV por CNPJ

### ⬇️ Download
Download de arquivos da web

#### Web
- Download Sequencial Inteligente
- Download Multiprocessamento
- Download de Link Específico
- Navegar e Baixar Específicos

### 🛠️ Utilitários
Ferramentas auxiliares e utilitários

#### Arquivos
- Mover e Copiar Arquivos

#### Bancos
- Adicionar Nomes de Bancos

## Estrutura de Pastas

```
options/
├── dados/
│   ├── remocao/
│   │   └── remover.py
│   ├── filtragem/
│   │   └── filters.py
│   ├── adicao_mesclagem/
│   │   └── add_or_mescle.py
│   └── correlacao/
│       └── correlacao_colunas.py
├── conversao/
│   ├── formatos/
│   │   ├── converter.py
│   │   └── txt_to_csv.py
│   └── extracao/
│       ├── extrator_cnpj.py
│       └── juntar_csv_cnpj.py
├── download/
│   └── web/
│       └── web_downloader.py
├── utilitarios/
│   ├── arquivos/
│   │   └── moves_copys.py
│   └── bancos/
│       └── banco_nomes.py
├── utils.py
└── estrutura_categorias.py
```

## Navegação do Menu

1. **Nível 1**: Selecionar Categoria (ex: 📊 Dados)
2. **Nível 2**: Selecionar SubCategoria (ex: Remoção)
3. **Nível 3**: Selecionar Opção/Programa (ex: Remover Duplicatas de CPF)
4. **Execução**: O programa é executado automaticamente

## Benefícios da Nova Estrutura

✅ **Organização Clara**: Cada funcionalidade está em sua categoria lógica
✅ **Navegação Intuitiva**: Menu hierárquico facilita encontrar funcionalidades
✅ **Manutenibilidade**: Estrutura de pastas reflete a organização lógica
✅ **Escalabilidade**: Fácil adicionar novas categorias e funcionalidades
✅ **Usabilidade**: Usuários administrativos encontram funções mais facilmente

