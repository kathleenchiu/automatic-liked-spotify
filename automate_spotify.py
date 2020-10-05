'''
Step 1: log into youtube
Step 2: Grab our Liked Videos (I'm hoping to make a separate playlist?  
	or eh.  I should test this on a diff email)
Step 3: Create a New Playlist
Step 4: Search For the Song
Step 5: Add this song into the new Spotify playlist

APIs to use:
- YouTube Data API
- Spotify Web API
- youtube Data Library

'''
import json
import requests
import youtube_dl

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from exceptions import ResponseException
from secrets import spotify_token, spotify_user_id



class CreatePlaylist:
	def __init__(self):
		self.user_id = spotify_user_id
		self.spotify_token = spotify_token
		self.youtube_client = self.get_youtube_client()
		self.song_info_dict = {}

	# Step 1: log into youtube
	def get_youtube_client(self):
		""" 
		Log Into Youtube, Copied from Youtube Data API 
		"""
		# Disable OAuthlib's HTTPS verification when running locally.
		# *DO NOT* leave this option enabled in production.
		os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

		api_service_name = "youtube"
		api_version = "v3"
		client_secrets_file = "client_secret.json"
		
		# Get credentials and create an API client
		scopes = ["https://www.googleapis.com/auth/youtube.readonly"]	
		flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
			client_secrets_file, scopes)
		credentials = flow.run_console()
		
		youtube_client = googleapiclient.discovery.build(
			api_service_name, api_version, credentials=credentials)
		return youtube_client


	# Step 2: Grab Liked Videos and create dictionary of song info
	def get_liked_videos(self):
		# due to YouTube update, we need a custom agent to extract the song and artist
		youtube_dl.utils.std_headers['User-Agent'] = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
		#youtube_dl.utils.std_headers["User-Agent"] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
		# works for the first video "Keep pushing; artist has to be mentioned in description???"
		request = self.youtube_client.videos().list(
			part="snippet,contentDetails,statistics", #only get what we need
			myRating="like",
			#get 50 liked videos, the maximum number - can retrieve more using the last nextPageToken
			maxResults=50	
		)
		response = request.execute()

		# iterate through videos and store information in all song info dict
			# dict maps song titles to dict of other info
		for item in response["items"]:
			video_title = item["snippet"]["title"]
			youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

			# use youtube_dl to get the song name and artist
				# rn this isn't working... maybe I can write a function that takes the title, deletes
				# anything that says MV, M/V, or Official Music Video, deletes any non-English characters
					# maybe get rid of [], (), / too?
			video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
			song_name = video["track"]
			artist = video["artist"]
			print("title", video_title)
			print("song:", song_name)
			print("artist:", artist)


			if song_name != None and artist != None:
				# store important info on valid songs to dictionary
				self.song_info_dict[video_title] = {
					"youtube_url": youtube_url,
					"song_name": song_name,
					"artist": artist,
					"spotify_uri": self.get_spotify_uri(song_name, artist)
				}
				print(youtube_url)


	# Step 3: Create a New Playlist on Spotify
	def create_playlist(self):
		# endpoint: 	https://api.spotify.com/v1/users/{user_id}/playlists
		# OAuth required, HTTP method POST
		request_body = json.dumps({
				"name": "YouTube Liked Videos",
				"description": "all liked YouTube videos",
				"public": True
			})
		# query is the POST endpoint
		query = "https://api.spotify.com/v1/users/{user_id}/playlists".format(user_id = self.user_id)
		response = requests.post(
			query,
			data=request_body,
			headers={
				"Content-Type":"application/json",
				"Authorization":"Bearer {}".format(self.spotify_token)
			}
		)
		# response_json is a dictionary of the post response
		response_json = response.json()

		# playlist id
		return response_json["id"]


	# Step 4: Search For the Song
	def get_spotify_uri(self, song_name, artist):
		'''
		Search for the song 
		'''
		# alternative query link:
		# "https://api.spotify.com/v1/search?q={}&type=track%2Cartist&limit=10&offset=0".format("%20".song_name.split().join())
		query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
			song_name,
			artist
		)

		response = requests.get(
			query,
			headers={
				"Content-Type": "application/json",
				"Authorization": "Bearer {}".format(self.spotify_token)
			}
		)
		response_json = response.json()
		songs = response_json["tracks"]["items"]

		# only use the first song
		uri = songs[0]["uri"]
		return uri

	# Step 5: Add songs into the new Spotify playlist
	def add_song_to_playlist(self):
		# get liked songs
		self.get_liked_videos()
		# make a uris list
		uris = [info["spotify_uri"] for song, info in self.song_info_dict.items()]

		# make a new spotify playlist
		playlist_id = self.create_playlist()

		query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
		request_data = json.dumps(uris)
		print("uris:", request_data)
		print("uri length", len(uris))
		response = requests.post(
			query,
			data=request_data, 
			headers={
				"Content-Type":"application/json",
				"Authorization":"Bearer {}".format(self.spotify_token)
			}
		)

		# Raise exception for invalid status code
		if response.status_code != 200:
			raise ResponseException(response.status_code)

		return response.json()


if __name__ == "__main__":
	playlistInstance = CreatePlaylist()
	playlistInstance.add_song_to_playlist()

