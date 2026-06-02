from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(url)

with engine.connect() as conn:
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_trips_neighborhood_amount ON taxi_trips (neighborhood, total_amount)'))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_trips_hour_neighborhood ON taxi_trips (hour, neighborhood)'))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_trips_season ON taxi_trips (season)'))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_trips_rush ON taxi_trips (is_rush_hour, total_amount)'))
    conn.commit()
    print('Índices criados!')