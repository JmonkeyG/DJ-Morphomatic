import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Expander:
    """
    Example usage::

        import morphomatic

        playlist = "example"
        m = morphomatic.Expander()

        try:
            m.expand(playlist)
            print('Songs Added to Spotify')
        except Exception as e:
            print(f'{e}')
    """

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 username_id: str,
                 redirect_uri="http://localhost:8888/callback",
                 scope="playlist-modify-public"
                 ):
        """
            A class that expands a spotify playlist by searching through the playlist and finding similar songs to add.

            Initial Defined Variables:
                client_id => provided client id
                client_secret => provided client secret

        :param client_id: The client id can be found on the spotify developer app details page
        :param client_secret: The client secret can be found on the spotify developer app details page
        :param username_id: The username id can be found on the spotify account overview page
        :param redirect_uri: redirect uri must be provided in spotify app. Default => http://localhost:8888/callback
        :param scope: scope must be provided in spotify app. Default => playlist-modify-public
        """
        self.playlist_data = None
        self.playlist_name = None
        self.playlist_id = None
        self.playlist_length = None
        self.expand_val = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.username_id = username_id
        self.redirect_uri = redirect_uri
        self.RECOMMENDATIONS_MAX_LIMIT = 50
        self.RETRY_MAX_COUNT = 8
        self.scope = scope
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=self.scope))
        # self.available_genres = self.sp.recommendation_genre_seeds()['genres']

    def expand(self,
               playlist_name,
               expand_val=5,
               ):
        """
        Searches through a playlist provided as a param (.lower() to the str) and find suggested songs to add. Then Adds the songs automatically.

        :param expand_val: An int that contains the number of songs to add to the playlist. Default => 5
        :param playlist_name: A str that contains the name of the playlist to expand. Default => None
        :return: A bool that contains if the playlist was expanded
        """
        if not playlist_name or type(playlist_name) is not str:  # makes sure that input contains a str
            raise ValueError('Error: param->playlist must contain a str')
        if expand_val > 20 or type(expand_val) is not int:  # makes sure that input contains an int less than or equal to 20
            raise ValueError('Error: param->expand_val must an int less than or equal to 20')

        self.playlist_data = self.sp.user_playlists(self.username_id)['items']  # get a list of the users playlists
        self.expand_val = expand_val  # set expand_val

        for playlist in self.playlist_data:  # see if the input is a valid playlist
            if playlist_name.lower() == playlist['name'].lower():  # if so, set variables
                self.playlist_name = playlist['name']
                self.playlist_id = playlist['id']
                self.playlist_length = playlist['tracks']['total']

        if not self.playlist_name:  # if playlist_name is not set, raise error
            raise KeyError('Error: input playlist is not in users playlists')

        if self.playlist_length > 5:  # if playlist is longer than 5 songs, get a random int
            rand_int = random.randint(0, self.playlist_length - 5)
        else:
            rand_int = 0

        for i in range(self.expand_val // 5):  # add 5 songs to playlist
            self.add_songs(self.playlist_id, self.suggest_songs(self.get_track_ids(rand_int), 5))

        if self.expand_val % 5 != 0:  # add the remaining songs to playlist
            self.add_songs(self.playlist_id, self.suggest_songs(self.get_track_ids(rand_int), self.expand_val % 5))

        return True

    def add_songs(self,
                  playlist_id: str,
                  song_uris: list
                  ):
        """
        Adds songs to a playlist

        :param playlist_id:
        :param song_uris:
        :return: A bool that contains if the songs were added to the playlist
        """
        if not song_uris:
            raise ValueError('Error: param->song_uris must contain a list of song uris')
        self.sp.playlist_add_items(playlist_id, self.check_valid_uris([song_uri['uri'] for song_uri in song_uris]))
        return True

    def get_track_ids(self,
                      rand_int: int
                      ):
        """
        Gets a list of track ids from a playlist

        :param rand_int: A random int that is used to get a random set of songs from a playlist
        :return: A list of track ids
        """
        playlist_data = self.sp.playlist_items(playlist_id=self.playlist_id, limit=5, offset=rand_int)['items']
        return [(item['track'])['id'] for item in playlist_data]

    def suggest_songs(self,
                      track_ids: list,
                      limit: int
                      ):
        """
        Gets a list of suggested songs from a list of track artists

        :param track_ids: A list of track ids
        :param limit: An int that contains the number of songs to add to the playlist. Default => 5
        :return: A list of suggested songs
        """
        seed_tracks = track_ids
        recommendations = []
        for i in range(self.RETRY_MAX_COUNT):
            spotify_recommendations = self.sp.recommendations(seed_tracks=seed_tracks, limit=limit)['tracks']
            for recommendation in spotify_recommendations:
                recommendations.append(recommendation)
            if limit > 0:
                spotify_recommendations = self.sp.recommendations(seed_artists=seed_tracks, limit=limit)['tracks']
                for recommendation in spotify_recommendations:
                    recommendations.append(recommendation)
        return recommendations[:limit]

    def check_valid_uris(self,
                         song_uris: list
                         ):
        """
        Checks if a list of song uris are valid

        :param song_uris: A list of song uris
        :return: A list of valid song uris
        """
        valid_song_uris = []
        range_val = 0
        while len(song_uris) > 0:
            range_val += 1
            song_uris = song_uris[100:]
        current_tracks = []
        for i in range(range_val):
            current_tracks += self.sp.tracks(song_uris[100 * i:100 * (i + 1)])['tracks']
            track_ids = [(item['track'])['id'] for item in current_tracks]
            for track_id in track_ids:
                current_tracks.append(f'spotify:track:{track_id}')
        for song_uri in song_uris:
            if song_uri not in current_tracks:
                valid_song_uris.append(song_uri)
            else:
                print('failed to add song: already in playlist')
        return valid_song_uris
