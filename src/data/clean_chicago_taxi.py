"""
Script de Limpeza de Dados - Chicago Taxi Trips
Projeto: Análise Geoespacial de Fluxo Urbano
Autor: Pâmela Lima Ziliotto

Limpeza completa dos dados brutos (data/raw/) aplicando regras de negócio definidas
no dossiê. Output salvo em data/processed/ com relatório de qualidade.
"""

# ====================================================
# IMPORTS
# ====================================================

import os
import logging
import pandas as pd
import numpy as np
import pathlib
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
 
load_dotenv()


# ====================================================
# CONFIGURAÇÕES
# ====================================================

# Diretórios
RAW_DIR       = Path("data/raw/taxi_trips")
PROCESSED_DIR = Path("data/processed/taxi_trips")
REPORTS_DIR   = Path("outputs/quality_reports")

# Tamanho do chunck - linhas por vez em memória
# 500k linhas ~500mb RAM
CHUNK_SIZE = 500_000

# ---------- Regras de Limpeza (encontrada no dossiê) ----------
# Bounding box de Chicago
CHICAGO_LAT_MIN =  41.6
CHICAGO_LAT_MAX =  42.1
CHICAGO_LON_MIN = -87.9
CHICAGO_LON_MAX = -87.5

# Distância
TRIP_MILES_MIN =   0.0        # Referente a corridas locais e canceladas
TRIP_MILES_MAX = 100.0

# Duração
TRIP_SECONDS_MIN =   60       # Mínimo de 1 minuto
TRIP_SECONDS_MAX = 7200    # Máximo de 2 horas

# Tarifa
FARE_MIN =   2.50
FARE_MAX  = 500.00


# ====================================================
# SETUP DE LOGGING
# ====================================================

Path("logs").mkdir(exist_ok=True)
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/cleaning.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

# ====================================================
# REGRAS DE LIMPEZA
# ====================================================

def remove_invalid_coordinates(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """
    Remove registros com lat/lon fora do bounding box de Chicago.

    A E2 já removeu os nulos, mas coordenadas podem estar dentro do dtype float e ainda assim serem geograficamente inválidas (ex: 0.0, 99,9).
    O box garante que só ficam corridas que realmente aconteceram em Chicago.
    """
    before = len(df)
    mask = (
        df["pickup_centroid_latitude"].between(CHICAGO_LAT_MIN, CHICAGO_LAT_MAX) &
        df["pickup_centroid_longitude"].between(CHICAGO_LON_MIN, CHICAGO_LON_MAX) &
        df["dropoff_centroid_latitude"].between(CHICAGO_LAT_MIN, CHICAGO_LAT_MAX) &
        df["dropoff_centroid_longitude"].between(CHICAGO_LON_MIN, CHICAGO_LON_MAX)
    )
    df = df[mask]
    stats["invalid_coordinates"] += before - len(df)
    return df



def remove_invalid_trip_miles(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """
    Remove corridas com distância inválida (negativa ou > 100 milhas).

    Valores negativos são erros de sistema. Corridas acima de 100 milhas são improváveis dentro de Chicago e indicam erro de registro.
    Nota: trip_miles = 0 é aceito - pois são corridas muito curtas ou canceladas após início da cobrança.
    """
    before = len(df)
    if "trip_miles" in df.columns:
        df["trip_miles"] = pd.to_numeric(df["trip_miles"], errors="coerce")
        mask = df["trip_miles"].between(TRIP_MILES_MIN, TRIP_MILES_MAX)
        # Mantém também os nulos (corridas sem campo de milhas preenchido)
        df = df[mask | df["trip_miles"].isna()]
    stats["invalid_trip_miles"] += before - len(df)
    return df


def remove_invalid_trip_seconds(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """
    Remove corridas com duração inválida (< 1 minuto ou > 2 horas)

    Corridas abaixo de 60 segundos provavelmente são corridas canceladas ou erros de registro.
    Acima de 7200 segundos (2h) são outliers que distorceriam métricas de tempo médio.
    """
    before = len(df)
    if "trip_seconds" in df.columns:
        df["trip_seconds"] = pd.to_numeric(df["trip_seconds"], errors="coerce")
        mask = df["trip_seconds"].between(TRIP_SECONDS_MIN, TRIP_SECONDS_MAX)
        df = df[mask | df["trip_seconds"].isna()]
    stats["invalid_trip_seconds"] += before - len(df)
    return df


def remove_invalid_fare(df: pd.DataFrame, stats:dict) -> pd.DataFrame:
    """ 
    Remove corridas com tarifa inválida (< $2.50 ou > $500)
    
    $2.50 é a tarifa mínima de taxi em Chicago (flag drop fee).
    Tarifas acima de $500 são outliers que distorceriam análises econômicas.
    """
    before = len(df)
    if "fare" in df.columns:
        df["fare"] = pd.to_numeric(df["fare"], errors="coerce")
        mask = df["fare"].between(FARE_MIN, FARE_MAX)
        df = df[mask | df["fare"].isna()]
    stats["invalid_fare"] += before - len(df)
    return df


def remove_invalid_timestamps(df: pd.DataFrame, stats:dict) -> pd.DataFrame:
    """ 
    Remove corridas onde o horário de fim é anterioao horário de início.

    Trip End < Trip Start é fisicamente impossível e indica erro de sistema ou registro corrompido.
    Esses registros distorceriam qualquer análise temporal e de duração.    
    """
    before = len(df)
    if "trip_start_timestamp" in df.columns and "trip_end_timestamp" in df.columns:
        # Garante que ambos são datetime
        df["trip_start_timestamp"] = pd.to_datetime(df["trip_start_timestamp"], errors="coerce")
        df["trip_end_timestamp"] = pd.to_datetime(df["trip_end_timestamp"], errors="coerce")

        # Mantém registro onde end >= start, ou onde algum timestamp é nulo
        both_present = df["trip_start_timestamp"].notna() & df["trip_end_timestamp"].notna()
        invalid = both_present & (df["trip_end_timestamp"] < df["trip_start_timestamp"])
        df = df[~invalid]
    stats["invalid_timestamps"] += before - len(df)
    return df


def apply_all_rules(df: pd.DataFrame, stats:dict) -> pd.DataFrame:
    """ 
    Aplica todas as regras de limpeza em sequência.
    A ordem importa: coordenadas primeiro (mais restritiva), depois as regras numéricas e por último timestamp.
    """
    df = remove_invalid_coordinates(df, stats)
    df = remove_invalid_trip_miles(df, stats)
    df = remove_invalid_trip_seconds(df, stats)
    df = remove_invalid_fare(df, stats)
    df = remove_invalid_timestamps(df, stats)
    return df

# ====================================================
# PROCESSAMENTO POR MÊS
# ====================================================

def get_raw_files() ->list[Path]:
    """
    Retorna todos os arquivos Parquet em data/raw/, ordenado por ano/mês.
    """
    files = sorted(RAW_DIR.rglob("*.parquet"))
    log.info(f"Arquivos encontrados: {len(files)}")
    return files


def already_processed(raw_path: Path) -> bool:
    """ 
    Verifica se o arquivo já foi processado (evita reprocessamento).
    """
    # Mantém a mesma estrutura year=/month= no diretório processed
    relative = raw_path.relative_to(RAW_DIR)
    processed_path = PROCESSED_DIR / relative
    return processed_path.exists() and processed_path.stat().st_size > 0


def process_file(raw_path: Path, skip_existing: bool = True) -> dict:
    """
    Processa um único arquivo Parquet em chunks.
 
    Lê o arquivo em pedaços de CHUNK_SIZE linhas, aplica as regras de limpeza em cada chunk e salva o resultado em data/processed/.
 
    Retorna um dicionário com as estatísticas de limpeza do arquivo.
    """
    relative   = raw_path.relative_to(RAW_DIR)
    output_path = PROCESSED_DIR / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
 
    if skip_existing and already_processed(raw_path):
        log.info(f"  ⏭️  {relative} já processado, pulando...")
        return {}
 
    log.info(f"\n🧹 Processando {relative}...")
 
    # Estatísticas acumuladas para este arquivo
    stats = {
        "file":                 str(relative),
        "rows_raw":             0,
        "rows_clean":           0,
        "invalid_coordinates":  0,
        "invalid_trip_miles":   0,
        "invalid_trip_seconds": 0,
        "invalid_fare":         0,
        "invalid_timestamps":   0,
    }

    """ 
    LEITURA EM CHUNKS
    pd.read_parquet não suporta chunck de forma nativa, então lemos o arquivo inteiro primeiro e o fatiamos de forma manual.
    Para 23M registros divididos em 50 arquivos de ~476k arquivos. Assim cada arquivo cabe confortavelmente em memória.
    O CHUNK_SIZE existe como proteção para meses com pico.
    """

    df_full = pd.read_parquet(raw_path)
    stats["rows_raw"] = len(df_full)
 
    cleaned_chunks = []
 
    for start in range(0, len(df_full), CHUNK_SIZE):
        chunk = df_full.iloc[start : start + CHUNK_SIZE].copy()
        chunk = apply_all_rules(chunk, stats)
        cleaned_chunks.append(chunk)
 
    del df_full  # libera memória antes de concatenar
 
    if cleaned_chunks:
        df_clean = pd.concat(cleaned_chunks, ignore_index=True)
    else:
        df_clean = pd.DataFrame()
 
    stats["rows_clean"] = len(df_clean)
    removed_total = stats["rows_raw"] - stats["rows_clean"]
    pct_removed   = (removed_total / stats["rows_raw"] * 100) if stats["rows_raw"] > 0 else 0

    # ----------- Salva os resultados -----------
    
    df_clean.to_parquet(output_path, index=False, engine="pyarrow", compression="snappy")
    size_mb = output_path.stat().st_size / 1024 / 1024
 
    log.info(f"  Bruto:  {stats['rows_raw']:>10,} registros")
    log.info(f"  Limpo:  {stats['rows_clean']:>10,} registros  ({pct_removed:.1f}% removidos)")
    log.info(f"  Coord:  {stats['invalid_coordinates']:>10,} removidos")
    log.info(f"  Miles:  {stats['invalid_trip_miles']:>10,} removidos")
    log.info(f"  Secs:   {stats['invalid_trip_seconds']:>10,} removidos")
    log.info(f"  Fare:   {stats['invalid_fare']:>10,} removidos")
    log.info(f"  Stamps: {stats['invalid_timestamps']:>10,} removidos")
    log.info(f"  Salvo:  {output_path} ({size_mb:.1f} MB)")
 
    return stats


# ====================================================
# RELATORIO DE QUALIDADE
# ====================================================

def generate_quality_report(all_stats: list[dict]) -> None:
    """
    Gera relatório consolidado de qualidade em CSV.
 
    O relatório mostra, por arquivo e no total:
    - Quantos registros foram removidos por cada regra
    - % de remoção global e por regra
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
 
    df = pd.DataFrame(all_stats)
    df["removed_total"]   = df["rows_raw"] - df["rows_clean"]
    df["pct_removed"]     = (df["removed_total"] / df["rows_raw"] * 100).round(2)
    df["pct_coordinates"] = (df["invalid_coordinates"]  / df["rows_raw"] * 100).round(2)
    df["pct_miles"]       = (df["invalid_trip_miles"]    / df["rows_raw"] * 100).round(2)
    df["pct_seconds"]     = (df["invalid_trip_seconds"]  / df["rows_raw"] * 100).round(2)
    df["pct_fare"]        = (df["invalid_fare"]          / df["rows_raw"] * 100).round(2)
    df["pct_timestamps"]  = (df["invalid_timestamps"]    / df["rows_raw"] * 100).round(2)
 
    # Linha de totais
    totals = {
        "file":                 "TOTAL",
        "rows_raw":             df["rows_raw"].sum(),
        "rows_clean":           df["rows_clean"].sum(),
        "invalid_coordinates":  df["invalid_coordinates"].sum(),
        "invalid_trip_miles":   df["invalid_trip_miles"].sum(),
        "invalid_trip_seconds": df["invalid_trip_seconds"].sum(),
        "invalid_fare":         df["invalid_fare"].sum(),
        "invalid_timestamps":   df["invalid_timestamps"].sum(),
        "removed_total":        df["removed_total"].sum(),
    }
    raw_total   = totals["rows_raw"]
    totals["pct_removed"]     = round(totals["removed_total"]        / raw_total * 100, 2)
    totals["pct_coordinates"] = round(totals["invalid_coordinates"]  / raw_total * 100, 2)
    totals["pct_miles"]       = round(totals["invalid_trip_miles"]   / raw_total * 100, 2)
    totals["pct_seconds"]     = round(totals["invalid_trip_seconds"] / raw_total * 100, 2)
    totals["pct_fare"]        = round(totals["invalid_fare"]         / raw_total * 100, 2)
    totals["pct_timestamps"]  = round(totals["invalid_timestamps"]   / raw_total * 100, 2)
 
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
 
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"quality_report_{timestamp}.csv"
    df.to_csv(report_path, index=False)
 
    # Imprime resumo no terminal
    total_row = df[df["file"] == "TOTAL"].iloc[0]
    log.info("\n" + "=" * 60)
    log.info("📊 RELATÓRIO DE QUALIDADE — RESUMO")
    log.info(f"  Registros brutos:      {int(total_row['rows_raw']):>12,}")
    log.info(f"  Registros limpos:      {int(total_row['rows_clean']):>12,}")
    log.info(f"  Total removido:        {int(total_row['removed_total']):>12,}  ({total_row['pct_removed']:.2f}%)")
    log.info(f"  → Coordenadas:         {int(total_row['invalid_coordinates']):>12,}  ({total_row['pct_coordinates']:.2f}%)")
    log.info(f"  → Trip Miles:          {int(total_row['invalid_trip_miles']):>12,}  ({total_row['pct_miles']:.2f}%)")
    log.info(f"  → Trip Seconds:        {int(total_row['invalid_trip_seconds']):>12,}  ({total_row['pct_seconds']:.2f}%)")
    log.info(f"  → Fare:                {int(total_row['invalid_fare']):>12,}  ({total_row['pct_fare']:.2f}%)")
    log.info(f"  → Timestamps:          {int(total_row['invalid_timestamps']):>12,}  ({total_row['pct_timestamps']:.2f}%)")
    log.info(f"  Relatório salvo em:    {report_path}")
    log.info("=" * 60)
 
# ============================================
# PIPELINE PRINCIPAL
# ============================================
 
def run_cleaning(skip_existing: bool = True) -> None:
    """
    Executa o pipeline completo de limpeza para todos os arquivos em data/raw/.
    """
    Path("logs").mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
 
    log.info("=" * 60)
    log.info("🧹 INICIANDO LIMPEZA - CHICAGO TAXI TRIPS")
    log.info(f"Input:  {RAW_DIR.resolve()}")
    log.info(f"Output: {PROCESSED_DIR.resolve()}")
    log.info(f"Chunk size: {CHUNK_SIZE:,} linhas")
    log.info("=" * 60)
 
    files     = get_raw_files()
    all_stats = []
    errors    = 0
 
    for raw_path in files:
        try:
            stats = process_file(raw_path, skip_existing=skip_existing)
            if stats:  # vazio se foi pulado
                all_stats.append(stats)
        except Exception as e:
            log.error(f"  ❌ Erro em {raw_path}: {e}")
            errors += 1
 
    if all_stats:
        generate_quality_report(all_stats)
 
    log.info(f"\n✅ Limpeza concluída. Arquivos com erro: {errors}")
 
 
# =======================================
# EXECUÇÃO DIRETA
# =======================================
 
if __name__ == "__main__":
    import argparse
 
    parser = argparse.ArgumentParser(
        description="Limpeza de dados - Chicago Taxi Trips"
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Reprocessa arquivos mesmo se já existem em data/processed/"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Processa apenas um arquivo específico (ex: year=2022/month=01/data.parquet)"
    )
 
    args = parser.parse_args()
 
    if args.file:
        # Modo arquivo único — útil para testar uma partição específica
        raw_path = RAW_DIR / args.file
        if not raw_path.exists():
            print(f"❌ Arquivo não encontrado: {raw_path}")
        else:
            stats = process_file(raw_path, skip_existing=not args.no_skip)
            if stats:
                generate_quality_report([stats])
    else:
        run_cleaning(skip_existing=not args.no_skip)