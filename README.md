# 🌾 FarmTech Solutions — Fase 7

**Sistema Integrado de Gestão Agrícola**  
FIAP – Engenharia de Software | PBL – Project-Based Learning

> **Aluno:** Gustavo Borges — RM: 567477  


---

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Fases Implementadas](#fases-implementadas)
- [Como Executar](#como-executar)
- [Serviço SNS Simulado (AWS)](#serviço-sns-simulado-aws)
- [Tecnologias](#tecnologias)

---

## Visão Geral

A Fase 7 consolida todos os módulos desenvolvidos nas Fases 1 a 6 em um **único projeto Python**, acessível por um **dashboard Streamlit central** com 7 abas. Cada aba representa uma fase e pode ser operada de forma integrada.

```
┌─────────────────────────────────────────────────────────┐
│              FARMTECH SOLUTIONS — FASE 7                │
│                  Dashboard Streamlit                    │
├────────┬────────┬────────┬────────┬────────┬────────────┤
│ Fase 1 │ Fase 2 │ Fase 3 │ Fase 4 │ Fase 5 │  Fase 6   │
│Plantios│  SQLite│  IoT   │   ML   │  SNS   │   YOLO    │
└────────┴────────┴────────┴────────┴────────┴────────────┘
            ↕           ↕           ↕           ↕
      Open-Meteo    Alertas     scikit-learn  Simulação
       (clima)     log JSON     Random Forest  imagens
```

---

## Estrutura do Projeto

```
farmtech_fase7/
├── dashboard.py              # 🏠 Dashboard central (Streamlit) — PONTO DE ENTRADA
├── app.py                    # Fase 1 – CRUD terminal original
├── estatisticas.R            # Fase 1 – Análise estatística R
├── plantios.csv              # Fase 1 – Dados exportados
├── requirements.txt
├── README.md
│
├── database/
│   ├── schema.sql            # Fase 2 – DDL completo (MER/DER)
│   ├── db.py                 # Fase 2 – Módulo de acesso SQLite
│   └── farmtech.db           # Gerado automaticamente na primeira execução
│
├── iot/
│   └── simulador.py          # Fase 3 – Sensores IoT simulados + lógica de irrigação
│
├── visao/
│   └── detector.py           # Fase 6 – YOLOv5 (simulado ou real)
│
├── alertas/
│   ├── sns_simulado.py       # Fase 5 – AWS SNS simulado localmente
│   └── alertas_log.json      # Log de mensagens "enviadas"
│
├── weather/
│   └── clima.py              # Fase 1 – API Open-Meteo (gratuito, sem chave)
│
└── assets/
    └── sample_images/        # Fase 6 – Imagens para visão computacional
```

---

## Fases Implementadas

### Fase 1 – Base de Dados e API Meteorológica

- **`app.py`**: CRUD completo de plantios em terminal (soja e milho)
- **`estatisticas.R`**: Análise estatística descritiva dos plantios exportados
- **`weather/clima.py`**: Integração com [Open-Meteo](https://open-meteo.com/) — temperatura, umidade, precipitação, vento, previsão 7 dias

### Fase 2 – Banco de Dados Estruturado (SQLite)

- **`database/schema.sql`**: DDL com 6 tabelas — `culturas`, `talhoes`, `plantios`, `leituras_iot`, `alertas`, `deteccoes_visao`
- **`database/db.py`**: Módulo de acesso com funções CRUD para todas as tabelas
- MER documentado com relacionamentos 1:N

### Fase 3 – IoT e Automação

- **`iot/simulador.py`**: Simula 5 sensores (umidade, pH, N, P, K)
- Lógica de decisão para bomba de irrigação baseada em limiares agronômicos
- 4 cenários: normal, seca, excesso d'água, crítico
- Salva histórico completo no banco SQLite

### Fase 4 – Dashboard e Machine Learning

- **`dashboard.py`**: Interface Streamlit com 8 abas
- Modelos: **Random Forest** e **Gradient Boosting** (scikit-learn)
- Predição em tempo real com sliders interativos
- Importância de features por sensor

### Fase 5 – Cloud Computing e Mensageria (SNS Simulado)

- **`alertas/sns_simulado.py`**: Simula AWS SNS localmente
- 3 tópicos: `farmtech-critico`, `farmtech-aviso`, `farmtech-info`
- Registra todos os "envios" em `alertas_log.json`
- Alertas disparados por: leituras IoT críticas, detecções de visão, condições climáticas adversas

### Fase 6 – Visão Computacional

- **`visao/detector.py`**: Detecção de pragas, doenças e crescimento irregular
- Funciona com YOLOv5 real (se PyTorch disponível) ou inferência simulada
- Processa imagens da pasta `assets/sample_images/`
- Upload de imagem própria disponível no dashboard

---

## Como Executar

### Pré-requisitos

```bash
python 3.10+
pip install -r requirements.txt
```

### Iniciar o Dashboard

```bash
cd farmtech_fase7
streamlit run dashboard.py
```

O banco de dados SQLite (`farmtech.db`) é criado automaticamente na primeira execução.

### Executar módulos individualmente (terminal)

```bash
# Fase 1 – CRUD terminal
python app.py

# Fase 3 – Simulador IoT
python iot/simulador.py

# Fase 5 – Testar SNS simulado
python alertas/sns_simulado.py

# Fase 6 – Processar imagens
python visao/detector.py
```

---

## Serviço SNS Simulado (AWS)

O serviço de alertas simula a arquitetura do **AWS SNS** sem necessidade de conta AWS:

| Tópico | ARN Simulado | Destinatários |
|--------|-------------|---------------|
| farmtech-critico | `arn:aws:sns:us-east-1:000000000000:farmtech-critico` | gestor@farmtech.com.br + SMS |
| farmtech-aviso | `arn:aws:sns:us-east-1:000000000000:farmtech-aviso` | operador@farmtech.com.br |
| farmtech-info | `arn:aws:sns:us-east-1:000000000000:farmtech-info` | relatorios@farmtech.com.br |

**Fluxo de alertas:**

```
Sensor IoT lê valor crítico
        ↓
iot/simulador.py → avaliar_alertas()
        ↓
alertas/sns_simulado.py → publicar_mensagem()
        ↓
database/alertas (banco SQLite)
        ↓
alertas/alertas_log.json  ←  "E-mail/SMS enviado"
```

**Estrutura de uma mensagem SNS simulada:**

```json
{
  "MessageId": "msg-20250101120000123456",
  "TopicArn": "arn:aws:sns:us-east-1:000000000000:farmtech-critico",
  "timestamp": "2025-01-01 12:00:00",
  "tipo": "iot",
  "severidade": "critico",
  "mensagem": "UMIDADE CRÍTICO BAIXO: 15.3 %. Ação imediata necessária.",
  "destinatarios": "Alertas críticos — requer ação imediata",
  "status": "ENVIADO (simulado)",
  "canal": "e-mail + SMS"
}
```

---

## Tecnologias

| Tecnologia | Uso |
|-----------|-----|
| Python 3.10+ | Linguagem principal |
| Streamlit | Dashboard interativo (Fase 4/7) |
| SQLite + sqlite3 | Banco de dados (Fase 2) |
| scikit-learn | Random Forest, Gradient Boosting (Fase 4) |
| YOLOv5 / simulado | Visão computacional (Fase 6) |
| Open-Meteo API | Dados meteorológicos, gratuito (Fase 1) |
| Plotly | Gráficos interativos |
| R + ggplot2 | Análise estatística (Fase 1) |
| AWS SNS (simulado) | Mensageria de alertas (Fase 5) |
| Pillow | Processamento de imagens |
