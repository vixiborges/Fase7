"""
FarmTech Solutions – Dashboard Central (Fases 4 + 7)
Integra todas as fases em uma única interface Streamlit.
Execute: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import json
import math
from datetime import datetime, timedelta
import random

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(__file__)
sys.path.insert(0, ROOT)

from database.db import (
    inicializar_banco, listar_plantios, inserir_plantio, deletar_plantio,
    listar_leituras, ultima_leitura_por_sensor, listar_alertas,
    listar_deteccoes, estatisticas_gerais, listar_talhoes, inserir_alerta
)
from iot.simulador import executar_ciclo, executar_multiplos_ciclos, LIMIARES
from alertas.sns_simulado import (
    publicar_mensagem, gerar_alerta_iot, gerar_alerta_visao,
    gerar_alerta_clima, listar_log_envios
)
from weather.clima import buscar_clima_atual, buscar_previsao_7dias, alerta_climatico
from visao.detector import processar_pasta, resumo_deteccoes, gerar_imagens_exemplo, CORES_CLASSE

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="FarmTech Solutions",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] { color: #1a7a1a !important; font-size: 2rem !important; }
[data-testid="stMetricLabel"] { color: #444 !important; }
[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background-color: #f0f7f0;
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] { background-color: #1a7a1a !important; color: white !important; }
.alerta-critico {
    background: #fee2e2; border-left: 4px solid #ef4444;
    padding: 10px 14px; border-radius: 4px; margin: 4px 0;
}
.alerta-aviso {
    background: #fef9c3; border-left: 4px solid #eab308;
    padding: 10px 14px; border-radius: 4px; margin: 4px 0;
}
.alerta-info {
    background: #dbeafe; border-left: 4px solid #3b82f6;
    padding: 10px 14px; border-radius: 4px; margin: 4px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Inicialização ─────────────────────────────────────────────────────────────
inicializar_banco()
gerar_imagens_exemplo()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/wheat.png", width=80)
    st.title("🌾 FarmTech Solutions")
    st.markdown("**Sistema Integrado de Gestão Agrícola**")
    st.divider()

    stats = estatisticas_gerais()
    st.metric("Plantios", stats["total_plantios"])
    st.metric("Leituras IoT", stats["total_leituras"])
    st.metric("Alertas Pendentes", stats["alertas_pendentes"],
              delta="⚠️" if stats["alertas_pendentes"] > 0 else "✅")
    st.metric("Detecções Visão", stats["total_deteccoes"])
    st.divider()
    st.caption(f"Atualizado: {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Atualizar Painel"):
        st.rerun()

# ── Abas principais ───────────────────────────────────────────────────────────
tabs = st.tabs([
    "🏠 Visão Geral",
    "🌱 Fase 1 – Plantios",
    "🗄️ Fase 2 – Banco de Dados",
    "📡 Fase 3 – IoT",
    "📊 Fase 4 – Machine Learning",
    "☁️ Fase 5 – Alertas SNS",
    "👁️ Fase 6 – Visão Computacional",
    "🌤️ Clima"
])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 0 – VISÃO GERAL
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.header("🏠 Visão Geral da Fazenda")
    st.markdown("Painel consolidado de todas as fases do sistema FarmTech Solutions.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🌱 Plantios", stats["total_plantios"])
    c2.metric("💧 Leituras IoT", stats["total_leituras"])
    c3.metric("🔔 Alertas", stats["total_alertas"])
    c4.metric("👁️ Detecções", stats["total_deteccoes"])
    c5.metric("🪣 Insumo Total", f"{stats['insumo_total_litros']:.0f} L")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📡 Status dos Sensores (Última Leitura)")
        ultima = ultima_leitura_por_sensor(talhao_id=1)
        if ultima:
            rows = []
            for sensor, dados in ultima.items():
                limiar = LIMIARES.get(sensor, {})
                ideal_min = limiar.get("ideal_min", 0)
                ideal_max = limiar.get("ideal_max", 999)
                v = dados["valor"]
                status = "✅" if ideal_min <= v <= ideal_max else ("🔴" if v < ideal_min * 0.7 or v > ideal_max * 1.3 else "⚠️")
                rows.append({"Sensor": sensor.title(), "Valor": f"{v} {dados['unidade']}",
                             "Status": status, "Bomba": "🟢" if dados["bomba_ativa"] else "⚫"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma leitura IoT registrada. Acesse a aba Fase 3 para simular.")

    with col_right:
        st.subheader("🔔 Últimos Alertas")
        alertas = listar_alertas()[:6]
        if alertas:
            for a in alertas:
                classe = f"alerta-{a['severidade']}"
                icone = {"critico": "🔴", "aviso": "⚠️", "info": "ℹ️"}.get(a["severidade"], "•")
                st.markdown(
                    f'<div class="{classe}">{icone} <b>[{a["tipo"].upper()}]</b> {a["mensagem"]}<br>'
                    f'<small>{a["criado_em"]}</small></div>',
                    unsafe_allow_html=True
                )
        else:
            st.success("✅ Nenhum alerta pendente.")

    st.divider()
    st.subheader("📈 Histórico de Leituras IoT")
    leituras = listar_leituras(100)
    if leituras:
        df_l = pd.DataFrame(leituras)
        df_l["lido_em"] = pd.to_datetime(df_l["lido_em"])
        sensor_sel = st.selectbox("Sensor", df_l["sensor"].unique().tolist(), key="vg_sensor")
        df_s = df_l[df_l["sensor"] == sensor_sel].sort_values("lido_em")
        fig = px.line(df_s, x="lido_em", y="valor", title=f"Histórico – {sensor_sel.title()}",
                      color_discrete_sequence=["#1a7a1a"])
        unidade = LIMIARES.get(sensor_sel, {}).get("unidade", "")
        fig.update_yaxes(title=unidade)
        limiar = LIMIARES.get(sensor_sel, {})
        if "ideal_min" in limiar:
            fig.add_hline(y=limiar["ideal_min"], line_dash="dash", line_color="orange",
                          annotation_text="Mín. ideal")
            fig.add_hline(y=limiar["ideal_max"], line_dash="dash", line_color="orange",
                          annotation_text="Máx. ideal")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Simule leituras IoT na aba Fase 3 para ver o histórico aqui.")


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 1 – FASE 1: PLANTIOS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.header("🌱 Fase 1 – Gestão de Plantios e Insumos")
    st.markdown("""
    Cálculo de área, número de ruas e consumo de insumos.
    Base de dados inicial que alimenta todo o ecossistema FarmTech.
    """)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("➕ Novo Plantio")
        talhoes = listar_talhoes()
        talhao_opts = {t["nome"]: t["id"] for t in talhoes}
        talhao_nome = st.selectbox("Talhão", list(talhao_opts.keys()))
        talhao_id = talhao_opts[talhao_nome]

        cultura = st.selectbox("Cultura", ["soja", "milho"])
        formato = st.radio("Formato da área", ["retangular", "circular"], horizontal=True)

        if formato == "retangular":
            comp = st.number_input("Comprimento (m)", min_value=1.0, value=100.0)
            larg = st.number_input("Largura (m)", min_value=1.0, value=40.0)
            area = comp * larg
            largura_calc = larg
        else:
            raio = st.number_input("Raio (m)", min_value=1.0, value=60.0)
            area = math.pi * raio ** 2
            largura_calc = raio * 2

        st.info(f"📐 Área calculada: **{area:.2f} m²**")

        espacamento = st.number_input("Espaçamento entre ruas (m)", min_value=0.1, value=0.5)
        ruas = int(largura_calc // espacamento)
        st.info(f"🌿 Número de ruas: **{ruas}**")

        insumo_rua = st.number_input("Insumo por rua (L)", min_value=0.1, value=4.0)
        insumo_total = ruas * insumo_rua
        st.success(f"🪣 Insumo total: **{insumo_total:.2f} L**")

        if st.button("💾 Salvar Plantio", type="primary"):
            inserir_plantio(talhao_id, cultura, area, ruas, insumo_rua)
            st.success("Plantio salvo com sucesso!")
            st.rerun()

    with col2:
        st.subheader("📋 Plantios Registrados")
        plantios = listar_plantios()
        if plantios:
            df_p = pd.DataFrame(plantios)
            df_p["area_m2"] = df_p["area_m2"].round(2)
            df_p["insumo_total"] = df_p["insumo_total"].round(2)
            st.dataframe(
                df_p[["id", "talhao", "cultura", "area_m2", "ruas", "insumo_total", "data_plantio"]],
                use_container_width=True, hide_index=True
            )

            # Gráfico de insumo por cultura
            fig_p = px.bar(df_p, x="cultura", y="insumo_total", color="cultura",
                           title="Insumo Total por Cultura (L)",
                           color_discrete_map={"soja": "#1a7a1a", "milho": "#f59e0b"})
            st.plotly_chart(fig_p, use_container_width=True)

            st.subheader("🗑️ Remover Plantio")
            ids = [str(p["id"]) for p in plantios]
            del_id = st.selectbox("ID do plantio", ids)
            if st.button("Remover", type="secondary"):
                deletar_plantio(int(del_id))
                st.warning(f"Plantio #{del_id} removido.")
                st.rerun()
        else:
            st.info("Nenhum plantio registrado ainda. Use o formulário ao lado.")

    # Análise R
    st.divider()
    st.subheader("📊 Análise Estatística (R)")
    st.markdown("O script `estatisticas.R` realiza análise descritiva dos plantios exportados para CSV.")
    with st.expander("Ver código R"):
        with open(os.path.join(ROOT, "estatisticas.R"), "r") as f:
            st.code(f.read(), language="r")

    if st.button("▶️ Exportar plantios.csv e executar análise R"):
        import csv
        csv_path = os.path.join(ROOT, "plantios.csv")
        campos = ["cultura", "area_m2", "ruas", "insumo_por_rua", "insumo_total"]
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=campos)
            writer.writeheader()
            for p in listar_plantios():
                writer.writerow({k: p[k] for k in campos})
        st.success(f"✅ plantios.csv exportado com {len(listar_plantios())} registros.")
        import subprocess
        result = subprocess.run(["Rscript", os.path.join(ROOT, "estatisticas.R")],
                                capture_output=True, text=True)
        if result.returncode == 0:
            st.code(result.stdout, language="text")
        else:
            st.warning("R não encontrado. Instale R para executar o script.")
            st.caption(result.stderr[:300] if result.stderr else "")


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 2 – FASE 2: BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.header("🗄️ Fase 2 – Banco de Dados Estruturado (SQLite)")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📐 MER — Modelo Entidade-Relacionamento")
        st.markdown("""
        ```
        CULTURAS ──< PLANTIOS >── TALHOES
                                     │
                               LEITURAS_IOT
        
        ALERTAS  (gerados pelo sistema)
        DETECCOES_VISAO (Fase 6)
        ```
        **Entidades principais:**
        - **culturas**: soja, milho, etc.
        - **talhões**: áreas físicas da fazenda
        - **plantios**: registro de cada ciclo de plantio
        - **leituras_iot**: histórico dos sensores (Fase 3)
        - **alertas**: mensagens geradas (Fase 5)
        - **detecções_visão**: resultados YOLO (Fase 6)
        """)

    with col2:
        st.subheader("📄 Schema SQL")
        with open(os.path.join(ROOT, "database/schema.sql"), "r") as f:
            st.code(f.read(), language="sql")

    st.divider()
    st.subheader("📊 Tabelas do Banco")

    tab_db1, tab_db2, tab_db3 = st.tabs(["Plantios", "Leituras IoT", "Alertas"])
    with tab_db1:
        df = pd.DataFrame(listar_plantios())
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.info("Vazio")
    with tab_db2:
        df = pd.DataFrame(listar_leituras(50))
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.info("Vazio")
    with tab_db3:
        df = pd.DataFrame(listar_alertas())
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.info("Vazio")


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 3 – FASE 3: IoT
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.header("📡 Fase 3 – Simulador IoT")
    st.markdown("""
    Simula sensores de **umidade**, **pH**, **nitrogênio**, **fósforo** e **potássio**
    com lógica automática de ativação da bomba de irrigação.
    """)

    col1, col2 = st.columns([1, 1])
    with col1:
        cenario = st.selectbox("Cenário de simulação", ["normal", "seca", "excesso", "critico"],
                               format_func=lambda x: {"normal": "🌿 Normal",
                                                       "seca": "🏜️ Seca",
                                                       "excesso": "🌊 Excesso de água",
                                                       "critico": "🚨 Crítico"}[x])
        n_ciclos = st.slider("Número de ciclos a simular", 1, 50, 10)
        talhao_id = st.selectbox("Talhão", [t["id"] for t in listar_talhoes()],
                                 format_func=lambda i: next(t["nome"] for t in listar_talhoes() if t["id"] == i))

        col_btn1, col_btn2 = st.columns(2)
        simular = col_btn1.button("▶️ Simular", type="primary")
        simular_alertas = col_btn2.button("🔔 Simular + Alertar")

    with col2:
        st.subheader("📏 Limiares Agronômicos")
        rows_lim = []
        for sensor, lim in LIMIARES.items():
            rows_lim.append({
                "Sensor": sensor.title(),
                "Crítico ↓": lim["critico_baixo"],
                "Ideal Min": lim["ideal_min"],
                "Ideal Max": lim["ideal_max"],
                "Crítico ↑": lim["critico_alto"],
                "Unidade": lim["unidade"]
            })
        st.dataframe(pd.DataFrame(rows_lim), use_container_width=True, hide_index=True)

    if simular or simular_alertas:
        resultados = executar_multiplos_ciclos(n_ciclos, talhao_id, cenario)
        st.success(f"✅ {n_ciclos} ciclos simulados e salvos no banco de dados.")

        # Último ciclo
        ultimo = resultados[-1]
        st.subheader("🔍 Última Leitura")
        cols = st.columns(5)
        sensores_ordem = ["umidade", "ph", "nitrogenio", "fosforo", "potassio"]
        for i, sensor in enumerate(sensores_ordem):
            v = ultimo["leitura"].get(sensor, 0)
            unidade = LIMIARES[sensor]["unidade"]
            cols[i].metric(sensor.title(), f"{v} {unidade}")

        bomba_status = "🟢 LIGADA" if ultimo["bomba_ativa"] else "🔴 DESLIGADA"
        st.info(f"**Bomba de Irrigação:** {bomba_status} — {ultimo['motivo_bomba']}")

        if ultimo["alertas"]:
            st.warning(f"⚠️ {len(ultimo['alertas'])} alerta(s) nesta leitura:")
            for sensor, sev, msg in ultimo["alertas"]:
                st.markdown(f'<div class="alerta-{sev}">• {msg}</div>', unsafe_allow_html=True)

        if simular_alertas and ultimo["alertas"]:
            enviados = gerar_alerta_iot(ultimo["leitura"], ultimo["bomba_ativa"], ultimo["alertas"])
            st.success(f"📨 {len(enviados)} alerta(s) publicados no SNS simulado.")

        # Gráfico dos ciclos
        st.subheader("📈 Leituras por Ciclo")
        dados_plot = []
        for i, r in enumerate(resultados):
            for sensor, valor in r["leitura"].items():
                dados_plot.append({"Ciclo": i + 1, "Sensor": sensor.title(), "Valor": valor})
        df_plot = pd.DataFrame(dados_plot)
        sensor_plot = st.selectbox("Sensor para gráfico", df_plot["Sensor"].unique().tolist())
        fig_iot = px.line(df_plot[df_plot["Sensor"] == sensor_plot],
                          x="Ciclo", y="Valor", title=f"{sensor_plot} — {n_ciclos} ciclos",
                          color_discrete_sequence=["#1a7a1a"])
        limiar = LIMIARES.get(sensor_plot.lower(), {})
        if "ideal_min" in limiar:
            fig_iot.add_hline(y=limiar["ideal_min"], line_dash="dash", line_color="orange")
            fig_iot.add_hline(y=limiar["ideal_max"], line_dash="dash", line_color="orange")
        st.plotly_chart(fig_iot, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 4 – FASE 4: MACHINE LEARNING
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.header("📊 Fase 4 – Machine Learning e Data Science")
    st.markdown("Análise preditiva de irrigação usando Random Forest (scikit-learn).")

    leituras_bd = listar_leituras(200)
    if len(leituras_bd) < 10:
        st.warning("Simule ao menos 10 ciclos IoT (Fase 3) para treinar o modelo.")
    else:
        df_ml = pd.DataFrame(leituras_bd)
        df_ml["lido_em"] = pd.to_datetime(df_ml["lido_em"])

        # Pivota sensores por timestamp aproximado
        df_pivot = df_ml.pivot_table(
            index="lido_em", columns="sensor", values="valor", aggfunc="mean"
        ).reset_index().dropna()

        if len(df_pivot) >= 10 and "umidade" in df_pivot.columns:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score

            features = [c for c in ["umidade", "ph", "nitrogenio", "fosforo", "potassio"]
                        if c in df_pivot.columns]
            X = df_pivot[features]
            y = (df_pivot["umidade"] < 40).astype(int)  # 1 = irrigar

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3,
                                                                  random_state=42)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🌲 Random Forest")
                rf = RandomForestClassifier(n_estimators=100, random_state=42)
                rf.fit(X_train, y_train)
                acc_rf = accuracy_score(y_test, rf.predict(X_test))
                st.metric("Acurácia", f"{acc_rf:.1%}")

                # Importância de features
                fi = pd.DataFrame({"Feature": features,
                                   "Importância": rf.feature_importances_}).sort_values(
                    "Importância", ascending=True)
                fig_fi = px.bar(fi, x="Importância", y="Feature", orientation="h",
                                title="Importância das Features",
                                color_discrete_sequence=["#1a7a1a"])
                st.plotly_chart(fig_fi, use_container_width=True)

            with col2:
                st.subheader("📈 Gradient Boosting")
                gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
                gb.fit(X_train, y_train)
                acc_gb = accuracy_score(y_test, gb.predict(X_test))
                st.metric("Acurácia", f"{acc_gb:.1%}")

                # Predição interativa
                st.subheader("🔮 Predição em Tempo Real")
                pred_input = {}
                for f in features:
                    lim = LIMIARES.get(f, {})
                    pred_input[f] = st.slider(
                        f"{f.title()} ({lim.get('unidade', '')})",
                        float(lim.get("critico_baixo", 0)),
                        float(lim.get("critico_alto", 100)),
                        float((lim.get("ideal_min", 0) + lim.get("ideal_max", 100)) / 2),
                        key=f"pred_{f}"
                    )
                pred_df = pd.DataFrame([pred_input])
                pred_rf = rf.predict(pred_df)[0]
                pred_prob = rf.predict_proba(pred_df)[0][1]
                if pred_rf == 1:
                    st.error(f"💧 **IRRIGAR** — probabilidade: {pred_prob:.0%}")
                else:
                    st.success(f"✅ **NÃO IRRIGAR** — probabilidade de irrigar: {pred_prob:.0%}")
        else:
            st.info("Dados insuficientes para o modelo. Simule mais ciclos na Fase 3.")


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 5 – FASE 5: ALERTAS SNS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.header("☁️ Fase 5 – Alertas AWS SNS (Simulado)")
    st.markdown("""
    Serviço de mensageria simulado localmente com a estrutura do **AWS SNS**.
    Registra todos os alertas em `alertas/alertas_log.json`.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📨 Publicar Alerta Manual")
        tipo_alerta = st.selectbox("Tipo", ["iot", "clima", "visao", "sistema"])
        sev_alerta = st.selectbox("Severidade", ["info", "aviso", "critico"])
        msg_alerta = st.text_area("Mensagem",
            "Sensor de umidade leu valor abaixo do limiar crítico. Verificar irrigação.")
        if st.button("📤 Publicar no SNS", type="primary"):
            payload = publicar_mensagem(tipo_alerta, sev_alerta, msg_alerta)
            st.success(f"✅ Publicado! MessageId: `{payload['MessageId']}`")
            st.json(payload)

    with col2:
        st.subheader("🏗️ Tópicos SNS Configurados")
        topicos_info = [
            {"Tópico": "farmtech-critico", "ARN (simulado)": "arn:aws:sns:…:farmtech-critico",
             "Destinatários": "gestor@farmtech.com.br | SMS"},
            {"Tópico": "farmtech-aviso",   "ARN (simulado)": "arn:aws:sns:…:farmtech-aviso",
             "Destinatários": "operador@farmtech.com.br"},
            {"Tópico": "farmtech-info",    "ARN (simulado)": "arn:aws:sns:…:farmtech-info",
             "Destinatários": "relatorios@farmtech.com.br"},
        ]
        st.dataframe(pd.DataFrame(topicos_info), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📋 Log de Envios (alertas_log.json)")
    envios = listar_log_envios(20)
    if envios:
        df_log = pd.DataFrame(envios)
        colunas = ["timestamp", "tipo", "severidade", "mensagem", "status"]
        colunas_disp = [c for c in colunas if c in df_log.columns]
        st.dataframe(df_log[colunas_disp], use_container_width=True, hide_index=True)

        # Gráfico de distribuição
        fig_sns = px.pie(df_log, names="severidade", title="Alertas por Severidade",
                         color_discrete_map={"critico": "#ef4444",
                                             "aviso": "#eab308",
                                             "info": "#3b82f6"})
        st.plotly_chart(fig_sns, use_container_width=True)
    else:
        st.info("Nenhum alerta publicado ainda. Use o formulário acima ou simule dados IoT.")


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 6 – FASE 6: VISÃO COMPUTACIONAL
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.header("👁️ Fase 6 – Visão Computacional (YOLOv5)")
    st.markdown("""
    Detecta **pragas**, **doenças** e **crescimento irregular** em imagens de lavoura.
    Usa imagens estáticas da pasta `assets/sample_images/`.
    """)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("⚙️ Configurações")
        pasta_custom = st.text_input("Pasta de imagens",
                                     value=os.path.join(ROOT, "assets/sample_images"))
        st.info("💡 Para usar YOLOv5 real, instale: `pip install torch torchvision yolov5`")
        gerar_img = st.checkbox("Gerar imagens de exemplo se pasta vazia", value=True)
        enviar_alertas_visao = st.checkbox("Publicar alertas no SNS ao detectar problemas", value=True)
        processar = st.button("🔍 Processar Imagens", type="primary")

    with col2:
        if processar:
            if gerar_img:
                gerar_imagens_exemplo()
            with st.spinner("Processando imagens..."):
                resultados = processar_pasta(pasta_custom)

            if not resultados:
                st.warning("Nenhuma imagem encontrada. Adicione imagens à pasta.")
            else:
                resumo = resumo_deteccoes(resultados)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🖼️ Imagens", len(resultados))
                c2.metric("🔍 Detecções", resumo["total"])
                c3.metric("✅ Saudável", f"{resumo['percentual_saudavel']}%")
                c4.metric("⚠️ Problemas", sum(1 for r in resultados if r["tem_problema"]))

                st.subheader("📋 Resultados por Imagem")
                for r in resultados:
                    with st.expander(f"📷 {r['imagem']} — {len(r['deteccoes'])} detecção(ões)"):
                        for d in r["deteccoes"]:
                            cor = CORES_CLASSE.get(d["classe"], (128, 128, 128))
                            hex_cor = "#{:02x}{:02x}{:02x}".format(*cor)
                            st.markdown(
                                f'<span style="background:{hex_cor};color:white;padding:3px 8px;'
                                f'border-radius:4px;font-size:0.85em;">'
                                f'{d["classe"].upper()}</span> '
                                f'Confiança: **{d["confianca"]:.1%}** | '
                                f'BBox: {d["bbox"]}',
                                unsafe_allow_html=True
                            )
                        if enviar_alertas_visao and r["tem_problema"]:
                            enviados = gerar_alerta_visao(r)
                            if enviados:
                                st.caption(f"📨 {len(enviados)} alerta(s) publicados no SNS.")

                # Gráfico de classes
                df_cls = pd.DataFrame([
                    {"Classe": k.title(), "Contagem": v}
                    for k, v in resumo["por_classe"].items()
                ])
                fig_v = px.bar(df_cls, x="Classe", y="Contagem",
                               title="Distribuição de Detecções por Classe",
                               color="Classe",
                               color_discrete_map={
                                   "Saudavel": "#22c55e", "Praga": "#ef4444",
                                   "Doenca": "#eab308", "Crescimento_Irregular": "#f97316"
                               })
                st.plotly_chart(fig_v, use_container_width=True)
        else:
            st.info("Clique em **Processar Imagens** para iniciar a análise.")

    # Upload de imagem personalizada
    st.divider()
    st.subheader("📤 Testar com Imagem Própria")
    uploaded = st.file_uploader("Faça upload de uma imagem da lavoura",
                                 type=["jpg", "jpeg", "png"])
    if uploaded:
        import tempfile
        from PIL import Image as PILImage
        img_pil = PILImage.open(uploaded)
        st.image(img_pil, caption="Imagem carregada", use_container_width=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img_pil.save(tmp.name)
            from visao.detector import processar_imagem
            dets, modo = processar_imagem(tmp.name)
        st.markdown(f"**Modo:** `{modo}` | **Detecções:** {len(dets)}")
        for d in dets:
            st.write(f"- `{d['classe'].upper()}` — {d['confianca']:.1%}")


# ═══════════════════════════════════════════════════════════════════════════════
# ABA 7 – CLIMA
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.header("🌤️ Meteorologia – Open-Meteo API")
    st.markdown("Dados climáticos em tempo real para **Ribeirão Preto – SP** (gratuito, sem chave).")

    if st.button("🔄 Buscar Dados Meteorológicos", type="primary"):
        with st.spinner("Consultando Open-Meteo..."):
            clima = buscar_clima_atual()
            previsao = buscar_previsao_7dias()

        if clima.get("sucesso"):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("🌡️ Temperatura", f"{clima['temperatura']} °C")
            c2.metric("💧 Umidade", f"{clima['umidade']} %")
            c3.metric("🌧️ Precipitação", f"{clima['precipitacao']} mm")
            c4.metric("💨 Vento", f"{clima['vento']} km/h")
            c5.metric("⛅ Tempo", clima["descricao"])

            # Alertas climáticos
            alertas_clim = alerta_climatico(clima)
            if alertas_clim:
                st.warning("**Alertas Climáticos:**")
                for titulo, acao in alertas_clim:
                    st.markdown(f'<div class="alerta-aviso">**{titulo}**: {acao}</div>',
                                unsafe_allow_html=True)
                if st.button("📨 Publicar alertas climáticos no SNS"):
                    enviados = gerar_alerta_clima(alertas_clim)
                    st.success(f"{len(enviados)} alertas publicados.")
            else:
                st.success("✅ Condições climáticas favoráveis.")

            # Previsão 7 dias
            if previsao.get("sucesso") and previsao["previsao"]:
                st.subheader("📅 Previsão 7 Dias")
                df_prev = pd.DataFrame(previsao["previsao"])
                fig_prev = go.Figure()
                fig_prev.add_trace(go.Scatter(x=df_prev["data"], y=df_prev["temp_max"],
                                              name="Temp. Máx.", line=dict(color="#ef4444")))
                fig_prev.add_trace(go.Scatter(x=df_prev["data"], y=df_prev["temp_min"],
                                              name="Temp. Mín.", line=dict(color="#3b82f6")))
                fig_prev.add_trace(go.Bar(x=df_prev["data"], y=df_prev["precipitacao"],
                                          name="Precipitação (mm)", yaxis="y2",
                                          marker_color="#60a5fa", opacity=0.5))
                fig_prev.update_layout(
                    title="Temperatura e Precipitação — 7 dias",
                    yaxis=dict(title="Temperatura (°C)"),
                    yaxis2=dict(title="Precipitação (mm)", overlaying="y", side="right"),
                    legend=dict(orientation="h")
                )
                st.plotly_chart(fig_prev, use_container_width=True)
                st.dataframe(df_prev, use_container_width=True, hide_index=True)
        else:
            st.error(f"Erro ao buscar clima: {clima.get('erro', 'desconhecido')}")
            st.info("Verifique sua conexão com a internet.")
