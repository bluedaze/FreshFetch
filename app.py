from flask import Flask, render_template, redirect, url_for, request
import requests.auth
import requests
import pickle
import uuid
from parser import Parser
from credentials import *
from psdb import *
from requests.exceptions import *
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Debug variable.
# "save" to go fetch data from the api
# "load" to use a pickle that you already have
pickle_status = "load"


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
        count = 0
        for thread in self.data:
            count = count + 1
            if thread["tag"] == "FRESH":
                self.configure_track(thread)
            elif thread["tag"] == "FRESH VIDEO":
                self.configure_video(thread)
            elif thread["tag"] == "FRESH ALBUM" or thread["tag"] == "FRESH EP":
                self.albums.append(thread)
        data_dict = {
            "albums": self.albums,
            "tracks": self.tracks,
            "videos": self.videos,
        }
        self.data = data_dict

    def get_best_thumbnail(self, video_id, is_live=False):
        thumbnail_names = [
            "maxresdefault", "hq720", "sddefault", "sd1", "sd2", "sd3", "hqdefault", "hq1", "hq2", "hq3", "0",
            "mqdefault", "mq1", "mq2", "mq3", "default", "1", "2", "3"
        ]
        thumbnail_urls = [
            "https://i.ytimg.com/vi{webp}/{video_id}/{name}{live}.{ext}".format(
                video_id=video_id,
                name=name,
                ext=ext,
                webp="_webp" if ext == "webp" else "",
                live="_live" if is_live else "",
            )
            for name in thumbnail_names
            for ext in ("webp", "jpg")
        ]

        for url in thumbnail_urls:
            try:
                r = requests.head(url)
                r.raise_for_status()
            except HTTPError:
                continue
            return url

    def yt_is_deleted(self, ytid):
        target_url = (
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={ytid}"
        )
        response_data = requests.get(target_url)
        return not response_data.status_code == 200

    def sanitize_youtube_id(self, thread):
        # This will work even on youtu.be domains.
        # We split to get the youtube_id at the end of the url.
        # Sometimes this will return data similar to the following:
        # 'watch?v=jR4AG5LdKYE'
        # We split based on the equations sign because that's easy.
        ytid = thread["url"].split("/")[-1]
        if ytid.find("=") >= 0:
            ytid = ytid.split("=")[1]
        if ytid.find("&amp;") > 0:
            ytid = ytid.split("&amp;")[0]
        return ytid

    def check_youtube_url(self, thread):
        ytid = self.sanitize_youtube_id(thread)
        isDeleted = self.yt_is_deleted(ytid)
        if (len(ytid) != 11) or isDeleted:
            print(f"id is {len(ytid)} characters long: ", end="")
            print(ytid)
            print(f"Invalid url: {thread['url']}")
            print("~" * 20)
            return None
        else:
            thread["url"] = f"https://www.youtube.com/watch?v={ytid}"
            return ytid

    def configure_video(self, thread):
        ytid = self.check_youtube_url(thread)
        if ytid:
            thread["ytid"] = ytid
            thread["image"] = self.get_best_thumbnail(ytid)
            thread["url"] = f"https://www.youtube.com/watch?v={ytid}"
            self.videos.append(thread)

    def configure_track(self, thread):
        # This function is probably unnecessary
        # But I didn't like how there were several
        # But I didn't like how there were several
        # url formats for YouTube links.
        is_youtube = thread["url"].find("youtu")
        if is_youtube >= 0:
            self.check_youtube_url(thread)
        self.tracks.append(thread)


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
@app.route("/data.json")
def data_json():
    request = RedditRequest()
    response = ParseResponse(request.data)
    response = {"albums": response.albums, "tracks": response.tracks}
    if __name__ == "__main__":
        pass
    else:
        return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('home'))
    return render_template('login.html', error=error)



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


def pickeler():
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
def render_table():
    db = DB()
    response = db.query()
    return render_template(
        "base.html",
        videos=response["videos"],
        tracks=response["tracks"],
        albums=response["albums"],
        zip=zip,
        uuid=uuid,
    )


def db_insert_response():
    response = pickeler()
    db = DB()
    for key, value in response.items():
        db.insert(key, value)


def db_create_database():
    db = DB()
    response = pickeler()
    for key, value in response.items():
        db.createDatabase(key)
        db.insert(key, value)


if __name__ == "__main__":
    db_insert_response()
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(db_insert_response, "interval", minutes=60)
    sched.start()
    atexit.register(lambda: sched.shutdown())
    app.run()
