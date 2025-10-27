# app.py
# --------------------------------------------
# MailMind – Analizador Inteligente de Correos
# Versión con ingreso manual del API Key
# --------------------------------------------

import streamlit as st
from openai import OpenAI
import io

# --------------------------------------------
# CONFIGURACIÓN INICIAL
# --------------------------------------------
st.set_page_config(page_title="MailMind - Analizador de Correos", layout="centered")

st.title("📧 MailMind – Analizador Inteligente de Correos")
st.caption("Genera resúmenes, identifica acuerdos, dudas, acciones y fechas importantes de tus correos electrónicos.")

# --------------------------------------------
# INGRESO DEL API KEY
# --------------------------------------------
st.sidebar.header("🔐 Configuración")
api_key_input = st.sidebar.text_input(
    "Introduce tu OpenAI API Key:",
    type="password",
    placeholder="sk-...",
    help="Tu clave nunca se almacena; se usa solo durante esta sesión."
)

# Guardamos el API key en la sesión
if api_key_input:
    st.session_state["api_key"] = api_key_input

# Validamos que haya API key
if "api_key" not in st.session_state or not st.session_state["api_key"]:
    st.warning("Por favor, introduce tu OpenAI API Key en la barra lateral para comenzar.")
    st.stop()

# Inicializa el cliente con la clave ingresada
client = OpenAI(api_key=st.session_state["api_key"])

# --------------------------------------------
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# --------------------------------------------
def analizar_correo(contenido):
    prompt = f"""
    Analiza el siguiente correo electrónico y genera una salida estructurada con:
    1. Resumen breve (máx 100 palabras)
    2. Acuerdos o compromisos
    3. Dudas o preguntas
    4. Acciones o tareas pendientes
    5. Fechas importantes (reuniones, entregas, etc.)

    Texto del correo:
    {contenido}

    Formatea la respuesta en secciones claras con títulos y emojis adecuados.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Error al procesar el correo: {str(e)}"

# --------------------------------------------
# ENTRADA DEL USUARIO
# --------------------------------------------
st.subheader("📩 Entrada de correo")

col1, col2 = st.columns(2)
with col1:
    correo_texto = st.text_area(
        "Pega el contenido del correo aquí:",
        height=200,
        placeholder="Copia aquí el texto de tu correo..."
    )
with col2:
    archivo = st.file_uploader("...o selecciona un archivo de texto (.txt o .eml):", type=["txt", "eml"])

# --------------------------------------------
# PROCESAR CONTENIDO
# --------------------------------------------
contenido = None

if archivo is not None:
    try:
        contenido = archivo.read().decode("utf-8", errors="ignore")
        st.success("✅ Archivo cargado correctamente.")
    except Exception:
        st.error("⚠️ No se pudo leer el archivo. Asegúrate de que sea un .txt o .eml válido.")
elif correo_texto.strip():
    contenido = correo_texto

if st.button("🔍 Analizar correo"):
    if not contenido:
        st.warning("Por favor, pega un correo o selecciona un archivo antes de analizar.")
    else:
        with st.spinner("Analizando el contenido... ⏳"):
            resultado = analizar_correo(contenido)
        st.markdown("---")
        st.subheader("🧠 Resultados del análisis")
        st.markdown(resultado)

        # Opción de descarga del resultado
        st.download_button(
            "⬇️ Descargar resultado",
            data=resultado,
            file_name="analisis_correo.txt",
            mime="text/plain"
        )

# --------------------------------------------
# PIE DE PÁGINA
# --------------------------------------------
st.markdown("---")
st.caption("Desarrollado con ❤️ usando Streamlit + OpenAI")
