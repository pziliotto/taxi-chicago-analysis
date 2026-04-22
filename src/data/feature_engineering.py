"""
Script de Feature Engineering - Chicago Taxi Trips
Projeto: Análise Geoespacial de Fluxo Urbano
Autor: Pâmela Lima Ziliotto
Data: 12/04/2026

Cria features temporais, espaciais e derivadas a partir dos dados limpos (E3).
Input:  data/processed/taxi_trips/year=YYYY/month=MM/data.parquet
Output: data/features/taxi_trips/year=YYYY/month=MM/data.parquet
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import h3
except ImportError:
    raise ImportError("Instale a biblioteca h3: pip install h3")

try:
    import holidays
except ImportError:
    raise ImportError("Instale a biblioteca holidays: pip install holidays")

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PROCESSED_DIR = Path("data/processed/taxi_trips")
FEATURES_DIR  = Path("data/features/taxi_trips")

CHUNK_SIZE = 500_000

# Resolução H3 (9 = ~174m de aresta)
H3_RESOLUTION = 9

# Feriados federais dos EUA
US_HOLIDAYS = holidays.US()

# Mapeamento das 77 Community Areas de Chicago
COMMUNITY_AREAS = {
    1: "Rogers Park", 2: "West Ridge", 3: "Uptown", 4: "Lincoln Square",
    5: "North Center", 6: "Lake View", 7: "Lincoln Park", 8: "Near North Side",
    9: "Edison Park", 10: "Norwood Park", 11: "Jefferson Park", 12: "Forest Glen",
    13: "North Park", 14: "Albany Park", 15: "Portage Park", 16: "Irving Park",
    17: "Dunning", 18: "Montclare", 19: "Belmont Cragin", 20: "Hermosa",
    21: "Avondale", 22: "Logan Square", 23: "Humboldt Park", 24: "West Town",
    25: "Austin", 26: "West Garfield Park", 27: "East Garfield Park", 28: "Near West Side",
    29: "North Lawndale", 30: "South Lawndale", 31: "Lower West Side", 32: "Loop",
    33: "Near South Side", 34: "Armour Square", 35: "Douglas", 36: "Oakland",
    37: "Fuller Park", 38: "Grand Boulevard", 39: "Kenwood", 40: "Washington Park",
    41: "Hyde Park", 42: "Woodlawn", 43: "South Shore", 44: "Chatham",
    45: "Avalon Park", 46: "South Chicago", 47: "Burnside", 48: "Calumet Heights",
    49: "Roseland", 50: "Pullman", 51: "South Deering", 52: "East Side",
    53: "West Pullman", 54: "Riverdale", 55: "Hegewisch", 56: "Garfield Ridge",
    57: "Archer Heights", 58: "Brighton Park", 59: "McKinley Park", 60: "Bridgeport",
    61: "New City", 62: "West Elsdon", 63: "Gage Park", 64: "Clearing",
    65: "West Lawn", 66: "Chicago Lawn", 67: "West Englewood", 68: "Englewood",
    69: "Greater Grand Crossing", 70: "Ashburn", 71: "Auburn Gresham", 72: "Beverly",
    73: "Washington Heights", 74: "Mount Greenwood", 75: "Morgan Park",
    76: "O'Hare", 77: "Edgewater"
}

# ============================================================
# SETUP DE LOGGING
# ============================================================

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/feature_engineering.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

# ============================================================
# FEATURES TEMPORAIS
# ============================================================

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai features temporais de trip_start_timestamp:
    hour, day_of_week, is_weekend, is_rush_hour, month, season, is_holiday
    """
    ts = df["trip_start_timestamp"]

    df["hour"]        = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek
    df["month"]       = ts.dt.month
    df["is_weekend"]  = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_rush_hour"] = (
        df["hour"].between(7, 9) | df["hour"].between(17, 19)
    ).astype(int)

    # Estação do ano — hemisfério norte
    conditions = [
        df["month"].isin([12, 1, 2]),
        df["month"].isin([3, 4, 5]),
        df["month"].isin([6, 7, 8]),
        df["month"].isin([9, 10, 11]),
    ]
    df["season"] = np.select(conditions, ["Winter", "Spring", "Summer", "Fall"], default="Unknown")

    # Feriados federais dos EUA
    dates = ts.dt.date
    df["is_holiday"] = dates.map(lambda d: 1 if d in US_HOLIDAYS else 0)

    return df

# ============================================================
# FEATURES ESPACIAIS
# ============================================================

def _safe_h3(lat, lon, resolution):
    """Converte lat/lon para célula H3. Retorna None se coordenadas inválidas."""
    try:
        if pd.isna(lat) or pd.isna(lon):
            return None
        return h3.latlng_to_cell(lat, lon, resolution)
    except Exception:
        return None


def _safe_h3_distance(h3_a, h3_b):
    """Calcula distância em hexágonos entre dois cells H3. Retorna None se inválido."""
    try:
        if h3_a is None or h3_b is None:
            return None
        if h3_a == h3_b:
            return 0
        return h3.grid_distance(h3_a, h3_b)
    except Exception:
        return None


def add_spatial_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features espaciais usando H3:
    pickup_h3, dropoff_h3, h3_distance, neighborhood
    """
    log.info("    Calculando células H3...")

    df["pickup_h3"] = df.apply(
        lambda row: _safe_h3(
            row["pickup_centroid_latitude"],
            row["pickup_centroid_longitude"],
            H3_RESOLUTION
        ), axis=1
    )

    df["dropoff_h3"] = df.apply(
        lambda row: _safe_h3(
            row["dropoff_centroid_latitude"],
            row["dropoff_centroid_longitude"],
            H3_RESOLUTION
        ), axis=1
    )

    log.info("    Calculando distâncias H3...")

    df["h3_distance"] = df.apply(
        lambda row: _safe_h3_distance(row["pickup_h3"], row["dropoff_h3"]),
        axis=1
    )

    # Bairro de origem a partir do community area
    if "pickup_community_area" in df.columns:
        df["neighborhood"] = pd.to_numeric(
            df["pickup_community_area"], errors="coerce"
        ).map(COMMUNITY_AREAS)
    else:
        df["neighborhood"] = None

    return df

# ============================================================
# FEATURES DERIVADAS
# ============================================================

def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features derivadas por cálculo:
    speed_mph, fare_per_mile, tip_percentage, total_amount
    """
    # Garante tipos numéricos
    for col in ["trip_miles", "trip_seconds", "fare", "tips"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Velocidade média (mph) — protege contra trip_seconds = 0
    df["speed_mph"] = np.where(
        df["trip_seconds"] > 0,
        df["trip_miles"] / (df["trip_seconds"] / 3600),
        np.nan
    )

    # Tarifa por milha — protege contra trip_miles = 0
    df["fare_per_mile"] = np.where(
        df["trip_miles"] > 0,
        df["fare"] / df["trip_miles"],
        np.nan
    )

    # Percentual de gorjeta — protege contra fare = 0
    if "tips" in df.columns:
        df["tip_percentage"] = np.where(
            df["fare"] > 0,
            (df["tips"] / df["fare"]) * 100,
            np.nan
        )
    else:
        df["tip_percentage"] = np.nan

    # Valor total
    if "tips" in df.columns:
        df["total_amount"] = df["fare"] + df["tips"]
    else:
        df["total_amount"] = df["fare"]

    return df

# ============================================================
# FUNÇÃO CENTRALIZADORA
# ============================================================

def apply_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica os três grupos de features em sequência.
    Ordem: temporais → derivadas → espaciais (H3 é o mais lento, fica por último).
    """
    df = add_temporal_features(df)
    df = add_derived_features(df)
    df = add_spatial_features(df)
    return df

# ============================================================
# PROCESSAMENTO POR ARQUIVO
# ============================================================

def already_processed(processed_path: Path) -> bool:
    """Verifica se o arquivo já foi processado."""
    relative      = processed_path.relative_to(PROCESSED_DIR)
    features_path = FEATURES_DIR / relative
    return features_path.exists() and features_path.stat().st_size > 0


def process_file(processed_path: Path, skip_existing: bool = True) -> bool:
    """
    Processa um arquivo Parquet da E3, adiciona todas as features
    e salva em data/features/.
    """
    relative      = processed_path.relative_to(PROCESSED_DIR)
    output_path   = FEATURES_DIR / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if skip_existing and already_processed(processed_path):
        log.info(f"  ⏭️  {relative} já processado, pulando...")
        return True

    log.info(f"\n⚙️  Processando {relative}...")
    start = datetime.now()

    df_full = pd.read_parquet(processed_path)
    total_rows = len(df_full)
    log.info(f"  Registros: {total_rows:,}")

    chunks_out = []

    for i, start_idx in enumerate(range(0, total_rows, CHUNK_SIZE)):
        chunk = df_full.iloc[start_idx : start_idx + CHUNK_SIZE].copy()
        log.info(f"  Chunk {i+1}: {len(chunk):,} registros...")
        chunk = apply_all_features(chunk)
        chunks_out.append(chunk)

    del df_full

    df_out = pd.concat(chunks_out, ignore_index=True)
    df_out.to_parquet(output_path, index=False, engine="pyarrow", compression="snappy")

    elapsed = (datetime.now() - start).total_seconds()
    size_mb = output_path.stat().st_size / 1024 / 1024
    log.info(f"  ✅ Concluído: {total_rows:,} registros em {elapsed:.1f}s ({size_mb:.1f} MB)")
    log.info(f"  Features adicionadas: {list(df_out.columns)}")

    return True

# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def run_pipeline(skip_existing: bool = True) -> None:
    """
    Processa todos os arquivos de data/processed/ e salva em data/features/.
    """
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(PROCESSED_DIR.rglob("*.parquet"))
    log.info("=" * 60)
    log.info("⚙️  INICIANDO FEATURE ENGINEERING - CHICAGO TAXI TRIPS")
    log.info(f"Input:  {PROCESSED_DIR.resolve()}")
    log.info(f"Output: {FEATURES_DIR.resolve()}")
    log.info(f"Arquivos encontrados: {len(files)}")
    log.info("=" * 60)

    errors = 0
    for path in files:
        try:
            process_file(path, skip_existing=skip_existing)
        except Exception as e:
            log.error(f"  ❌ Erro em {path}: {e}")
            errors += 1

    log.info(f"\n✅ Pipeline concluído. Erros: {errors}")

# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Feature Engineering - Chicago Taxi Trips"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Processa apenas um arquivo (ex: year=2022/month=01/data.parquet)"
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Reprocessa mesmo se arquivo já existe em data/features/"
    )

    args = parser.parse_args()
    skip = not args.no_skip

    if args.file:
        path = PROCESSED_DIR / args.file
        if not path.exists():
            print(f"❌ Arquivo não encontrado: {path}")
        else:
            process_file(path, skip_existing=skip)
    else:
        run_pipeline(skip_existing=skip)