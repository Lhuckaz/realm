## 🌐 Realm: Your Gateway to Movie & Series Streams 🎬📺

Welcome to **Realm**, a simple web application designed to help you discover and access torrent streams for your favorite movies and TV series using their IMDb IDs. Say goodbye to endless searching and hello to direct magnet links!

---

## ✨ Features

* **🔍 Intuitive Search:** Easily find movies and TV shows by name, powered by a popular film data service.
* **🆔 Smart ID Resolution:** Automatically fetches IMDb IDs (or a fallback ID) for seamless integration with stream providers.
* **🔗 Instant Stream Discovery:** Connects with a public stream API to fetch available torrent streams for your selected content.
* **🧲 Direct Magnet Links:** Generates ready-to-use magnet links, complete with embedded public trackers for improved downloadability.
* **📋 One-Click Copy:** Conveniently copy magnet links to your clipboard.
* **⚡ Direct Magnet Button:** Immediately open magnet links in your system's default torrent client.
* **🏠 User-Friendly Interface:** A clean and straightforward UI for quick navigation and usage.
* **🐳 Dockerized Deployment:** Designed for easy setup and deployment using Docker containers.
* **⭐ Custom Favicon:** A small detail that adds a polished touch to your browser tabs.

---

## ⚙️ How It Works

Realm acts as a bridge between you and the vast world of torrent streams:

1.  **You Search:** Enter the name of a movie or series on the homepage.
2.  **Film Data Powers Discovery:** Realm queries a film data service to find relevant titles and retrieve their unique identifiers (including IMDb IDs).
3.  **Stream API Provides Streams:** Using the IMDb ID, Realm then pings a public stream API, a popular provider of torrent stream information.
4.  **Magnet Link Magic:** For each found stream, Realm constructs a complete magnet link, enhancing it with a list of public trackers to help your torrent client find peers more efficiently.
5.  **Access & Enjoy:** You get both a direct "Magnet Link" button to instantly open in your torrent client and a "Copy Magnet Link" button for manual use!

---

## 🚀 Technologies Used

* **Backend:** Python 🐍
* **Web Framework:** Flask 💧
* **Movie/Series Data:** FilmData API 🎬
* **Stream Data:** Public Stream API 🔗
* **Environment Variables:** `python-dotenv` 🔒
* **Containerization:** Docker 🐳

---

## 📦 Getting Started

To get Realm up and running, you'll need Docker installed on your system.

### Prerequisites

* **Docker** (Docker Desktop recommended for Windows/macOS)
* **Git** (for cloning the repository)

### Installation Steps

1.  **Fork the Repository:**
    ```bash
    git clone https://github.com/your-github-username/realm.git
    cd realm
    ```

2.  **Set Up Environment Variables:**
    Create a file named `.env` in the root directory of your project (where `app.py` is located).
    ```
    .env
    ```
    Populate it with the following required variables:

    ```ini
    # --- Film Data API ---
    TMDB_API_KEY="YOUR_API_KEY_HERE"
    TMDB_API_BASE_URL="https://api.fake-filmdata.org/3/"
    TMDB_IMAGE_BASE_URL="https://image.fake-filmdata.org/t/p/"
    PLACEHOLDER_IMAGE_URL="https://fake-placehold.co/120x180?text=No+Poster"

    # --- Public Stream API ---
    # Default public stream instance.
    TORRENT_BASE_URLS="https://public-stream-api.fake-domain.com/streams/v1/,https://another-stream-api.fake-domain.com/streams/v1/"
    # List of public trackers to append to magnet links
    TRACKERS_LIST_URL="https://raw.fake-githubusercontent.com/fake-trackers/list/master/trackers_best.txt"
    ```

3.  **Build the Docker Image:**
    ```bash
    docker build -t realm .
    ```

4.  **Run the Docker Container:**
    ```bash
    docker run -p 8000:8000 \
    -e TMDB_API_KEY="YOUR_TMDB_API_KEY_HERE" \
    -e TMDB_API_BASE_URL="https://api.fake-filmdata.org/3/" \
    -e TMDB_IMAGE_BASE_URL="https://image.fake-filmdata.org/t/p/" \
    -e PLACEHOLDER_IMAGE_URL="https://fake-placehold.co/120x180?text=No+Poster" \
    -e TORRENT_BASE_URLS="https://public-stream-api.fake-domain.com/streams/v1/,https://another-stream-api.fake-domain.com/streams/v1/" \
    -e TRACKERS_LIST_URL="https://raw.fake-githubusercontent.com/fake-trackers/list/master/trackers_best.txt" \
    realm
    ```

6.  **Access the Application:**
    Open your web browser and navigate to:
    [http://localhost:8000](http://localhost:5000)

---

## ✍️ Author

* This application was built with the help of AI.

## 👀 Observations

* Be careful with block of IP from stream api's
