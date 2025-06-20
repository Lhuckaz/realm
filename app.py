from flask import Flask, request, render_template_string, url_for
import requests
import os
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- Load API Keys and URLs from environment variables ---
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_BASE_URL = os.getenv("TMDB_API_BASE_URL")
TMDB_IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL")
PLACEHOLDER_IMAGE_URL = os.getenv("PLACEHOLDER_IMAGE_URL")
TORRENT_BASE_URL = os.getenv("TORRENT_BASE_URL")
TRACKERS_LIST_URL = os.getenv("TRACKERS_LIST_URL")

# --- Validate essential environment variables ---
if not TMDB_API_KEY:
    raise Exception("TMDB_API_KEY is not set in the environment variables.")
if not TMDB_API_BASE_URL:
    raise Exception("TMDB_API_BASE_URL is not set in the environment variables.")
if not TMDB_IMAGE_BASE_URL:
    raise Exception("TMDB_IMAGE_BASE_URL is not set in the environment variables.")
if not PLACEHOLDER_IMAGE_URL:
    raise Exception("PLACEHOLDER_IMAGE_URL is not set in the environment variables.")
if not TORRENT_BASE_URL:
    raise Exception("TORRENT_BASE_URL is not set in the environment variables.")
if not TRACKERS_LIST_URL:
    raise Exception("TRACKERS_LIST_URL is not set in the environment variables.")


# Function to load trackers from the URL. If unavailable, an empty list is returned.
def load_trackers():
    trackers = []
    try:
        print(f"Attempting to fetch trackers from: {TRACKERS_LIST_URL}")
        # Add a timeout to prevent the app from hanging indefinitely
        response = requests.get(TRACKERS_LIST_URL, timeout=10) 
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        # Process the fetched content
        for line in response.text.splitlines():
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith("#"):
                trackers.append(stripped_line)
        print(f"Successfully loaded {len(trackers)} trackers from URL.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching trackers from URL ({TRACKERS_LIST_URL}): {e}")
        print("No trackers will be used for this session.")
        trackers = [] # Explicitly set to empty list if fetch fails
    except Exception as e:
        print(f"An unexpected error occurred while loading trackers: {e}")
        print("No trackers will be used for this session.")
        trackers = [] # Explicitly set to empty list if other errors occur
    
    return trackers

# Initialize TRACKERS by loading from URL (or an empty list if unavailable)
TRACKERS = load_trackers()

# Function to build magnet link
def build_magnet_link(info_hash, encoded_display_name):
    magnet = f"magnet:?xt=urn:btih:{info_hash}"
    if encoded_display_name:
        magnet += f"&dn={encoded_display_name}"
    for tracker in TRACKERS: # Use the global TRACKERS variable (could be empty)
        magnet += f"&tr={quote(tracker, safe='')}"
    return magnet

def extract_display_name(title):
    if not title:
        return ''
    return title.split('👤')[0].strip()

# ================================
# Common HTML Snippets for Buttons and Styles
# ================================
common_button_styles = """
    .home-button {
        display: inline-block;
        padding: 8px 15px;
        margin-bottom: 20px;
        background-color: #3e3e3e; /* Darker gray for general buttons */
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        border: none;
        cursor: pointer;
        margin-right: 10px; /* Space between buttons */
    }
    .error { color: red; margin-bottom: 10px; font-weight: bold; }
    .message { color: green; margin-bottom: 10px; font-weight: bold; }
    /* Styles for the new magnet link button */
    .magnet-button {
        display: inline-block;
        padding: 8px 15px;
        background-color: #007bff; /* A nice blue color */
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        border: none;
        cursor: pointer;
        margin-right: 10px;
        margin-top: 5px; /* Add some space above if needed */
    }
    .search-form {
        display: flex; /* Make input and button sit side-by-side */
        gap: 10px; /* Space between input and button */
        margin-bottom: 20px;
        align-items: center; /* Vertically align them */
        flex-wrap: wrap; /* Allow wrapping on small screens */
    }

    /* Updated selector to include input[type="number"] */
    .search-form input[type="text"],
    .search-form input[type="number"] {
        flex-grow: 1; /* Allow input to take available space */
        padding: 12px 18px; /* More padding for a softer look */
        border: 1px solid #ddd; /* Light grey border */
        border-radius: 25px; /* Pill shape */
        font-size: 16px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); /* Subtle inner shadow */
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        min-width: 150px; /* Adjusted min-width for number inputs too */
    }

    .search-form input[type="text"]:focus,
    .search-form input[type="number"]:focus { /* Added focus for number inputs */
        border-color: #007bff; /* Highlight on focus */
        box-shadow: 0 0 0 3px rgba(0,123,255,0.25); /* Blue glow on focus */
        outline: none; /* Remove default outline */
    }

    .search-form button[type="submit"] {
        padding: 12px 25px; /* Matching padding */
        background-color: #007bff; /* Blue, consistent with magnet button */
        color: white;
        border: none;
        border-radius: 25px; /* Pill shape */
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2); /* Subtle shadow */
    }

    .search-form button[type="submit"]:hover {
        background-color: #0056b3; /* Darker blue on hover */
        transform: translateY(-1px); /* Slight lift */
    }

    .header-container {
        text-align: center; /* Centers inline-block elements like h1 and the home button */
        margin-bottom: 20px; /* Adds space below the header section */
    }
"""

common_buttons_html = f"""
    <a href="{{{{ url_for('index') }}}}" class="home-button">🏠 Home</a>
"""

# Common HTML Head for Favicon (add this new variable)
# Assumes favicon.ico is in your 'static' folder
common_head_html = f"""
    <link rel="icon" href="{{{{ url_for('static', filename='favicon.ico') }}}}" type="image/x-icon">
"""

# ================================
# Index Route - App name: Realm
# ================================
@app.route("/", methods=["GET", "POST"])
def index():
    query = None
    search_results = []
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if query:
            # Use TMDB_API_BASE_URL from .env
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
                        continue  # Skip other types

                    # --- CONSOLIDATED IMDB ID FETCHING LOGIC ---
                    imdb_id = None
                    # Use TMDB_API_BASE_URL from .env
                    external_ids_url = f"{TMDB_API_BASE_URL}{media_type}/{tmdb_id}/external_ids"
                    external_ids_params = {"api_key": TMDB_API_KEY}
                    
                    try:
                        external_ids_response = requests.get(external_ids_url, params=external_ids_params)
                        external_ids_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                        external_ids_data = external_ids_response.json()
                        imdb_id = external_ids_data.get('imdb_id')
                    except requests.exceptions.RequestException as e:
                        print(f"Error fetching external IDs for {media_type} (ID: {tmdb_id}): {e}")
                        pass # Continue to the fallback logic below

                    # Fallback to TMDb ID if IMDb ID is missing or external_ids call failed
                    if not imdb_id:
                        imdb_id = f"tm{tmdb_id}"

                    search_results.append(
                        {
                            "Title": item.get("title") or item.get("name"),
                            "Year": (item.get("release_date") or item.get("first_air_date") or "")[:4],
                            "imdbID": imdb_id,
                            "Poster": (
                                # Use TMDB_IMAGE_BASE_URL from .env
                                f"{TMDB_IMAGE_BASE_URL}w200{item.get('poster_path')}"
                                if item.get("poster_path")
                                else PLACEHOLDER_IMAGE_URL # Use PLACEHOLDER_IMAGE_URL from .env
                            ),
                            "Type": media_type,
                        }
                    )
                if not search_results:
                    error = "Nenhum item com IMDb ID encontrado."
            else:
                error = f"TMDb API Error: {resp.status_code}"
        else:
            error = "Por favor, insira o nome do filme ou série."

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Realm</title>
        {common_head_html}
        <style>
            body {{ font-family: Arial; background: #f4f4f4; padding: 20px; }}
            .card {{
                background: white;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                gap: 15px;
                align-items: center;
            }}
            .card img {{
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                width: 120px;
                height: auto;
            }}
            .error {{ color: red; margin-bottom: 20px; }}
            {common_button_styles}
        </style>
    </head>
    <body>
        <div class="header-container">
            <h1>Realm</h1>
            {common_buttons_html}
        </div>
        <form method="POST" class="search-form">
            <input type="text" name="query" placeholder="Enter movie or series name" required value="{{{{ query or '' }}}}">
            <button type="submit">Search</button>
        </form>

        {{% if error %}}
            <div class="error">{{{{ error }}}}</div>
        {{% endif %}}

        {{% for item in search_results %}}
            <div class="card">
                <img src="{{{{ item.Poster }}}}" alt="Poster">
                <div>
                    <h3>{{{{ item.Title }}}} ({{{{ item.Year }}}})</h3>
                    {{% if item.Type == 'movie' %}}
                        <a href="{{{{ url_for('streams', imdb_id=item.imdbID) }}}}">🎬 View Movie Streams</a>
                    {{% elif item.Type == 'tv' %}}
                        <a href="{{{{ url_for('series', imdb_id=item.imdbID) }}}}">📺 View Series Episodes</a>
                    {{% endif %}}
                </div>
            </div>
        {{% endfor %}}
    </body>
    </html>
    """, query=query, search_results=search_results, error=error)


# ================================
# Movie Streams Route
# ================================
@app.route("/streams/<imdb_id>")
def streams(imdb_id):
    # Use TORRENT_BASE_URL from .env
    return fetch_and_display_streams(
        f"{TORRENT_BASE_URL}movie/{imdb_id}.json",
        imdb_id,
        is_series=False
    )

# ================================
# Series Streams Route (Episodes)
# ================================
@app.route("/series/<imdb_id>", methods=["GET", "POST"])
def series(imdb_id):
    validation_error = None
    
    # Get values from form or set defaults
    season_str = request.form.get("season", "1")
    episode_str = request.form.get("episode", "1")

    # Validate inputs as integers and positive
    try:
        season = int(season_str)
        episode = int(episode_str)
        
        if season <= 0 or episode <= 0:
            validation_error = "Season and Episode numbers must be positive integers."
            # Set them back to '1' for display if invalid, or keep user input if that's preferred
            season = 1
            episode = 1
    except ValueError:
        validation_error = "Season and Episode must be valid numbers."
        season = 1
        episode = 1

    if request.method == "POST" and not validation_error:
        # Proceed only if no validation error
        # Use TORRENT_BASE_URL from .env
        url = f"{TORRENT_BASE_URL}series/{imdb_id}:{season}:{episode}.json"
        return fetch_and_display_streams(url, imdb_id, is_series=True, season=season, episode=episode)

    # For GET request (initial page load) or if there's a validation error
    return render_template_string(f"""
    <html>
    <head>
        <title>Series IMDb ID: {{{{ imdb_id }}}} Stream Selection</title>
        {common_head_html}
        <style>
            body {{ font-family: Arial; background: #f4f4f4; padding: 20px; }}
            .error {{ color: red; }} 
            {common_button_styles} 
            /* Specific style for season/episode input widths if needed, but flex should handle it */
            .search-form input[type="number"] {{
                max-width: 120px; /* Adjust if needed for number inputs */
            }}
        </style>
    </head>
    <body>
        <div class="header-container">
            <h1>Series IMDb ID: {{{{ imdb_id }}}}</h1>
            {common_buttons_html}
        </div>
        <form method="POST" class="search-form"> {{% if validation_error %}}
                <div class="error" style="color: red; margin-bottom: 10px;">{{{{ validation_error }}}}</div>
            {{% endif %}}
            <input type="number" name="season" placeholder="Season" required value="{{{{ season }}}}" min="1">
            <input type="number" name="episode" placeholder="Episode" required value="{{{{ episode }}}}" min="1">
            <button type="submit">Fetch Streams</button>
        </form>
    </body>
    </html>
    """, imdb_id=imdb_id, season=season, episode=episode, validation_error=validation_error)


# ================================
# Generic Fetch & Display Function
# ================================
def fetch_and_display_streams(stream_url, imdb_id, is_series=False, season=None, episode=None):
    streams = []
    error = None

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(stream_url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict) and "streams" in data:
                streams = data["streams"]
            elif isinstance(data, list):
                streams = data
            else:
                error = f"Unexpected JSON structure: {data}"
        except Exception as e:
            error = f"Error parsing JSON: {e}"
    else:
        error = f"Failed to fetch streams: {response.status_code}"

    # Generate magnet links
    for stream in streams:
        title = stream.get("title", "")
        display_name = extract_display_name(title)
        stream["encoded_display_name"] = quote(display_name, safe='')
        info_hash = stream.get("infoHash")
        if info_hash:
            # build_magnet_link will now use global TRACKERS, which might be empty
            stream["magnet_link"] = build_magnet_link(info_hash, stream["encoded_display_name"])
        else:
            stream["magnet_link"] = None

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Streams</title>
        {common_head_html}
        <style>
            body {{ font-family: Arial; background: #f4f4f4; padding: 20px; }}
            .card {{
                background: white;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .error {{ color: red; }}
            {common_button_styles}
        </style>
        <script>
        function copyMagnet(magnet) {{
            navigator.clipboard.writeText(magnet).then(() => {{
                const msg = document.getElementById('copy-message');
                msg.style.display = 'block';
                clearTimeout(msg.timeoutId);
                msg.timeoutId = setTimeout(() => {{
                    msg.style.display = 'none';
                }}, 3000);
            }});
        }}
        </script>
    </head>
    <body>
        <div class="header-container">
            <h1>{{{{ 'Series' if is_series else 'Movie' }}}} IMDb ID: {{{{ imdb_id }}}}</h1>
            {{% if is_series %}}
                <div>Season: {{{{ season }}}} | Episode: {{{{ episode }}}}</div>
            {{% endif %}}
            {common_buttons_html}
        </div>

        {{% if error %}}
            <div class="error">{{{{ error }}}}</div>
        {{% endif %}}

        {{% if streams %}}
            {{% for stream in streams %}}
                <div class="card">
                    <h3>{{{{ stream.get('name', 'No Name') }}}}</h3>
                    <div><b>Title:</b> {{{{ stream.get('title', 'No Title') }}}}</div>
                    <div><b>InfoHash:</b> {{{{ stream.get('infoHash', 'N/A') }}}}</div>
                    {{% if stream.magnet_link %}}
                        <a href="{{{{ stream.magnet_link }}}}" class="magnet-button">🧲 Magnet Link</a>
                        <button onclick="copyMagnet('{{{{ stream.magnet_link }}}}')">📋 Copy Magnet Link</button>
                    {{% endif %}}
                </div>
            {{% endfor %}}
        {{% else %}}
            <div>No streams found.</div>
        {{% endif %}}

        <div id="copy-message" style="
            display:none;
            position: fixed;
            top: 10px;
            right: 10px;
            background: #4caf50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            font-weight: bold;
            z-index: 1000;">
            Magnet link copied to clipboard!
        </div>
    </body>
    </html>
    """, imdb_id=imdb_id, streams=streams, error=error,
    is_series=is_series, season=season, episode=episode)


# ================================
# Run the app
# ================================
if __name__ == "__main__":
    app.run(debug=True)