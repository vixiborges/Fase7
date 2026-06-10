"""
FarmTech Solutions – Fase 5
Serviço de Mensageria AWS SNS — Simulado Localmente
Simula SNS com boto3 + moto (ou filesystem fallback) sem conta AWS real.
Gera log de "e-mails/SMS enviados" em alertas_log.json
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import inserir_alerta, listar_alertas, marcar_alerta_enviado, inicializar_banco

LOG_PATH = os.path.join(os.path.dirname(__file__), "alertas_log.json")

# ── Configuração simulada de tópicos SNS ──────────────────────────────────────
TOPICOS = {
    "critico": {
        "arn": "arn:aws:sns:us-east-1:000000000000:farmtech-critico",
        "descricao": "Alertas críticos — requer ação imediata",
        "destinatarios": ["gestor@farmtech.com.br", "+55119999-0000"]
    },
    "aviso": {
        "arn": "arn:aws:sns:us-east-1:000000000000:farmtech-aviso",
        "descricao": "Avisos de monitoramento",
        "destinatarios": ["operador@farmtech.com.br"]
    },
    "info": {
        "arn": "arn:aws:sns:us-east-1:000000000000:farmtech-info",
        "descricao": "Informações gerais do sistema",
        "destinatarios": ["relatorios@farmtech.com.br"]
    }
}


def _carregar_log():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _salvar_log(log):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def _tentar_boto3_moto():
    """Tenta usar boto3 + moto para simular SNS real. Retorna cliente ou None."""
    try:
        import boto3
        from moto import mock_sns
        return True
    except ImportError:
        return False


def publicar_mensagem(tipo, severidade, mensagem, salvar_bd=True):
    """
    Publica uma mensagem no tópico SNS correspondente à severidade.
    - Salva no banco de dados
    - Registra no log local (alertas_log.json)
    - Simula envio de e-mail/SMS
    Retorna dict com detalhes do envio simulado.
    """
    if salvar_bd:
        inicializar_banco()
        inserir_alerta(tipo, severidade, mensagem)

    topico = TOPICOS.get(severidade, TOPICOS["info"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Monta payload simulado
    payload = {
        "MessageId": f"msg-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "TopicArn": topico["arn"],
        "timestamp": timestamp,
        "tipo": tipo,
        "severidade": severidade,
        "mensagem": mensagem,
        "destinatarios": topico["descricao"],
        "status": "ENVIADO (simulado)",
        "canal": "e-mail + SMS"
    }

    # Registra no log
    log = _carregar_log()
    log.append(payload)
    _salvar_log(log)

    return payload


def processar_fila_pendente():
    """
    Verifica alertas não enviados no banco e os publica.
    Retorna quantidade de alertas processados.
    """
    inicializar_banco()
    pendentes = listar_alertas(apenas_pendentes=True)
    enviados = 0
    for alerta in pendentes:
        publicar_mensagem(
            alerta["tipo"],
            alerta["severidade"],
            alerta["mensagem"],
            salvar_bd=False
        )
        marcar_alerta_enviado(alerta["id"])
        enviados += 1
    return enviados


def listar_log_envios(limite=20):
    """Retorna os últimos N envios registrados no log."""
    log = _carregar_log()
    return log[-limite:][::-1]  # mais recentes primeiro


def gerar_alerta_iot(leitura, bomba_ativa, alertas_sensores):
    """
    Gera e publica alertas a partir de leitura IoT.
    Retorna lista de mensagens publicadas.
    """
    publicados = []
    for sensor, severidade, msg in alertas_sensores:
        payload = publicar_mensagem("iot", severidade, msg)
        publicados.append(payload)

    if bomba_ativa:
        payload = publicar_mensagem(
            "iot", "info",
            f"Bomba de irrigação ATIVADA automaticamente. "
            f"Umidade: {leitura.get('umidade', '?')}%"
        )
        publicados.append(payload)

    return publicados


def gerar_alerta_visao(resultado_imagem):
    """
    Gera e publica alertas a partir de detecção de visão computacional.
    """
    publicados = []
    for det in resultado_imagem.get("deteccoes", []):
        if det["classe"] == "saudavel":
            continue
        sev = "critico" if det["confianca"] > 0.80 else "aviso"
        msg = (
            f"Visão Computacional detectou '{det['classe'].upper()}' "
            f"na imagem {resultado_imagem['imagem']} "
            f"(confiança: {det['confianca']:.0%}). "
            f"Inspecione o talhão imediatamente."
        )
        payload = publicar_mensagem("visao", sev, msg)
        publicados.append(payload)
    return publicados


def gerar_alerta_clima(alertas_climaticos):
    """Gera alertas a partir de condições climáticas adversas."""
    publicados = []
    for titulo, acao in alertas_climaticos:
        msg = f"{titulo}: {acao}"
        payload = publicar_mensagem("clima", "aviso", msg)
        publicados.append(payload)
    return publicados


if __name__ == "__main__":
    print("=== FarmTech Solutions – SNS Simulado (Fase 5) ===\n")
    inicializar_banco()

    # Testa publicação em cada tópico
    testes = [
        ("iot",   "critico", "pH CRÍTICO BAIXO: 4.8 pH. Correção imediata de acidez necessária."),
        ("visao", "aviso",   "Praga detectada com 73% de confiança na imagem lavoura_01.jpg"),
        ("clima", "aviso",   "🌧️ CHUVA FORTE: Suspenda irrigação e aplicação de defensivos."),
    ]
    for tipo, sev, msg in testes:
        payload = publicar_mensagem(tipo, sev, msg)
        print(f"✅ [{sev.upper():8s}] {msg[:70]}...")
        print(f"   MessageId: {payload['MessageId']}")
        print(f"   Tópico   : {payload['TopicArn']}")
        print()

    print(f"Log salvo em: {LOG_PATH}")
    print(f"Total de envios no log: {len(_carregar_log())}")
