import streamlit as st
import json

st.set_page_config(page_title="🔴 Live Match Viewer", layout="wide")
st.title("🎥 Matchs en direct - Vue détaillée")

@st.cache_data
def load_matches(filepath=r'C:/Users/pc/Desktop/fifa_kafka/consumers/kafka_data/live_matches_data.json'):
    with open(filepath, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

matches = load_matches()

# 🎯 Filtres
st.sidebar.header("Filtres")
competition_list = sorted({m['fixture']['league']['name'] for m in matches})
selected_competitions = st.sidebar.multiselect("Filtrer par compétition", competition_list, default=[])

# 📌 Appliquer filtre
filtered_matches = matches if not selected_competitions else [
    m for m in matches if m['fixture']['league']['name'] in selected_competitions
]

# 📌 Gestion de l'état de sélection
if "selected_match_index" not in st.session_state:
    st.session_state.selected_match_index = None

# 🧾 Affichage des matchs filtrés
for idx, match in enumerate(filtered_matches):
    teams = match["fixture"]["teams"]
    score = match["fixture"]["score"]
    home = teams["home"]["name"]
    away = teams["away"]["name"]
    logo_home = teams["home"]["logo"]
    logo_away = teams["away"]["logo"]

    with st.container():
        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            st.image(logo_home, width=60)
            st.markdown(f"### {home}")
        with col2:
            st.markdown("### Score")
            st.markdown(f"## {score['fulltime']['home'] or 0} - {score['fulltime']['away'] or 0}")
        with col3:
            st.image(logo_away, width=60)
            st.markdown(f"### {away}")

        if st.button(f"📊 Voir les détails : {home} vs {away}", key=f"btn_{idx}"):
            if st.session_state.selected_match_index == idx:
                st.session_state.selected_match_index = None
            else:
                st.session_state.selected_match_index = idx

    if st.session_state.selected_match_index == idx:
        details = match

        st.subheader("📌 Événements")
        events = details.get("events", [])
        col1, col2 = st.columns(2)
        events_home = [e for e in events if e['team']['name'] == home]
        events_away = [e for e in events if e['team']['name'] == away]

        with col1:
            st.markdown(f"### 🟥 {home}")
            for e in events_home:
                st.markdown(f"- **{e['time']['elapsed']}'** | {e['type']} - *{e['player']['name']}* ({e['detail']})")

        with col2:
            st.markdown(f"### 🟦 {away}")
            for e in events_away:
                st.markdown(f"- **{e['time']['elapsed']}'** | {e['type']} - *{e['player']['name']}* ({e['detail']})")

        st.subheader("📊 Statistiques comparées")
        stats_data = details.get("statistics", [])
        if len(stats_data) == 2:
            t1, t2 = stats_data[0], stats_data[1]
            st.markdown(f"<h4 style='text-align:center; color:#eee'>{t1['team']['name']} ⚔️ {t2['team']['name']}</h4>", unsafe_allow_html=True)

            for s1, s2 in zip(t1['statistics'], t2['statistics']):
                try:
                    v1 = int(str(s1['value']).replace('%', '')) if isinstance(s1['value'], str) else int(s1['value'])
                    v2 = int(str(s2['value']).replace('%', '')) if isinstance(s2['value'], str) else int(s2['value'])
                    total = max(v1 + v2, 1)
                    p1, p2 = v1 / total * 100, v2 / total * 100
                except:
                    continue

                st.markdown(f"""
                <div style='margin:10px 0;'>
                    <div style='display:flex; justify-content:space-between; color:white;'>
                        <span>{v1}</span>
                        <span>{s1['type']}</span>
                        <span>{v2}</span>
                    </div>
                    <div style='display:flex; height:10px; background:#333; border-radius:5px; overflow:hidden;'>
                        <div style='width:{p1}%; background:#00c37d;'></div>
                        <div style='width:{p2}%; background:#4177f6;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.subheader("🏟️ Formations - Vue Terrain")
        lineups = details.get("lineups", [])
        cols = st.columns(2)
        for i, team in enumerate(lineups):
            with cols[i]:
                formation = team.get("formation", "N/A")
                coach = team.get("coach", {}).get("name", "")
                players = [p["player"]["name"] for p in team.get("startXI", [])]
                formation_lines = list(map(int, formation.split("-")))
                lines, idx2 = [], 0
                for nb in formation_lines:
                    lines.append(players[idx2:idx2 + nb])
                    idx2 += nb
                lines.insert(0, [players[-1]])
                lines = lines[::-1]

                st.markdown(f"""
                <div style='background:linear-gradient(to bottom, #4caf50, #2e7d32);
                            padding:20px; border-radius:15px; margin-bottom:20px;'>
                    <h4 style='color:white; text-align:center;'>{team['team']['name']} ({formation})</h4>
                    <p style='color:white; text-align:center;'>🧳 Coach : {coach}</p>
                </div>
                """, unsafe_allow_html=True)

                for line in lines:
                    player_line = "".join(
                        f"<span style='padding:8px 14px; background:#333; color:white; border-radius:10px; margin:5px; display:inline-block;'>{p}</span>"
                        for p in line
                    )
                    st.markdown(f"<div style='text-align:center; margin:10px 0;'>{player_line}</div>", unsafe_allow_html=True)

        st.subheader("👤 Statistiques des Joueurs")
        teams_players = details.get("players", [])
        cols = st.columns(2)
        for i, team in enumerate(teams_players):
            with cols[i]:
                team_name = team['team']['name']
                team_id = team['team']['id']
                st.markdown(f"### 🛡️ {team_name}")

                players = team.get("players", [])
                player_names = [p["player"]["name"] for p in players]

                if player_names:
                    st.selectbox(
                        f"Sélectionner un joueur - {team_name}",
                        options=player_names,
                        key=f"selected_player_{team_id}"
                    )
                    selected_player = st.session_state[f"selected_player_{team_id}"]

                    for p in players:
                        if p["player"]["name"] == selected_player:
                            stats = p.get("statistics", [{}])[0]
                            st.markdown("---")
                            st.markdown(f"**🎯 Position :** {stats['games'].get('position', '?')}")
                            st.markdown(f"**⏱️ Temps de jeu :** {stats['games'].get('minutes', '?')} min")
                            st.markdown(f"**⭐ Note :** {stats['games'].get('rating', '?')}")
                            st.markdown(f"**📦 Passes :** {stats.get('passes', {}).get('total', 0)} (🎯 Précision : {stats.get('passes', {}).get('accuracy', '?')}%)")
                            st.markdown(f"**🎯 Tirs cadrés :** {stats.get('shots', {}).get('on', 0)} / {stats.get('shots', {}).get('total', 0)}")
                            st.markdown(f"**⚽ Buts :** {stats.get('goals', {}).get('total', 0)} | 🎁 Assist : {stats.get('goals', {}).get('assists', 0)}")
                            st.markdown(f"**🛡️ Tacles :** {stats.get('tackles', {}).get('total', 0)} | 🕵️ Interceptions : {stats.get('tackles', {}).get('interceptions', 0)}")
                            st.markdown(f"**🤼 Duels gagnés :** {stats.get('duels', {}).get('won', 0)} / {stats.get('duels', {}).get('total', 0)}")
                            st.markdown(f"**🟨🟥 Cartons :** 🟨 {stats.get('cards', {}).get('yellow', 0)} | 🟥 {stats.get('cards', {}).get('red', 0)}")
