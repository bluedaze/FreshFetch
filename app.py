from __future__ import unicode_literals
import requests
import requests.auth
from flask import Flask, render_template
from credentials import CLIENT_ID, SECRET_TOKEN
import yt_dlp
from parser import Parser
import sqlite3
import pickle
import uuid
app = Flask(__name__)

class redditRequest:
    def __init__(self):
        self.data = []
        self.access_token = ""
        self.headers = {"User-Agent": "hhhcli"}
        self.params = {"limit": "100"}
        self.makeRequests()

    def getToken(self):
        client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_TOKEN)
        post_data = {"grant_type": "client_credentials"}
        response = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=client_auth,
            data=post_data,
            headers=self.headers,
        )
        rj = response.json()
        self.access_token = rj["access_token"]
        self.headers = {"Authorization": f"bearer {self.access_token}", "User-Agent": "hhhcli"}

    def requestPosts(self):
        self.getToken()
        api = "https://oauth.reddit.com"
        res = requests.get(
            f'{api}/r/hiphopheads/search.json?q="Fresh"&restrict_sr=on&include_over_18=on&sort=new',
            headers=self.headers,
            params=self.params,
        )
        response = res.json()
        return response

    def parseResponse(self, response):
        for item in response:
            if item["data"]["ups"] > 10:
                thread = Parser(item).parse()
                self.data.append(thread)

    def makeRequests(self):
        # We call three times because Reddit search api only returns data the first three times
        # When I looked up why this happens it seems that the number of results has a cap.
        # Supposedly this is around 1,000 returned results.
        # I suspect this isn't true. I think instead you are only allowed to search up to 1,000
        # posts back - starting with the most recent post.
        for i in range(3):
            request = self.requestPosts()
            response = request["data"]["children"]
            self.parseResponse(response)
            # We update the parameters after performing a search
            # so that we can start a search after the index.
            # The index in this case is the "name" of the last post returned.
            index = response[-1]["data"]["name"]
            self.params = {"limit": "100", "after": index}

class parseResponse:
    def __init__(self, data):
        self.data = data
        self.tracks = []
        self.videos = []
        self.albums = []
        self.parseData()

    def parseData(self):
        for thread in self.data:
            if thread["tag"] == "FRESH":
                self.configureTrack(thread)
            elif thread["tag"] == "FRESH VIDEO":
                self.configureVideo(thread)
            elif thread["tag"] == "FRESH ALBUM" or thread["tag"] == "FRESH EP":
                self.albums.append(thread)

    def pingYoutube(self, thread):
        isVideo = True
        ydl = yt_dlp.YoutubeDL({"simulate": True, "quiet": True, "preference": 0})
        with ydl:
            try:
                result = ydl.extract_info(thread["url"], download=False, process=False, ie_key="Youtube")
                thread["url"] = result["webpage_url"]
                thread["ytid"] = result["id"]
                thread['image'] = result["thumbnail"]
            except Exception:
                isVideo = False
        return isVideo

    def configureTrack(self, thread):
        # This function is probably unnecessary
        # But I didn't like how there were several
        # url formats for YouTube links.
        isYoutube = thread["url"].find('youtu')
        if isYoutube >= 0:
            self.pingYoutube(thread)
        self.tracks.append(thread)

    def configureVideo(self, thread):
        isVideo = self.pingYoutube(thread)
        if isVideo:
            self.videos.append(thread)

        thread = {"post_id": "",
                  "tag": "",
                  "url": "",
                  "image": "",
                  "name": "",
                  "tokens": [],
                  "comments": [],
                  "feat": [],
                  "text": ""}

class Db:
    def __init__(self):
        pass

    def create_db(self):
        conn = sqlite3.connect("refresher.db")
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS refresher (post_id TEXT, tag TEXT, url TEXT, image TEXT, name TEXT, tokens TEXT, comments TEXT, feat TEXT, text TEXT)"
        )
        c.close()
        conn.close()

def main():
    request = redditRequest()
    response = parseResponse(request.data)
    if __name__ == "__main__":
        pass
    else:
        return render_template(
            "base.html",
            videos=response.videos,
            tracks=response.tracks,
            albums=response.albums,
            zip=zip,
        )


# Created a json api.
# Got bored, and didn't want to write a database.
@app.route("/data.json")
def dataJson():
    request = redditRequest()
    response = parseResponse(request.data)
    response ={"albums": response.albums, "tracks": response.tracks}
    if __name__ == "__main__":
        pass
    else:
        return response


# The pickle stuff is pretty useful for rapid prototyping
# if you don't want to go through the effort of setting up
# a database.
def savePickle(response):
    file_to_store = open("stored_object.pickle", "wb")
    pickle.dump(response, file_to_store)
    file_to_store.close()

def loadPickle():
    file_to_read = open("stored_object.pickle", "rb")
    response = pickle.load(file_to_read)
    file_to_read.close()
    return response

def start_app():
    request = redditRequest()
    response = parseResponse(request.data)
    return response

def pickelize(pickle_status):
    response = ""
    if pickle_status == "load":
        response = loadPickle()
    elif pickle_status == "save":
        response = start_app()
        savePickle(response)
    elif pickle_status == None:
        response = start_app()
    return response

@app.route("/")
@app.route("/index")
@app.route("/table")
def render_table():
    response = pickelize("load")
    if __name__ == "__main__":
        pass
    else:
        return render_template(
            "table.html",
            videos=response.videos,
            tracks=response.tracks,
            albums=response.albums,
            zip=zip,
            uuid=uuid
        )

# This route is useful for prototyping some js
# or w/e real quick.
@app.route("/test")
def testFetch():
    response = pickelize("save")
    return render_template("test.html",
                           videos=response.videos)

if __name__ == "__main__":
    main()
