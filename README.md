# Análise Geoespacial de Fluxo Urbano - Táxis Chicago
    
## 📋 Descrição do Projeto
   
Plataforma de análise espaço-temporal para inferir padrões de fluxo urbano a partir de dados históricos de corridas de táxi, com objetivo de apoiar decisões estratégicas de localização de empreendimentos.

## 🎯 Objetivos

- Utilizar dados públicos de táxis como proxy de fluxo urbano
- Modelar a cidade como grafo dirigido e ponderado
- Identificar padrões espaciais e temporais de movimentação
- Fornecer insights para localização de empreendimentos

## 🏗️ Estrutura do Projeto

```
taxi-chicago-analysis/
├── data/                 # Dados brutos e processados
├── notebooks/            # Análises exploratórias (Jupyter)
├── src/                  # Código fonte
│   ├── data/            # Pipeline de dados
│   ├── geoprocessing/   # Processamento geoespacial
│   ├── graph/           # Modelagem de grafos
│   ├── api/             # Backend (FastAPI)
│   └── utils/           # Utilitários
├── dashboard/           # Frontend (Streamlit)
├── docker/              # Configurações Docker
├── tests/               # Testes unitários
└── docs/                # Documentação
```

## 🛠️ Tecnologias

- **Python 3.11+**
- **PostgreSQL + PostGIS** (banco geoespacial)
- **FastAPI** (backend)
- **Streamlit** (dashboard)
- **NetworkX / igraph** (teoria de grafos)
- **GeoPandas / H3** (geoprocessamento)

## 🚀 Como Começar

### 1. Ativar ambiente virtual

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar banco de dados

```bash
cd docker
docker-compose up -d
```

### 4. Rodar análises exploratórias

```bash
jupyter notebook notebooks/
```

## 📝 Autor

Pâmela Lima Ziliotto

## 📄 Licença

Projeto acadêmico - Uso educacional   
    
