"""
FarmTech Solutions – Fase 2
Módulo de Banco de Dados SQLite
Fornece funções CRUD usadas por todas as outras fases.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "farmtech.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # acesso por nome de coluna
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco():
    """Cria tabelas e dados iniciais se ainda não existirem."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    with get_connection() as conn:
        conn.executescript(schema)
    return True


# ── Plantios ─────────────────────────────────────────────────────────────────

def inserir_plantio(talhao_id, cultura_nome, area, ruas, insumo_por_rua):
    insumo_total = ruas * insumo_por_rua
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM culturas WHERE nome = ?", (cultura_nome,))
        row = cur.fetchone()
        if not row:
            conn.execute("INSERT OR IGNORE INTO culturas(nome) VALUES(?)", (cultura_nome,))
            cur = conn.execute("SELECT id FROM culturas WHERE nome = ?", (cultura_nome,))
            row = cur.fetchone()
        cultura_id = row["id"]
        conn.execute(
            """INSERT INTO plantios(talhao_id, cultura_id, area_m2, ruas,
               insumo_por_rua, insumo_total) VALUES(?,?,?,?,?,?)""",
            (talhao_id, cultura_id, area, ruas, insumo_por_rua, insumo_total)
        )
    return insumo_total


def listar_plantios():
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT p.id, t.nome AS talhao, c.nome AS cultura,
                   p.area_m2, p.ruas, p.insumo_por_rua, p.insumo_total,
                   p.data_plantio
            FROM plantios p
            JOIN talhoes t ON t.id = p.talhao_id
            JOIN culturas c ON c.id = p.cultura_id
            ORDER BY p.criado_em DESC
        """)
        return [dict(r) for r in cur.fetchall()]


def deletar_plantio(plantio_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM plantios WHERE id = ?", (plantio_id,))


# ── Leituras IoT ─────────────────────────────────────────────────────────────

def inserir_leitura(talhao_id, sensor, valor, unidade, bomba_ativa=False):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO leituras_iot(talhao_id, sensor, valor, unidade, bomba_ativa)
               VALUES(?,?,?,?,?)""",
            (talhao_id, sensor, valor, unidade, int(bomba_ativa))
        )


def listar_leituras(limite=100):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT l.id, t.nome AS talhao, l.sensor, l.valor,
                   l.unidade, l.bomba_ativa, l.lido_em
            FROM leituras_iot l
            LEFT JOIN talhoes t ON t.id = l.talhao_id
            ORDER BY l.lido_em DESC LIMIT ?
        """, (limite,))
        return [dict(r) for r in cur.fetchall()]


def ultima_leitura_por_sensor(talhao_id=1):
    """Retorna o último valor de cada sensor para um talhão."""
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT sensor, valor, unidade, bomba_ativa, lido_em
            FROM leituras_iot
            WHERE talhao_id = ?
            GROUP BY sensor
            HAVING lido_em = MAX(lido_em)
        """, (talhao_id,))
        return {r["sensor"]: dict(r) for r in cur.fetchall()}


# ── Alertas ──────────────────────────────────────────────────────────────────

def inserir_alerta(tipo, severidade, mensagem):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO alertas(tipo, severidade, mensagem) VALUES(?,?,?)",
            (tipo, severidade, mensagem)
        )


def listar_alertas(apenas_pendentes=False):
    with get_connection() as conn:
        query = "SELECT * FROM alertas"
        if apenas_pendentes:
            query += " WHERE enviado = 0"
        query += " ORDER BY criado_em DESC LIMIT 50"
        cur = conn.execute(query)
        return [dict(r) for r in cur.fetchall()]


def marcar_alerta_enviado(alerta_id):
    with get_connection() as conn:
        conn.execute("UPDATE alertas SET enviado = 1 WHERE id = ?", (alerta_id,))


# ── Detecções de Visão ────────────────────────────────────────────────────────

def inserir_deteccao(imagem, classe, confianca, bbox=None):
    bbox_json = json.dumps(bbox) if bbox else None
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO deteccoes_visao(imagem, classe, confianca, bbox)
               VALUES(?,?,?,?)""",
            (imagem, classe, confianca, bbox_json)
        )


def listar_deteccoes(limite=50):
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM deteccoes_visao ORDER BY processado_em DESC LIMIT ?",
            (limite,)
        )
        return [dict(r) for r in cur.fetchall()]


# ── Utilitários ───────────────────────────────────────────────────────────────

def listar_talhoes():
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM talhoes ORDER BY id")
        return [dict(r) for r in cur.fetchall()]


def estatisticas_gerais():
    with get_connection() as conn:
        stats = {}
        stats["total_plantios"] = conn.execute("SELECT COUNT(*) FROM plantios").fetchone()[0]
        stats["total_leituras"] = conn.execute("SELECT COUNT(*) FROM leituras_iot").fetchone()[0]
        stats["total_alertas"] = conn.execute("SELECT COUNT(*) FROM alertas").fetchone()[0]
        stats["alertas_pendentes"] = conn.execute(
            "SELECT COUNT(*) FROM alertas WHERE enviado=0").fetchone()[0]
        stats["total_deteccoes"] = conn.execute("SELECT COUNT(*) FROM deteccoes_visao").fetchone()[0]
        row = conn.execute("SELECT SUM(insumo_total) FROM plantios").fetchone()
        stats["insumo_total_litros"] = row[0] or 0.0
        return stats
