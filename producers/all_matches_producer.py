# all_matches_producer.py
from kafka import KafkaProducer
import requests
import json
import time
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_KEY = 'd84f4110d854d49599cb684104af8b58'
HEADERS = {'x-apisports-key': API_KEY}
KAFKA_SERVER = 'localhost:9093'
TOPIC_NAME = 'all-matches'
API_DELAY_SECONDS = 1.0  # Adjust based on API rate limits

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    batch_size=16384,
    linger_ms=5,
    compression_type='gzip',
    retries=5,
    max_block_ms=10000
)

def get_matches_by_date(date):
    url = f'https://v3.football.api-sports.io/fixtures?date={date}'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"API response for date {date}: {json.dumps(data)}")  # Log full response for debugging
        return data.get('response', [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch matches for date {date}: {e}, Status Code: {getattr(e.response, 'status_code', 'N/A')}, Response: {getattr(e.response, 'text', 'N/A')}")
        return []

def get_events(fixture_id):
    url = f'https://v3.football.api-sports.io/fixtures/events?fixture={fixture_id}'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('response', [])
    except requests.RequestException:
        return []

def get_statistics(fixture_id):
    url = f'https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('response', [])
    except requests.RequestException:
        return []

def get_lineups(fixture_id):
    url = f'https://v3.football.api-sports.io/fixtures/lineups?fixture={fixture_id}'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('response', [])
    except requests.RequestException:
        return []

def get_players_stats(fixture_id):
    url = f'https://v3.football.api-sports.io/fixtures/players?fixture={fixture_id}'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('response', [])
    except requests.RequestException:
        return []

logger.info("Starting producer for 10 historical matches (2021-01-01 to 2021-12-31)... Press Ctrl+C to stop.")

try:
    today = datetime.today()
    start_date = today - timedelta(days=1)  # Start date is today - 1 day
    end_date = today   # End date is today + 1 day

    current_date = start_date

    match_count = 0
    max_matches = 10  # Stop after 10 matches

    while current_date <= end_date and match_count < max_matches:
        date_str = current_date.strftime('%Y-%m-%d')
        logger.info(f"Processing matches for date: {date_str}")
        matches = get_matches_by_date(date_str)
        if not matches:
            logger.warning(f"No matches found for date {date_str}.")
        for match in matches:
            if match_count >= max_matches:
                break
            fixture_id = match['fixture']['id']
            league_id = match['league']['id']
            payload = {
                'fixture': match,
                'league_id': league_id,
                'events': get_events(fixture_id),
                'statistics': get_statistics(fixture_id),
                'lineups': get_lineups(fixture_id),
                'players': get_players_stats(fixture_id)
            }

            # 🔍 Afficher le contenu dans la console
            # Afficher tout le contenu du match dans la console
            print("=" * 60)
            print(f"📅 Match: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
            print(f"⚽ Fixture ID: {fixture_id}")
            print(f"🗂️ League ID: {league_id}")

            print("\n📌 EVENTS:")
            print(json.dumps(payload['events'], indent=2, ensure_ascii=False))

            print("\n📊 STATISTICS:")
            print(json.dumps(payload['statistics'], indent=2, ensure_ascii=False))

            print("\n🧤 LINEUPS:")
            print(json.dumps(payload['lineups'], indent=2, ensure_ascii=False))

            print("\n🧑‍ PLAYER STATS:")
            print(json.dumps(payload['players'], indent=2, ensure_ascii=False))

            print("=" * 60 + "\n\n")


            producer.send(TOPIC_NAME, key=str(fixture_id).encode('utf-8'), value=payload)
            logger.info(f"Sent historical match #{match_count + 1}: {fixture_id} - {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
            match_count += 1
        
        producer.flush()
        time.sleep(API_DELAY_SECONDS)  # Respect API rate limits
        current_date += timedelta(days=1)  # Move to next day

except KeyboardInterrupt:
    logger.info("Producer stopped.")
finally:
    producer.close()