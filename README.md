# Chicago Traffic Analysis System (CTAS)

Plataforma de análise espaço-temporal de fluxo urbano desenvolvida como projeto supervisionado de Ciência de Dados no INFNET (2026).

Utiliza dados históricos de corridas de táxi da cidade de Chicago como proxy de fluxo urbano, aplicando geoprocessamento H3, teoria de grafos e visualização interativa para apoiar decisões de localização comercial.

---

## Resultados

| Métrica | Valor |
|---|---|
| Registros ingeridos | 23.8M corridas |
| Registros após limpeza | 17.5M corridas |
| Período coberto | Janeiro/2022 — Fevereiro/2026 |
| Hexágonos H3 com fluxo | 414 (resolução 9, ~174m) |
| Arestas no grafo | 12.058 pares O-D |
| Comunidades detectadas | 2 (Leiden, modularidade 0.49) |
| Bairros cobertos | 77 Community Areas |

---

## Arquitetura

```
Chicago Data Portal (Socrata API)
        ↓
  E2 — Ingestão (Parquet, particionado por year/month)
        ↓
  E3 — Limpeza (bbox, outliers, timestamps)
        ↓
  E4 — Feature Engineering (H3, temporais, derivadas)
        ↓
  E5 — Análise de Grafos (igraph, Leiden, PageRank)
        ↓
  E6 — Banco de Dados (PostgreSQL + PostGIS via Docker)
        ↓
  E7 — API REST (FastAPI)
        ↓
  E8 — Frontend (React + Vite)
```

---

## Stack Tecnológica

**Backend & Dados**
- Python 3.11
- pandas, numpy, pyarrow
- h3, igraph, holidays
- SQLAlchemy, psycopg2
- FastAPI, uvicorn
- PostgreSQL 15 + PostGIS 3.3 (Docker)

**Frontend**
- React 18 + Vite
- Framer Motion
- Recharts
- Axios
- Tailwind CSS

**Infraestrutura**
- Docker (banco de dados)
- Git / GitHub

---

## Pré-requisitos

- Python 3.11+
- Node.js 18+ e npm
- Docker Desktop
- Git

---

## Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/pziliotto/taxi-chicago-analysis.git
cd taxi-chicago-analysis
```

### 2. Configure o ambiente Python

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env`:

```env
# API Socrata (obtenha em data.cityofchicago.org)
SOCRATA_APP_TOKEN=seu_token_aqui

# Banco de dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chicago_taxi
DB_USER=chicago_user
DB_PASSWORD=chicago_pass
```

### 4. Suba o banco de dados

```bash
cd docker
docker-compose up -d
cd ..
```

Verifique se o container está rodando:

```bash
docker ps
```

### 5. Execute o pipeline de dados

> ⚠️ O pipeline completo pode levar várias horas dependendo da conexão e do hardware.

```bash
# Ingestão de dados (2022–presente)
python src/data/ingest_chicago_taxi.py --mode full

# Limpeza
python src/data/clean_chicago_taxi.py

# Feature Engineering
python src/data/feature_engineering.py

# Análise de Grafos
python src/graph/graph_analysis.py

# Carga no banco
python src/database/database_load.py
```

Para testar com um único mês antes de rodar tudo:

```bash
python src/data/ingest_chicago_taxi.py --mode month --year 2024 --month 1
python src/data/clean_chicago_taxi.py --file year=2024/month=01/data.parquet
python src/data/feature_engineering.py --file year=2024/month=01/data.parquet
```

### 6. Inicie a API

```bash
uvicorn src.api.api:app --reload
```

A API estará disponível em `http://localhost:8000`.
Documentação interativa: `http://localhost:8000/docs`

### 7. Inicie o Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

O dashboard estará disponível em `http://localhost:5173`.

---

## Estrutura do Projeto

```
taxi-chicago-analysis/
├── data/
│   ├── raw/              ← dados brutos (Parquet, ignorado pelo Git)
│   ├── processed/        ← dados limpos (Parquet, ignorado pelo Git)
│   └── features/         ← dados com features (Parquet, ignorado pelo Git)
├── docker/
│   └── docker-compose.yml
├── frontend/             ← aplicação React
│   ├── src/
│   │   ├── components/   ← LandingPage, Dashboard, LoadingSequence, FlowSystem
│   │   ├── hooks/        ← useAPI.js
│   │   └── chicago_hexagons.json
│   └── package.json
├── notebooks/            ← análises exploratórias e visualizações
├── outputs/
│   ├── graph/            ← resultados da análise de grafos
│   └── quality_reports/  ← relatórios de qualidade da limpeza
├── src/
│   ├── api/              ← api.py (FastAPI)
│   ├── data/             ← ingest, clean, feature_engineering
│   ├── database/         ← database_load.py
│   └── graph/            ← graph_analysis.py
├── logs/                 ← logs de execução (ignorado pelo Git)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Health check |
| GET | `/stats/summary` | Resumo geral do dataset |
| GET | `/neighborhoods` | Lista de bairros com métricas |
| GET | `/neighborhoods/{name}` | Detalhes de um bairro |
| GET | `/flow/hourly` | Fluxo por hora do dia |
| GET | `/flow/weekly` | Fluxo por dia da semana |
| GET | `/flow/seasonal` | Fluxo por estação do ano |
| GET | `/flow/rush` | Rush hour vs fora de pico |
| GET | `/hexagons/top` | Top hexágonos por métrica |
| GET | `/hexagons/{h3_cell}` | Métricas de um hexágono |
| GET | `/graph/communities` | Comunidades do grafo |
| GET | `/graph/edges` | Arestas do grafo |

---

## Fontes de Dados

- **Chicago Data Portal** — Taxi Trips (2013–2023): `wrvz-psew`
- **Chicago Data Portal** — Taxi Trips (2024–presente): `ajtu-isnz`
- Acesso via API Socrata com paginação de 50.000 registros por request

---

## Decisões Técnicas Relevantes

- **Chicago em vez de NYC** — NYC removeu coordenadas geográficas precisas em 2013, tornando análise H3 inviável
- **Socrata API em vez de download direto** — o portal trava com exports grandes
- **Parquet + Snappy** — redução de ~70% no tamanho em relação a CSV
- **H3 resolução 9** — ~174m de aresta, equilíbrio entre granularidade e performance
- **igraph em vez de python-louvain** — compatibilidade com Windows
- **React em vez de Streamlit** — maior expressividade visual e adequação para portfólio
- **2022–presente** — exclui distorções da pandemia (2020–2021) e era pré-Uber/Lyft

---

## Autora

**Pâmela Lima Ziliotto**
Ciência de Dados — INFNET, 2026
Supervisor: Diego da Silva Rodrigues