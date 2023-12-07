import os
import random
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

RECOMMENDATIONS_MAX_LIMIT = 30
RETRY_MAX_COUNT = 8

load_dotenv()

scope = "playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

available_genres = sp.recommendation_genre_seeds()['genres']


def add_songs(playlist_id, song_uris):
    if not song_uris:
        return
    sp.playlist_add_items(playlist_id, song_uris)


def add_songs_prompt(recommendations, playlist_title):
    song_uris = {}
    for song in recommendations:
        song_artist = ', '.join([artist['name'] for artist in song['artists']])
        song_title = song['name']
        while True:
            match input(f'\nWould you like to add "{song_title}" by {song_artist}, to {playlist_title}? (y/n)\n-> ').lower():
                case "y":
                    song_uris[(song['uri'])] = {'title': song_title, 'artists': song_artist}
                    break
                case "yes":
                    song_uris[(song['uri'])] = {'title': song_title, 'artists': song_artist}
                    break
                case "n":
                    break
                case "no":
                    break
    return song_uris


def suggest_songs(track_ids, track_artists, track_genres, limit, range_val):
    seed_tracks = track_ids
    seed_artists = [track_artists]
    seed_genres = [track_genres]

    recommendations = []
    for i in range(range_val):
        spotify_recommendations = sp.recommendations(seed_artists=seed_artists, seed_genres=seed_genres, seed_tracks=seed_tracks, limit=20)['tracks']
        for recommendation in spotify_recommendations:
            recommendations.append(recommendation)
    if limit > 0:
        spotify_recommendations = sp.recommendations(seed_artists=seed_artists, seed_genres=seed_genres, seed_tracks=seed_tracks, limit=limit)['tracks']
        for recommendation in spotify_recommendations:
            recommendations.append(recommendation)
    return recommendations


def get_track_data(track_ids):
    track_artists = []
    track_genres = []
    tracks = sp.tracks(track_ids)['tracks']
    for track in tracks:
        artist = track['artists'][0]['id']
        genre = sp.artist(artist)['genres']
        if genre:
            genre = genre[0]
        track_artists.append(artist)
        track_genres.append(genre)
    temp_lst = []
    for genre in track_genres:
        if genre in available_genres:
            temp_lst.append(genre)
    return track_artists, temp_lst


def check_playlist_contains_track(song_uris, playlist_length, playlist_id):
    valid_song_uris = []
    range_val = 0
    while playlist_length > 0:
        range_val += 1
        playlist_length -= 100
    current_tack_uris = []
    for i in range(range_val):
        current_tracks = sp.playlist_items(playlist_id=playlist_id, offset=100 * i, limit=100, market='US')
        track_ids = [(item['track'])['id'] for item in current_tracks['items']]
        for track_id in track_ids:
            current_tack_uris.append(f'spotify:track:{track_id}')
    for song_uri in song_uris:
        if song_uri not in current_tack_uris:
            valid_song_uris.append(song_uri)
        else:
            print('failed to add song: already in playlist')
    return valid_song_uris


def manual_genre(playlist_title, temp_lst):
    user_genre = input(f"\nProgram couldn't find a genre from {playlist_title}. Please enter one manually\n-> ").lower()

    if user_genre in available_genres:
        temp_lst.append(user_genre)
    else:
        match input(f"Entered genre wasn't in available genre list. Would you like to try another? (y/n)\n-> ").lower():
            case "y":
                return manual_genre(playlist_title, temp_lst)
            case "yes":
                return manual_genre(playlist_title, temp_lst)
            case "n":
                raise Exception('Error: Genre never found. Ending program...')
            case "no":
                raise Exception('Error: Genre never found. Ending program...')
    return temp_lst


def run_expand_playlist():
    search_playlist = str(input("\nWhat playlist would you like to expand?\n-> ")).lower()
    user_playlist_data = sp.user_playlists(os.getenv("USERNAME_ID"))
    playlists_data = user_playlist_data['items']
    result_playlist = None
    for playlist in playlists_data:
        playlist_name = str(playlist['name']).lower()
        if playlist_name == search_playlist:
            result_playlist = playlist
            break
    if result_playlist is None:
        raise ValueError('Error: input playlist is not in user_playlists')
    playlist_id = result_playlist["id"]
    track_length = result_playlist['tracks']['total']
    if track_length < 3:
        raise Exception('Error: Playlist must contain at least 3 song in order to expand.')
    playlist_title = result_playlist['name']
    rand_int = random.randint(0, track_length - 3)
    playlist_data = sp.playlist_items(playlist_id=playlist_id, limit=3, offset=rand_int)
    track_ids = [(item['track'])['id'] for item in playlist_data['items']]
    track_artists, temp_lst = get_track_data(track_ids)

    retry_count = 0
    while not temp_lst:
        if retry_count > RETRY_MAX_COUNT:
            break

        rand_int = random.randint(0, track_length - 3)

        new_playlist_items = sp.playlist_items(playlist_id=playlist_id, limit=3, offset=rand_int)
        track_ids = [item['track']['id'] for item in new_playlist_items['items']]

        track_artists, temp_lst = get_track_data(track_ids)
        retry_count += 1

    if not temp_lst:
        temp_lst = manual_genre(playlist_title, temp_lst)

    track_genres = temp_lst
    recommendation_limit = input(
        f'\nHow many recommendations would you like for {playlist_title}? (MAX -> {RECOMMENDATIONS_MAX_LIMIT}, default -> 5)\n-> ')
    if not recommendation_limit or not recommendation_limit.isdigit():
        recommendation_limit = 5
    recommendation_limit = int(recommendation_limit)
    if recommendation_limit > RECOMMENDATIONS_MAX_LIMIT:
        recommendation_limit = RECOMMENDATIONS_MAX_LIMIT

    range_val = 0
    while recommendation_limit >= 20:
        range_val += 1
        recommendation_limit -= 20

    recommendations = suggest_songs(track_ids, track_artists[0], track_genres[0], recommendation_limit, range_val)
    song_uris = add_songs_prompt(recommendations, playlist_title)
    print('\nadding songs...\n')
    time.sleep(1)
    valid_song_uris = check_playlist_contains_track(song_uris, track_length, playlist_id)
    add_songs(playlist_id, valid_song_uris)
    print(f'\nNew songs added to {playlist_title}. Check out the new songs on Spotify!')
    time.sleep(1)
    while True:
        match input(f'Would you like more recommendations? (y/n)\n-> ').lower():
            case "y":
                run_expand_playlist()
                break
            case "yes":
                run_expand_playlist()
                break
            case "n":
                break
            case "no":
                break


def main():
    try:
        requested_task = input('What would you like to do? (expand or play)\n-> ').lower()
        match requested_task:
            case "expand":
                run_expand_playlist()
            case "play":
                pass
            case _:
                main()
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()
