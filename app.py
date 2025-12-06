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
st.write("Test de la connexion avec l’API Google Gemini, puis lecture vocale de la réponse (edge-tts et gTTS).")

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

# --- FONCTIONS DE SYNTHÈSE VOCALE ---

def synthese_edge(texte: str) -> io.BytesIO:
    """
    Génère un MP3 avec edge-tts (voix neurale Microsoft).
    Soulève une exception si aucun audio n'est reçu.
    """
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
    try:
        audio_fp = loop.run_until_complete(_generate_edge(texte))
    finally:
        loop.close()

    # Si pour une raison quelconque aucun octet n'est reçu :
    if audio_fp.getbuffer().nbytes == 0:
        raise RuntimeError("edge-tts n'a renvoyé aucun audio.")
    return audio_fp


def synthese_gtts(texte: str) -> io.BytesIO:
    """
    Génère un MP3 avec gTTS (fallback fiable).
    """
    tts = gTTS(text=texte, lang="fr", slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

# --- BLOC UI : LECTURE AUDIO ---
st.subheader("🔊 Lecture audio de la réponse")

col1, col2 = st.columns(2)

with col1:
    if st.button("Voix neurale (edge-tts)"):
        if not st.session_state.reponse_ia:
            st.warning("⚠️ Vous devez d’abord envoyer une question et obtenir une réponse.")
        else:
            try:
                audio_fp = synthese_edge(st.session_state.reponse_ia)
                st.audio(audio_fp, format="audio/mp3")
            except Exception as e:
                st.error("Erreur edge-tts :")
                st.code(repr(e))

with col2:
    if st.button("Voix standard (gTTS)"):
        if not st.session_state.reponse_ia:
            st.warning("⚠️ Vous devez d’abord envoyer une question et obtenir une réponse.")
        else:
            try:
                audio_fp = synthese_gtts(st.session_state.reponse_ia)
                st.audio(audio_fp, format="audio/mp3")
            except Exception as e:
                st.error("Erreur gTTS :")
                st.code(repr(e))
