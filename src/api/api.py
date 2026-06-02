"""
API REST - Chicago Taxi Trips
Projeto: Análise Geoespacial de Fluxo Urbano
Autor: Pâmela Lima Ziliotto
 
API FastAPI que expõe os dados do banco PostgreSQL para o dashboard (E8).
 
Endpoints:
- GET /                          → health check
- GET /neighborhoods             → lista de bairros disponíveis
- GET /neighborhoods/{name}      → métricas de um bairro específico
- GET /flow/hourly               → volume de corridas por hora do dia
- GET /flow/weekly               → volume por dia da semana
- GET /flow/seasonal             → volume por estação do ano
- GET /flow/rush                 → comparação rush hour vs fora de pico
- GET /hexagons/top              → top hexágonos por fluxo
- GET /hexagons/{h3_cell}        → métricas de um hexágono específico
- GET /graph/communities         → comunidades do grafo
- GET /graph/edges               → arestas do grafo (limitado)
- GET /stats/summary             → resumo geral do dataset
"""

# ============================================================
# IMPORTS
# ============================================================
 
import os
import logging
from typing import Optional
from dotenv import load_dotenv
 
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
 
load_dotenv()
 
# ============================================================
# CONFIGURAÇÕES
# ============================================================
 
Path_logs = "logs"
os.makedirs(Path_logs, exist_ok=True)
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{Path_logs}/api.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)
 
# ============================================================
# BANCO DE DADOS
# ============================================================
 
def get_engine():
    host     = os.getenv("DB_HOST",     "localhost")
    port     = os.getenv("DB_PORT",     "5432")
    name     = os.getenv("DB_NAME",     "chicago_taxi")
    user     = os.getenv("DB_USER",     "chicago_user")
    password = os.getenv("DB_PASSWORD", "chicago_pass")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url, echo=False, pool_pre_ping=True)
 
engine = get_engine()
 
def query_df(sql: str, params: dict = {}):
    """Executa uma query e retorna lista de dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        cols = result.keys()
        return [dict(zip(cols, row)) for row in result]
 
# ============================================================
# APLICAÇÃO
# ============================================================
 
app = FastAPI(
    title="Chicago Taxi Flow API",
    description="API de análise geoespacial de fluxo urbano via dados de táxi",
    version="1.0.0"
)
 
# CORS — permite que o Streamlit (E8) acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ============================================================
# HEALTH CHECK
# ============================================================
 
@app.get("/", tags=["Health"])
def root():
    """Health check — confirma que a API está rodando."""
    return {"status": "ok", "message": "Chicago Taxi Flow API rodando!"}
 
@app.get("/health", tags=["Health"])
def health():
    """Verifica conexão com o banco."""
    try:
        result = query_df("SELECT COUNT(*) as total FROM taxi_trips")
        return {"status": "ok", "total_trips": result[0]["total"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
# ============================================================
# RESUMO GERAL
# ============================================================
 
@app.get("/stats/summary", tags=["Stats"])
def get_summary():
    """
    Retorna resumo geral do dataset:
    total de corridas, período coberto, bairros, hexágonos.
    """
    sql = """
        SELECT
            COUNT(*)                                    AS total_trips,
            MIN(trip_start_timestamp)                   AS period_start,
            MAX(trip_start_timestamp)                   AS period_end,
            COUNT(DISTINCT neighborhood)                AS total_neighborhoods,
            COUNT(DISTINCT pickup_h3)                   AS total_h3_cells,
            ROUND(AVG(total_amount)::numeric, 2)        AS avg_ticket,
            ROUND(AVG(trip_miles)::numeric, 2)          AS avg_miles,
            ROUND(AVG(trip_seconds / 60.0)::numeric, 2) AS avg_duration_min
        FROM taxi_trips
    """
    result = query_df(sql)
    return result[0]
 
# ============================================================
# BAIRROS
# ============================================================
 
@app.get("/neighborhoods", tags=["Neighborhoods"])
def list_neighborhoods():
    """Lista todos os bairros com contagem de corridas e ticket médio."""
    sql = """
        SELECT
            neighborhood,
            COUNT(*)                                    AS total_trips,
            ROUND(AVG(total_amount)::numeric, 2)        AS avg_ticket,
            ROUND(AVG(trip_miles)::numeric, 2)          AS avg_miles,
            ROUND(AVG(speed_mph)::numeric, 2)           AS avg_speed_mph,
            ROUND(AVG(tip_percentage)::numeric, 2)      AS avg_tip_pct
        FROM taxi_trips
        WHERE neighborhood IS NOT NULL
        GROUP BY neighborhood
        ORDER BY total_trips DESC
    """
    return query_df(sql)
 
 
@app.get("/neighborhoods/{name}", tags=["Neighborhoods"])
def get_neighborhood(name: str):
    """
    Retorna métricas detalhadas de um bairro específico,
    incluindo distribuição por hora e por dia da semana.
    """
    # Métricas gerais
    sql_general = """
        SELECT
            neighborhood,
            COUNT(*)                                            AS total_trips,
            ROUND(AVG(total_amount)::numeric, 2)                AS avg_ticket,
            ROUND(AVG(trip_miles)::numeric, 2)                  AS avg_miles,
            ROUND(AVG(trip_seconds / 60.0)::numeric, 2)         AS avg_duration_min,
            ROUND(AVG(speed_mph)::numeric, 2)                   AS avg_speed_mph,
            ROUND(AVG(tip_percentage)::numeric, 2)              AS avg_tip_pct,
            SUM(CASE WHEN is_weekend = 1 THEN 1 ELSE 0 END)     AS weekend_trips,
            SUM(CASE WHEN is_rush_hour = 1 THEN 1 ELSE 0 END)   AS rush_trips
        FROM taxi_trips
        WHERE neighborhood = :name
        GROUP BY neighborhood
    """
    general = query_df(sql_general, {"name": name})
    if not general:
        raise HTTPException(status_code=404, detail=f"Bairro '{name}' não encontrado")
 
    # Distribuição por hora
    sql_hourly = """
        SELECT hour, COUNT(*) AS trips
        FROM taxi_trips
        WHERE neighborhood = :name
        GROUP BY hour
        ORDER BY hour
    """
    hourly = query_df(sql_hourly, {"name": name})
 
    # Distribuição por dia da semana
    sql_weekly = """
        SELECT day_of_week, COUNT(*) AS trips
        FROM taxi_trips
        WHERE neighborhood = :name
        GROUP BY day_of_week
        ORDER BY day_of_week
    """
    weekly = query_df(sql_weekly, {"name": name})
 
    return {
        "general":  general[0],
        "hourly":   hourly,
        "weekly":   weekly,
    }
 
# ============================================================
# FLUXO TEMPORAL
# ============================================================
 
@app.get("/flow/hourly", tags=["Flow"])
def flow_hourly(
    neighborhood: Optional[str] = Query(None, description="Filtrar por bairro"),
    season: Optional[str]       = Query(None, description="Filtrar por estação (Winter/Spring/Summer/Fall)"),
):
    """Volume de corridas por hora do dia. Aceita filtros opcionais."""
    where = "WHERE 1=1"
    params = {}
    if neighborhood:
        where += " AND neighborhood = :neighborhood"
        params["neighborhood"] = neighborhood
    if season:
        where += " AND season = :season"
        params["season"] = season
 
    sql = f"""
        SELECT hour, COUNT(*) AS trips
        FROM taxi_trips
        {where}
        GROUP BY hour
        ORDER BY hour
    """
    return query_df(sql, params)
 
 
@app.get("/flow/weekly", tags=["Flow"])
def flow_weekly(
    neighborhood: Optional[str] = Query(None),
):
    """Volume de corridas por dia da semana (0=Segunda, 6=Domingo)."""
    where = "WHERE 1=1"
    params = {}
    if neighborhood:
        where += " AND neighborhood = :neighborhood"
        params["neighborhood"] = neighborhood
 
    sql = f"""
        SELECT day_of_week, COUNT(*) AS trips
        FROM taxi_trips
        {where}
        GROUP BY day_of_week
        ORDER BY day_of_week
    """
    return query_df(sql, params)
 
 
@app.get("/flow/seasonal", tags=["Flow"])
def flow_seasonal():
    """Volume de corridas por estação do ano."""
    sql = """
        SELECT season, COUNT(*)                     AS trips,
               ROUND(AVG(total_amount)::numeric, 2) AS avg_ticket
        FROM taxi_trips
        WHERE season IS NOT NULL
        GROUP BY season
        ORDER BY trips DESC
    """
    return query_df(sql)
 
 
@app.get("/flow/rush", tags=["Flow"])
def flow_rush():
    """Comparação de volume e ticket médio em rush hour vs fora de pico."""
    sql = """
        SELECT
            is_rush_hour,
            COUNT(*) AS trips,
            ROUND(AVG(total_amount)::numeric, 2) AS avg_ticket,
            ROUND(AVG(trip_miles)::numeric, 2)   AS avg_miles
        FROM taxi_trips
        GROUP BY is_rush_hour
        ORDER BY is_rush_hour
    """
    return query_df(sql)
 
# ============================================================
# HEXÁGONOS H3
# ============================================================
 
@app.get("/hexagons/top", tags=["Hexagons"])
def top_hexagons(
    limit: int = Query(20, ge=1, le=100, description="Número de hexágonos a retornar"),
    metric: str = Query("total_flow", description="Métrica de ordenação: total_flow, pagerank, betweenness_norm")
):
    """
    Retorna os hexágonos com maior fluxo, cruzando métricas de grafo
    com dados de bairro e ticket médio.
    """
    allowed_metrics = ["total_flow", "pagerank", "betweenness_norm", "in_strength", "out_strength"]
    if metric not in allowed_metrics:
        raise HTTPException(status_code=400, detail=f"Métrica inválida. Use: {allowed_metrics}")
 
    sql = f"""
        SELECT
            n.h3_cell,
            n.total_flow,
            n.in_strength,
            n.out_strength,
            n.pagerank,
            n.betweenness_norm,
            n.rank,
            c.community,
            t.neighborhood,
            t.avg_ticket,
            t.avg_miles
        FROM node_metrics n
        LEFT JOIN communities c ON n.h3_cell = c.h3_cell
        LEFT JOIN (
            SELECT pickup_h3,
                   MODE() WITHIN GROUP (ORDER BY neighborhood) AS neighborhood,
                   ROUND(AVG(total_amount)::numeric, 2)        AS avg_ticket,
                   ROUND(AVG(trip_miles)::numeric, 2)          AS avg_miles
            FROM taxi_trips
            WHERE pickup_h3 IS NOT NULL
            GROUP BY pickup_h3
        ) t ON n.h3_cell = t.pickup_h3
        ORDER BY n.{metric} DESC
        LIMIT :limit
    """
    return query_df(sql, {"limit": limit})
 
 
@app.get("/hexagons/{h3_cell}", tags=["Hexagons"])
def get_hexagon(h3_cell: str):
    """Retorna métricas completas de um hexágono H3 específico."""
    sql_metrics = """
        SELECT n.*, c.community, c.community_size
        FROM node_metrics n
        LEFT JOIN communities c ON n.h3_cell = c.h3_cell
        WHERE n.h3_cell = :h3_cell
    """
    metrics = query_df(sql_metrics, {"h3_cell": h3_cell})
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Hexágono '{h3_cell}' não encontrado")
 
    # Corridas originadas nesse hexágono
    sql_trips = """
        SELECT
            COUNT(*)                                    AS total_trips,
            ROUND(AVG(total_amount)::numeric, 2)        AS avg_ticket,
            ROUND(AVG(trip_miles)::numeric, 2)          AS avg_miles,
            ROUND(AVG(speed_mph)::numeric, 2)           AS avg_speed,
            MODE() WITHIN GROUP (ORDER BY neighborhood) AS neighborhood
        FROM taxi_trips
        WHERE pickup_h3 = :h3_cell
    """
    trips = query_df(sql_trips, {"h3_cell": h3_cell})
 
    return {
        "metrics": metrics[0],
        "trips":   trips[0] if trips else {}
    }
 
# ============================================================
# GRAFO
# ============================================================
 
@app.get("/graph/communities", tags=["Graph"])
def get_communities():
    """Retorna comunidades detectadas com métricas agregadas."""
    sql = """
        SELECT
            c.community,
            COUNT(*)                                AS hexagon_count,
            SUM(n.total_flow)                       AS total_flow,
            ROUND(AVG(n.pagerank)::numeric, 6)      AS avg_pagerank
        FROM communities c
        JOIN node_metrics n ON c.h3_cell = n.h3_cell
        GROUP BY c.community
        ORDER BY total_flow DESC
    """
    return query_df(sql)
 
 
@app.get("/graph/edges", tags=["Graph"])
def get_edges(
    min_weight: int = Query(100, description="Peso mínimo da aresta"),
    limit: int      = Query(500, ge=1, le=5000)
):
    """
    Retorna arestas do grafo com peso acima do mínimo.
    Limitado para não sobrecarregar o frontend.
    """
    sql = """
        SELECT pickup_h3, dropoff_h3, weight
        FROM edge_list
        WHERE weight >= :min_weight
        ORDER BY weight DESC
        LIMIT :limit
    """
    return query_df(sql, {"min_weight": min_weight, "limit": limit})