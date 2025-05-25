from kafka import KafkaProducer
import requests
import json
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_KEY = 'd84f4110d854d49599cb684104af8b58'
HEADERS = {'x-apisports-key': API_KEY}
KAFKA_SERVER = 'localhost:9093'
TOPIC_NAME = 'live-matches'

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    batch_size=16384,
    linger_ms=5,
    compression_type='gzip',
    retries=5,
    max_block_ms=10000
)

# === API Helper Functions ===
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        return r.json().get('response', [])
    except requests.RequestException:
        return []

def get_live_matches():
    return fetch('https://v3.football.api-sports.io/fixtures?live=all')

def get_events(fixture_id):
    return fetch(f'https://v3.football.api-sports.io/fixtures/events?fixture={fixture_id}')

def get_statistics(fixture_id):
    return fetch(f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}')

def get_lineups(fixture_id):
    return fetch(f'https://v3.football.api-sports.io/fixtures/lineups?fixture={fixture_id}')

def get_players_stats(fixture_id):
    return fetch(f'https://v3.football.api-sports.io/fixtures/players?fixture={fixture_id}')

# Main loop
logger.info("🚨 Starting live match producer... Press Ctrl+C to stop.")

try:
    while True:
        matches = get_live_matches()
        if not matches:
            logger.warning("⛔ No live matches found.")
            time.sleep(60)
            continue

        for match in matches:
            fixture_id = match['fixture']['id']
            league_id = match['league']['id']

            # Gather all data
            payload = {
                'fixture': match,
                'league_id': league_id,
                'events': get_events(fixture_id),
                'statistics': get_statistics(fixture_id),
                'lineups': get_lineups(fixture_id),
                'players': get_players_stats(fixture_id)
            }

            # === Display in Console ===
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            elapsed = match['fixture']['status'].get('elapsed', 'N/A')
            status = match['fixture']['status']['long']
            venue = match['fixture']['venue']

            print("=" * 70)
            print(f"📺 LIVE: {home} vs {away}")
            print(f"⏱️ {status} ({elapsed} min)")
            print(f"🏟️ {venue['name']} - {venue['city']}")
            print(f"🔢 Score: {match['score']['fulltime']['home']} - {match['score']['fulltime']['away']}")

            # Events
            print("\n📌 EVENTS:")
            events = payload['events']
            if events:
                for e in events:
                    print(f" - {e['time']['elapsed']}' {e['team']['name']} | {e['type']} - {e['player']['name']} ({e['detail']})")
            else:
                print("  Aucun événement.")

            # Statistics
            print("\n📊 STATISTICS:")
            for stat in payload['statistics']:
                print(f"📊 {stat['team']['name']}")
                for s in stat['statistics']:
                    print(f"   - {s['type']}: {s['value']}")

            # Lineups
            print("\n🧤 LINEUPS:")
            for team in payload['lineups']:
                formation = team.get('formation', 'N/A')
                print(f"{team['team']['name']} ({formation})")
                starters = [p["player"]["name"] for p in team.get("startXI", [])]
                print("   ➤ " + ", ".join(starters) if starters else "   ➤ (Non disponible)")

            # Players
            print("\n👤 PLAYERS:")
            for team in payload['players']:
                print(f"{team['team']['name']}")
                for player in team.get('players', []):
                    print(f"   - {player['player']['name']} : {player['statistics']}")
            print("=" * 70 + "\n")

            # Send to Kafka
            producer.send(TOPIC_NAME, key=str(fixture_id).encode('utf-8'), value=payload)
            logger.info(f"✅ Sent live match: {fixture_id} - {home} vs {away}")

        producer.flush()
        time.sleep(30)

except KeyboardInterrupt:
    logger.info("🛑 Producer manually stopped.")
finally:
    producer.close()
    logger.info("Kafka producer closed.")
