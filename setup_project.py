"""
Script de Configuração Automática do Projeto
Análise Geoespacial de Fluxo Urbano - Táxis Chicago

Autora: Pâmela Lima Ziliotto
Data: 17/02/2026
Atualizado: 02/06/2026
"""

import os
from pathlib import Path


def create_directory_structure():
    """Cria toda a estrutura de diretórios do projeto"""

    directories = [
        # Dados
        "data/raw",
        "data/processed",
        "data/features",
        "data/models",
        "data/external",
        # Código fonte
        "src/data",
        "src/geoprocessing",
        "src/graph",
        "src/api",
        "src/database",
        "src/utils",
        # Frontend (React)
        "frontend",
        # Notebooks
        "notebooks",
        # Infraestrutura
        "docker",
        # Outputs
        "outputs/graph",
        "outputs/quality_reports",
        # Outros
        "tests",
        "docs",
        "logs",
    ]

    print("🚀 Criando estrutura de diretórios...\n")

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Criado: {directory}/")

    print("\n" + "=" * 60)


def create_gitignore():
    """Cria arquivo .gitignore"""

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
data/raw/
data/processed/
data/features/
data/models/

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Outputs gerados
outputs/quality_reports/

# Environment variables
.env
.env.local

# Node / Frontend
frontend/node_modules/
frontend/dist/
frontend/.env

# Misc
*.h5
*.hdf5
"""

    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    print("✅ Criado: .gitignore")


def create_requirements():
    """Cria arquivo requirements.txt com dependências do projeto"""

    requirements_content = """# Análise e Manipulação de Dados
pandas>=2.1.0
numpy>=1.24.0
scipy>=1.11.0
pyarrow>=14.0.0

# Geoprocessamento
geopandas>=0.14.0
shapely>=2.0.0
h3>=3.7.6
folium>=0.15.0

# Grafos
igraph>=0.11.0

# Banco de Dados
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.0
geoalchemy2>=0.14.0

# API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Visualização
plotly>=5.18.0
matplotlib>=3.8.0

# Jupyter
jupyter>=1.0.0
ipykernel>=6.26.0

# Utilitários
python-dotenv>=1.0.0
tqdm>=4.66.0
requests>=2.31.0
holidays>=0.46

# Testes
pytest>=7.4.0
"""

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)

    print("✅ Criado: requirements.txt")


def create_docker_compose():
    """Cria docker-compose.yml para PostgreSQL + PostGIS"""

    docker_compose_content = """services:
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
    restart: unless-stopped

volumes:
  postgres_data:
"""

    docker_dir = Path("docker")
    with open(docker_dir / "docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose_content)

    print("✅ Criado: docker/docker-compose.yml")


def create_env_example():
    """Cria arquivo .env.example com variáveis de ambiente"""

    env_content = """# Socrata API (obtenha em data.cityofchicago.org)
SOCRATA_APP_TOKEN=seu_token_aqui

# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chicago_taxi
DB_USER=chicago_user
DB_PASSWORD=chicago_pass

# API
API_HOST=0.0.0.0
API_PORT=8000
"""

    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("✅ Criado: .env.example")


def create_init_files():
    """Cria arquivos __init__.py para tornar diretórios em pacotes Python"""

    init_dirs = [
        "src",
        "src/data",
        "src/geoprocessing",
        "src/graph",
        "src/api",
        "src/database",
        "src/utils",
        "tests",
    ]

    for directory in init_dirs:
        init_file = Path(directory) / "__init__.py"
        init_file.touch()

    print("✅ Criados: arquivos __init__.py")


def create_sample_config():
    """Cria arquivo de configuração global"""

    config_content = """\"\"\"
Configurações Globais do Projeto
\"\"\"

from pathlib import Path

# Diretórios
BASE_DIR           = Path(__file__).parent.parent
DATA_DIR           = BASE_DIR / "data"
RAW_DATA_DIR       = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DATA_DIR  = DATA_DIR / "features"

# Parâmetros de Geoprocessamento
H3_RESOLUTION = 9        # ~174m de aresta
CRS           = "EPSG:4326"

# Parâmetros de Grafos
MIN_EDGE_WEIGHT = 5      # Mínimo de corridas para criar aresta

# Recorte temporal
START_YEAR = 2022        # Pós-pandemia
# 2020-2021 excluídos por distorção pandêmica

# API
API_TITLE   = "Chicago Traffic Analysis API"
API_VERSION = "1.0.0"
"""

    with open("src/config.py", "w", encoding="utf-8") as f:
        f.write(config_content)

    print("✅ Criado: src/config.py")


def main():
    """Função principal"""

    print("\n" + "=" * 60)
    print("🚕 SETUP - Análise Geoespacial Táxis Chicago")
    print("=" * 60 + "\n")

    funcoes = [
        ("Estrutura de diretórios", create_directory_structure),
        (".gitignore",              create_gitignore),
        ("requirements.txt",        create_requirements),
        ("docker-compose.yml",      create_docker_compose),
        (".env.example",            create_env_example),
        ("Arquivos __init__.py",    create_init_files),
        ("Configuração",            create_sample_config),
    ]

    for nome, funcao in funcoes:
        try:
            funcao()
        except FileExistsError:
            print(f"⚠️  {nome} já existe, pulando...")
        except Exception as e:
            print(f"❌ Erro ao criar {nome}: {e}")

    print("\n" + "=" * 60)
    print("✨ SETUP CONCLUÍDO!")
    print("=" * 60 + "\n")

    print("📋 PRÓXIMOS PASSOS:\n")
    print("1. Criar e ativar ambiente virtual:")
    print("   python -m venv .venv")
    print("   .venv\\Scripts\\activate\n")
    print("2. Instalar dependências Python:")
    print("   pip install -r requirements.txt\n")
    print("3. Configurar variáveis de ambiente:")
    print("   copy .env.example .env\n")
    print("4. Subir banco de dados:")
    print("   cd docker && docker-compose up -d\n")
    print("5. Executar pipeline de dados:")
    print("   python src/data/ingest_chicago_taxi.py --mode full")
    print("   python src/data/clean_chicago_taxi.py")
    print("   python src/data/feature_engineering.py")
    print("   python src/graph/graph_analysis.py")
    print("   python src/database/database_load.py\n")
    print("6. Iniciar API:")
    print("   uvicorn src.api.api:app --reload\n")
    print("7. Instalar e iniciar frontend:")
    print("   cd frontend && npm install && npm run dev\n")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()