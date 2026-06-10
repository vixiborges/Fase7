"""
FarmTech Solutions – Fase 1
Módulo de Meteorologia via Open-Meteo (gratuito, sem chave de API)
Coordenadas padrão: Ribeirão Preto-SP (principal polo agrícola do Brasil)
"""

import requests
from datetime import datetime

LATITUDE = -21.1775
LONGITUDE = -47.8103
CIDADE = "Ribeirão Preto - SP"

def buscar_clima_atual():
    """Retorna dados meteorológicos atuais como dicionário."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,"
        "wind_speed_10m,weather_code"
        "&timezone=America%2FSao_Paulo"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        c = dados["current"]
        return {
            "cidade": CIDADE,
            "temperatura": c["temperature_2m"],
            "umidade": c["relative_humidity_2m"],
            "precipitacao": c["precipitation"],
            "vento": c["wind_speed_10m"],
            "codigo_tempo": c["weather_code"],
            "descricao": _descricao_wmo(c["weather_code"]),
            "horario": c["time"],
            "sucesso": True
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def buscar_previsao_7dias():
    """Retorna previsão de 7 dias como lista de dicionários."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "wind_speed_10m_max,weather_code"
        "&timezone=America%2FSao_Paulo"
        "&forecast_days=7"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        dados = resp.json()["daily"]
        previsao = []
        for i in range(len(dados["time"])):
            previsao.append({
                "data": dados["time"][i],
                "temp_max": dados["temperature_2m_max"][i],
                "temp_min": dados["temperature_2m_min"][i],
                "precipitacao": dados["precipitation_sum"][i],
                "vento_max": dados["wind_speed_10m_max"][i],
                "descricao": _descricao_wmo(dados["weather_code"][i])
            })
        return {"sucesso": True, "previsao": previsao}
    except Exception as e:
        return {"sucesso": False, "erro": str(e), "previsao": []}


def _descricao_wmo(code):
    """Converte código WMO para descrição em português."""
    tabela = {
        0: "Céu limpo", 1: "Predominantemente limpo", 2: "Parcialmente nublado",
        3: "Nublado", 45: "Névoa", 48: "Névoa com geada",
        51: "Garoa leve", 53: "Garoa moderada", 55: "Garoa densa",
        61: "Chuva leve", 63: "Chuva moderada", 65: "Chuva forte",
        71: "Neve leve", 73: "Neve moderada", 75: "Neve forte",
        80: "Pancadas leves", 81: "Pancadas moderadas", 82: "Pancadas fortes",
        95: "Tempestade", 96: "Tempestade com granizo leve",
        99: "Tempestade com granizo forte"
    }
    return tabela.get(code, f"Código {code}")


def alerta_climatico(clima):
    """Gera alertas baseados nas condições climáticas."""
    alertas = []
    if not clima.get("sucesso"):
        return alertas
    if clima["precipitacao"] > 10:
        alertas.append(("🌧️ CHUVA FORTE", "Suspenda irrigação e aplicação de defensivos."))
    if clima["temperatura"] > 35:
        alertas.append(("🌡️ CALOR EXTREMO", "Risco de estresse hídrico. Aumente irrigação."))
    if clima["temperatura"] < 10:
        alertas.append(("🥶 FRIO INTENSO", "Risco de geada. Monitore plantações sensíveis."))
    if clima["vento"] > 40:
        alertas.append(("💨 VENTO FORTE", "Não aplique defensivos. Risco de deriva."))
    if clima["umidade"] < 30:
        alertas.append(("🏜️ UMIDADE BAIXA", "Solo seco. Considere irrigação preventiva."))
    return alertas
