1) Downloading proper libraries
	- Be sure to have the most updated versions of the following packages

	- To install on Mac Terminal: "python3 -m pip install [package name]"

2) Spotify Credentials
	- Secrets.py must be updated with:
		- your Spotify token (with public scope, can be retrieved here: https://developer.spotify.com/console/post-playlists/) 
		- your Spotify username

3) Google OAuth Client Credentials
	- Setting this part up is a little tricky, but you need to create a project on google console and fill out the client_secret.json with:
		- client_id
		- cilent_secret
	- Both should be retrieved for a NATIVE desktop applciation


4) Getting a KeyError?
	- Spotify tokens expire hourly, so if you're getting a KeyError, it should go away if you update the token in secrets.py

5) Title Parsing
	- This function is still looking to be improved.  The youtube_dl library is currently unable to retrieve the artist and song so the program parses the title to search for it in Spotify.