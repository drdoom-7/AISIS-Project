#!/bin/bash

# Check if spotdl is installed, and install if not
if ! pip show spotdl &>/dev/null; then
    echo "spotdl not found. Installing spotdl..."
    pip install spotdl
    if [ $? -ne 0 ]; then
        echo "Failed to install spotdl. Exiting."
        exit 1
    fi
    echo "spotdl installed successfully."
else
    echo "spotdl is already installed."
fi

# Check if a playlist URL is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <spotify_playlist_url>"
    exit 1
fi

# Call the Python script to download the playlist
python3 /a0/instruments/default/spotify_playlist_downloader/spotify_download.py "$1"
