import json
import requests
import re

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
			#youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

			self.song_info_dict[video_title] = {
					"spotify_uri": self.get_spotify_uri(video_title)
				}


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

	# Step 3.5: 
	def clean_title(self, video_title):
		# delete irrelevant phrases for Spotify search
		take_out = ["official music video", "mv", "m/v", "official video", "music video", "ft", "feat", 
				"official audio", "lyrics", "eng", "lyric video"]
		title = video_title.lower()
		for word in take_out:
			title = title.replace(word, "")
		# get only alphanumeric characters and insert the %20 formatting for searching
		regex = re.compile('[^a-z0-9 ]')
		title = regex.sub('', title)
		title = "%20".join(title.split())
		print("title", title)
		return title

	# Step 4: Search For the Song
	def get_spotify_uri(self, video_title):
		'''
		Search for the song 
		'''

		video_title = self.clean_title(video_title)
		# alternative query link:
		query = "https://api.spotify.com/v1/search?q={}&type=track%2Cartist&limit=10&offset=0".format(video_title)

		response = requests.get(
			query,
			headers={
				"Content-Type": "application/json",
				"Authorization": "Bearer {}".format(self.spotify_token)
			}
		)
		response_json = response.json()
		songs = response_json["tracks"]["items"]

		if len(songs) == 0:
			# nothing came up in the Spotify search
			return None
		# only use the first song
		uri = songs[0]["uri"]
		print("uri found:", uri)
		return uri

	# Step 5: Add songs into the new Spotify playlist
	def add_song_to_playlist(self):
		# get liked songs
		self.get_liked_videos()
		# make a uris list
		uris = [info["spotify_uri"] for song, info in self.song_info_dict.items() 
				if info["spotify_uri"] != None]

		# make a new spotify playlist
		playlist_id = self.create_playlist()

		query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
		request_data = json.dumps(uris)
		print(len(uris), "songs found")
		response = requests.post(
			query,
			data=request_data, 
			headers={
				"Content-Type":"application/json",
				"Authorization":"Bearer {}".format(self.spotify_token)
			}
		)

		# Raise exception for invalid status code
		if response.status_code >= 400:
			raise ResponseException(response.status_code)

		print("Successfully completed.")
		return response.json()


if __name__ == "__main__":
	playlistInstance = CreatePlaylist()
	playlistInstance.add_song_to_playlist()

