import subprocess
import sys

def download_spotify_playlist(playlist_url):
    command = ["spotdl", playlist_url]
    try:
        print(f"Attempting to download playlist: {playlist_url}")
        process = subprocess.run(command, capture_output=True, text=True, check=False) # check=False to handle spotdl errors gracefully
        print("STDOUT:\n", process.stdout)
        print("STDERR:\n", process.stderr)
        if process.returncode != 0:
            print(f"spotdl command exited with non-zero status: {process.returncode}")
            return False, process.stdout + process.stderr
        print("Playlist download initiated successfully or completed.")
        return True, process.stdout + process.stderr
    except FileNotFoundError:
        error_message = "Error: 'spotdl' command not found. Make sure spotdl is installed and in your PATH."
        print(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        return False, error_message

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python spotify_download.py <spotify_playlist_url>")
        sys.exit(1)
    
    playlist_url = sys.argv[1]
    success, output = download_spotify_playlist(playlist_url)
    if not success:
        sys.exit(1)
