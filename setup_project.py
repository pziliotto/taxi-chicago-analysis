"""
Script de Configuração Automática do Projeto
Análise Geoespacial de Fluxo Urbano - Táxis Chicago

Autora: Pâmela Lima Ziliotto
Data: 17/02/2026
"""
# %%
import os
from pathlib import Path

# %%
def create_directory_structure():
    """Cria toda a estrutura do projeto"""

    # Estrutura das pastas
    directories = [
        "data/raw",
        "data/processed",
        "data/models",
        "data/external",
        "notebooks",
        "src/data",
        "src/geoprocessing",
        "src/graph",
        "src/api",
        "src/utils",
        "dashboard",
        "docker",
        "tests",
        "docs",
        "logs",
        "outputs"
    ]

    print("🚀 Criando estrutura de diretórios...\n")

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Criado: {directory}/")
    
    print("\n" + "="*60)

""" Diretórios criados com sucesso! """
# %%
def create_gitignore():
    """ Cria arquivo .gitignore """

    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Jupyter Notebook
.ipynb_checkpoints
*.ipynb_checkpoints/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Data files (não commitar dados grandes)
data/raw/*.csv
data/raw/*.parquet
data/processed/*.csv
data/processed/*.parquet
*.h5
*.hdf5

# Logs
logs/
*.log

# OS
.DS_Store
*.log
Thumbs.db

# Docker
docker-compose.override.yml

# Outputs
outputs/*.png
outputs/*.html
outputs/*.pdf

# Environment variables
.env
.env.local
"""

    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    
    print("✅ Criado: .gitignore")

""" Gitignore criado com sucesso!"""
# %%
def create_readme():
    """ Cria README.md inicial """

    readme_content = """# Análise Geoespacial de Fluxo Urbano - Táxis Chicago
    
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
venv\\Scripts\\activate

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
    
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("✅ Criado: README.md")

""" README criado com sucesso! """


# %%
def create_requirements():
    """ Cria arquivo requirements.txt com dependências principais"""

    requirements_content = """# Análise e Manipulação de Dados
pandas>=2.1.0
numpy>=1.24.0
scipy>=1.11.0

# Geoprocessamento
geopandas>=0.14.0
shapely>=2.0.0
h3>=3.7.6
folium>=0.15.0
contextily>=1.4.0

# Grafos
networkx>=3.2
igraph>=0.11.0
python-louvain>=0.16

# Banco de Dados
psycopg2-binary>=2.9.9
sqlachemy>=2.0.0
geoalchemy>=0.14.0

# API
fastap>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Dashboard
streamlit>=1.28.0
plotly>=5.18.0
pydeck>=0.8.0

# Visualização
matplotlib>=3.8.0
seaborn>=0.13.0

# Jupyter
jupyter>=1.0.0
ipykernel>=6.26.0

# Utilitários
python-detenv>=1.0.0
tqdm>=4.66.0
requests>=2.31.0

# Testes
pytest>=7.4.0
pytest-cov>=4.1.0

# Qualidade de Código
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
 
"""

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)

    print("✅ Criado: requirements.txt")

""" Requirements criado com sucesso! """

# %%
def create_docker_compose():
    """Cria docker-compose.yml para PostgreSQL + PostGIS"""
    
    docker_compose_content = """version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: chicago-taxi-db
    environment:
      POSTGRES_USER: chicago_user
      POSTGRES_PASSWORD: chicago_pass
      POSTGRES_DB: chicago_taxi
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - chicago-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  chicago-network:
    driver: bridge
"""
    
    docker_dir = Path("docker")
    with open(docker_dir / "docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose_content)
    
    print("✅ Criado: docker/docker-compose.yml")

""" Docker-Compose criado com sucesso! """

# %%
def create_env_example():
    """ Cria arquivo .env.example com variáveis de ambiente"""

    env_content = """# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chicago_taxi
DB_USER=chicago_user
DB_PASSWORD=chicago_pass

# API
API_HOST=0.0.0.0
API_PORT=8000

# Dashboard
DASHBOARD_PORT=8501

# DADOS
DATA_URL=https://data.cityofchicago.org/resources/ajtu-isnz.json
 
"""

    with open(".env.example", "w", encoding="utf=8") as f:
        f.write(env_content)

    print("✅ Criado: .env.example")

""" env_example criado com sucesso! """

# %%
def create_init_files():
    """Cria arquivos __init__.py para tornar diretórios em pacotes Python"""
    
    init_dirs = [
        "src",
        "src/data",
        "src/geoprocessing",
        "src/graph",
        "src/api",
        "src/utils",
        "tests"
    ]
    
    for directory in init_dirs:
        init_file = Path(directory) / "__init__.py"
        init_file.touch()
    
    print("✅ Criados: arquivos __init__.py")

""" Arquivos init criado com sucesso! """






# %%
def create_sample_notebook():
    """Cria notebook de exemplo para análise exploratória"""
    
    notebook_content = """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Análise Exploratória - Dados de Táxi Chicago\\n",
    "\\n",
    "**Objetivo:** Primeira exploração dos dados brutos\\n",
    "**Data:** 17/02/2026\\n",
    "**Etapa:** E2 - Ingestão de dados"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\\n",
    "import geopandas as gpd\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "\\n",
    "# Configurações\\n",
    "plt.style.use('seaborn-v0_8')\\n",
    "sns.set_palette('husl')\\n",
    "%matplotlib inline"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Carregamento dos Dados"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# TODO: Carregar dados\\n",
    "# df = pd.read_csv('../data/raw/taxi_trips_sample.csv')\\n",
    "# df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Análise Descritiva"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# TODO: Estatísticas descritivas\\n",
    "# df.describe()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Visualizações Iniciais"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# TODO: Gráficos exploratórios"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
"""
    
    with open("notebooks/01_exploratory_analysis.ipynb", "w", encoding="utf-8") as f:
        f.write(notebook_content)
    
    print("✅ Criado: notebooks/01_exploratory_analysis.ipynb")

""" Notebooks exploratórios criados com sucesso! """




# %%
def create_sample_config():
    """Cria arquivo de configuração"""
    
    config_content = """\"\"\"
Configurações Globais do Projeto
\"\"\"

from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

# Parâmetros de Geoprocessamento
H3_RESOLUTION = 9  # Resolução H3 (aproximadamente 174m de aresta)
CRS = "EPSG:4326"  # WGS84

# Parâmetros de Grafos
GRAPH_WEIGHT_COLUMN = "trip_count"
MIN_EDGE_WEIGHT = 5  # Mínimo de viagens para criar aresta

# API
API_TITLE = "Chicago Taxi Analysis API"
API_VERSION = "1.0.0"

# Dashboard
DASHBOARD_TITLE = "Análise Geoespacial - Táxis Chicago"
"""
    
    with open("src/config.py", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print("✅ Criado: src/config.py")


""" Config criado com sucesso! """

# %%

def main():
    """Função principal"""
    
    print("\n" + "="*60)
    print("🚕 SETUP - Análise Geoespacial Táxis Chicago")
    print("="*60 + "\n")
    
    # Lista de funções para executar
    funcoes = [
        ("Estrutura de diretórios", create_directory_structure),
        (".gitignore", create_gitignore),
        ("README.md", create_readme),
        ("requirements.txt", create_requirements),
        ("docker-compose.yml", create_docker_compose),
        (".env.example", create_env_example),
        ("Arquivos __init__.py", create_init_files),
        ("Notebook de exemplo", create_sample_notebook),
        ("Configuração", create_sample_config)
    ]
    
    # Executar cada função com tratamento de erro
    for nome, funcao in funcoes:
        try:
            funcao()
        except FileExistsError:
            print(f"⚠️  {nome} já existe, pulando...")
        except Exception as e:
            print(f"❌ Erro ao criar {nome}: {e}")
            print(f"   Continuando com as próximas etapas...\n")
    
    print("\n" + "="*60)
    print("✨ SETUP CONCLUÍDO COM SUCESSO!")
    print("="*60 + "\n")
    
    print("📋 PRÓXIMOS PASSOS:\n")
    print("1. Ativar ambiente virtual:")
    print("   venv\\Scripts\\activate\n")
    print("2. Instalar dependências:")
    print("   pip install -r requirements.txt\n")
    print("3. Copiar variáveis de ambiente:")
    print("   copy .env.example .env\n")
    print("4. Subir banco de dados:")
    print("   cd docker")
    print("   docker-compose up -d\n")
    print("5. Abrir notebook exploratório:")
    print("   jupyter notebook notebooks/01_exploratory_analysis.ipynb\n")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

