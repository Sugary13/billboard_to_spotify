from bs4 import BeautifulSoup
import requests
import webbrowser
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
USERNAME = os.getenv("USERNAME")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = "playlist-modify-private"

date = input("A que año quieres viajar? Recuerda escribirlo en este formato YYYY-MM-DD: ")
if not date:
    raise ValueError("Debes especificar la fecha con formato YYYY-MM-DD")

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/140.0.0.0 Safari/537.36'}

response = requests.get(f"https://www.billboard.com/charts/hot-100/{date}", headers=header)

if response.status_code != 200:
    raise ValueError("No se ha podido conectar al servidor o la fecha esta mal escrita.")

soup = BeautifulSoup(response.text, 'html.parser')
songs = soup.select('li ul li h3', id='title-of-a-story')


songs_clean = [song.text.strip() for song in songs]

if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and REDIRECT_URI) :
    raise ValueError("You must specify all environment variables and try again.")

CACHE = ".cache-spotify"


sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE,
)

# Si ya hay token válido, Spotipy lo devuelve; si no, abre el flujo de auth.
token_info = sp_oauth.get_cached_token()
if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    print("Abre esta URL en tu navegador para autorizar la app:\n", auth_url)
    # opcional: abrir automáticamente
    webbrowser.open(auth_url, new=2)
    # Spotipy intentará capturar la respuesta si tu REDIRECT_URI es local (ej: http://localhost:8888/callback)
    # Si no hay servidor, el usuario puede pegar la URL a la que Spotify redirigió:
    response_url = input("Después de autorizar, pega aquí la URL completa a la que fuiste redirigido: ").strip()
    code = sp_oauth.parse_response_code(response_url)
    token_info = sp_oauth.get_access_token(code)

year = date.split("-")[0]

access_token = token_info['access_token']
sp = spotipy.Spotify(auth=access_token)
print("Listo. Token obtenido.")

current_user = sp.current_user()
current_user_id = current_user['id']

playlist = sp.user_playlist_create(current_user_id, f"Mejores canciones de {date}", False, False,
                                   f"Este es una playlist creada en base a la pagina de Billboard utilizando "
                                   f"sus top 100 en base a una fecha, la fecha elegida fue {date}. (Si la cancion no "
                                   f"fue encontrada en Spotify se omite).")
playlist_id = playlist['id']

song_ids = []

for song in songs_clean:
    try:
        song_data = sp.search(q=f"track: {song} year: {year}" , type="track", limit=1)
        song_id = song_data['tracks']['items'][0]['id']
        song_ids.append(song_id)
    except IndexError:
        print(f"La cancion {song} no fue encontrada.")

sp.playlist_add_items(playlist_id=playlist_id,items= song_ids)
print(f"La playlist con el nombre de Top 100 de {date}, ¡Fueron agregadas {len(song_ids)} canciones con exito!.")






