# Sistema de Gestão de Transferências entre Filiais & Motor Fiscal DANFE XML

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Pytest](https://img.shields.io/badge/Tests-100%25%20Passing-success?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean%20%26%20SOLID-blue?style=for-the-badge)](https://blog.cleancoder.com/)
[![Security](https://img.shields.io/badge/AppSec-Pentest%20Hardened-darkgreen?style=for-the-badge)](https://owasp.org/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel%20Serverless-black?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

> Sistema inteligente e seguro para análise multi-planilhas de estoque e demanda de vendas, balanceamento de mercadorias entre matriz e filiais, e geração instantânea de notas fiscais eletrônicas (DANFE NF-e modelo 55) em formato XML homologado pela SEFAZ.

---

## 📑 Sumário

- [1. Propósito do Projeto](#1-propósito-do-projeto)
- [2. O Problema de Negócio & Desafios](#2-o-problema-de-negócio--desafios)
- [3. Solução Elaborada (Motor de Decisão & Arquitetura)](#3-solução-elaborada-motor-de-decisão--arquitetura)
- [4. Tour do Sistema & Funcionalidades](#4-tour-do-sistema--funcionalidades)
- [5. Arquitetura de Software & Princípios de Engenharia](#5-arquitetura-de-software--princípios-de-engenharia)
- [6. Segurança Defensiva & Pentest (AppSec)](#6-segurança-defensiva--pentest-appsec)
- [7. Suíte de Testes Automatizados (TDD)](#7-suíte-de-testes-automatizados-tdd)
- [8. Como Executar Localmente](#8-como-executar-localmente)
- [9. Deploy em Produção (Vercel)](#9-deploy-em-produção-vercel)

---

## 1. Propósito do Projeto

No gerenciamento de redes de varejo e centros de distribuição, o balanceamento de inventário entre a matriz e suas lojas filiais é uma operação crítica que envolve altos custos logísticos e risco fiscal. 

O **Sistema de Transferência de Mercadorias** foi desenvolvido para:
1. **Eliminar a adivinhação e o excesso de estoque**: Cruzar automaticamente relatórios de vendas semanais com as posições de estoque de ambas as pontas.
2. **Garantir a disponibilidade contínua de mercadorias**: Proteger a filial contra rupturas de vendas mensais sem comprometer a cobertura de vendas da matriz.
3. **Automatizar a conformidade fiscal**: Transformar decisões de transferência em arquivos XML da NF-e (DANFE Modelo 55) prontos para transmissão ou importação direta no ERP da empresa.

---

## 2. O Problema de Negócio & Desafios

### O Cenário Real
- A filial vende uma determinada quantidade na semana e solicita reposição da matriz.
- Se a filial já possui saldo em prateleira suficiente para atender as próximas semanas, a transferência é desnecessária e geraria custo de frete e capital imobilizado.
- Se a matriz enviar mercadorias sem verificar seu próprio estoque versus suas vendas dos últimos 30 dias, ela mesma entrará em ruptura e não conseguirá atender sua demanda.
- Por outro lado, se a filial possui excesso de um determinado SKU e a matriz está deficitária, existe a oportunidade de **transferência reversa segura** (Filial → Matriz).

### Os Principais Desafios Enfrentados
1. **Heterogeneidade de Planilhas**: Relatórios extraídos de diferentes ERPs chegam nos formatos `.xls` (BIFF8 antigo) e `.xlsx` moderno, com estruturas de colunas distintas (colunas consolidadas ou de saldo líquido).
2. **Conformidade Fiscal Rigorosa da SEFAZ**: O XML gerado deve conter todos os grupos fiscais obrigatórios (`ide`, `emit`, `dest`, `det`, `total`, `transp`), cálculo preciso de chave de acesso de 44 dígitos com dígito verificador Módulo 11, CFOPs fiscais corretos (5152/6152), tributação de ICMS (CSOSN 400), IPI, PIS/COFINS e estimativa tributária IBPT.
3. **Ergonomia Operacional para o Usuário**: Processar 4 planilhas sem gerar fricção cognitiva, permitindo edição dinâmica de quantidade e preço unitário com recálculo instantâneo em tempo real.
4. **Segurança e Privacidade**: Nenhuma informação corporativa sensível deve ficar gravada permanentemente no servidor; a sessão do navegador deve ter controle total de descarte e proteção estrita contra injeções.

---

## 3. Solução Elaborada (Motor de Decisão & Arquitetura)

O núcleo do sistema opera sobre a **Matriz de Decisão de Estoque**:

```
Demanda Mês da Filial   = 4 × Venda Semanal da Filial
Saldo Projetado Filial  = Estoque Atual Filial - Demanda Mês da Filial
Saldo Projetado Matriz  = Estoque Atual Matriz - Vendas Últimos 30 Dias Matriz
```

### Classificação Determinística em 5 Estados de Domínio

| Cenário de Negócio | Condição Matemática | Ação do Sistema | Destino no Painel |
| :--- | :--- | :--- | :--- |
| **Transferência Normal Aprovada** | Filial em déficit e Matriz com saldo seguro suficiente | Calcula quantidade exata de reposição e libera emissão da DANFE | Aba 1 (Matriz → Filial) |
| **Matriz com Saldo Insuficiente** | Filial em déficit, mas envio comprometeria o mês da matriz | Bloqueia envio para proteger a matriz e gera alerta de compra | Aba 2 (Removidos & Alertas) |
| **Ruptura Crítica em Ambas** | Filial e Matriz operando abaixo da demanda | Remove da transferência e emite notificação urgente para compras | Aba 2 (Removidos & Alertas) |
| **Cobertura Suprida (Estáveis)** | Filial e Matriz já possuem estoque para suprir o mês | Não necessita movimentação física | Aba 2 (Removidos & Alertas) |
| **Transferência Reversa Segura** | Filial com excedente comprovado e Matriz deficitária | Calcula excedente transferível preservando 100% da filial | Aba 3 (Filial → Matriz) |

---

## 4. Tour do Sistema & Funcionalidades

### 4.1 Assistente de Importação Progressivo (Wizard 4 Etapas)
- Interface flat minimalista em modo escuro inspirada nos designs de ferramentas modernas como Notion, Linear e Apple.
- Carregamento guiado e seguro das 4 planilhas com drag-and-drop:
  1. *Relatório de Vendas da Semana (Filial)*
  2. *Relatório de Saldo de Estoque Atual (Filial)*
  3. *Relatório de Vendas dos Últimos 30 Dias (Matriz)*
  4. *Relatório de Saldo de Estoque Atual (Matriz)*
- **Recolhimento Inteligente (Foco Total nos Dados)**: Concluída a análise, o assistente se recolhe automaticamente em uma barra compacta de status (`✅ 4 relatórios carregados e analisados`), dando visibilidade prioritária às tabelas de mercadorias e aos indicadores consolidados. O usuário pode reexibir o assistente a qualquer momento com um clique.

### 4.2 Dashboard de Métricas em Tempo Real
Exibe instantaneamente:
- **Itens Aprovados** para envio.
- **Volume Total de Peças** calculadas.
- **Valor Total Financeiro** da operação.
- **Contador de Alertas de Compra** que necessitam ação do setor de suprimentos.

### 4.3 Gestão em 3 Abas Especializadas
1. **Aba 1: Transferência Matriz → Filial**
   - Tabela interativa com Checklist de conferência (persistente no navegador).
   - Botão para copiar SKU com 1 clique.
   - **Edição Inline em Tempo Real**: O operador pode ajustar quantidade e preço unitário diretamente na tabela com recálculo automático instantâneo do valor da linha e do total geral.
   - Exclusão de linhas e exportação em XML da DANFE oficial.
2. **Aba 2: Produtos Removidos & Alertas de Compra**
   - Exibe a justificativa auditável de cada exclusão.
   - **Diferenciação Visual de Estoque vs. Vendas**: Apresenta micro-cards estilizados separando categoricamente **📦 Estoque Físico** (em tom azul escuro) de **🛒 Vendas / Demanda Projetada** (em tom grafite/amarelo), eliminando qualquer confusão entre saldos e demanda.
3. **Aba 3: Transferência Inversa Opcional (Filial → Matriz)**
   - Identifica oportunidades de redistribuição de estoque ocioso da filial para a matriz.
   - Visualização e edição inline idêntica à transferência normal (edição de quantidade, preço unitário, total recalculado, checklist e exclusão).
   - Botão dedicado para baixar o XML da DANFE Inversa com emissor e destinatário invertidos de forma automática.

### 4.4 Gestão Bilateral de Empresas (Matriz & Filial) & Trava de Segurança
- **Configuração Completa das Duas Pontas**: Modal com abas independentes para a **Empresa Emitente (Matriz)** e a **Empresa Destinatária (Filial)**, eliminando qualquer dado fixo no código e tornando o sistema 100% universal para qualquer empresa.
- **Consulta Automatizada**: Consulta instantânea via **BrasilAPI / MinhaReceita** (por CNPJ) e **ViaCEP** (por CEP), preenchendo automaticamente Razão Social, Logradouro, Bairro, Município, UF e Código IBGE.
- **Trava de Segurança Fiscal (Duas Camadas)**: A emissão da DANFE XML é estritamente protegida no client-side e server-side; tentativas de download sem os cadastros completos disparam alertas instrutivos e abrem o formulário correspondente.
- **Permuta Simétrica Perfeita na Nota Reversa**: Na transferência reversa (Filial → Matriz), o sistema permuta os papéis de emitente e destinatário com 100% dos dados fiscais válidos, sem campos vazios ou inconsistências na SEFAZ.
- **Persistência Inteligente**: A Matriz permanece gravada no navegador local para conveniência nas próximas utilizações, permitindo purgar relatórios e filiais sem perder as configurações da matriz.

---

## 5. Arquitetura de Software & Princípios de Engenharia

O projeto foi construído sobre as diretrizes de **Clean Architecture** e **SOLID**, assegurando total desacoplamento e testabilidade:

```
┌─────────────────────────────────────────────────────────┐
│                 Frameworks & Web Drivers                │
│             (Flask API, Vercel Serverless)              │
│                           │                             │
│                           ▼                             │
│                 Adapters & Formatters                   │
│   (SpreadsheetParser, XLS/XLSX, NFeXmlBuilder, CEP/CNPJ)│
│                           │                             │
│                           ▼                             │
│                   Use Cases & Services                  │
│       (StockTransferAnalyzer, TaxCalculator)            │
│                           │                             │
│                           ▼                             │
│                   Enterprise Domain                     │
│    (Product, CompanyInfo, TransferReport, TransferItem) │
└─────────────────────────────────────────────────────────┘
```

### Princípios SOLID Aplicados
- **Single Responsibility Principle (SRP)**:
  - `SpreadsheetParser`: Responsável exclusivamente pela leitura e normalização de planilhas.
  - `StockTransferAnalyzer`: Responsável unicamente pela aplicação da matriz de decisão.
  - `NFeXmlBuilder`: Focado estritamente na construção estrutural da árvore XML da NF-e.
  - `TaxCalculator`: Especializado no cálculo de alíquotas tributárias e estimativas do IBPT.
- **Open/Closed Principle (OCP)**: Novos layouts de planilhas ou novos formatos de exportação podem ser adicionados sem modificar as regras de negócio centrais de domínio.
- **Liskov Substitution Principle (LSP)**: Parsers de `.xls` e `.xlsx` implementam contratos intercambiáveis garantindo comportamento idêntico.
- **Interface Segregation Principle (ISP)**: Módulos no frontend e backend consomem apenas os métodos e atributos necessários à sua finalidade.
- **Dependency Inversion Principle (DIP)**: O domínio central não possui nenhuma dependência de bibliotecas de terceiros ou frameworks web.

---

## 6. Segurança Defensiva & Pentest (AppSec)

O sistema foi submetido a baterias de pentest e modelagem de ameaças com foco nas diretrizes OWASP:

1. **Validação de Assinatura Binária (Magic Bytes)**:
   - Bloqueio preventivo de arquivos maliciosos renomeados (ex: arquivos executáveis com extensão `.xls`). Apenas assinaturas válidas de OLE2/BIFF8 (`\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1`) e ZIP/OpenXML (`PK\x03\x04`) são aceitas.
2. **Proteção contra XXE (XML External Entity)**:
   - Resolução de entidades externas e DTDs desativadas na geração e manipulação de documentos XML.
3. **Defesa contra Formula Injections**:
   - Sanitização de células e strings para impedir execução de comandos maliciosos em planilhas (`=cmd`, `@sum`, caracteres de controle `\x00-\x1f`).
4. **Isolamento de Cache & Proteção de Memória**:
   - Dados locais não expõem credenciais e possuem mecanismo de purga imediata via interface ("Limpar Sessão").
5. **Cabeçalhos HTTP Hardened & CSP**:
   - Imposição de `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection` e `Content-Security-Policy` estrita.

---

## 7. Suíte de Testes Automatizados (TDD)

O desenvolvimento seguiu rigorosamente a metodologia **TDD (Test-Driven Development)**, cobrindo cenários positivos, negativos e limites:

```bash
& "C:\Users\marco\AppData\Local\Python\bin\python.exe" -m pytest -v
```

### Resultados da Bateria de Testes
```text
core/tests/test_api.py .................. PASSED
core/tests/test_domain.py ............... PASSED
core/tests/test_nfe_builder.py .......... PASSED
core/tests/test_nfe_generator.py ........ PASSED
core/tests/test_parser.py ............... PASSED
core/tests/test_security_pentest.py ..... PASSED
core/tests/test_spreadsheet_parser.py ... PASSED
core/tests/test_stock_transfer_analyzer.py PASSED
core/tests/test_tax_calculator.py ....... PASSED
core/tests/test_validator.py ............ PASSED

============================== 40 passed in 0.77s ==============================
```

---

## 8. Como Executar Localmente

### Pré-requisitos
- Python 3.10 ou superior
- Git

### 1. Clonar o Repositório
```bash
git clone https://github.com/marc-vinn/Gerador-de-Notas-de-Transferencia.git
cd Gerador-de-Notas-de-Transferencia
```

### 2. Criar e Ativar o Ambiente Virtual (Opcional, mas recomendado)
```bash
python -m venv .venv
# No Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# No Linux/macOS:
source .venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Iniciar o Servidor
```bash
python api/index.py
```

O servidor será iniciado na porta 5000:
- **Acesso no Navegador:** `http://localhost:5000` ou `http://127.0.0.1:5000`

---

## 9. Deploy em Produção (Vercel)

A aplicação está configurada para deploy serverless via `vercel.json`:
- Rotas de API (`/api/*`) são roteadas automaticamente para a função serverless Python `api/index.py`.
- O frontend estático (`/frontend/*`) é servido via CDN de borda da Vercel.

Para realizar o deploy utilizando a Vercel CLI:
```bash
vercel --prod
```

---

## 👤 Autor

Desenvolvido por **Marco Vinn**  
Repositório Oficial: [Gerador-de-Notas-de-Transferencia](https://github.com/marc-vinn/Gerador-de-Notas-de-Transferencia)
