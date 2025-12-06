import os
import io
import asyncio

import streamlit as st
import google.generativeai as genai
import edge_tts

# --- CONFIG GEMINI ---
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Simulateur CRCD",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Simulateur CRCD - Prototype initial")
st.write("Testons la connexion avec l’API Google Gemini, puis lisons la réponse à voix haute.")

# --- ÉTAT POUR STOCKER LA RÉPONSE IA ---
if "reponse_ia" not in st.session_state:
    st.session_state.reponse_ia = None

# --- SAISIE UTILISATEUR ---
question = st.text_area("Pose une question :", "Bonjour, peux-tu répondre ?")

# --- APPEL GEMINI ---
if st.button("Envoyer"):
    if not api_key:
        st.error("❌ GOOGLE_API_KEY n'est pas définie dans les variables d'environnement.")
    else:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            reponse = model.generate_content(question)
            texte_reponse = reponse.text

            st.session_state.reponse_ia = texte_reponse  # on mémorise pour la synthèse vocale

            st.subheader("Réponse de l’IA :")
            st.write(texte_reponse)

        except Exception as e:
            st.error(f"Erreur lors de l’appel à l’API : {e}")


# --- AFFICHAGE DE LA DERNIÈRE RÉPONSE (SI PRESENTE) ---
if st.session_state.reponse_ia:
    st.subheader("Dernière réponse générée :")
    st.write(st.session_state.reponse_ia)


# --- SYNTHÈSE VOCALE AVEC EDGE-TTS ---
st.subheader("🔊 Lecture audio de la réponse")

def synthese_vocale(texte: str) -> io.BytesIO:
    """Génère un flux audio MP3 à partir d'un texte avec edge-tts."""
    async def _generate(texte_inner: str) -> io.BytesIO:
        voix = "fr-FR-DeniseNeural"
        communicate = edge_tts.Communicate(texte_inner, voice=voix)
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        audio_buffer.seek(0)
        return audio_buffer

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio_fp = loop.run_until_complete(_generate(texte))
    loop.close()
    return audio_fp

if st.button("Lire la réponse à voix haute"):
    if not st.session_state.reponse_ia:
        st.warning("⚠️ Vous devez d’abord envoyer une question et obtenir une réponse.")
    else:
        try:
            audio_fp = synthese_vocale(st.session_state.reponse_ia)
            st.audio(audio_fp, format="audio/mp3")
        except Exception as e:
            st.error(f"Erreur audio : {e}")
