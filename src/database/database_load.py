"""
Script de Carga no Banco de Dados - Chicago Taxi Trips
Projeto: Análise Geoespacial de Fluxo Urbano
Autor: Pâmela Lima Ziliotto
 
Carrega os dados com features (E4) e resultados de grafos (E5)
no PostgreSQL + PostGIS.
 
Tabelas criadas:
- taxi_trips       → corridas com todas as features
- node_metrics     → métricas de centralidade por hexágono H3
- communities      → comunidades detectadas pelo Leiden
- edge_list        → arestas do grafo (pares origem-destino)
"""
 
# ============================================================
# IMPORTS
# ============================================================
 
import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
 
load_dotenv()
 
# ============================================================
# CONFIGURAÇÕES
# ============================================================
 
FEATURES_DIR = Path("data/features/taxi_trips")
GRAPH_DIR    = Path("outputs/graph")
 
# Tamanho do batch para inserção no banco
BATCH_SIZE = 50_000
 
# ============================================================
# SETUP DE LOGGING
# ============================================================
 
Path("logs").mkdir(exist_ok=True)
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/database_load.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)
 
# ============================================================
# CONEXÃO
# ============================================================
 
def get_engine():
    """
    Cria engine SQLAlchemy a partir das variáveis do .env.
    A engine gerencia o pool de conexões automaticamente.
    """
    host     = os.getenv("DB_HOST",     "localhost")
    port     = os.getenv("DB_PORT",     "5432")
    name     = os.getenv("DB_NAME",     "chicago_taxi")
    user     = os.getenv("DB_USER",     "chicago_user")
    password = os.getenv("DB_PASSWORD", "chicago_pass")
 
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    engine = create_engine(url, echo=False)
    log.info(f"Conectado em: {host}:{port}/{name}")
    return engine
 
 
def test_connection(engine) -> bool:
    """Testa se a conexão com o banco está funcionando."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("✅ Conexão com o banco OK")
        return True
    except Exception as e:
        log.error(f"❌ Erro na conexão: {e}")
        return False
 
# ============================================================
# CRIAÇÃO DAS TABELAS
# ============================================================
 
def create_tables(engine) -> None:
    """
    Cria as tabelas no PostgreSQL se não existirem.
    Usa IF NOT EXISTS para ser idempotente — pode rodar várias vezes sem erro.
    PostGIS é habilitado para suporte a tipos geográficos.
    """
    log.info("Criando tabelas...")
 
    sql = """
    -- Habilita extensão PostGIS
    CREATE EXTENSION IF NOT EXISTS postgis;
 
    -- Tabela principal de corridas
    CREATE TABLE IF NOT EXISTS taxi_trips (
        trip_id                     TEXT PRIMARY KEY,
        taxi_id                     TEXT,
        trip_start_timestamp        TIMESTAMP,
        trip_end_timestamp          TIMESTAMP,
        trip_seconds                FLOAT,
        trip_miles                  FLOAT,
        fare                        FLOAT,
        tips                        FLOAT,
        tolls                       FLOAT,
        extras                      FLOAT,
        trip_total                  FLOAT,
        payment_type                TEXT,
        company                     TEXT,
        pickup_community_area       FLOAT,
        dropoff_community_area      FLOAT,
        pickup_centroid_latitude    FLOAT,
        pickup_centroid_longitude   FLOAT,
        dropoff_centroid_latitude   FLOAT,
        dropoff_centroid_longitude  FLOAT,
        pickup_census_tract         TEXT,
        dropoff_census_tract        TEXT,
        -- Features temporais
        hour                        INTEGER,
        day_of_week                 INTEGER,
        month                       INTEGER,
        is_weekend                  INTEGER,
        is_rush_hour                INTEGER,
        season                      TEXT,
        is_holiday                  INTEGER,
        -- Features derivadas
        speed_mph                   FLOAT,
        fare_per_mile               FLOAT,
        tip_percentage              FLOAT,
        total_amount                FLOAT,
        -- Features espaciais
        pickup_h3                   TEXT,
        dropoff_h3                  TEXT,
        h3_distance                 FLOAT,
        neighborhood                TEXT
    );
 
    -- Índices para queries frequentes
    CREATE INDEX IF NOT EXISTS idx_trips_pickup_h3
        ON taxi_trips (pickup_h3);
    CREATE INDEX IF NOT EXISTS idx_trips_dropoff_h3
        ON taxi_trips (dropoff_h3);
    CREATE INDEX IF NOT EXISTS idx_trips_start_timestamp
        ON taxi_trips (trip_start_timestamp);
    CREATE INDEX IF NOT EXISTS idx_trips_neighborhood
        ON taxi_trips (neighborhood);
    CREATE INDEX IF NOT EXISTS idx_trips_hour
        ON taxi_trips (hour);
    CREATE INDEX IF NOT EXISTS idx_trips_is_rush_hour
        ON taxi_trips (is_rush_hour);
 
    -- Tabela de métricas de nós do grafo
    CREATE TABLE IF NOT EXISTS node_metrics (
        h3_cell          TEXT PRIMARY KEY,
        in_strength      FLOAT,
        out_strength     FLOAT,
        total_flow       FLOAT,
        pagerank         FLOAT,
        betweenness      FLOAT,
        betweenness_norm FLOAT,
        rank             INTEGER
    );
 
    -- Tabela de comunidades
    CREATE TABLE IF NOT EXISTS communities (
        h3_cell         TEXT PRIMARY KEY,
        community       INTEGER,
        community_size  INTEGER
    );
 
    -- Tabela de arestas do grafo
    CREATE TABLE IF NOT EXISTS edge_list (
        pickup_h3   TEXT,
        dropoff_h3  TEXT,
        weight      INTEGER,
        PRIMARY KEY (pickup_h3, dropoff_h3)
    );
 
    CREATE INDEX IF NOT EXISTS idx_edges_pickup
        ON edge_list (pickup_h3);
    CREATE INDEX IF NOT EXISTS idx_edges_dropoff
        ON edge_list (dropoff_h3);
    """
 
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
 
    log.info("✅ Tabelas criadas com sucesso")
 
 
# ============================================================
# CARGA DOS DADOS
# ============================================================
 
def load_taxi_trips(engine) -> None:
    """
    Carrega todos os arquivos Parquet de data/features/ na tabela taxi_trips.
    Usa inserção em batches de BATCH_SIZE linhas para não explodir a memória.
    O IF EXISTS no SELECT verifica se o trip_id já foi inserido — evita duplicatas
    em caso de reexecução parcial.
    """
    files = sorted(FEATURES_DIR.rglob("*.parquet"))
    log.info(f"\n📂 Carregando taxi_trips — {len(files)} arquivos...")
 
    # Colunas que existem na tabela (descarta colunas extras do Parquet)
    keep_cols = [
        "trip_id", "taxi_id", "trip_start_timestamp", "trip_end_timestamp",
        "trip_seconds", "trip_miles", "fare", "tips", "tolls", "extras",
        "trip_total", "payment_type", "company",
        "pickup_community_area", "dropoff_community_area",
        "pickup_centroid_latitude", "pickup_centroid_longitude",
        "dropoff_centroid_latitude", "dropoff_centroid_longitude",
        "pickup_census_tract", "dropoff_census_tract",
        "hour", "day_of_week", "month", "is_weekend", "is_rush_hour",
        "season", "is_holiday",
        "speed_mph", "fare_per_mile", "tip_percentage", "total_amount",
        "pickup_h3", "dropoff_h3", "h3_distance", "neighborhood"
    ]
 
    total_inserted = 0
 
    for f in files:
        relative = f.relative_to(FEATURES_DIR)
        log.info(f"  Processando {relative}...")
 
        df = pd.read_parquet(f)
 
        # Mantém só colunas que existem tanto no Parquet quanto na tabela
        cols_present = [c for c in keep_cols if c in df.columns]
        df = df[cols_present]
 
        # Remove linhas sem trip_id (chave primária)
        df = df.dropna(subset=["trip_id"])
        df = df.drop_duplicates(subset=["trip_id"])
 
        # Insere em batches
        for start in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[start : start + BATCH_SIZE]
            batch.to_sql(
                "taxi_trips",
                engine,
                if_exists="append",
                index=False,
                method="multi"
            )
            total_inserted += len(batch)
 
        log.info(f"    ✅ {len(df):,} registros inseridos")
 
    log.info(f"  Total taxi_trips inseridos: {total_inserted:,}")
 
 
def load_graph_data(engine) -> None:
    """
    Carrega os resultados da análise de grafos (E5) no banco.
    Tabelas: node_metrics, communities, edge_list.
    Usa if_exists='replace' porque são tabelas pequenas e
    é mais simples recriar do que fazer upsert.
    """
    log.info("\n📂 Carregando dados do grafo...")
 
    # Node metrics
    metrics_path = GRAPH_DIR / "node_metrics.csv"
    if metrics_path.exists():
        df = pd.read_csv(metrics_path)
        df.to_sql("node_metrics", engine, if_exists="replace", index=False)
        log.info(f"  ✅ node_metrics: {len(df):,} nós")
    else:
        log.warning(f"  ⚠️  {metrics_path} não encontrado")
 
    # Communities
    comm_path = GRAPH_DIR / "communities.csv"
    if comm_path.exists():
        df = pd.read_csv(comm_path)
        df.to_sql("communities", engine, if_exists="replace", index=False)
        log.info(f"  ✅ communities: {len(df):,} hexágonos")
    else:
        log.warning(f"  ⚠️  {comm_path} não encontrado")
 
    # Edge list
    edge_path = GRAPH_DIR / "edge_list.csv"
    if edge_path.exists():
        df = pd.read_csv(edge_path)
        df.to_sql("edge_list", engine, if_exists="replace", index=False)
        log.info(f"  ✅ edge_list: {len(df):,} arestas")
    else:
        log.warning(f"  ⚠️  {edge_path} não encontrado")
 
 
# ============================================================
# VERIFICAÇÃO PÓS-CARGA
# ============================================================
 
def verify_load(engine) -> None:
    """
    Faz queries simples para confirmar que os dados foram carregados corretamente.
    """
    log.info("\n🔍 Verificando carga...")
 
    queries = {
        "taxi_trips":   "SELECT COUNT(*) FROM taxi_trips",
        "node_metrics": "SELECT COUNT(*) FROM node_metrics",
        "communities":  "SELECT COUNT(*) FROM communities",
        "edge_list":    "SELECT COUNT(*) FROM edge_list",
    }
 
    with engine.connect() as conn:
        for table, query in queries.items():
            count = conn.execute(text(query)).scalar()
            log.info(f"  {table}: {count:,} registros")
 
        # Query de validação — top 5 bairros por volume
        log.info("\n  Top 5 bairros por corridas:")
        result = conn.execute(text("""
            SELECT neighborhood, COUNT(*) as trips
            FROM taxi_trips
            WHERE neighborhood IS NOT NULL
            GROUP BY neighborhood
            ORDER BY trips DESC
            LIMIT 5
        """))
        for row in result:
            log.info(f"    {row[0]}: {row[1]:,} corridas")
 
        # Ticket médio por bairro (top 5)
        log.info("\n  Top 5 bairros por ticket médio:")
        result = conn.execute(text("""
            SELECT neighborhood, ROUND(AVG(total_amount)::numeric, 2) as avg_ticket
            FROM taxi_trips
            WHERE neighborhood IS NOT NULL AND total_amount > 0
            GROUP BY neighborhood
            ORDER BY avg_ticket DESC
            LIMIT 5
        """))
        for row in result:
            log.info(f"    {row[0]}: ${row[1]}")
 
 
# ============================================================
# PIPELINE PRINCIPAL
# ============================================================
 
def run_database_load(skip_trips: bool = False) -> None:
    """
    Pipeline completo de carga no banco de dados.
 
    Args:
        skip_trips: Se True, pula a carga de taxi_trips (útil para recarregar
                    só os dados de grafo sem reprocessar 17M de registros).
    """
    log.info("=" * 60)
    log.info("🗄️  INICIANDO CARGA NO BANCO - CHICAGO TAXI TRIPS")
    log.info(f"Features: {FEATURES_DIR.resolve()}")
    log.info(f"Grafos:   {GRAPH_DIR.resolve()}")
    log.info("=" * 60)
 
    engine = get_engine()
 
    if not test_connection(engine):
        log.error("Abortando — não foi possível conectar ao banco.")
        return
 
    create_tables(engine)
 
    if not skip_trips:
        load_taxi_trips(engine)
    else:
        log.info("⏭️  Carga de taxi_trips pulada (--skip-trips)")
 
    load_graph_data(engine)
    verify_load(engine)
 
    log.info("\n✅ Carga concluída!")
 
 
# ============================================================
# EXECUÇÃO DIRETA
# ============================================================
 
if __name__ == "__main__":
    import argparse
 
    parser = argparse.ArgumentParser(
        description="Carga no banco de dados - Chicago Taxi Trips"
    )
    parser.add_argument(
        "--skip-trips",
        action="store_true",
        help="Pula a carga de taxi_trips — útil para recarregar só dados de grafo"
    )
 
    args = parser.parse_args()
    run_database_load(skip_trips=args.skip_trips)