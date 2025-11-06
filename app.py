# app.py
# MailMind PRO - Bilingüe, modelos extendidos, copy-to-clipboard, main_app parseable (método C)
import streamlit as st
from openai import OpenAI
import json
import html
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="MailMind PRO", layout="wide")

# -----------------------
# Helpers
# -----------------------
def safe_parse_json(text):
    """
    Intenta extraer un objeto JSON del texto. Primero intenta parseo directo,
    luego busca la primera ocurrencia de {...} grande y la parsea.
    """
    try:
        return json.loads(text), None
    except Exception:
        # buscar bloque JSON en el texto
        match = re.search(r'(\{(?:.|\n)*\})', text)
        if match:
            try:
                return json.loads(match.group(1)), None
            except Exception as e:
                return None, f"Error al parsear JSON interno: {e}"
        return None, "No se encontró JSON válido en la respuesta."

def render_copy_button(text, key):
    """
    Renderiza un botón que copia 'text' al portapapeles usando JS.
    key: string único por botón
    """
    safe_text = html.escape(text)
    html_code = f"""
    <div>
      <button id="btn_{key}">📋 Copiar</button>
      <button id="dl_{key}">⬇️ Descargar</button>
      <script>
        const btn = document.getElementById("btn_{key}");
        const dl = document.getElementById("dl_{key}");
        const text = `{safe_text}`;
        btn.addEventListener("click", () => {{
          navigator.clipboard.writeText(text).then(() => {{
            btn.textContent = "✅ Copiado";
            setTimeout(()=>{{ btn.textContent = "📋 Copiar"; }},1500);
          }});
        }});
        dl.addEventListener("click", () => {{
          const blob = new Blob([text], {{ type: 'text/plain;charset=utf-8' }});
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = "mailmind_analysis.txt";
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        }});
      </script>
    </div>
    """
    components.html(html_code, height=45)

# -----------------------
# UI - Sidebar
# -----------------------
st.title("📧 MailMind PRO")
st.caption("Analiza correos y genera resultados estructurados en Español e Inglés. Incluye detección de la aplicación principal (main_app).")

st.sidebar.header("🔧 Configuración")
api_key = st.sidebar.text_input("🔑 Ingresa tu OpenAI API Key:", type="password", help="Tu API key se usa sólo en esta sesión y no se guarda en el servidor.")

# Model list (ordenada mayor costo -> menor)
models_extended = [
    "gpt-4o",             # alto costo (ejemplo)
    "gpt-4",              # alto costo
    "gpt-4o-mini",        # medio-alto
    "gpt-4-mini",         # medio
    "gpt-4o-research-preview", # experimental (si disponible)
    "gpt-3.5-turbo-16k",  # mayor contexto, menor costo que 4
    "gpt-3.5-turbo"       # más económico
]

model = st.sidebar.selectbox("Modelo (mayor costo → menor)", options=models_extended, index=0)

max_tokens = st.sidebar.selectbox(
    "Máx. tokens (salida)",
    options=[300, 500, 800, 1000, 1500, 2000, 3000],
    index=2
)

temperature = st.sidebar.selectbox(
    "Temperatura",
    options=[0.0, 0.2, 0.5, 0.8, 1.0],
    index=2,
    help="Controla la aleatoriedad de la respuesta. 0.0 = respuestas más deterministas y conservadoras. 1.0 = respuestas más creativas/variadas."
)

st.sidebar.markdown("---")
st.sidebar.info("Sugerencia: para pruebas de bajo costo usa `gpt-3.5-turbo` y max_tokens bajos. Para salidas más largas y separadas, sube max_tokens.")

# -----------------------
# Entrada de correo
# -----------------------
st.subheader("📩 Entrada de correo")
col_main = st.columns([2,1])
with col_main[0]:
    input_method = st.radio("Cómo ingresar el correo:", ("Pegar texto", "Subir archivo (.txt, .eml)"))
    email_text = ""
    if input_method == "Pegar texto":
        email_text = st.text_area("Pega aquí el contenido del correo:", height=260)
    else:
        uploaded = st.file_uploader("Selecciona archivo (.txt, .eml)", type=["txt", "eml"])
        if uploaded:
            try:
                email_text = uploaded.read().decode("utf-8", errors="ignore")
                st.success("✅ Archivo cargado.")
            except Exception:
                st.error("⚠️ No se pudo leer el archivo. Asegúrate de que sea .txt o .eml.")

with col_main[1]:
    st.markdown("### Vista previa")
    st.caption("Aquí puedes revisar el texto pegado o cargado antes de analizar.")
    preview = email_text[:1000] + ("..." if len(email_text) > 1000 else "")
    st.code(preview or "Esperando contenido...")

# -----------------------
# Botón analizar
# -----------------------
analyze_btn = st.button("🔍 Analizar correo")

# -----------------------
# Processing
# -----------------------
if analyze_btn:
    if not api_key:
        st.error("Introduce tu API Key en la barra lateral.")
    elif not email_text.strip():
        st.error("Ingresa o carga el contenido del correo.")
    else:
        client = OpenAI(api_key=api_key)
        # Construir prompt que obliga a retornar JSON bien formado
        system_msg = {
            "role": "system",
            "content": (
                "You are a JSON-output specialist. For any email analysis request, return a single valid JSON object "
                "and nothing else. The JSON structure MUST be exactly: "
                '{"main_app": string, "spanish": {"summary": string, "agreements": [string], "doubts": [string], "actions": [string], "dates": [string], "people": [string]}, '
                '"english": {same fields as spanish}}. '
                "Each action in the arrays must NOT include any prefix — the assistant will output plain action text, "
                "and the client/UI will prefix each action with the main_app followed by ' - '. "
                "If the email does not mention an app, set main_app to 'Unknown'. Ensure JSON is valid and parsable."
            )
        }

        user_msg = {
            "role": "user",
            "content": (
                "Analiza el siguiente correo y genera la estructura solicitada en español e inglés. "
                "Usa lenguaje claro y conciso. No añadas explicaciones fuera del JSON. "
                f"Correo:\n\n{email_text}"
            )
        }

        try:
            with st.spinner("Analizando... (puede tardar según el modelo y max_tokens)..."):
                response = client.chat.completions.create(
                    model=model,
                    messages=[system_msg, user_msg],
                    temperature=float(temperature),
                    max_tokens=int(max_tokens)
                )

            raw_text = response.choices[0].message.content.strip()

            # Intentar parseo JSON
            parsed, parse_err = safe_parse_json(raw_text)
            if parsed is None:
                # mostrar raw y error
                st.warning("⚠️ No se obtuvo JSON parseable del modelo. Se mostrará la respuesta cruda y se intentará formatear.")
                st.markdown("**Respuesta cruda del modelo:**")
                st.code(raw_text)
                st.error(parse_err)
            else:
                # Validamos estructura mínima
                main_app = parsed.get("main_app", "Unknown")
                spanish = parsed.get("spanish", {})
                english = parsed.get("english", {})

                # Normalizar campos con fallback
                def ensure_fields(section):
                    return {
                        "summary": section.get("summary", "").strip() if isinstance(section.get("summary", ""), str) else "",
                        "agreements": section.get("agreements", []) if isinstance(section.get("agreements", []), list) else [],
                        "doubts": section.get("doubts", []) if isinstance(section.get("doubts", []), list) else [],
                        "actions": section.get("actions", []) if isinstance(section.get("actions", []), list) else [],
                        "dates": section.get("dates", []) if isinstance(section.get("dates", []), list) else [],
                        "people": section.get("people", []) if isinstance(section.get("people", []), list) else [],
                    }

                spanish = ensure_fields(spanish)
                english = ensure_fields(english)

                # Construir textos formateados "pretty" (A)
                def build_pretty_text(main_app_name, sec, lang_label):
                    lines = []
                    lines.append(f"**{main_app_name}**")  # first line with main_app
                    lines.append("")
                    lines.append("📄 **Resumen**")
                    lines.append(sec["summary"] or "—")
                    lines.append("")
                    lines.append("✅ **Acuerdos**")
                    if sec["agreements"]:
                        for it in sec["agreements"]:
                            lines.append(f"- {it}")
                    else:
                        lines.append("- —")
                    lines.append("")
                    lines.append("❓ **Dudas**")
                    if sec["doubts"]:
                        for it in sec["doubts"]:
                            lines.append(f"- {it}")
                    else:
                        lines.append("- —")
                    lines.append("")
                    lines.append("🔧 **Acciones / Tareas**")
                    if sec["actions"]:
                        for it in sec["actions"]:
                            # prefix with main_app
                            lines.append(f"- {main_app_name} - {it}")
                    else:
                        lines.append("- —")
                    lines.append("")
                    lines.append("⏰ **Fechas importantes / Plazos**")
                    if sec["dates"]:
                        for it in sec["dates"]:
                            lines.append(f"- {it}")
                    else:
                        lines.append("- —")
                    lines.append("")
                    lines.append("💬 **Personas / Equipos mencionados**")
                    if sec["people"]:
                        for it in sec["people"]:
                            lines.append(f"- {it}")
                    else:
                        lines.append("- —")
                    return "\n".join(lines)

                pretty_es = build_pretty_text(main_app, spanish, "ES")
                pretty_en = build_pretty_text(main_app, english, "EN")

                # Mostrar en tabs
                tab_es, tab_en = st.tabs([f"🇪🇸 Español ({main_app})", "🇬🇧 English"])

                with tab_es:
                    st.markdown(pretty_es)
                    render_copy_button(pretty_es, key="es")
                    st.download_button("⬇️ Descargar Español", data=pretty_es, file_name="mailmind_es.txt", mime="text/plain")

                with tab_en:
                    st.markdown(pretty_en)
                    render_copy_button(pretty_en, key="en")
                    st.download_button("⬇️ Descargar English", data=pretty_en, file_name="mailmind_en.txt", mime="text/plain")

                st.success("✅ Análisis completado.")

        except Exception as e:
            st.error(f"⚠️ Error al procesar la petición:\n\n{e}")
