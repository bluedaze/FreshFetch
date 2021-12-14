from __future__ import unicode_literals
import requests
import requests.auth
from flask import Flask, render_template
from credentials import *
import yt_dlp
from parser import Parser
import pickle
import uuid
from psdb import *

app = Flask(__name__)


class RedditRequest:
    def __init__(self):
        self.data = []
        self.access_token = ""
        self.headers = {"User-Agent": "hhhcli"}
        self.params = {"limit": "100"}
        self.make_requests()

    def get_token(self):
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
        self.headers = {
            "Authorization": f"bearer {self.access_token}",
            "User-Agent": "hhhcli",
        }

    def request_posts(self):
        self.get_token()
        api = "https://oauth.reddit.com"
        res = requests.get(
            f'{api}/r/hiphopheads/search.json?q="Fresh"&restrict_sr=on&include_over_18=on&sort=new',
            headers=self.headers,
            params=self.params,
        )
        response = res.json()
        return response

    def parse_response(self, response):
        for item in response:
            if item["data"]["ups"] > 10:
                thread = Parser(item).parse()
                self.data.append(thread)

    def make_requests(self):
        # We call three times because Reddit search api only returns data the first three times
        # When I looked up why this happens it seems that the number of results has a cap.
        # Supposedly this is around 1,000 returned results.
        # I suspect this isn't true. I think instead you are only allowed to search up to 1,000
        # posts back - starting with the most recent post.
        count = 0
        for i in range(3):
            count += 1
            print(count)
            request = self.request_posts()
            response = request["data"]["children"]
            self.parse_response(response)
            # We update the parameters after performing a search
            # so that we can start a search after the index.
            # The index in this case is the "name" of the last post returned.
            index = response[-1]["data"]["name"]
            self.params = {"limit": "100", "after": index}


class ParseResponse:
    def __init__(self, data):
        self.data = data
        self.tracks = []
        self.videos = []
        self.albums = []
        self.parse_data()

    def parse_data(self):
        for thread in self.data:
            if thread["tag"] == "FRESH":
                self.configure_track(thread)
            elif thread["tag"] == "FRESH VIDEO":
                self.configure_video(thread)
            elif thread["tag"] == "FRESH ALBUM" or thread["tag"] == "FRESH EP":
                self.albums.append(thread)
        data_dict = {"albums": self.albums, "tracks": self.tracks, "videos": self.videos}
        self.data = data_dict

    def ping_youtube(self, thread):
        is_video = True
        ydl = yt_dlp.YoutubeDL({"simulate": True, "quiet": True, "preference": 0})
        with ydl:
            try:
                print("Fetching video")
                result = ydl.extract_info(
                    thread["url"], download=False, process=False, ie_key="Youtube"
                )
                thread["url"] = result["webpage_url"]
                thread["ytid"] = result["id"]
                thread["image"] = result["thumbnail"]
            except Exception:
                is_video = False
        return is_video

    def configure_track(self, thread):
        # This function is probably unnecessary
        # But I didn't like how there were several
        # url formats for YouTube links.
        is_youtube = thread["url"].find("youtu")
        if is_youtube >= 0:
            self.ping_youtube(thread)
        self.tracks.append(thread)

    def configure_video(self, thread):
        is_video = self.ping_youtube(thread)
        if is_video:
            self.videos.append(thread)


def main():
    request = RedditRequest()
    response = ParseResponse(request.data)
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
def data_json():
    request = RedditRequest()
    response = ParseResponse(request.data)
    response = {"albums": response.albums, "tracks": response.tracks}
    if __name__ == "__main__":
        pass
    else:
        return response


# The pickle stuff is pretty useful for rapid prototyping
# if you don't want to go through the effort of setting up
# a database.
def save_pickle(response):
    file_to_store = open("stored_object.pickle", "wb")
    pickle.dump(response, file_to_store)
    file_to_store.close()


def load_pickle():
    file_to_read = open("stored_object.pickle", "rb")
    response = pickle.load(file_to_read)
    file_to_read.close()
    return response


def start_app():
    request = RedditRequest()
    response = ParseResponse(request.data)
    return response.data


def pickeler(pickle_status):
    response = ""
    if pickle_status == "load":
        response = load_pickle()
    elif pickle_status == "save":
        response = start_app()
        save_pickle(response)
    elif pickle_status is None:
        response = start_app()
    return response


@app.route("/")
@app.route("/index")
@app.route("/table")
def render_table():
    db = DB()
    response = db.query()
    if __name__ == "__main__":
        pass
    else:
        return render_template(
            "table.html",
            videos=response["videos"],
            tracks=response["tracks"],
            albums=response["albums"],
            zip=zip,
            uuid=uuid,
        )

# Need to update this, since it is no longer useful.
# def db_insert_response():
#     response = pickeler("save")
#     for key, value in response.items():
#         db_insert(key, value)


# This route is useful for prototyping
# some js or w/e real quick.
@app.route("/test")
def test_fetch():
    response = pickeler("save")
    return render_template("test.html", videos=response.videos)


if __name__ == "__main__":
    render_table()
