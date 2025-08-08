import os
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

st.set_page_config(page_title="LLM Data Dictionary", page_icon="📊", layout="wide")
st.title("LLM-Powered Data Dictionary Builder (OpenRouter)")
st.caption("Upload a CSV. The app summarizes columns and asks an open-source LLM to draft a data dictionary for you.")

# ---- Sidebar controls
with st.sidebar:
    st.header("Model & Settings")
    model = st.selectbox(
        "Model",
        [
            "mistralai/mistral-7b-instruct",
            "openchat/openchat-3.5-1210",
            "nousresearch/hermes-2-pro-mistral",
        ],
        index=0,
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    max_tokens = st.number_input("Max tokens", 256, 4096, 1200, step=64)
    st.divider()
    st.write("API key loaded:", "✅" if API_KEY else "❌ (set OPENROUTER_API_KEY in .env)")

headers = {
    "Authorization": f"Bearer {API_KEY}" if API_KEY else "",
    "Content-Type": "application/json",
    # These two are recommended by OpenRouter etiquette (optional but nice to include):
    "HTTP-Referer": "http://localhost",
    "X-Title": "LLM Data Dictionary",
}

uploaded_file = st.file_uploader("Upload a CSV", type=["csv"])

def build_prompt(df: pd.DataFrame) -> str:
    lines = []
    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        null_pct = f"{s.isna().mean():.2%}"
        # safer sample extraction
        non_na = s.dropna()
        if non_na.empty:
            sample = "N/A"
        else:
            try:
                sample = str(non_na.sample(1, random_state=42).iloc[0])
            except Exception:
                sample = str(non_na.iloc[0])

        # simple signal for mixed types
        unique_types = {type(v).__name__ for v in non_na.head(200).tolist()}
        mixed_flag = "yes" if len(unique_types) > 1 else "no"

        lines.append(
            f"Column: {col}\nType: {dtype}\nNull %: {null_pct}\nMixed types in sample?: {mixed_flag}\nSample: {sample}"
        )

    cols_block = "\n\n".join(lines)

    return f"""You are a senior analytics engineer creating a data dictionary from column summaries.

For each column:
1) Give a clear one-sentence description of what the field represents.
2) Suggest a clearer column name (only if needed).
3) List any data quality risks: unclear naming, mixed types, unexpected values, or high null rate.

Return your answer strictly as a Markdown table with the columns:
| column | suggested_name | description | issues |

Column summaries:
{cols_block}
"""

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

    st.subheader("Preview")
    st.dataframe(df.head(), use_container_width=True)

    prompt = build_prompt(df)

    run = st.button("Generate Data Dictionary", type="primary", disabled=not API_KEY)
    if not API_KEY:
        st.info("Add your OpenRouter key to a `.env` file as `OPENROUTER_API_KEY=...` to enable the button.")

    if run:
        with st.spinner("Asking the model…"):
            try:
                resp = requests.post(
                    API_URL,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": float(temperature),
                        "max_tokens": int(max_tokens),
                    },
                    timeout=90,
                )
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()

        if not resp.ok:
            st.error(f"OpenRouter error {resp.status_code}:\n{resp.text[:800]}")
        else:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not content:
                st.warning("No content returned from the model.")
            else:
                st.markdown("### Model Output")
                st.markdown(content)
                # simple export
                st.download_button(
                    "Download Markdown",
                    data=content.encode("utf-8"),
                    file_name="data_dictionary.md",
                    mime="text/markdown",
                )
else:
    st.info("Upload a CSV to get started.")
