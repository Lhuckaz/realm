from flask import Flask, request, render_template, jsonify
import requests
import os
from dotenv import load_dotenv
from urllib.parse import quote

from utils import (
    load_trackers,
    build_magnet_link,
    extract_display_name,
    validate_positive_int
)

# =====================
# App Initialization
# =====================
load_dotenv()
app = Flask(__name__)

# =====================
# Environment Variables
# =====================
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_BASE_URL = os.getenv("TMDB_API_BASE_URL")
TMDB_IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL")
PLACEHOLDER_IMAGE_URL = os.getenv("PLACEHOLDER_IMAGE_URL")
TORRENT_BASE_URL = os.getenv("TORRENT_BASE_URL")
QB_URL = os.getenv("QB_URL")
QB_USERNAME = os.getenv("QB_USERNAME")
QB_PASSWORD = os.getenv("QB_PASSWORD")

# Validate required environment variables
for var in [
    "TMDB_API_KEY", "TMDB_API_BASE_URL", "TMDB_IMAGE_BASE_URL",
    "PLACEHOLDER_IMAGE_URL", "TORRENT_BASE_URL", "QB_URL", "QB_USERNAME", "QB_PASSWORD"
]:
    if not os.getenv(var):
        raise Exception(f"{var} is not set in the environment variables.")

# =====================
# Load Trackers
# =====================
TRACKERS = load_trackers()

# =====================
# Routes
# =====================

@app.route("/", methods=["GET", "POST"])
def index():
    query = None
    search_results = []
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            search_url = f"{TMDB_API_BASE_URL}search/multi"
            params = {
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": "pt-BR",
                "include_adult": False,
                "page": 1,
            }

            resp = requests.get(search_url, params=params)

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])

                for item in results:
                    media_type = item.get("media_type")
                    tmdb_id = item.get("id")

                    if media_type not in ["movie", "tv"]:
                        continue

                    imdb_id = None
                    external_ids_url = f"{TMDB_API_BASE_URL}{media_type}/{tmdb_id}/external_ids"
                    external_ids_params = {"api_key": TMDB_API_KEY}

                    try:
                        external_ids_response = requests.get(
                            external_ids_url, params=external_ids_params)
                        external_ids_response.raise_for_status()
                        imdb_id = external_ids_response.json().get('imdb_id')
                    except:
                        pass

                    if not imdb_id:
                        imdb_id = f"tm{tmdb_id}"

                    search_results.append({
                        "Title": item.get("title") or item.get("name"),
                        "Year": (item.get("release_date") or item.get("first_air_date") or "")[:4],
                        "imdbID": imdb_id,
                        "Poster": f"{TMDB_IMAGE_BASE_URL}w200{item.get('poster_path')}" if item.get("poster_path") else PLACEHOLDER_IMAGE_URL,
                        "Type": media_type,
                    })
                if not search_results:
                    error = "Nenhum item com IMDb ID encontrado."
            else:
                error = f"TMDb API Error: {resp.status_code}"
        else:
            error = "Por favor, insira o nome do filme ou série."

    return render_template("index.html", query=query, search_results=search_results, error=error)


@app.route("/streams/<imdb_id>")
def streams(imdb_id):
    url = f"{TORRENT_BASE_URL}movie/{imdb_id}.json"
    return fetch_and_display_streams(url, imdb_id, is_series=False)


@app.route("/series/<imdb_id>/<item_title>", methods=["GET", "POST"])
def series(imdb_id, item_title):
    validation_error = None

    season, season_error = validate_positive_int(request.form.get("season", "1"))
    episode, episode_error = validate_positive_int(request.form.get("episode", "1"))

    if season_error or episode_error:
        validation_error = season_error or episode_error

    if request.method == "POST" and not validation_error:
        url = f"{TORRENT_BASE_URL}series/{imdb_id}:{season}:{episode}.json"
        return fetch_and_display_streams(url, imdb_id, is_series=True, season=season, episode=episode, item_title=item_title)

    return render_template("series.html", imdb_id=imdb_id, season=season, episode=episode, validation_error=validation_error)


# ----------------- Send to qBittorrent -----------------
@app.route('/send_to_qb', methods=['POST'])
def send_to_qb():
    magnet = request.json.get('magnet')
    raw_is_series = request.json.get('is_series', False)

    if isinstance(raw_is_series, str):
        is_series = raw_is_series.lower() == 'true'
    else:
        is_series = bool(raw_is_series)

    if is_series:
        season = request.json.get('season')
        series_name = request.json.get('item_title')

    if not magnet:
        return jsonify({'status': 'error', 'message': 'Missing magnet link'}), 400
    
    s = requests.Session()
    r = s.post(f"{QB_URL}/api/v2/auth/login", data={'username': QB_USERNAME, 'password': QB_PASSWORD})

    if r.status_code != 200:
        return jsonify({
            'status': 'error',
            'message': f"Failed to login to qBittorrent. Check credentials and URL. Status: {r.status_code}, Response: '{r.text.strip()}'"
        }), 401

    # Determine save path
    save_path = f"/downloads/Séries/{series_name}/Temporada {season}" if is_series else "/downloads/Filmes"

    data = {
        'urls': magnet,
        'savepath': save_path
    }
    r = s.post(f"{QB_URL}/api/v2/torrents/add", data=data)

    if r.status_code == 200:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to add torrent'}), 400


# =====================
# Helper Function
# =====================

def fetch_and_display_streams(stream_url, imdb_id, is_series=False, season=None, episode=None, item_title=None):
    streams = []
    error = None

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(stream_url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            streams = data.get("streams") if isinstance(data, dict) else data
        except Exception as e:
            error = f"Error parsing JSON: {e}"
    else:
        error = f"Failed to fetch streams: {response.status_code}"

    for stream in streams:
        title = stream.get("title", "")
        display_name = extract_display_name(title)
        stream["encoded_display_name"] = quote(display_name, safe='')
        info_hash = stream.get("infoHash")
        if info_hash:
            stream["magnet_link"] = build_magnet_link(info_hash, stream["encoded_display_name"], TRACKERS)
        else:
            stream["magnet_link"] = None

    return render_template(
        "streams.html",
        imdb_id=imdb_id,
        streams=streams,
        error=error,
        is_series=is_series,
        season=season,
        episode=episode,
        item_title=item_title
    )


# =====================
# Run App
# =====================

if __name__ == "__main__":
    app.run(debug=False)
