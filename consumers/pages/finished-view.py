import streamlit as st
import pandas as pd
import json
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="⚽ Dashboard Matchs", layout="wide")
st_autorefresh(interval=60 * 1000, key="match_refresh")
st.title("⚽ Tableau de bord des matchs - Football")

@st.cache_data
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# 🔁 Charge les données
all_matches = load_json(r"C:\Users\pc\Desktop\fifa_kafka\consumers\kafka_data\all_matches_data.json")

# 📊 Préparer DataFrame
def parse_matches(data):
    rows = []
    for item in data:
        fxt = item.get("fixture", {}).get("fixture", {})
        league = item.get("fixture", {}).get("league", {})
        teams = item.get("fixture", {}).get("teams", {})
        score = item.get("fixture", {}).get("score", {})
        rows.append({
            "Date": fxt.get("date", ""),
            "Stade": fxt.get("venue", {}).get("name", "Inconnu"),
            "Ville": fxt.get("venue", {}).get("city", "Inconnu"),
            "Statut": fxt.get("status", {}).get("long", ""),
            "Compétition": league.get("name", "Inconnu"),
            "Pays": league.get("country", "Inconnu"),
            "Drapeau": league.get("flag", None),
            "Équipe Domicile": teams.get("home", {}).get("name", ""),
            "Équipe Extérieure": teams.get("away", {}).get("name", ""),
            "Logo Home": teams.get("home", {}).get("logo", ""),
            "Logo Away": teams.get("away", {}).get("logo", ""),
            "Score": f"{score.get('fulltime', {}).get('home', '?')} - {score.get('fulltime', {}).get('away', '?')}",
            "Raw": item  # pour détail plus tard
        })
    return pd.DataFrame(rows)

df_matches = parse_matches(all_matches)

# 🎯 Filtres
st.sidebar.header("Filtres")

# Compétitions
df_matches["Comp_Logo"] = df_matches["Drapeau"].fillna("https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Crystal_Project_missing_image.png/600px-Crystal_Project_missing_image.png")
competitions = df_matches[["Compétition", "Comp_Logo"]].drop_duplicates()
comp_options = competitions["Compétition"].tolist()
selected_comp = st.sidebar.multiselect("Filtrer par compétition", comp_options)

# Filtrage DataFrame
if selected_comp:
    filtered_df = df_matches[
        (df_matches["Statut"] == "Match Finished") &
        (df_matches["Compétition"].isin(selected_comp))
    ]
else:
    filtered_df = df_matches[
        df_matches["Statut"] == "Match Finished"
    ]

# 📌 Affichage des matchs
st.subheader("📅 Liste des matchs")
for _, row in filtered_df.iterrows():
    home, away, score = row["Équipe Domicile"], row["Équipe Extérieure"], row["Score"]
    logo_home = row["Logo Home"]
    logo_away = row["Logo Away"]

    with st.container():
        st.markdown(f"""
        <div style='background-color:#111; padding:20px; border-radius:10px; margin-bottom:20px;'>
            <div style='display:flex; justify-content:center; align-items:center; gap:50px;'>
                <div style='text-align:center;'>
                    <img src="{logo_home}" width='60'/><br>
                    <span style='color:white;'>{home}</span>
                </div>
                <div style='text-align:center; font-size:26px; color:white; font-weight:bold;'>
                    {score}
                </div>
                <div style='text-align:center;'>
                    <img src="{logo_away}" width='60'/><br>
                    <span style='color:white;'>{away}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 🎯 Si on clique pour voir les détails
        if st.button(f"📊 Voir les détails : {home} vs {away}", key=f"{home}-{away}"):
            details = row["Raw"]
            st.subheader("📌 Événements")

            col1, col2 = st.columns(2)

            # Séparer les événements par équipe
            events_home = []
            events_away = []

            for e in details.get("events", []):
                event_str = f"**{e['time']['elapsed']}'** | {e['type']} - *{e['player']['name']}* ({e['detail']})"
                if e['team']['name'] == home:
                    events_home.append(event_str)
                elif e['team']['name'] == away:
                    events_away.append(event_str)

            with col1:
                st.markdown(f"### 🟥 {home}")
                for ev in events_home:
                    st.markdown(f"- {ev}")

            with col2:
                st.markdown(f"### 🟦 {away}")
                for ev in events_away:
                    st.markdown(f"- {ev}")

            # 📊 Statistiques comparées
            st.subheader("📊 Statistiques comparées")
            stats_data = details.get("statistics", [])
            if len(stats_data) == 2:
                t1, t2 = stats_data[0], stats_data[1]
                team1_name = t1['team']['name']
                team2_name = t2['team']['name']

                st.markdown(f"""
                <h4 style='text-align:center; color:#eee'>
                    {team1_name} ⚔️ {team2_name}
                </h4>
                """, unsafe_allow_html=True)

                for s1, s2 in zip(t1['statistics'], t2['statistics']):
                    try:
                        val1 = s1['value']
                        val2 = s2['value']

                        v1 = int(str(val1).replace('%', '')) if isinstance(val1, str) else int(val1)
                        v2 = int(str(val2).replace('%', '')) if isinstance(val2, str) else int(val2)
                        total = v1 + v2 if (v1 + v2) != 0 else 1
                        p1 = v1 / total * 100
                        p2 = v2 / total * 100
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

                        # Découper la formation (ex: "3-4-3" → [3, 4, 3])
                        formation_lines = list(map(int, formation.split("-")))
                        lines = []
                        idx = 0
                        for nb in formation_lines:
                            lines.append(players[idx:idx + nb])
                            idx += nb
                        lines.insert(0, [players[-1]])  # Ajouter le gardien en bas
                        lines = lines[::-1]  # Remettre le gardien tout en haut

                        # Bloc vert équipe + coach
                        st.markdown(f"""
                        <div style='background:linear-gradient(to bottom, #4caf50, #2e7d32);
                                    padding:20px; border-radius:15px; margin-bottom:20px;'>
                            <h4 style='color:white; text-align:center;'>{team['team']['name']} ({formation})</h4>
                            <p style='color:white; text-align:center;'>🧳 Coach : {coach}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Affichage des joueurs avec fond sombre et espacement
                        for line in lines:
                            player_line = "".join(
                                f"<span style='padding:8px 14px; background:#333; color:white; border-radius:10px; margin:5px; display:inline-block;'>{p}</span>"
                                for p in line
                            )
                            st.markdown(f"<div style='text-align:center; margin:10px 0;'>{player_line}</div>", unsafe_allow_html=True)

                # Statistiques des Joueurs
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
