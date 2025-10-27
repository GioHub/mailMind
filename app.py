import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="MailMind - Analizador de Correos", layout="wide")

st.title("📧 MailMind")
st.write("Analiza correos electrónicos para generar resúmenes, identificar acuerdos, dudas, acciones, pendientes y fechas importantes.")

# === Sidebar ===
st.sidebar.header("⚙️ Configuración")

# Campo para API Key
api_key = st.sidebar.text_input("🔑 Ingresa tu OpenAI API Key:", type="password")

# Listas desplegables
model = st.sidebar.selectbox(
    "Modelo",
    options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    index=0  # Valor por defecto: gpt-4o-mini
)

max_tokens = st.sidebar.selectbox(
    "Máx. tokens",
    options=[100, 300, 500, 1000],
    index=1  # Valor por defecto: 300
)

temperature = st.sidebar.selectbox(
    "Temperatura",
    options=[0.2, 0.5, 0.8, 1.0],
    index=1  # Valor por defecto: 0.5
)

# === Entradas ===
st.subheader("📩 Entrada de correo")

option = st.radio("Selecciona cómo ingresar el correo:", ("Pegar texto", "Subir archivo (.txt, .eml)"))

email_text = ""
if option == "Pegar texto":
    email_text = st.text_area("Pega aquí el contenido del correo:", height=200)
else:
    uploaded_file = st.file_uploader("Selecciona un archivo", type=["txt", "eml"])
    if uploaded_file:
        email_text = uploaded_file.read().decode("utf-8", errors="ignore")

# === Procesamiento ===
if st.button("🔍 Analizar correo"):
    if not api_key:
        st.error("Por favor, ingresa tu API Key en la barra lateral.")
    elif not email_text.strip():
        st.error("Por favor, ingresa o carga el contenido del correo.")
    else:
        try:
            client = OpenAI(api_key=api_key)
            prompt = f"""
            Analiza el siguiente correo electrónico y genera un resumen estructurado con los siguientes apartados:
            - 📄 **Resumen general**
            - ✅ **Acuerdos**
            - ❓ **Dudas**
            - 🔧 **Acciones / Tareas**
            - ⏰ **Fechas importantes o plazos**
            - 💬 **Personas o equipos mencionados**

            Contenido del correo:
            {email_text}
            """

            with st.spinner("Analizando correo..."):
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            analysis = response.choices[0].message.content
            st.success("✅ Análisis completado con éxito")
            st.markdown(analysis)

        except Exception as e:
            st.error(f"⚠️ Error al procesar el correo:\n\n{e}")
