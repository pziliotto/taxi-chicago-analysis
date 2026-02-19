"""
Configurações Globais do Projeto
"""

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
