import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="Presupuesto EMCALI", layout="centered")

# Mostrar el logo en la barra lateral
st.sidebar.image("LOGO-EMCALI-vertical-color.png", use_container_width=True)

# Estilo corporativo personalizado
st.markdown("""
<style>
    /* Fuente personalizada: Prometo (sustituida por Segoe UI o sans-serif si no disponible) */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }

    /* Logo centrado en la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #ef5f17;
        padding-top: 1rem;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #ef5f17;
        font-weight: bold;
    }

    /* Botones */
    .stButton > button {
        background-color: #ef5f17;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5em 1.5em;
        border: none;
        transition: background-color 0.3s;
    }

    .stButton > button:hover {
        background-color: #cc4d12;
        color: white;
    }

    /* Inputs y tablas */
    .stTextInput, .stNumberInput, .stSelectbox {
        font-size: 16px;
    }

    /* Área principal */
    .main {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 0 8px rgba(0, 0, 0, 0.05);
    }

    /* Iconos y decoraciones */
    div[data-testid="stDecoration"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

credenciales = {
    "admin": {"password": "1234", "centros": ["52000", "52010", "52012", "51000", "51010"]},
    "usuario": {"password": "abcd", "centros": ["52000"]},
    "jtandrade": {"password": "5678", "centros": ["52012"]}
}

def mostrar_login():
    st.title("\U0001F512 Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username in credenciales and credenciales[username]["password"] == password:
            st.session_state["logueado"] = True
            st.session_state["usuario"] = username
            st.session_state["centros_autorizados"] = credenciales[username]["centros"]
            st.success(f"Bienvenido, {username}!")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")

def mostrar_logout():
    with st.sidebar:
        st.markdown(f"👤 Usuario: `{st.session_state['usuario']}`")
        if st.button("Cerrar sesión"):
            st.session_state["logueado"] = False
            st.session_state["usuario"] = None
            st.session_state["centros_autorizados"] = []
            st.rerun()

if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

if not st.session_state["logueado"]:
    mostrar_login()
    st.stop()
else:
    mostrar_logout()

if st.session_state.get("usuario") != "admin":
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stDecoration"] {display:none;}
    /* div[data-testid="stSidebarUserContent"] {display:none;} */  <-- ¡COMENTADA O ELIMINADA!
    button[title="View app in Streamlit Community Cloud"] {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
st.title("📊 Gestión Presupuestal UENE 2026")

RELACION_FILE = "presupuesto.xlsx"
BITACORA_FILE = "bitacora_admin.csv"

@st.cache_data
def cargar_relaciones(path):
    hojas = pd.read_excel(path, sheet_name=None)
    return hojas["Grupos_Centros"], hojas["Centro_Unidades"], hojas["Centro_Conceptos"]

grupos_centros_df, centro_unidades_df, centro_conceptos_df = cargar_relaciones(RELACION_FILE)

if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Ítem", "Grupo", "Centro Gestor", "Unidad", "Concepto de Gasto",
        "Descripción del Gasto", "Cantidad", "Valor Unitario", "Total", "Fecha"
    ])

def obtener_centros(grupo):
    return grupos_centros_df[grupos_centros_df["Grupo"] == grupo]["Centro Gestor"].unique().tolist()

def obtener_unidades(centro):
    return centro_unidades_df[centro_unidades_df["Centro Gestor"] == centro]["Unidad"].unique().tolist()

def obtener_conceptos(centro):
    return centro_conceptos_df[centro_conceptos_df["Centro Gestor"] == centro]["Concepto de Gasto"].unique().tolist()

def registrar_bitacora(accion, usuario, item):
    ahora = datetime.now(pytz.timezone("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S")
    fila = pd.DataFrame([[usuario, ahora, accion, item]], columns=["Usuario", "Hora", "Acción", "Ítem"])
    if os.path.exists(BITACORA_FILE):
        existente = pd.read_csv(BITACORA_FILE)
        nueva = pd.concat([existente, fila], ignore_index=True)
    else:
        nueva = fila
    nueva.to_csv(BITACORA_FILE, index=False)

# Menú por tipo de usuario
if st.session_state["usuario"] == "admin":
    opciones_menu = ["Agregar", "Buscar", "Editar", "Eliminar", "Ver Todo", "Historial"]
else:
    opciones_menu = ["Agregar", "Ver Todo"]

menu = st.sidebar.selectbox("Menú", opciones_menu)

df = st.session_state.datos

if menu == "Agregar":
    st.subheader("➕ Agregar Registro")
    item = st.text_input("Ítem")
    grupo = st.selectbox("Grupo", grupos_centros_df["Grupo"].unique())
    centros = obtener_centros(grupo)
    centro = st.selectbox("Centro Gestor", centros if centros else ["-"])
    unidades = obtener_unidades(centro)
    unidad = st.selectbox("Unidad", unidades if unidades else ["-"])
    conceptos = obtener_conceptos(centro)
    concepto = st.selectbox("Concepto de Gasto", conceptos if conceptos else ["-"])
    descripcion = st.text_area("Descripción del Gasto")
    cantidad = st.number_input("Cantidad", min_value=1, format="%d")
    valor_unitario = st.number_input("Valor Unitario", min_value=0.0, format="%.2f")
    total = cantidad * valor_unitario
    fecha = st.date_input("Fecha", value=datetime.today())
    st.write(f"💲 **Total Calculado:** {total:,.2f}")
    if st.button("Guardar"):
        nuevo = pd.DataFrame([[item, grupo, centro, unidad, concepto,
                               descripcion, cantidad, valor_unitario, total, fecha]],
                             columns=df.columns)
        st.session_state.datos = pd.concat([df, nuevo], ignore_index=True)
        registrar_bitacora("Agregar", st.session_state["usuario"], item)
        st.success("✅ Registro guardado correctamente")
    if not st.session_state.datos.empty:
        st.subheader("📋 Registros Agregados")
        st.dataframe(st.session_state.datos, use_container_width=True)

elif menu == "Buscar":
    st.subheader("🔍 Buscar por Ítem")
    buscar_item = st.text_input("Ingrese Ítem")
    if st.button("Buscar"):
        resultado = df[df["Ítem"] == buscar_item]
        if not resultado.empty:
            st.dataframe(resultado)
        else:
            st.warning("No se encontró el ítem")

elif menu == "Editar":
    st.subheader("✏️ Editar Registro")
    editar_item = st.text_input("Ítem a editar")
    if st.button("Cargar"):
        resultado = df[df["Ítem"] == editar_item]
        if not resultado.empty:
            index = resultado.index[0]
            registro = resultado.iloc[0]
            grupo = st.selectbox("Grupo", grupos_centros_df["Grupo"].unique(), index=list(grupos_centros_df["Grupo"].unique()).index(registro["Grupo"]))
            centros = obtener_centros(grupo)
            centro = st.selectbox("Centro Gestor", centros, index=centros.index(registro["Centro Gestor"]))
            unidades = obtener_unidades(centro)
            unidad = st.selectbox("Unidad", unidades, index=unidades.index(registro["Unidad"]))
            conceptos = obtener_conceptos(centro)
            concepto = st.selectbox("Concepto de Gasto", conceptos, index=conceptos.index(registro["Concepto de Gasto"]))
            descripcion = st.text_area("Descripción del Gasto", value=registro["Descripción del Gasto"])
            cantidad = st.number_input("Cantidad", min_value=1, value=int(registro["Cantidad"]), format="%d")
            valor_unitario = st.number_input("Valor Unitario", min_value=0.0, value=float(registro["Valor Unitario"]), format="%.2f")
            total = cantidad * valor_unitario
            fecha = st.date_input("Fecha", value=pd.to_datetime(registro["Fecha"]))
            st.write(f"💲 **Total Calculado:** {total:,.2f}")
            if st.button("Actualizar"):
                st.session_state.datos.at[index, "Grupo"] = grupo
                st.session_state.datos.at[index, "Centro Gestor"] = centro
                st.session_state.datos.at[index, "Unidad"] = unidad
                st.session_state.datos.at[index, "Concepto de Gasto"] = concepto
                st.session_state.datos.at[index, "Descripción del Gasto"] = descripcion
                st.session_state.datos.at[index, "Cantidad"] = cantidad
                st.session_state.datos.at[index, "Valor Unitario"] = valor_unitario
                st.session_state.datos.at[index, "Total"] = total
                st.session_state.datos.at[index, "Fecha"] = fecha
                registrar_bitacora("Editar", st.session_state["usuario"], editar_item)
                st.success("✅ Registro actualizado")
        else:
            st.warning("Ítem no encontrado")

elif menu == "Eliminar":
    st.subheader("🗑️ Eliminar Registro")
    eliminar_item = st.text_input("Ítem a eliminar")
    if st.button("Eliminar"):
        if eliminar_item in df["Ítem"].values:
            st.session_state.datos = df[df["Ítem"] != eliminar_item]
            registrar_bitacora("Eliminar", st.session_state["usuario"], eliminar_item)
            st.success("✅ Registro eliminado")
        else:
            st.error("Ítem no encontrado")

elif menu == "Ver Todo":
    st.subheader("📋 Todos los Registros")
    st.dataframe(df)

elif menu == "Historial" and st.session_state["usuario"] == "admin":
    st.subheader("🕓 Historial de Actividades")
    if os.path.exists("bitacora_admin.csv"):
        log = pd.read_csv("bitacora_admin.csv")
        st.dataframe(log, use_container_width=True)
        st.download_button("📥 Descargar Historial", data=log.to_csv(index=False), file_name="bitacora_admin.csv", mime="text/csv")
    else:
        st.info("No hay registros de historial aún.")
