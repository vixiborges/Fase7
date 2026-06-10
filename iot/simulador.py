"""
FarmTech Solutions – Fase 3
Simulador IoT: sensores de umidade, pH, nutrientes (N, P, K)
Substitui o ESP32 físico com DHT22 e LDR por valores simulados realistas.
Lógica de irrigação automática baseada em limiares agronômicos.
"""

import random
import time
import sys
import os
from datetime import datetime

# Adiciona raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import inserir_leitura, inicializar_banco

# ── Limiares agronômicos ───────────────────────────────────────────────────────
LIMIARES = {
    "umidade": {
        "critico_baixo": 20.0,   # %
        "ideal_min": 40.0,
        "ideal_max": 70.0,
        "critico_alto": 85.0,
        "unidade": "%"
    },
    "ph": {
        "critico_baixo": 5.0,
        "ideal_min": 6.0,
        "ideal_max": 7.0,
        "critico_alto": 8.0,
        "unidade": "pH"
    },
    "nitrogenio": {
        "critico_baixo": 10.0,   # mg/kg
        "ideal_min": 20.0,
        "ideal_max": 50.0,
        "critico_alto": 80.0,
        "unidade": "mg/kg"
    },
    "fosforo": {
        "critico_baixo": 5.0,
        "ideal_min": 15.0,
        "ideal_max": 40.0,
        "critico_alto": 60.0,
        "unidade": "mg/kg"
    },
    "potassio": {
        "critico_baixo": 50.0,
        "ideal_min": 100.0,
        "ideal_max": 200.0,
        "critico_alto": 300.0,
        "unidade": "mg/kg"
    }
}

# Perfis de cenários para simulação
CENARIOS = {
    "normal":   {"umidade": (45, 65), "ph": (6.2, 6.8), "nitrogenio": (25, 45),
                 "fosforo": (18, 35), "potassio": (120, 180)},
    "seca":     {"umidade": (10, 30), "ph": (6.0, 7.2), "nitrogenio": (15, 30),
                 "fosforo": (10, 25), "potassio": (90, 150)},
    "excesso":  {"umidade": (75, 90), "ph": (5.5, 6.5), "nitrogenio": (20, 40),
                 "fosforo": (15, 30), "potassio": (100, 160)},
    "critico":  {"umidade": (8, 18),  "ph": (4.5, 5.2), "nitrogenio": (5, 12),
                 "fosforo": (3, 8),   "potassio": (30, 60)},
}


def simular_leitura(cenario="normal"):
    """Gera uma leitura de todos os sensores para um cenário."""
    faixas = CENARIOS.get(cenario, CENARIOS["normal"])
    leitura = {}
    for sensor, (vmin, vmax) in faixas.items():
        ruido = random.uniform(-0.5, 0.5)
        valor = round(random.uniform(vmin, vmax) + ruido, 2)
        leitura[sensor] = valor
    return leitura


def decisao_irrigacao(leitura):
    """
    Lógica de decisão para acionamento da bomba de irrigação.
    Retorna (bool, str) — ativa_bomba, motivo
    """
    umidade = leitura.get("umidade", 50)
    ph = leitura.get("ph", 6.5)

    if umidade < LIMIARES["umidade"]["critico_baixo"]:
        return True, f"Umidade crítica: {umidade:.1f}% < {LIMIARES['umidade']['critico_baixo']}%"
    if umidade < LIMIARES["umidade"]["ideal_min"]:
        return True, f"Umidade baixa: {umidade:.1f}% — irrigação preventiva"
    if umidade > LIMIARES["umidade"]["critico_alto"]:
        return False, f"Solo encharcado: {umidade:.1f}% — bomba DESLIGADA"
    if ph < LIMIARES["ph"]["ideal_min"] or ph > LIMIARES["ph"]["ideal_max"]:
        return False, f"pH fora do ideal: {ph:.1f} — aguardar correção do solo"
    return False, f"Solo em condição ideal: {umidade:.1f}% umidade"


def avaliar_alertas(leitura):
    """Retorna lista de alertas com (sensor, severidade, mensagem)."""
    alertas = []
    for sensor, valor in leitura.items():
        limiar = LIMIARES.get(sensor)
        if not limiar:
            continue
        unidade = limiar["unidade"]
        if valor <= limiar["critico_baixo"]:
            alertas.append((sensor, "critico",
                f"{sensor.upper()} CRÍTICO BAIXO: {valor} {unidade}. Ação imediata necessária."))
        elif valor < limiar["ideal_min"]:
            alertas.append((sensor, "aviso",
                f"{sensor.upper()} abaixo do ideal: {valor} {unidade}. Monitorar."))
        elif valor >= limiar["critico_alto"]:
            alertas.append((sensor, "critico",
                f"{sensor.upper()} CRÍTICO ALTO: {valor} {unidade}. Risco de dano ao plantio."))
        elif valor > limiar["ideal_max"]:
            alertas.append((sensor, "aviso",
                f"{sensor.upper()} acima do ideal: {valor} {unidade}. Atenção."))
    return alertas


def executar_ciclo(talhao_id=1, cenario="normal", salvar_bd=True):
    """
    Executa um ciclo completo de leitura IoT:
    - Simula sensores
    - Decide irrigação
    - Avalia alertas
    - Salva no banco (opcional)
    Retorna dicionário com todos os resultados.
    """
    leitura = simular_leitura(cenario)
    bomba, motivo_bomba = decisao_irrigacao(leitura)
    alertas = avaliar_alertas(leitura)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if salvar_bd:
        inicializar_banco()
        for sensor, valor in leitura.items():
            unidade = LIMIARES[sensor]["unidade"]
            inserir_leitura(talhao_id, sensor, valor, unidade, bomba_ativa=bomba)

    return {
        "timestamp": timestamp,
        "talhao_id": talhao_id,
        "cenario": cenario,
        "leitura": leitura,
        "bomba_ativa": bomba,
        "motivo_bomba": motivo_bomba,
        "alertas": alertas,
    }


def executar_multiplos_ciclos(n=10, talhao_id=1, cenario="normal", intervalo=0):
    """Executa N ciclos e retorna lista de resultados (uso em batch/dashboard)."""
    resultados = []
    for _ in range(n):
        resultado = executar_ciclo(talhao_id, cenario, salvar_bd=True)
        resultados.append(resultado)
        if intervalo > 0:
            time.sleep(intervalo)
    return resultados


if __name__ == "__main__":
    print("=== FarmTech Solutions – Simulador IoT (Fase 3) ===\n")
    inicializar_banco()
    for cenario in ["normal", "seca", "critico"]:
        print(f"--- Cenário: {cenario.upper()} ---")
        res = executar_ciclo(cenario=cenario)
        print(f"  Timestamp : {res['timestamp']}")
        for s, v in res["leitura"].items():
            print(f"  {s:12s}: {v} {LIMIARES[s]['unidade']}")
        status = "🟢 LIGADA" if res["bomba_ativa"] else "🔴 DESLIGADA"
        print(f"  Bomba     : {status}")
        print(f"  Motivo    : {res['motivo_bomba']}")
        if res["alertas"]:
            print("  Alertas   :")
            for sensor, sev, msg in res["alertas"]:
                print(f"    [{sev.upper()}] {msg}")
        print()
