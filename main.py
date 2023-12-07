import os
import morphomatic
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
username_id = os.getenv("USERNAME_ID")

m = morphomatic.Expander(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, username_id=username_id)


def main():
    try:
        requested_task = input('What would you like to do? (expand | play | end)\n-> ').lower()
        match requested_task:
            case "expand":
                search_playlist = str(input("\nWhat playlist would you like to expand?\n-> "))
                expand_val = int(input("\nHow many songs would you like to add?\n-> "))
                m.expand(playlist_name=search_playlist, expand_val=expand_val)
                print('Songs Added to Spotify')
                main()
            case "play":
                pass
            case "end":
                pass
            case _:
                main()
    except Exception as e:
        brackets = ''
        for i in range(len(str(e))):
            brackets += '-'
        print(f"{brackets}\n{e}\n{brackets}")
        main()


if __name__ == "__main__":
    main()
