-- ============================================================
-- FarmTech Solutions – Fase 2
-- MER/DER: Banco de Dados Relacional (SQLite)
-- ============================================================
-- ENTIDADES:
--   culturas        → tipos de cultura disponíveis
--   talhoes         → áreas de plantio (talhões da fazenda)
--   plantios        → registro de cada plantio por talhão
--   leituras_iot    → histórico de sensores IoT (Fase 3)
--   alertas         → alertas gerados pelo sistema (Fase 5)
--   deteccoes_visao → resultados da visão computacional (Fase 6)
-- ============================================================

CREATE TABLE IF NOT EXISTS culturas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL UNIQUE,  -- ex: soja, milho
    descricao   TEXT,
    criado_em   TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS talhoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,         -- ex: Talhão A1
    area_m2     REAL    NOT NULL,
    formato     TEXT    DEFAULT 'retangular', -- retangular | circular
    criado_em   TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plantios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id       INTEGER NOT NULL REFERENCES talhoes(id),
    cultura_id      INTEGER NOT NULL REFERENCES culturas(id),
    area_m2         REAL    NOT NULL,
    ruas            INTEGER NOT NULL,
    insumo_por_rua  REAL    NOT NULL,
    insumo_total    REAL    NOT NULL,
    data_plantio    TEXT    DEFAULT (date('now')),
    criado_em       TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leituras_iot (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    talhao_id   INTEGER REFERENCES talhoes(id),
    sensor      TEXT    NOT NULL,   -- umidade | ph | nitrogenio | fosforo | potassio
    valor       REAL    NOT NULL,
    unidade     TEXT    NOT NULL,   -- % | pH | mg/kg
    bomba_ativa INTEGER DEFAULT 0,  -- 0=desligada 1=ligada
    lido_em     TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alertas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo        TEXT    NOT NULL,   -- iot | clima | visao
    severidade  TEXT    NOT NULL,   -- info | aviso | critico
    mensagem    TEXT    NOT NULL,
    enviado     INTEGER DEFAULT 0,  -- 0=pendente 1=enviado
    criado_em   TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS deteccoes_visao (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    imagem      TEXT    NOT NULL,
    classe      TEXT    NOT NULL,   -- saudavel | praga | doenca | crescimento_irregular
    confianca   REAL    NOT NULL,
    bbox        TEXT,               -- JSON: [x1,y1,x2,y2]
    processado_em TEXT DEFAULT (datetime('now'))
);

-- Dados iniciais de culturas
INSERT OR IGNORE INTO culturas (nome, descricao) VALUES
    ('soja',  'Glycine max – principal oleaginosa do Brasil'),
    ('milho', 'Zea mays – cereal essencial para ração e etanol');

-- Talhão padrão
INSERT OR IGNORE INTO talhoes (id, nome, area_m2, formato) VALUES
    (1, 'Talhão A1', 4000.0,  'retangular'),
    (2, 'Talhão B1', 11309.7, 'circular');
