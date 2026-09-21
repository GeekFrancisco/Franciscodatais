# Organização do Projeto Pyhton_Web

Esta estrutura organiza código, dados e relatórios de forma clara e sustentável.

## Estrutura de Pastas
- `src/` — código-fonte
  - `src/api/` — integrações (`API_*.py`)
  - `src/etl/` — consolidação e tratamento de dados (`consolidacao_planilhas.py`)
  - `src/reports/` — scripts de relatórios (`backlog_30dias_iti.py`, `backlog_2semanas_spn.py`)
  - `src/validation/` — validações (`validate_indicadores.py`)
  - `src/utils/` — utilitários comuns
- `app/` — aplicação web (conteúdo movido de `web_project/`)
- `data/` — dados
  - `data/base/` — arquivos de entrada/planilhas
  - `data/saida/` — relatórios gerados
- `archive/` — código legado e versões antigas
- Raiz: `.venv/`, `.env`, `.vscode/`, `requirements.txt`

## Como Executar
- Consolidação das planilhas:
  - `python src/etl/consolidacao_planilhas.py`
  - Saída: `data/base/consolidado.xlsx`
- Relatório ITI (Backlog > 30 dias, tab ITI):
  - `python src/reports/backlog_30dias_iti.py`
- Relatório SPN (Backlog > 2 semanas, tab SPN):
  - `python src/reports/backlog_2semanas_spn.py`
- Validação de indicadores (SPN/ITI):
  - `python src/validation/validate_indicadores.py`
  - Saída: `data/base/indicador_inconsistencias.csv`

## Notas
- Os scripts foram ajustados para ler de `data/base/`.
- Caso adicione novas planilhas (ex.: `Backlog_44.xlsx`), salve em `data/base/`.
- Recomenda-se parametrizar períodos (ex.: semanas/dias) via `argparse` futuramente.

## Aplicação Ativa (Streamlit)
- App principal: `app_refatorado.py`
  - Ícone: `data/base/IMG/Designer.jpeg`
  - Dados: `data/base/consolidado.xlsx`
  - Modo mínimo: controlado por `.env` com `MINIMAL_MODE=true|false` (quando `true`, exibe apenas o Dashboard).

### Executar o Dashboard
- `streamlit run app_refatorado.py`
- Abra `http://localhost:8501`
- Para reativar a aba de Relatórios: defina `MINIMAL_MODE=false` no `.env` e reinicie.

## Limpeza Realizada
- Arquivados: `app.py`, `app_moderno.py`, `app - Copia.py`
- O app Flask foi movido para: `archive/app_flask/`
- Removidos: `Base/` (vazia), `web_project/` (obsoleto)
- Mantidos: `data/base/` como fonte única de dados

## Próximos Passos Sugeridos
- Parametrizar caminhos via `.env` para relatórios em `src/reports/*`
- Consolidar `requirements.txt` conforme necessidades do Streamlit
- Se desejar, arquivar a pasta `Franciscodatais/` (não referenciada pelo app atual)