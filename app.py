import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="MailMind - Analizador de Correos", layout="wide")

st.title("📧 MailMind")
st.write("Analiza correos electrónicos y genera resúmenes estructurados en español e inglés, con detección de acuerdos, dudas, tareas y fechas clave.")

# === Sidebar ===
st.sidebar.header("⚙️ Configuración")

# API Key
api_key = st.sidebar.text_input("🔑 Ingresa tu OpenAI API Key:", type="password")

# Parámetros personalizables
model = st.sidebar.selectbox(
    "Modelo",
    options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    index=0
)
max_tokens = st.sidebar.selectbox(
    "Máx. tokens",
    options=[300, 500, 800, 1000],
    index=1
)
temperature = st.sidebar.selectbox(
    "Temperatura",
    options=[0.2, 0.5, 0.8, 1.0],
    index=1
)

# Campo para prefijo de aplicativo
app_prefix = st.sidebar.text_input("🏷️ Prefijo del aplicativo (para Acciones/Tareas):", value="MailMind")

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

            # Prompt principal
            prompt = f"""
            Analiza el siguiente correo electrónico y genera una respuesta estructurada con los siguientes apartados:
            - 📄 **Resumen general**
            - ✅ **Acuerdos**
            - ❓ **Dudas**
            - 🔧 **Acciones / Tareas** (cada tarea debe iniciar con el prefijo '{app_prefix}-')
            - ⏰ **Fechas importantes o plazos**
            - 💬 **Personas o equipos mencionados**

            Responde primero en español y luego traduce toda la respuesta completa al inglés.

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

            full_output = response.choices[0].message.content

            # Separar las dos versiones (español / inglés)
            # El modelo puede no separar de forma exacta, así que usamos una heurística
            split_markers = ["\n---\n", "\n### English Version", "### Versión en inglés", "### English"]
            spanish_output = full_output
            english_output = ""

            for marker in split_markers:
                if marker in full_output:
                    parts = full_output.split(marker)
                    spanish_output = parts[0].strip()
                    english_output = parts[-1].strip()
                    break

            # === Mostrar resultados en pestañas ===
            tab_es, tab_en = st.tabs(["🇪🇸 Español", "🇬🇧 English"])

            with tab_es:
                st.markdown(spanish_output)

            with tab_en:
                if english_output:
                    st.markdown(english_output)
                else:
                    st.info("No se detectó versión en inglés. Puedes aumentar 'max_tokens' o pedirle explícitamente al modelo que traduzca más texto.")

            st.success("✅ Análisis completado con éxito")

        except Exception as e:
            st.error(f"⚠️ Error al procesar el correo:\n\n{e}")
