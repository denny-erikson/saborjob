# SaborJob

O `SaborJob` e um projeto experimental que transforma um scraper de vagas em um produto com foco em triagem rapida, leitura objetiva e apoio a aplicacoes no dia a dia.

A motivacao inicial era simples: centralizar vagas de diferentes plataformas para facilitar a analise de oportunidades. Nesta versao, optei por seguir apenas com a `Solides`, de forma intencional, para manter o escopo controlado e didatico.

Mais do que "pedir codigo para IA", a proposta deste projeto foi usar IA como parceira de engenharia:

- melhorar fluxo
- revisar decisoes
- separar responsabilidades
- aplicar boas praticas
- evoluir a base com mais clareza e manutencao

O `Codex` entrou exatamente nesse papel de `pair programming`, ajudando na evolucão do produto com intencao tecnica, e nao apenas como atalho.

## O que o projeto faz

Hoje o `SaborJob`:

- coleta vagas automaticamente da Solides
- organiza os dados em um dashboard feito com `Streamlit`
- permite filtrar vagas por empresa, localizacao e tags
- le o curriculo do usuario em `PDF`
- calcula `% de aderência` entre curriculo e vagas localmente
- adiciona uma leitura complementar chamada `sabor` para ajudar na interpretacao rapida do valor da vaga
- pode atualizar o arquivo de dados automaticamente com `GitHub Actions`

Exemplo de leitura no app:

`61% aderencia · bom sabor`

## Proposta do produto

O projeto foi pensado para responder uma pergunta pratica:

`essa vaga merece minha atencao agora?`

Para isso, o sistema trabalha com duas camadas:

- `aderência`
  Metrica principal, mais racional, que estima o quanto a vaga combina com o curriculo.
- `sabor`
  Leitura mais intuitiva e rapida do potencial da vaga.

Na pratica, a ideia e reduzir o tempo gasto com vagas genericas e aumentar o foco nas oportunidades que realmente fazem sentido para o perfil.

## Aprendizado do projeto

O maior aprendizado aqui foi usar IA como parceira em preocupacoes reais de software:

- revisao de fluxo
- clareza arquitetural
- experiencia de uso
- separacao de responsabilidades
- manutenibilidade

Ao longo da evolucao, o projeto recebeu melhorias em:

- experiencia do dashboard
- fluxo de analise do curriculo
- arquitetura da base
- aplicacao de principios `SOLID`
- organizacao mais proxima de `Clean Architecture`
- automacao operacional

## Stack

O projeto foi construido com:

- `Python`
- `Streamlit`
- `Playwright`
- `PyMuPDF`
- `sentence-transformers`
- `GitHub Actions`

## Estrutura do projeto

Atualmente, o projeto esta organizado assim:

```text
.
├── app.py
├── scraper_solides.py
├── data/
├── .github/workflows/update-solides-jobs.yml
└── saborjob_app/
    ├── config.py
    ├── domain/
    │   ├── models.py
    │   └── rules.py
    ├── application/
    │   ├── ports.py
    │   └── services/
    │       ├── job_catalog.py
    │       └── resume_matching.py
    ├── infrastructure/
    │   ├── json_job_repository.py
    │   ├── local_resume_extractor.py
    │   └── sentence_transformer_encoder.py
    └── presentation/
        ├── components.py
        ├── state.py
        └── styles.py
```

### Visao das camadas

- `domain`
  Regras de negocio puras, modelos e funcoes de apoio.
- `application`
  Casos de uso e servicos que orquestram o comportamento do sistema.
- `infrastructure`
  Implementacoes concretas para arquivo JSON, leitura de PDF e embeddings locais.
- `presentation`
  Interface com `Streamlit`, componentes visuais, estilos e estado de tela.
- `app.py`
  Entry point da aplicacao. Faz a composicao das dependencias e coordena o fluxo principal.

## Requisitos de ambiente

Para rodar o projeto localmente, voce precisa de:

- `Python 3.12`
- `pip`
- `venv`
- `Chromium` do Playwright instalado

## Como preparar o ambiente

### 1. Criar a virtual environment

```bash
python3.12 -m venv .venv
```

### 2. Ativar a virtual environment

```bash
source .venv/bin/activate
```

### 3. Instalar as dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar o navegador do Playwright

```bash
playwright install chromium
```

Se voce estiver em um ambiente mais limpo e precisar de dependencias extras do sistema:

```bash
playwright install --with-deps chromium
```

## Como executar o projeto

### Rodar o scraper localmente

Modo padrao local:

- abre o navegador
- usa `slow_mo`
- salva artefatos de debug

```bash
python scraper_solides.py
```

Esse comando atualiza:

- `data/solides_jobs.json`

E, quando o modo debug estiver ativo, tambem salva:

- `data/solides-search.html`
- `data/solides-search.png`

### Rodar o scraper em modo headless

```bash
SCRAPER_HEADLESS=true SCRAPER_SAVE_DEBUG=false SCRAPER_SLOW_MO=0 python scraper_solides.py
```

### Variaveis de ambiente do scraper

- `SCRAPER_HEADLESS`
  Define se o navegador roda sem interface grafica.
- `SCRAPER_SAVE_DEBUG`
  Controla se o scraper salva os artefatos de debug.
- `SCRAPER_SLOW_MO`
  Define atraso artificial entre operacoes do Playwright.

## Como abrir o dashboard

Com o ambiente ativado:

```bash
streamlit run app.py
```

Depois disso, o app deve ficar acessivel em algo como:

- `http://localhost:8501`

## Como usar o dashboard

Dentro do app, voce pode:

- navegar pelas vagas coletadas
- buscar por titulo, empresa, local ou tag
- aplicar filtros
- paginar os resultados
- subir um curriculo em PDF
- calcular aderência localmente
- visualizar a leitura complementar de `sabor`

## Automacao com GitHub Actions

Existe uma workflow pronta em:

- `.github/workflows/update-solides-jobs.yml`

Ela faz o seguinte:

- roda manualmente com `workflow_dispatch`
- roda automaticamente por `schedule`
- instala `Playwright`
- instala o `Chromium`
- executa o scraper em modo headless
- faz commit de `data/solides_jobs.json` se houver mudanca

### Como usar no GitHub

1. subir o projeto para um repositorio
2. abrir a aba `Actions`
3. executar `Update Solides Jobs`

## Observacoes importantes

- o matching roda localmente, sem depender de API paga
- na primeira execucao do modelo de embeddings, pode haver download local do modelo
- se a pasta do projeto for movida depois da criacao da `.venv`, pode ser necessario recriar o ambiente virtual

## Possiveis evolucoes

Alguns proximos passos naturais para o projeto:

- adicionar testes unitarios para dominio e servicos
- suportar mais plataformas alem da Solides
- persistir historico de execucoes do scraper
- melhorar ainda mais o ranking com sinais adicionais
- evoluir a camada de apresentacao com mais view models e componentes

## Resumo

O `SaborJob` e um experimento de produto + engenharia com IA.

Ele junta:

- scraping
- dashboard
- UX
- branding
- IA local
- automacao
- arquitetura limpa

tudo isso em uma base enxuta, funcional e pensada para crescer com mais clareza e manutencao.
