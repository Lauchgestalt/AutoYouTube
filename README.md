# AutoYouTube
Automatically downloading Twitch Clips, merging them to one video and uploading it to YouTube

## Installation

- Make sure you have all the pip modules installed for both bot.py and uploadVideo.py. Simply use the requirements.txt with ```pip install -r requirements.txt```
- Make sure you have the msedgedriver in your PATH/the root directory or replace the driver initialization if you plan on using a different Webengine ```(bot.py ln 26)```
- That's basically it.

## Usage
- Get yourself some YouTube Data API credentials and save them in the root directory as 'credentials.json'
- Get to the bottom of bot.py and configure things like title, description, tags etc. Those will be used when uploading to YouTube
- Feel free to change some other stuff early in that file to pull other videos or something idk
- Simply run bot.py
- The first time you use it, you will have to authorize the tool to upload videos and edit them for you

#### Fin.
