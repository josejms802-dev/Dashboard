import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------
# Configuración de la Página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Epidemiológico interactivo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Función para Generación de Datos Sintéticos
# ---------------------------------------------------------
@st.cache_data
def generar_datos_epidemiologicos(n_registros=1000, seed=42):
    """
    Genera un DataFrame sintético con datos epidemiológicos realistas.
    """
    np.random.seed(seed)
    
    # Parámetros y categorías
    regiones = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
    prob_regiones = [0.35, 0.25, 0.20, 0.12, 0.08]
    
    enfermedades = ['Dengue', 'Malaria', 'COVID-19', 'Influenza AH1N1', 'Chikungunya']
    prob_enfermedades = [0.30, 0.20, 0.25, 0.15, 0.10]
    
    generos = ['Femenino', 'Masculino']
    vacunados = ['Sí', 'No', 'Incompleto']
    
    # Generación de campos
    ids = [f"PAT-{10000 + i}" for i in range(n_registros)]
    edades = np.random.gamma(shape=3.0, scale=12.0, size=n_registros).astype(int)
    edades = np.clip(edades, 0, 95)
    
    lista_generos = np.random.choice(generos, size=n_registros)
    lista_regiones = np.random.choice(regiones, p=prob_regiones, size=n_registros)
    lista_enfermedades = np.random.choice(enfermedades, p=prob_enfermedades, size=n_registros)
    lista_vacunas = np.random.choice(vacunados, p=[0.55, 0.30, 0.15], size=n_registros)
    
    # Fechas de diagnóstico en un rango determinado
    fecha_inicio = datetime(2025, 1, 1)
    dias_aleatorios = np.random.randint(0, 365, size=n_registros)
    fechas_diagnostico = [fecha_inicio + timedelta(days=int(d)) for d in dias_aleatorios]
    
    # Asignación de Severidad y Estado basada en probabilidad
    severidades = []
    estados = []
    hospitalizados = []
    uci_list = []
    
    for i in range(n_registros):
        # Mayor probabilidad de severidad en adultos mayores o según condición
        e = edades[i]
        enf = lista_enfermedades[i]
        
        prob_severo = 0.1
        if e > 60 or enf in ['COVID-19', 'Malaria']:
            prob_severo += 0.15
            
        sev = np.random.choice(['Leve', 'Moderado', 'Grave'], p=[1 - prob_severo - 0.1, 0.1, prob_severo])
        severidades.append(sev)
        
        # Hospitalización y UCI
        hosp = 'Sí' if sev in ['Moderado', 'Grave'] and np.random.rand() > 0.3 else 'No'
        uci = 'Sí' if sev == 'Grave' and np.random.rand() > 0.4 else 'No'
        
        hospitalizados.append(hosp)
        uci_list.append(uci)
        
        # Estado final
        if sev == 'Grave' and uci == 'Sí' and np.random.rand() < 0.2:
            est = 'Fallecido'
        elif hosp == 'Sí' or sev == 'Moderado':
            est = 'Recuperado' if np.random.rand() > 0.15 else 'En Tratamiento'
        else:
            est = 'Recuperado' if np.random.rand() > 0.05 else 'En Tratamiento'
            
        estados.append(est)
        
    df = pd.DataFrame({
        'ID_Paciente': ids,
        'Fecha_Diagnostico': fechas_diagnostico,
        'Region': lista_regiones,
        'Enfermedad': lista_enfermedades,
        'Edad': edades,
        'Genero': lista_generos,
        'Estado_Vacunacion': lista_vacunas,
        'Severidad': severidades,
        'Hospitalizado': hospitalizados,
        'Ingreso_UCI': uci_list,
        'Estado_Final': estados
    })
    
    return df

# ---------------------------------------------------------
# Sidebar e Interacción del Usuario
# ---------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2877/2877028.png", width=100)
st.sidebar.title("⚙️ Configuración")

st.sidebar.subheader("1. Generación de Datos Sintéticos")
n_muestras = st.sidebar.slider("Tamaño de la muestra", min_value=100, max_value=5000, value=1500, step=100)
semilla_sem = st.sidebar.number_input("Semilla aleatoria (Seed)", value=42, step=1)

# Cargar datos sintéticos
df_raw = generar_datos_epidemiologicos(n_registros=n_muestras, seed=semilla_sem)

st.sidebar.subheader("2. Filtros de Análisis")
regiones_sel = st.sidebar.multiselect("Filtrar por Región:", options=df_raw['Region'].unique(), default=df_raw['Region'].unique())
enfermedades_sel = st.sidebar.multiselect("Filtrar por Enfermedad:", options=df_raw['Enfermedad'].unique(), default=df_raw['Enfermedad'].unique())
severidad_sel = st.sidebar.multiselect("Filtrar por Severidad:", options=df_raw['Severidad'].unique(), default=df_raw['Severidad'].unique())

rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    value=[df_raw['Fecha_Diagnostico'].min(), df_raw['Fecha_Diagnostico'].max()],
    min_value=df_raw['Fecha_Diagnostico'].min(),
    max_value=df_raw['Fecha_Diagnostico'].max()
)

# Aplicar Filtros
df_filtrado = df_raw[
    (df_raw['Region'].isin(regiones_sel)) &
    (df_raw['Enfermedad'].isin(enfermedades_sel)) &
    (df_raw['Severidad'].isin(severidad_sel))
]

if len(rango_fechas) == 2:
    f_inicio, f_fin = rango_fechas
    df_filtrado = df_filtrado[
        (df_filtrado['Fecha_Diagnostico'].dt.date >= f_inicio) &
        (df_filtrado['Fecha_Diagnostico'].dt.date <= f_fin)
    ]

# ---------------------------------------------------------
# Encabezado Principal
# ---------------------------------------------------------
st.title("🔬 Plataforma de Análisis Epidemiológico (EDA)")
st.markdown("""
Esta aplicación permite generar **datos sintéticos epidemiológicos**, realizar un **Análisis Exploratorio de Datos (EDA)** 
cuantitativo y cualitativo, e interactuar dinámicamente con las variables epidemiológicas.
""")

st.divider()

# ---------------------------------------------------------
# Métricas Clave (KPIs)
# ---------------------------------------------------------
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

total_casos = len(df_filtrado)
tasa_hospitalizacion = (df_filtrado['Hospitalizado'] == 'Sí').mean() * 100 if total_casos > 0 else 0
tasa_uci = (df_filtrado['Ingreso_UCI'] == 'Sí').mean() * 100 if total_casos > 0 else 0
tasa_mortalidad = (df_filtrado['Estado_Final'] == 'Fallecido').mean() * 100 if total_casos > 0 else 0

col_kpi1.metric("Total Casos Registrados", f"{total_casos:,}")
col_kpi2.metric("Tasa Hospitalización", f"{tasa_hospitalizacion:.1f}%")
col_kpi3.metric("Tasa Ingreso UCI", f"{tasa_uci:.1f}%")
col_kpi4.metric("Tasa de Letalidad", f"{tasa_mortalidad:.2f}%")

st.divider()

# ---------------------------------------------------------
# Pestañas de Análisis
# ---------------------------------------------------------
tab_datos, tab_cuanti, tab_cuali, tab_graficos = st.tabs([
    "📋 Vista de Datos", 
    "🔢 Análisis Cuantitativo", 
    "📊 Análisis Cualitativo", 
    "📈 Visualizaciones Interactivas"
])

# ---------------------------------------------------------
# TAB 1: Vista de Datos
# ---------------------------------------------------------
with tab_datos:
    st.subheader("Exploración del Dataset Sintético")
    st.write(f"Mostrando **{len(df_filtrado)}** registros según los filtros seleccionados.")
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Botón de Descarga
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Dataset Filtrado en CSV",
        data=csv,
        file_name="datos_epidemiologicos_sinteticos.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------
# TAB 2: Análisis Cuantitativo
# ---------------------------------------------------------
with tab_cuanti:
    st.subheader("Estadística Descriptiva de Variables Numéricas")
    
    if len(df_filtrado) > 0:
        col_q1, col_q2 = st.columns([1, 1])
        
        with col_q1:
            st.markdown("#### Resumen Numérico (Edad)")
            resumen_edad = df_filtrado['Edad'].describe().to_frame().T
            resumen_edad['Mediana'] = df_filtrado['Edad'].median()
            resumen_edad['Varianza'] = df_filtrado['Edad'].var()
            resumen_edad['Rango Intercuartílico (IQR)'] = df_filtrado['Edad'].quantile(0.75) - df_filtrado['Edad'].quantile(0.25)
            st.dataframe(resumen_edad.style.format("{:.2f}"), use_container_width=True)
            
        with col_q2:
            st.markdown("#### Distribución por Grupos de Edad")
            bins = [0, 12, 18, 30, 50, 65, 100]
            labels = ['Infantil (0-12)', 'Adolescente (13-18)', 'Adulto Joven (19-30)', 'Adulto (31-50)', 'Adulto Mayor (51-65)', 'Senior (>65)']
            df_filtrado['Grupo_Edad'] = pd.cut(df_filtrado['Edad'], bins=bins, labels=labels, right=True)
            
            dist_grupo_edad = df_filtrado['Grupo_Edad'].value_counts().reset_index()
            dist_grupo_edad.columns = ['Grupo de Edad', 'Cantidad']
            dist_grupo_edad['Porcentaje (%)'] = (dist_grupo_edad['Cantidad'] / len(df_filtrado) * 100).round(2)
            st.dataframe(dist_grupo_edad, use_container_width=True)
            
        st.markdown("#### Estadísticas Promedio por Enfermedad")
        est_enf = df_filtrado.groupby('Enfermedad').agg(
            Casos=('ID_Paciente', 'count'),
            Edad_Promedio=('Edad', 'mean'),
            Edad_Mediana=('Edad', 'median'),
            Hospitalizados=('Hospitalizado', lambda x: (x == 'Sí').sum()),
            Fallecidos=('Estado_Final', lambda x: (x == 'Fallecido').sum())
        ).reset_index()
        est_enf['Tasa_Letalidad (%)'] = (est_enf['Fallecidos'] / est_enf['Casos'] * 100).round(2)
        st.dataframe(est_enf.style.format({'Edad_Promedio': '{:.1f}', 'Edad_Mediana': '{:.1f}', 'Tasa_Letalidad (%)': '{:.2f}%'}), use_container_width=True)
    else:
        st.warning("No hay datos disponibles con los filtros aplicados.")

# ---------------------------------------------------------
# TAB 3: Análisis Cualitativo
# ---------------------------------------------------------
with tab_cuali:
    st.subheader("Análisis de Frecuencias y Tablas Cruzadas")
    
    if len(df_filtrado) > 0:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### Frecuencia por Enfermedad y Severidad")
            ct_enf_sev = pd.crosstab(df_filtrado['Enfermedad'], df_filtrado['Severidad'], margins=True, margins_name="Total")
            st.dataframe(ct_enf_sev, use_container_width=True)
            
        with col_c2:
            st.markdown("#### Estado de Vacunación vs Estado Final")
            ct_vac_est = pd.crosstab(df_filtrado['Estado_Vacunacion'], df_filtrado['Estado_Final'], margins=True, margins_name="Total")
            st.dataframe(ct_vac_est, use_container_width=True)
            
        st.markdown("#### Distribución de Pacientes por Región y Género")
        ct_reg_gen = pd.crosstab(df_filtrado['Region'], df_filtrado['Genero'], normalize='index') * 100
        st.markdown("*Porcentaje (%) relativo a cada región:*")
        st.dataframe(ct_reg_gen.style.format("{:.2f}%"), use_container_width=True)
    else:
        st.warning("No hay datos disponibles con los filtros aplicados.")

# ---------------------------------------------------------
# TAB 4: Visualizaciones Interactivas (Plotly)
# ---------------------------------------------------------
with tab_graficos:
    st.subheader("Visualizaciones Interactivas Epidemiológicas")
    
    if len(df_filtrado) > 0:
        # Curva Epidemiológica
        st.markdown("#### 1. Curva Epidemiológica (Casos por Fecha de Diagnóstico)")
        df_temporal = df_filtrado.groupby([pd.Grouper(key='Fecha_Diagnostico', freq='W-MON'), 'Enfermedad']).size().reset_index(name='Casos')
        
        fig_epi = px.line(
            df_temporal, 
            x='Fecha_Diagnostico', 
            y='Casos', 
            color='Enfermedad',
            markers=True,
            title="Evolución Semanal de Casos por Enfermedad",
            labels={'Fecha_Diagnostico': 'Fecha (Semana)', 'Casos': 'Número de Casos'}
        )
        fig_epi.update_layout(hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig_epi, use_container_width=True)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### 2. Distribución de Edad según Severidad")
            fig_box = px.box(
                df_filtrado, 
                x='Severidad', 
                y='Edad', 
                color='Severidad',
                points="all",
                title="Distribución de Edad por Severidad del Caso",
                category_orders={'Severidad': ['Leve', 'Moderado', 'Grave']}
            )
            fig_box.update_layout(template="plotly_white")
            st.plotly_chart(fig_box, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 3. Distribución de Casos por Región y Estado Final")
            fig_bar = px.bar(
                df_filtrado, 
                x='Region', 
                color='Estado_Final',
                barmode='group',
                title="Estado Final del Paciente por Región",
                labels={'Region': 'Región', 'count': 'Cantidad de Pacientes'}
            )
            fig_bar.update_layout(template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            st.markdown("#### 4. Proporción de Estado de Vacunación")
            fig_pie = px.pie(
                df_filtrado, 
                names='Estado_Vacunacion', 
                title="Distribución por Estado de Vacunación",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_g4:
            st.markdown("#### 5. Mapa de Calor de Interacción (Enfermedad vs Severidad)")
            ct_heatmap = pd.crosstab(df_filtrado['Enfermedad'], df_filtrado['Severidad'])
            fig_heat = px.imshow(
                ct_heatmap,
                text_auto=True,
                aspect="auto",
                title="Mapa de Calor: Enfermedad vs Severidad",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para mostrar gráficos con los filtros seleccionados.")

# ---------------------------------------------------------
# Pie de Página
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Ajusta la muestra y los filtros en este panel para observar cómo reacciona el análisis epidemiológico.")
