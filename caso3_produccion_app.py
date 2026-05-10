import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MetalParts Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { color: #1e3a5f; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CARGA DE DATOS (con caché para mejor rendimiento)
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), "caso3_produccion_dataset.csv")
    df = pd.read_csv(ruta)
    df["fecha_produccion"] = pd.to_datetime(df["fecha_produccion"])
    return df

df = cargar_datos()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🏭 MetalParts")
    st.markdown("**Control de Producción 2024**")
    st.markdown("---")
    st.header("🔧 Filtros")

    lineas_sel = st.multiselect(
        "Línea de Producción",
        options=sorted(df["linea_produccion"].unique()),
        default=list(df["linea_produccion"].unique())
    )

    turnos_sel = st.multiselect(
        "Turno",
        options=sorted(df["turno"].unique()),
        default=list(df["turno"].unique())
    )

    maquinas_sel = st.multiselect(
        "Máquina",
        options=sorted(df["maquina"].unique()),
        default=list(df["maquina"].unique())
    )

    fecha_min = df["fecha_produccion"].min().date()
    fecha_max = df["fecha_produccion"].max().date()
    rango_fecha = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    st.markdown("---")
    st.caption("📅 Datos: Año 2024 | MetalParts Colombia S.A.S.")

# ═══════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ═══════════════════════════════════════════════════════════════
df_f = df.copy()
if lineas_sel:
    df_f = df_f[df_f["linea_produccion"].isin(lineas_sel)]
if turnos_sel:
    df_f = df_f[df_f["turno"].isin(turnos_sel)]
if maquinas_sel:
    df_f = df_f[df_f["maquina"].isin(maquinas_sel)]
if len(rango_fecha) == 2:
    df_f = df_f[
        (df_f["fecha_produccion"].dt.date >= rango_fecha[0]) &
        (df_f["fecha_produccion"].dt.date <= rango_fecha[1])
    ]

# ═══════════════════════════════════════════════════════════════
# TÍTULO PRINCIPAL
# ═══════════════════════════════════════════════════════════════
st.title("🏭 MetalParts — Dashboard de Control de Producción")
st.markdown("**Panel de operaciones industriales · Itagüí, Antioquia · 2024**")
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# TABS DE NAVEGACIÓN
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📊 Resumen General", "⚙️ Análisis de Producción", "⚠️ Alertas"])

# ───────────────────────────────────────────────────────────────
with tab1:
    # ── KPIs ──────────────────────────────────────────────────
    total = len(df_f)
    eficiencia_prom  = df_f["eficiencia_pct"].mean()      if total > 0 else 0
    tasa_defectos    = df_f["tasa_defectos_pct"].mean()   if total > 0 else 0
    total_unidades   = df_f["unidades_producidas"].sum()  if total > 0 else 0
    costo_total      = df_f["costo_produccion_cop"].sum() if total > 0 else 0
    paro_total       = df_f["tiempo_paro_min"].sum()      if total > 0 else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("📋 Órdenes",          f"{total:,}")
    k2.metric("⚙️ Eficiencia Prom.", f"{eficiencia_prom:.1f}%",
              delta=f"{eficiencia_prom - 75:.1f}% vs meta 75%")
    k3.metric("❌ Tasa Defectos",    f"{tasa_defectos:.2f}%")
    k4.metric("📦 Unidades Prod.",   f"{total_unidades:,.0f}")
    k5.metric("⏸️ Paro Total",       f"{paro_total/60:.0f} hrs")

    st.markdown("---")

    # ── Fila 1: Boxplot eficiencia + Pie causas de paro ───────
    col1, col2 = st.columns([1.5, 1])

    with col1:
        fig_box = px.box(
            df_f, x="linea_produccion", y="eficiencia_pct",
            color="linea_produccion",
            title="⚙️ Eficiencia por Línea de Producción (%)",
            labels={"linea_produccion": "Línea", "eficiencia_pct": "Eficiencia (%)"},
            color_discrete_sequence=px.colors.qualitative.Bold,
            points="outliers"
        )
        fig_box.add_hline(
            y=df_f["eficiencia_pct"].mean(), line_dash="dash",
            line_color="red", annotation_text="Promedio"
        )
        fig_box.update_layout(height=320, showlegend=False, margin=dict(t=40, b=20))
        st.plotly_chart(fig_box, use_container_width=True)

    with col2:
        causa_counts = df_f["causa_paro"].value_counts().reset_index()
        fig_pie = px.pie(
            causa_counts, names="causa_paro", values="count",
            title="🔍 Causas de Paro",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Fila 2: Scatter temperatura vs defectos ────────────────
    fig_scatter = px.scatter(
        df_f, x="temperatura_c", y="tasa_defectos_pct",
        color="linea_produccion",
        size="unidades_producidas",
        hover_data=["id_orden", "maquina", "turno", "producto"],
        trendline="ols",
        title="🌡️ Temperatura del Proceso vs Tasa de Defectos",
        labels={
            "temperatura_c": "Temperatura (°C)",
            "tasa_defectos_pct": "Tasa Defectos (%)",
            "linea_produccion": "Línea"
        },
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_scatter.update_layout(height=380, margin=dict(t=40, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ───────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns([1, 1.5])

    with col1:
        # Tasa de defectos por turno
        defectos_turno = (
            df_f.groupby("turno")["tasa_defectos_pct"]
            .mean().round(2).reset_index()
            .sort_values("tasa_defectos_pct", ascending=False)
        )
        fig_turno = px.bar(
            defectos_turno, x="turno", y="tasa_defectos_pct",
            color="turno",
            title="🌙 Tasa de Defectos por Turno (%)",
            labels={"turno": "Turno", "tasa_defectos_pct": "Tasa Defectos (%)"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
            text_auto=".2f"
        )
        fig_turno.update_layout(height=320, showlegend=False, margin=dict(t=40, b=20))
        st.plotly_chart(fig_turno, use_container_width=True)

    with col2:
        # Tiempo de paro por máquina (barras horizontales)
        paro_maq = (
            df_f.groupby("maquina")["tiempo_paro_min"]
            .sum().reset_index()
            .sort_values("tiempo_paro_min", ascending=True)
        )
        fig_paro = px.bar(
            paro_maq, y="maquina", x="tiempo_paro_min",
            orientation="h",
            color="tiempo_paro_min",
            color_continuous_scale="Reds",
            title="⏸️ Tiempo Total de Paro por Máquina (min)",
            labels={"maquina": "Máquina", "tiempo_paro_min": "Paro (min)"},
            text_auto=".0f"
        )
        fig_paro.update_layout(height=320, showlegend=False, margin=dict(t=40, b=20))
        st.plotly_chart(fig_paro, use_container_width=True)

    # ── Evolución semanal (línea dual eje) ─────────────────────
    st.markdown("### 📅 Evolución Semanal de Producción")
    prod_sem = (
        df_f.groupby("semana")
        .agg(
            unidades_producidas=("unidades_producidas", "sum"),
            eficiencia_prom=("eficiencia_pct", "mean")
        )
        .round(2).reset_index()
    )

    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(
        x=prod_sem["semana"], y=prod_sem["unidades_producidas"],
        name="Unidades Producidas", mode="lines+markers",
        line=dict(color="#1e3a5f", width=2), marker=dict(size=6)
    ))
    fig_linea.add_trace(go.Scatter(
        x=prod_sem["semana"], y=prod_sem["eficiencia_prom"],
        name="Eficiencia Prom (%)", mode="lines+markers",
        line=dict(color="#e67e22", width=2, dash="dot"), marker=dict(size=6),
        yaxis="y2"
    ))
    fig_linea.update_layout(
        title="Unidades Producidas y Eficiencia Promedio por Semana",
        xaxis_title="Semana del Año",
        yaxis=dict(title="Unidades Producidas"),
        yaxis2=dict(title="Eficiencia (%)", overlaying="y", side="right", range=[0, 130]),
        height=380, legend=dict(x=0.01, y=0.99), margin=dict(t=40, b=20)
    )
    st.plotly_chart(fig_linea, use_container_width=True)

    # ── Heatmap: Eficiencia por Línea y Turno ─────────────────
    st.markdown("### 🌡️ Mapa de Calor — Eficiencia Promedio por Línea y Turno")
    pivot = df_f.pivot_table(
        values="eficiencia_pct",
        index="linea_produccion",
        columns="turno",
        aggfunc="mean"
    ).round(1)

    fig_heat = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn",
        text_auto=True,
        title="Eficiencia (%) — Verde = Mayor eficiencia"
    )
    fig_heat.update_layout(height=300, margin=dict(t=40, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

# ───────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### ⚠️ Órdenes con Tasa de Defectos > 10%")

    criticas = df_f[df_f["tasa_defectos_pct"] > 10][[
        "id_orden", "fecha_produccion", "linea_produccion", "maquina",
        "turno", "producto", "tasa_defectos_pct", "causa_paro"
    ]].sort_values("tasa_defectos_pct", ascending=False)

    if len(criticas) > 0:
        st.warning(f"⚠️ Se encontraron **{len(criticas)}** órdenes con defectos críticos (>10%)")
        st.dataframe(criticas, use_container_width=True)
    else:
        st.success("✅ No hay órdenes con tasa de defectos crítica en el período seleccionado.")

    st.markdown("---")
    st.markdown("### 📋 Datos completos filtrados")
    cols_show = ["id_orden", "fecha_produccion", "linea_produccion", "producto",
                 "turno", "maquina", "unidades_planificadas", "unidades_producidas",
                 "unidades_defectuosas", "eficiencia_pct", "tasa_defectos_pct",
                 "tiempo_paro_min", "causa_paro", "costo_produccion_cop"]
    with st.expander("📋 Ver tabla completa"):
        st.dataframe(df_f[cols_show].sort_values("fecha_produccion", ascending=False),
                     use_container_width=True)

    st.download_button(
        "⬇️ Descargar CSV filtrado",
        df_f.to_csv(index=False),
        "produccion_filtrado.csv"
    )

st.caption("🔧 Desarrollado con Streamlit + Plotly | Clase de Visualización de Datos")
