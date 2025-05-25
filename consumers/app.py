import streamlit as st

st.set_page_config(page_title="🏠 Accueil - Dashboard FIFA", layout="wide")

st.markdown("""
    <div style='text-align:center; padding-top:50px;'>
        <h1 style='font-size: 3em;'>🏟️ Bienvenue sur le <span style="color:#1E90FF;">Dashboard FIFA</span></h1>
        <p style='font-size: 1.5em; margin-top: 30px;'>Choisissez une vue pour continuer :</p>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    c1, c2 = st.columns(2)

    with c1:
        if st.button("✅ Matchs Terminés", use_container_width=True):
            st.switch_page("pages/finished-view.py")

    with c2:
        if st.button("📺 Matchs en Direct", use_container_width=True):
            st.switch_page("pages/live-view.py")
