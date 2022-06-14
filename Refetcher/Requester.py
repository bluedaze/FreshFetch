import requests.auth
import requests
from parser import Parser
from requests.exceptions import HTTPError
from debugTools import Debugger
from urllib.parse import urlparse, parse_qs
import logging
from Reserver.environment import get_env
from Reserver.psdb import DB


class RedditRequest:
    def __init__(self):
        self.data = []
        self.access_token = ""
        self.headers = {"User-Agent": "hhhcli"}
        self.params = {"limit": "100"}
        self.make_requests()

    def get_token(self):
        ''' gets oauth token '''
        config = get_env()
        CLIENT_ID = config['CLIENT_ID']
        SECRET_TOKEN = config["SECRET_TOKEN"]
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
        ''' requests posts from subreddit '''
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
        ''' sends every item to the parser, then adds the result to a dictionary'''
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
        for i in range(3):
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
        data_dict = {
            "albums": self.albums,
            "tracks": self.tracks,
            "videos": self.videos,
        }
        self.data = data_dict

    def get_thumbnail_urls(self, video_id):
        is_live = False
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
        return thumbnail_urls

    def get_best_thumbnail(self, video_id):
        thumbnail_urls = self.get_thumbnail_urls(video_id)

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
        if response_data.status_code == 200:
            logging.debug(f"Request Status: {response_data.status_code}")
            return False
        else:
            logging.debug("Success status not returned.".format(len(ytid)))
            return True

    def sanitize_youtube_id(self, thread):
        # There are several different kinds of youtube
        # urls so we use this function to ensure
        # that we use the same format every time.
        u_pars = urlparse(thread["url"])
        quer_v = parse_qs(u_pars.query).get('v')
        if quer_v:
            return quer_v[0]
        pth = u_pars.path.split('/')
        if pth:
            return pth[-1]

    def check_youtube_url(self, thread):
        ytid = self.sanitize_youtube_id(thread)
        isDeleted = self.yt_is_deleted(ytid)
        if (len(ytid) != 11) or isDeleted:
            logging.debug(f"id {ytid} is {len(ytid)} characters long\n Invalid url: {thread['url']}")
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
        # url formats for YouTube links.
        is_youtube = thread["url"].find("youtu")
        if is_youtube >= 0:
            self.check_youtube_url(thread)
        self.tracks.append(thread)

def request_reddit_api():
    request = RedditRequest()
    response = ParseResponse(request.data)
    return response.data

def send_request():
    # We use this so that we don't hammer Reddit with API requests.
    debug = Debugger("save")
    if debug.status == "load":
        debug.load_pickle()
    else:
        response = request_reddit_api()
        debug.save_pickle(response)
        config = get_env()
        db = DB()
        db.db_insert_response(response)

if __name__ == "__main__":
    send_request()
