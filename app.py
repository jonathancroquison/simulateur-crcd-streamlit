import os
import streamlit as st
import google.generativeai as genai

# --- CONFIG GEMINI ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY n'est pas définie dans les variables d'environnement.")
else:
    genai.configure(api_key=api_key)

# --- INTERFACE ---
st.set_page_config(page_title="Simulateur CRCD", page_icon="🎧", layout="wide")

st.title("🎧 Simulateur CRCD - Prototype initial")
st.write("Testons la connexion avec l’API Google Gemini.")

question = st.text_area("Pose une question :", "Bonjour, peux-tu répondre ?")

if st.button("Envoyer"):
    if not api_key:
        st.error("⚠️ Impossible d’appeler Gemini : pas de clé API définie.")
    else:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            reponse = model.generate_content(question)
            st.subheader("Réponse de l’IA :")
            st.write(reponse.text)
        except Exception as e:
            st.error(f"Erreur lors de l’appel à l’API : {e}")
