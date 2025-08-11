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
TORRENT_BASE_URLS = [url.strip() for url in os.getenv("TORRENT_BASE_URLS", "").split(",") if url.strip()]
QB_URL = os.getenv("QB_URL")
QB_USERNAME = os.getenv("QB_USERNAME")
QB_PASSWORD = os.getenv("QB_PASSWORD")

# Validate required environment variables
for var in [
    "TMDB_API_KEY", "TMDB_API_BASE_URL", "TMDB_IMAGE_BASE_URL",
    "PLACEHOLDER_IMAGE_URL", "TORRENT_BASE_URLS", "QB_URL", "QB_USERNAME", "QB_PASSWORD"
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
    streams, error = fetch_streams_from_urls(f"movie/{imdb_id}.json")
    return fetch_and_display_streams(streams, error, imdb_id, is_series=False)


@app.route("/series/<imdb_id>/<item_title>", methods=["GET", "POST"])
def series(imdb_id, item_title):
    validation_error = None

    season, season_error = validate_positive_int(request.form.get("season", "1"))
    episode, episode_error = validate_positive_int(request.form.get("episode", "1"))

    if season_error or episode_error:
        validation_error = season_error or episode_error

    if request.method == "POST" and not validation_error:
        streams, error = fetch_streams_from_urls(f"series/{imdb_id}:{season}:{episode}.json")
        return fetch_and_display_streams(streams, error, imdb_id, is_series=True, season=season, episode=episode, item_title=item_title)

    return render_template("series.html", imdb_id=imdb_id, season=season, episode=episode, validation_error=validation_error)


def get_tmdb_info_from_imdb(imdb_id):
    """
    Get TMDB ID and media type from IMDb ID.
    """
    if not imdb_id.startswith("tt"):
        return None, None

    find_url = f"{TMDB_API_BASE_URL}find/{imdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "external_source": "imdb_id"
    }
    response = requests.get(find_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("movie_results"):
            return data["movie_results"][0]["id"], "movie"
        elif data.get("tv_results"):
            return data["tv_results"][0]["id"], "tv"
    return None, None


def get_tmdb_details(tmdb_id, media_type):
    """
    Get details from TMDb.
    """
    if not tmdb_id or not media_type:
        return None

    details_url = f"{TMDB_API_BASE_URL}{media_type}/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }
    response = requests.get(details_url, params=params)
    if response.status_code == 200:
        return response.json()
    return None


# ----------------- Send to qBittorrent -----------------
@app.route('/send_to_qb', methods=['POST'])
def send_to_qb():
    magnet = request.json.get('magnet')
    imdb_id = request.json.get('imdb_id')
    is_series = request.json.get('is_series', False)

    if not magnet or not imdb_id:
        return jsonify({'status': 'error', 'message': 'Missing magnet link or IMDb ID'}), 400

    tmdb_id, media_type = get_tmdb_info_from_imdb(imdb_id)
    details = get_tmdb_details(tmdb_id, media_type)

    if not details:
        return jsonify({'status': 'error', 'message': 'Could not get details from TMDb'}), 400

    if media_type == 'movie':
        title = details.get('title', '').replace(":", " -")
        year = details.get('release_date', '')[:4]
        save_path_name = f"{title} ({year})" if year else title
        save_path = f"/downloads/Filmes/{save_path_name}"
    elif media_type == 'tv':
        series_name = details.get('name', '').replace(":", " -")
        season = request.json.get('season')
        save_path = f"/downloads/Séries/{series_name}/Season {season}"
    else:
        return jsonify({'status': 'error', 'message': 'Unsupported media type'}), 400

    s = requests.Session()
    try:
        r = s.post(f"{QB_URL}/api/v2/auth/login", data={'username': QB_USERNAME, 'password': QB_PASSWORD})
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f"Failed to login to qBittorrent: {e}"}), 401

    data = {
        'urls': magnet,
        'savepath': save_path
    }
    
    try:
        r = s.post(f"{QB_URL}/api/v2/torrents/add", data=data)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f"Failed to add torrent: {e}"}), 400

    return jsonify({'status': 'success'})


# =====================
# Helper Function
# =====================

def fetch_streams_from_urls(path):
    streams = []
    error = None
    headers = {"User-Agent": "Mozilla/5.0"}

    for base_url in TORRENT_BASE_URLS:
        url = f"{base_url}{path}".replace("|", ",")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            fetched_streams = data.get("streams") if isinstance(data, dict) else data
            if fetched_streams:
                streams.extend(fetched_streams)
        except requests.exceptions.RequestException as e:
            error = f"Failed to fetch streams from {base_url}: {e}"
        except Exception as e:
            error = f"Error parsing JSON from {base_url}: {e}"
    
    if not streams:
        error = "No streams found from any provider."

    return streams, error


def fetch_and_display_streams(streams, error, imdb_id, is_series=False, season=None, episode=None, item_title=None):
    if error:
        return render_template(
            "streams.html",
            imdb_id=imdb_id,
            streams=[],
            error=error,
            is_series=is_series,
            season=season,
            episode=episode,
            item_title=item_title
        )

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
        error=None,
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
