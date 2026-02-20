"""
Teste inicial da API Socrata - Chicago Taxi Data
Autor: Pâmela Lima Ziliotto
Data: 18/02/2026
"""

import requests
import pandas as pd
from datetime import datetime

def test_api_connection():
    """Testa conexão básica com a API"""
    
    print("="*60)
    print("🚕 TESTANDO API DE CHICAGO - TAXI TRIPS")
    print("="*60 + "\n")
    
    # Endpoint da API
    url = "https://data.cityofchicago.org/resource/ajtu-isnz.json"
    
    # Pegar só 10 registros para teste
    params = {
        "$limit": 10,
        "$order": "trip_start_timestamp DESC"  # Mais recentes primeiro
    }
    
    try:
        print("📡 Fazendo request para API...")
        response = requests.get(url, params=params, timeout=30)
        
        print(f"✅ Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 Registros recebidos: {len(data)}\n")
            
            # Converter para DataFrame
            df = pd.DataFrame(data)
            
            print("📋 Colunas disponíveis:")
            print(df.columns.tolist())
            print("\n")
            
            print("👀 Primeiras 3 corridas:")
            print(df[['trip_id', 'trip_start_timestamp', 'pickup_centroid_latitude', 
                      'pickup_centroid_longitude', 'fare']].head(3))
            print("\n")
            
            print("📈 Informações do DataFrame:")
            print(df.info())
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False


if __name__ == "__main__":
    test_api_connection()

