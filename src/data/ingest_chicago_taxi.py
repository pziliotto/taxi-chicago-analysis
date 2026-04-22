
"""
Script de Ingestão de Dados - Chicago Taxi Trips
Projeto: Análise Geoespacial de Fluxo Urbano
Autor: Pâmela Lima Ziliotto
Data: 23/02/2026

Pipeline de download incremental via API Socrata.
Salva dados em formato Parquet particionado por ano/mês em data/raw/.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import time
import logging
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # load_dotenv() precisa ser chamado ANTES do os.getenv()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Endpoints da API Socrata - Chicago Taxi Trips
# O portal de Chicago separou os dados em dois datasets:
API_URL_HISTORICAL = "https://data.cityofchicago.org/resource/wrvz-psew.json"  # 2013–2023
API_URL_CURRENT    = "https://data.cityofchicago.org/resource/ajtu-isnz.json"   # 2024–atual

def get_api_url(year: int) -> str:
    """Retorna o endpoint correto baseado no ano."""
    return API_URL_CURRENT if year >= 2024 else API_URL_HISTORICAL

# App Token para evitar throttling
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN", "")

# Diretório de saída
OUTPUT_DIR = Path("data/raw/taxi_trips")

# Limite por request (Máximo da API Socrata)
PAGE_SIZE = 50_000

# Anos disponíveis no dataset
START_YEAR = 2022
END_YEAR = datetime.now().year

# Colunas com lat/lon válidos - descartaremos instâncias sem elas
GEO_COLS = ["pickup_centroid_latitude", "pickup_centroid_longitude",
            "dropoff_centroid_latitude", "dropoff_centroid_longitude"]

# Delay entre requests (segundos) para evitar rate limiting
REQUEST_DELAY = 0.5

# Número de tentativas em caso de erro
MAX_RETRIES = 3

# ============================================================
# SETUP DE LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/ingestion.log", mode="a", encoding="utf-8")
    ]
)

log = logging.getLogger(__name__)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def build_headers() -> dict:
    """ Monta cabeçalhos da requisição, incluindo App Token"""
    headers = {"Accept": "application/json"}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    else:
        log.warning("APP_TOKEN não definido. Requests sem token possuem limite menor.")
    return headers

def fetch_page(year: int, month: int, offset: int, headers: dict) -> list[dict]:
    """
    Faz uma requisição paginada para um mês específico.
    
    Retorna lista de registros - dicts - ou lança exceção após MAX_RETRIES falhas.
    """
    month_start = f"{year}-{month:02d}-01T00:00:00"
    if month == 12:
        month_end = f"{year + 1}-01-01T00:00:00"
    else:
        month_end = f"{year}-{month + 1:02d}-01T00:00:00"

    params = {
        "$where": f"trip_start_timestamp >= '{month_start}' AND trip_start_timestamp < '{month_end}'",
        "$limit": PAGE_SIZE,
        "$offset": offset,
        "$order": "trip_start_timestamp ASC",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(get_api_url(year), params=params, headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log.warning(f"   Tentativa {attempt}/{MAX_RETRIES} falhou: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise


def download_month(year: int, month: int, headers: dict) -> pd.DataFrame: 
    """
    Baixa todos os registros de um mês via paginação.
    Retorna DataFrame com todos os registros do mês.
    """
    all_records = []
    offset = 0
    page = 1

    log.info(f"    Baixando {year}-{month:02d}...")

    while True:
        records = fetch_page(year, month, offset, headers)

        if not records:
            break
        all_records.extend(records)
        count = len(records)
        log.info(f"    Página {page}: {count:,} registros (total: {len(all_records):,})")

        if count < PAGE_SIZE:
            break
    
        offset += PAGE_SIZE
        page += 1
        time.sleep(REQUEST_DELAY)
    
    if not all_records:
        log.warning(f"    Nenhum registro encontrado para {year}-{month:02d}")
        return pd.DataFrame()
    
    return pd.DataFrame(all_records)


def clean_and_cast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica limpeza mínima necessária antes de salvar:
    - Remove registros sem coordenadas geográficas
    - Converte tipos básicos (lat/lon para float, timestamps para datetime)
    - Remove duplicatas de trip_id

    Observação: Limpeza completa (outliers, regras de negócio) será feita na Etapa 3.
    """
    original_count = len(df)

    # 1. Remove registros sem coordenadas
    geo_present = [c for c in GEO_COLS if c in df.columns]
    if geo_present:
        df = df.dropna(subset=geo_present)
        for col in geo_present:
            df = df[df[col].astype(str).str.strip() != ""]

    # 2. Converte lat/lon para float
    for col in geo_present:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=geo_present)

    # 3. Converte timestamps
    for ts_col in ["trip_start_timestamp", "trip_end_timestamp"]:
        if ts_col in df.columns:
            df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

    # 4. Remove duplicatas de trip_id
    if "trip_id" in df.columns:
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["trip_id"], keep="first")
        removed_dedup = before_dedup - len(df)
        if removed_dedup > 0:
            log.info(f"    Duplicatas removidas: {removed_dedup:,}")
    
    removed = original_count - len(df)
    pct = (removed / original_count * 100) if original_count > 0 else 0
    log.info(f"    Registros válidos: {len(df):,} / {original_count:,} "
             f"({pct:.1f}% removidos na ingestão)")
    
    return df


def save_parquet(df: pd.DataFrame, year: int, month: int) -> Path:
    """ Salva DataFrame em Parquet particionado por ano/mês."""
    month_dir = OUTPUT_DIR / f"year={year}" / f"month={month:02d}"
    month_dir.mkdir(parents=True, exist_ok=True)

    filepath = month_dir / "data.parquet"
    df.to_parquet(filepath, index=False, engine="pyarrow", compression="snappy")

    size_mb = filepath.stat().st_size / 1024 / 1024
    log.info(f"    Salvo em: {filepath} ({size_mb:.1f} MB)")
    return filepath


def month_already_downloaded(year: int, month: int) -> bool:
    """ Verifica se o mês já foi baixado (arquivo Parquet existe e não está vazio). """
    filepath = OUTPUT_DIR / f"year={year}" / f"month={month:02d}" / "data.parquet"
    return filepath.exists() and filepath.stat().st_size > 0


def save_download_log(log_records: list[dict]) -> None:
    """ Salva log de download em CSV para acompanhamento. """
    log_path = OUTPUT_DIR / "download_log.csv"
    log_df = pd.DataFrame(log_records)

    if log_path.exists():
        existing = pd.read_csv(log_path)
        log_df = pd.concat([existing, log_df], ignore_index=True)
        log_df = log_df.drop_duplicates(subset=["year", "month"], keep="last")

    log_df.to_csv(log_path, index=False)
    log.info(f"Log de download atualizado: {log_path}")


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def run_ingestion(
    years: list[int] | None = None,
    months: list[int] | None = None,
    skip_existing: bool = True,
):
    """
    Executa o pipeline completo de ingestão.

    Args:
        years:         Lista de anos para baixar. None = todos (2022 até hoje).
        months:        Lista de meses para baixar. None = todos (1-12).
        skip_existing: Se True, pula meses que já foram baixados.
    """
    Path("logs").mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    years = years or list(range(START_YEAR, END_YEAR + 1))
    months = months or list(range(1, 13))
    headers = build_headers()

    log.info("=" * 60)
    log.info("🚕 INICIANDO INGESTÃO - CHICAGO TAXI TRIPS")
    log.info(f"Anos: {years[0]} → {years[-1]}")
    log.info(f"Meses: {months}")
    log.info(f"Endpoints: histórico (≤2023) = wrvz-psew | atual (≥2024) = ajtu-isnz")
    log.info(f"Output: {OUTPUT_DIR.resolve()}")
    log.info("=" * 60)

    download_log = []
    total_records = 0
    skipped = 0
    errors = 0

    for year in years:
        current_year = datetime.now().year
        current_month = datetime.now().month

        for month in months:
            if year == current_year and month > current_month:
                continue
            if year > current_year:
                continue

            if skip_existing and month_already_downloaded(year, month):
                log.info(f"  ⏭️  {year}-{month:02d} já existe, pulando...")
                skipped += 1
                continue

            log.info(f"\n📅 Processando {year}-{month:02d}...")
            start_time = time.time()

            try:
                df = download_month(year, month, headers)

                if df.empty:
                    download_log.append({
                        "year": year, "month": month,
                        "records": 0, "status": "empty",
                        "downloaded_at": datetime.now().isoformat()
                    })
                    continue

                df = clean_and_cast(df)
                save_parquet(df, year, month)

                elapsed = time.time() - start_time
                records = len(df)
                total_records += records

                download_log.append({
                    "year": year, "month": month,
                    "records": records, "status": "ok",
                    "elapsed_seconds": round(elapsed, 1),
                    "downloaded_at": datetime.now().isoformat()
                })

                log.info(f"  ✅ {year}-{month:02d} concluído: "
                         f"{records:,} registros em {elapsed:.1f}s")

            except Exception as e:
                log.error(f"  ❌ Erro em {year}-{month:02d}: {e}")
                errors += 1
                download_log.append({
                    "year": year, "month": month,
                    "records": 0, "status": f"error: {e}",
                    "downloaded_at": datetime.now().isoformat()
                })

    if download_log:
        save_download_log(download_log)

    log.info("\n" + "=" * 60)
    log.info("📊 RESUMO DA INGESTÃO")
    log.info(f"  Total de registros baixados: {total_records:,}")
    log.info(f"  Meses pulados (já existiam): {skipped}")
    log.info(f"  Erros: {errors}")
    log.info("=" * 60)


# ============================================================
# ENTRY POINTS DE CONVENIÊNCIA
# ============================================================

def ingest_sample(n_records: int = 1000) -> pd.DataFrame:
    """
    Baixa uma amostra rápida para testes e exploração.
    Retorna DataFrame sem salvar em disco.
    """
    log.info(f"🧪 Baixando amostra de {n_records} registros...")
    headers = build_headers()

    params = {
        "$limit": n_records,
        "$order": "trip_start_timestamp DESC",
    }

    response = requests.get(API_URL_CURRENT, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    df = pd.DataFrame(response.json())
    log.info(f"✅ Amostra carregada: {len(df)} registros, {len(df.columns)} colunas")
    return df


def ingest_year(year: int, skip_existing: bool = True) -> None:
    """ Baixa todos os meses de um ano específico. """
    run_ingestion(years=[year], skip_existing=skip_existing)


def ingest_month(year: int, month: int, skip_existing: bool = False) -> None:
    """ Baixa um único mês. """
    run_ingestion(years=[year], months=[month], skip_existing=skip_existing)


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingestão de dados - Chicago Taxi Trips via Socrata API"
    )

    parser.add_argument(
        "--mode",
        choices=["full", "year", "month", "sample"],
        default="sample",
        help=(
            "full   = baixa tudo (2022-hoje)\n"
            "year   = baixa um ano (use --year)\n"
            "month  = baixa um mês (use --year e --month)\n"
            "sample = baixa 1000 registros para teste (padrão)"
        )
    )

    parser.add_argument("--year", type=int, default=2024, help="Ano (para mode=year ou month)")
    parser.add_argument("--month", type=int, default=1, help="Mês 1-12 (para mode=month)")
    parser.add_argument("--no-skip", action="store_true", help="Re-baixa mesmo se arquivo já existe")

    args = parser.parse_args()
    skip = not args.no_skip

    if args.mode == "sample":
        df = ingest_sample()
        print("\n📋 Colunas disponíveis:")
        print(df.columns.tolist())
        print("\n👀 Primeiros registros:")
        print(df[["trip_id", "trip_start_timestamp",
                   "pickup_centroid_latitude", "pickup_centroid_longitude",
                   "fare"]].head(5).to_string())

    elif args.mode == "month":
        ingest_month(args.year, args.month, skip_existing=skip)

    elif args.mode == "year":
        ingest_year(args.year, skip_existing=skip)

    elif args.mode == "full":
        run_ingestion(skip_existing=skip)