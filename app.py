import os
import io
import asyncio

import streamlit as st
import google.generativeai as genai
import edge_tts
from gtts import gTTS

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
st.write("Test de la connexion avec l’API Google Gemini, puis lecture vocale de la réponse.")

# --- ÉTAT : DERNIÈRE RÉPONSE IA ---
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

            st.session_state.reponse_ia = texte_reponse

            st.subheader("Réponse de l’IA :")
            st.write(texte_reponse)

        except Exception as e:
            st.error(f"Erreur lors de l’appel à l’API : {e}")

# --- AFFICHER LA DERNIÈRE RÉPONSE ---
if st.session_state.reponse_ia:
    st.subheader("Dernière réponse générée :")
    st.write(st.session_state.reponse_ia)

# --- FONCTION DE SYNTHÈSE VOCALE ---
def synthese_vocale(texte: str) -> io.BytesIO:
    """
    1. Tente d'utiliser edge-tts (voix Neural)
    2. Si échec, bascule automatiquement sur gTTS
    Retourne un BytesIO contenant du MP3.
    """

    # 1️⃣ Tentative avec edge-tts
    try:
        async def _generate_edge(texte_inner: str) -> io.BytesIO:
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
        audio_fp = loop.run_until_complete(_generate_edge(texte))
        loop.close()

        # sécurité : si vraiment rien n'a été reçu
        if audio_fp.getbuffer().nbytes == 0:
            raise RuntimeError("edge-tts n'a renvoyé aucun audio.")

        return audio_fp

    except Exception:
        # 2️⃣ Fallback avec gTTS
        tts = gTTS(text=texte, lang="fr", slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer

# --- BLOC UI : LECTURE AUDIO ---
st.subheader("🔊 Lecture audio de la réponse")

if st.button("Lire la réponse à voix haute"):
    if not st.session_state.reponse_ia:
        st.warning("⚠️ Vous devez d’abord envoyer une question et obtenir une réponse.")
    else:
        try:
            audio_fp = synthese_vocale(st.session_state.reponse_ia)
            st.audio(audio_fp, format="audio/mp3")
        except Exception as e:
            st.error(f"Erreur audio : {e}")
