"""
Script de Análise de Grafos - Chicago Taxi Trips
Projeto: Análise Geoespacial de Fluxo Urbano
Autor: Pâmela Lima Ziliotto
Data: 23/04/2026

Constrói grafo de fluxo urbano a partir dos dados com features (E4).
Nós = hexágonos H3 | Arestas = corridas entre hexágonos | Peso = volume de corridas
Calcula métricas de centralidade e detecta comunidades.

Output: outputs/graph/
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import logging
import pandas as pd
import numpy as np
import igraph as ig
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

FEATURES_DIR = Path("data/features/taxi_trips")
OUTPUT_DIR   = Path("outputs/graph")

# Mínimo de corridas entre dois hexágonos para criar uma aresta
# Filtra ruído — pares com 1 ou 2 corridas no período todo são irrelevantes
MIN_EDGE_WEIGHT = 5

# ============================================================
# SETUP DE LOGGING
# ============================================================

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/graph_analysis.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

def load_all_features() -> pd.DataFrame:
    """
    Carrega todos os arquivos Parquet de data/features/ e retorna
    um DataFrame consolidado com apenas as colunas necessárias para o grafo.

    Carregamos só pickup_h3, dropoff_h3 e neighborhood para economizar memória —
    não precisamos de todas as 38 colunas para construir o grafo.
    """
    files = sorted(FEATURES_DIR.rglob("*.parquet"))
    log.info(f"Arquivos encontrados: {len(files)}")

    cols = ["pickup_h3", "dropoff_h3", "neighborhood",
            "hour", "is_weekend", "is_rush_hour", "season"]

    chunks = []
    for f in files:
        df = pd.read_parquet(f, columns=cols)
        chunks.append(df)

    df_all = pd.concat(chunks, ignore_index=True)
    log.info(f"Total de corridas carregadas: {len(df_all):,}")
    return df_all


# ============================================================
# CONSTRUÇÃO DO GRAFO
# ============================================================

def build_edge_list(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega as corridas por par (pickup_h3, dropoff_h3) para criar a lista de arestas.

    Cada linha do resultado representa uma aresta do grafo:
    - source: hexágono de origem
    - target: hexágono de destino
    - weight: número de corridas entre esse par

    Remove pares com menos de MIN_EDGE_WEIGHT corridas (ruído).
    Remove corridas onde origem == destino (corridas dentro do mesmo hexágono).
    """
    log.info("Construindo lista de arestas...")

    # Remove nulos
    df = df.dropna(subset=["pickup_h3", "dropoff_h3"])

    # Remove corridas intra-hexágono
    df = df[df["pickup_h3"] != df["dropoff_h3"]]

    # Agrega por par origem-destino
    edges = (
        df.groupby(["pickup_h3", "dropoff_h3"])
        .size()
        .reset_index(name="weight")
    )

    # Filtra arestas com peso mínimo
    edges = edges[edges["weight"] >= MIN_EDGE_WEIGHT]

    log.info(f"Arestas geradas: {len(edges):,} pares com >= {MIN_EDGE_WEIGHT} corridas")
    return edges


def build_graph(edges: pd.DataFrame) -> ig.Graph:
    """
    Constrói o grafo direcionado (DiGraph) usando igraph.

    Direcionado porque o fluxo A→B é diferente de B→A —
    um hexágono pode ser muito mais gerador de corridas do que receptor, ou vice-versa.

    Cada nó recebe o atributo 'name' com o identificador H3.
    Cada aresta recebe o atributo 'weight' com o volume de corridas.
    """
    log.info("Construindo grafo com igraph...")

    # Lista de nós únicos
    all_nodes = pd.unique(edges[["pickup_h3", "dropoff_h3"]].values.ravel())
    node_index = {node: i for i, node in enumerate(all_nodes)}

    # Converte arestas para índices numéricos
    edge_list = [
        (node_index[row["pickup_h3"]], node_index[row["dropoff_h3"]])
        for _, row in edges.iterrows()
    ]
    weights = edges["weight"].tolist()

    # Cria grafo direcionado
    G = ig.Graph(directed=True)
    G.add_vertices(len(all_nodes))
    G.vs["name"] = list(all_nodes)
    G.add_edges(edge_list)
    G.es["weight"] = weights

    log.info(f"Grafo construído: {G.vcount():,} nós | {G.ecount():,} arestas")
    return G


# ============================================================
# MÉTRICAS DE CENTRALIDADE
# ============================================================

def calculate_centrality(G: ig.Graph) -> pd.DataFrame:
    """
    Calcula métricas de centralidade para cada nó do grafo.

    - in_strength:   soma dos pesos das arestas de entrada (corridas recebidas)
                     → indica regiões de DESTINO — onde as pessoas vão
    - out_strength:  soma dos pesos das arestas de saída (corridas geradas)
                     → indica regiões de ORIGEM — onde as corridas começam
    - pagerank:      importância do nó considerando a estrutura da rede inteira
                     → hexágonos com alto PageRank são centrais no fluxo urbano
                     mesmo que não tenham o maior volume absoluto
    - betweenness:   quantas vezes o nó aparece nos caminhos mais curtos entre
                     outros nós → identifica "pontes" e corredores de fluxo

    Nota: betweenness em grafos grandes é computacionalmente pesado.
    Usamos a versão normalizada para comparabilidade.
    """
    log.info("Calculando métricas de centralidade...")

    names = G.vs["name"]

    log.info("  → in_strength e out_strength...")
    in_strength  = G.strength(mode="in",  weights="weight")
    out_strength = G.strength(mode="out", weights="weight")

    log.info("  → PageRank...")
    pagerank = G.pagerank(weights="weight", directed=True)

    log.info("  → Betweenness (pode demorar)...")
    betweenness = G.betweenness(weights="weight", directed=True)

    df_metrics = pd.DataFrame({
        "h3_cell":      names,
        "in_strength":  in_strength,
        "out_strength": out_strength,
        "total_flow":   [i + o for i, o in zip(in_strength, out_strength)],
        "pagerank":     pagerank,
        "betweenness":  betweenness,
    })

    # Normaliza betweenness para 0-1
    max_b = df_metrics["betweenness"].max()
    df_metrics["betweenness_norm"] = df_metrics["betweenness"] / max_b if max_b > 0 else 0

    df_metrics = df_metrics.sort_values("total_flow", ascending=False).reset_index(drop=True)
    df_metrics["rank"] = df_metrics.index + 1

    log.info(f"Métricas calculadas para {len(df_metrics):,} nós")
    return df_metrics


# ============================================================
# DETECÇÃO DE COMUNIDADES
# ============================================================

def detect_communities(G: ig.Graph) -> pd.DataFrame:
    """
    Detecta comunidades (clusters) de hexágonos com fluxo intenso entre si.

    Usa o algoritmo Leiden via igraph, que é superior ao Louvain em qualidade
    de partição e reprodutibilidade. Trabalha com o grafo não-direcionado
    (versão simplificada) porque detecção de comunidades clássica é definida
    para grafos não-direcionados.

    Cada comunidade representa um "polo de fluxo" — um conjunto de hexágonos
    que trocam corridas intensamente entre si, potencialmente correspondendo
    a bairros ou zonas funcionais da cidade.
    """
    log.info("Detectando comunidades (Leiden)...")

    # Converte para não-direcionado somando pesos bidirecionais
    G_undirected = G.as_undirected(combine_edges={"weight": "sum"})

    # Algoritmo Leiden
    partition = G_undirected.community_leiden(
        objective_function="modularity",
        weights="weight",
        n_iterations=10
    )

    log.info(f"Comunidades detectadas: {len(partition)}")
    log.info(f"Modularidade: {partition.modularity:.4f}")

    df_communities = pd.DataFrame({
        "h3_cell":    G.vs["name"],
        "community":  partition.membership,
    })

    # Tamanho de cada comunidade
    community_sizes = df_communities["community"].value_counts().rename("community_size")
    df_communities  = df_communities.join(community_sizes, on="community")

    return df_communities


# ============================================================
# ANÁLISE DE FLUXO TEMPORAL
# ============================================================

def analyze_temporal_flow(df: pd.DataFrame, top_n: int = 20) -> dict:
    """
    Analisa como o fluxo varia ao longo do tempo para os hexágonos mais movimentados.

    Retorna dicionário com:
    - fluxo por hora do dia
    - fluxo por dia da semana
    - fluxo em dias úteis vs fins de semana
    - fluxo em horários de pico vs fora de pico
    """
    log.info("Analisando fluxo temporal...")

    # Top hexágonos por volume de saída
    top_h3 = (
        df["pickup_h3"].value_counts()
        .head(top_n)
        .index.tolist()
    )

    df_top = df[df["pickup_h3"].isin(top_h3)]

    # Fluxo por hora
    hourly = (
        df.groupby("hour")
        .size()
        .reset_index(name="trips")
        .to_dict(orient="records")
    )

    # Fluxo por dia da semana
    weekly = (
        df.groupby("is_weekend")
        .size()
        .reset_index(name="trips")
        .to_dict(orient="records")
    )

    # Rush hour vs fora de pico
    rush = (
        df.groupby("is_rush_hour")
        .size()
        .reset_index(name="trips")
        .to_dict(orient="records")
    )

    # Por estação
    seasonal = (
        df.groupby("season")
        .size()
        .reset_index(name="trips")
        .to_dict(orient="records")
    )

    return {
        "hourly_flow":   hourly,
        "weekend_flow":  weekly,
        "rush_flow":     rush,
        "seasonal_flow": seasonal,
        "top_h3_cells":  top_h3,
    }


# ============================================================
# SALVAMENTO DOS RESULTADOS
# ============================================================

def save_results(
    edges:       pd.DataFrame,
    metrics:     pd.DataFrame,
    communities: pd.DataFrame,
    temporal:    dict,
    G:           ig.Graph,
) -> None:
    """
    Salva todos os outputs da análise de grafos em outputs/graph/.

    Arquivos gerados:
    - edge_list.csv          → lista de arestas com pesos
    - node_metrics.csv       → métricas de centralidade por hexágono
    - communities.csv        → comunidades detectadas
    - temporal_analysis.json → análise temporal do fluxo
    - graph_summary.json     → resumo estatístico do grafo
    - graph.graphml          → grafo completo em formato padrão (para Gephi, etc.)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Edge list
    edge_path = OUTPUT_DIR / "edge_list.csv"
    edges.to_csv(edge_path, index=False)
    log.info(f"Salvo: {edge_path}")

    # Métricas de nós
    metrics_path = OUTPUT_DIR / "node_metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    log.info(f"Salvo: {metrics_path}")

    # Comunidades
    comm_path = OUTPUT_DIR / "communities.csv"
    communities.to_csv(comm_path, index=False)
    log.info(f"Salvo: {comm_path}")

    # Análise temporal
    temporal_path = OUTPUT_DIR / "temporal_analysis.json"
    with open(temporal_path, "w") as f:
        json.dump(temporal, f, indent=2)
    log.info(f"Salvo: {temporal_path}")

    # Resumo do grafo
    summary = {
        "generated_at":      timestamp,
        "nodes":             G.vcount(),
        "edges":             G.ecount(),
        "min_edge_weight":   MIN_EDGE_WEIGHT,
        "is_directed":       G.is_directed(),
        "density":           G.density(),
        "top_10_by_flow":    metrics.head(10)[["h3_cell", "total_flow", "pagerank"]].to_dict(orient="records"),
    }
    summary_path = OUTPUT_DIR / "graph_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Salvo: {summary_path}")

    # GraphML (formato padrão para visualização em Gephi)
    graphml_path = OUTPUT_DIR / "graph.graphml"
    G.write_graphml(str(graphml_path))
    log.info(f"Salvo: {graphml_path}")


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def run_graph_analysis() -> None:
    """
    Pipeline completo de análise de grafos.
    """
    log.info("=" * 60)
    log.info("🕸️  INICIANDO ANÁLISE DE GRAFOS - CHICAGO TAXI TRIPS")
    log.info(f"Input:  {FEATURES_DIR.resolve()}")
    log.info(f"Output: {OUTPUT_DIR.resolve()}")
    log.info("=" * 60)

    # 1. Carrega dados
    df = load_all_features()

    # 2. Análise temporal (antes de filtrar pares)
    temporal = analyze_temporal_flow(df)

    # 3. Constrói lista de arestas
    edges = build_edge_list(df)

    # 4. Constrói grafo
    G = build_graph(edges)

    # 5. Calcula métricas de centralidade
    metrics = calculate_centrality(G)

    # 6. Detecta comunidades
    communities = detect_communities(G)

    # 7. Salva tudo
    save_results(edges, metrics, communities, temporal, G)

    # 8. Imprime resumo
    log.info("\n" + "=" * 60)
    log.info("📊 RESUMO DA ANÁLISE DE GRAFOS")
    log.info(f"  Nós (hexágonos H3):    {G.vcount():,}")
    log.info(f"  Arestas (pares O-D):   {G.ecount():,}")
    log.info(f"  Comunidades:           {communities['community'].nunique()}")
    log.info(f"  Densidade do grafo:    {G.density():.6f}")
    log.info(f"\n  Top 5 hexágonos por fluxo total:")
    for _, row in metrics.head(5).iterrows():
        log.info(f"    {row['h3_cell']}  |  fluxo: {int(row['total_flow']):,}  |  PageRank: {row['pagerank']:.6f}")
    log.info("=" * 60)


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":
    run_graph_analysis()