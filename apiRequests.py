import requests.auth
import requests
from credentials import *
from parser import Parser
from requests.exceptions import *
from debugTools import debug_status, load_pickle, save_pickle
from psdb import *
from urllib.parse import urlparse, parse_qs
import logging
import sys

logging.basicConfig(level=logging.DEBUG)


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
        logging.debug(f"{__name__}")
        logging.debug(f"{__class__.__name__}")
        logging.debug(f"{__class__}")
        logging.debug(f"{sys._getframe(1).f_lineno}")
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
        if response_data.status_code == 200:
            return False
        else:
            logging.debug("Success status not returned.".format(len(ytid)))
            return True

    def sanitize_youtube_id(self, thread):
        # This will work even on youtu.be domains.
        # We split to get the youtube_id at the end of the url.
        # Sometimes this will return data similar to the following:
        # 'watch?v=jR4AG5LdKYE'
        # We split based on the equations sign because that's easy.
        # ytid = thread["url"].split("/")[-1]
        # if ytid.find("=") >= 0:
        #     ytid = ytid.split("=")[1]
        # if ytid.find("&amp;") > 0:
        #     ytid = ytid.split("&amp;")[0]
        # return ytid
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
            logging.debug(f"id {ytid} is {len(ytid)} characters long")
            logging.debug(f"Invalid url: {thread['url']}")
            logging.debug("~" * 20)
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

def request_reddit_api():
    request = RedditRequest()
    response = ParseResponse(request.data)
    return response.data

def send_request():
    status = debug_status()
    response = ""
    if status == "load":
        response = load_pickle()
    elif status == "save":
        response = request_reddit_api()
        save_pickle(response)
        db = DB()
        db.db_insert_response(response)
    elif status is None:
        response = request_reddit_api()
    return response