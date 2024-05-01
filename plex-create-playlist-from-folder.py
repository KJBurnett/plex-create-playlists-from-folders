# 04/29/2024
# Kyler Burnett

import json
import os
import sys
from plexapi.server import PlexServer
import requests
import time
import math
import time

from plexapi.playlist import Playlist

# Internal modules
from config import Config

def loadArguments(configFilePath: str) -> Config:
    with open(configFilePath) as configFile:
        configJson = json.load(configFile)

    config = Config(
        configJson["LIBRARY_NAME"],
        configJson["PLEX_URL"],
        configJson["PLEX_TOKEN"],
        configJson["PLAYLIST_FOLDERS"]
    )
    print(f"Loading config file from {configFilePath} was successful.")
    return config


def getRequiredVariables() -> dict[str, str]:
    return {
        "LIBRARY_NAME": "The name of your Music library in Plex. eg: 'Music'",
        "PLEX_URL": "the url of your plex server. eg: 'https://localhost:32400'",
        "PLEX_TOKEN": "The token required to access your plex api. See https://tinyurl.com/get-plex-token",
    }

# Error checking for initial startup of the script.
# We require these environment variables to ensure a smooth and successful run.
def environmentVariableError(missingVariable: str) -> None:
    requiredVariables = getRequiredVariables()
    errorMessage = f"\nError. Missing environment variable '{missingVariable}'. You must supply all required environment variables.\n\nRequired Environment Variables:{json.dumps(requiredVariables, indent=4, separators=(',', ': '))}"
    print(errorMessage)
    sys.exit()


def loadEnvironmentVariables():
    # Ensure the environment variables exist. Otherwise throw an error and quit.
    musicLibrary = os.environ.get("LIBRARY_NAME")
    if not musicLibrary:
        environmentVariableError("LIBRARY_NAME")
        sys.exit()
    baseurl = os.environ.get("PLEX_URL")
    if not baseurl:
        environmentVariableError("PLEX_URL")
        sys.exit()
    token = os.environ.get("PLEX_TOKEN")
    if not token:
        environmentVariableError("PLEX_TOKEN")
        sys.exit()

    config = Config(
        musicLibrary,
        baseurl,
        token,
    )

    print("All environment variables successfully loaded.\n")

    return config

def run():
    configFilePath = None
    if len(sys.argv) > 1:
        configFilePath = sys.argv[1]
    config = None

    if configFilePath is not None and configFilePath.endswith("json"):
        config = loadArguments(configFilePath)
    else:
        config = loadEnvironmentVariables()
    # These environment variables should be hardcoded, otherwise python will flood the terminal with warnings that the user is using an unverified https
    # connection. This can only be resolved by publishing your app. (Which we're not going to do lol)
    os.environ["SECONDS_TO_WAIT"] = "3600"
    os.environ["PYTHONWARNINGS"] = "ignore:Unverified HTTPS request"

    # Start a PlexServer API session.
    session = requests.Session()
    session.verify = False
    plex = PlexServer(config.baseurl, config.token, session)

    # ===== Let's get to work ===== #
    # We want to convert a folder of music files into a Plex playlist.                                 
    musicLibrary = plex.library.section(config.musicLibrary)

    print ("Collecting all tracks from Plex Music Library (This can take several minutes!)...")

    # Get all tracks in the library. This can take up to several minutes.
    allTracks = musicLibrary.searchTracks()

    print(f"Successfully queried all song tracks. Found: {len(allTracks)} tracks.")

    playlistFolders = []
    if isinstance(config.playlistFolders, str):
        # Convert single string into a list
        playlistFolders = [config.playlistFolders]
    else:
        playlistFolders = config.playlistFolders

    for playlistFolder in playlistFolders:
        foundPlaylistTracks = []
        for track in allTracks:
            if playlistFolder in track.locations[0]:
                foundPlaylistTracks.append(track)

        playlistName = os.path.basename(playlistFolder)

        # Create a new playlist with the folder's name
        playlist = plex.createPlaylist(playlistName, items=foundPlaylistTracks)

        if playlist:
            print(f"Playlist '{playlistName}' created with {len(foundPlaylistTracks)} tracks.")
        else:
            print("Error. Something went wrong.")

    print(f"\nSuccessfully created playlists from all folders provided.top 5")

if __name__ == "__main__":
    # Initialize runtime timer. So we can see how long it takes the script to run at the end.
    startTime = time.time()

    # Run the tool.
    runtimeResult = run()

    # Completion, cleanup.
    totalTime = time.time() - startTime
    print(
        f"\Playlists creation completed. Total run time: {math.trunc(totalTime)} seconds."
    )

    # Cool TRON reference.
    print("\nEnd of Line.")