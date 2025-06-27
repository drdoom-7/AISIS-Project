# Spotify Playlist Downloader Instrument

## Description
This instrument allows you to download a Spotify playlist by providing its URL. It uses the `spotdl` library, which fetches metadata from Spotify and then downloads the audio tracks from YouTube.

## Usage
To use this instrument, simply run the `spotify_download.sh` script with the Spotify playlist URL as an argument:

```bash
bash /a0/instruments/default/spotify_playlist_downloader/spotify_download.sh <spotify_playlist_url>
```

Replace `<spotify_playlist_url>` with the actual URL of the Spotify playlist you wish to download.

## Prerequisites
This instrument requires `spotdl` to be installed. The `spotify_download.sh` script will attempt to install `spotdl` automatically if it's not found on your system. However, if you encounter issues, you can manually install it using pip:

```bash
pip install spotdl
```

## How it Works
- The `spotify_download.sh` script first checks for `spotdl` installation and installs it if necessary.
- It then calls the `spotify_download.py` Python script, passing the provided playlist URL as a command-line argument.
- The `spotify_download.py` script then uses `spotdl` to process and download the playlist.
