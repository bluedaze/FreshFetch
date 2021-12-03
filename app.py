from __future__ import unicode_literals
import requests
import requests.auth
from flask import Flask, render_template
from credentials import CLIENT_ID, SECRET_TOKEN
import youtube_dl

app = Flask(__name__)

class Thread:
    def __init__(self):
        self.post_id = ""
        self.tag = ""
        self.url = ""
        self.image = ""
        self.name = ""
        self.tokens = []
        self.comments = []
        self.feat = []
        self.text = ""

class Tokenizer:
    def __init__(self, child):
        self.thread = Thread()
        self.constructToken(child)
        self.pos = 0
        self.char = ""

    def constructToken(self, child):
        self.thread.text = child["data"]["title"]
        self.thread.url = child["data"]["url"]
        self.tokens = self.thread.tokens
        self.text = self.thread.text

    def normalizeCharacters(self):
        # There are some characters that look weird, or are harder to parse. So we discard those.
        if "&amp;" in self.text:
            self.text = self.text.replace("&amp;", "&")
        if "–" in self.text:
            self.text = self.text.replace("–", "-")

    def getID(self):
        result = ""
        while self.char.isalnum() and self.pos < len(self.text):
            result += self.char
            self.nextChar()
        self.tokens.append(result)

    def peek(self):
        if self.pos < len(self.text):
            try:
                nextChar = self.text[self.pos + 1]
                return nextChar
            except:
                return None

    def addToken(self, result):
        self.tokens.append(result)
        self.nextChar()

    def nextChar(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.char = self.text[self.pos]

    def createToken(self):
        if self.char.isalnum():
            self.getID()
        elif self.char.isspace():
            self.addToken(self.char)
        elif self.char:
            self.addToken(self.char)
        else:
            self.nextChar()

    def parseText(self):
        self.normalizeCharacters()
        self.char = self.text[self.pos]
        while self.pos < len(self.text):
            self.createToken()
        return self.thread

class parser:
    def __init__(self, child):
        self.thread = Tokenizer(child).parseText()
        self.tokens = self.thread.tokens
        self.pos = 0
        self.currentToken = self.thread.tokens[self.pos]
        self.parse()

    def parseParens(self):
        comment = ""
        while self.currentToken != ")":
            comment += self.currentToken
            self.advance()
        self.thread.comments.append(comment)
        self.advance()

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.currentToken = self.tokens[self.pos]

    def nextToken(self):
        nextToken = ""
        if self.pos < len(self.tokens):
            nextToken = self.tokens[self.pos + 1]
        return nextToken

    def parseSquarebrackets(self):
        tag = ""
        keywords = ["fresh", "video", "album", "EP"]
        while self.currentToken != "]":
            if self.currentToken.lower() in keywords or self.currentToken.isspace():
                tag += self.currentToken.upper()
                self.advance()
            else:
                self.advance()
        self.thread.tag = tag
        self.advance()

    def getName(self):
        stopChars = ["(", "["]
        while self.pos < len(self.tokens):
            if self.currentToken in stopChars:
                self.thread.name = self.thread.name.rstrip()
                break
            elif self.currentToken:
                self.thread.name += self.currentToken
                self.advance()

    def containAlphaNum(self):
        if any(char.isalnum() for char in self.currentToken):
            return True
        else:
            return False

    def parseTokens(self):
        if self.currentToken == "[":
            self.parseSquarebrackets()
        elif self.currentToken == "(":
            self.parseParens()
        elif self.currentToken.isalnum():
            self.getName()
        elif self.currentToken.isspace():
            self.advance()
        elif self.containAlphaNum():
            self.getName()
        else:
            self.getName()

    def parse(self):
        while self.pos < len(self.tokens):
            self.parseTokens()
        return self.thread

class redditRequest:
    def __init__(self):
        self.data = {}
        self.tracks = []
        self.videos = []
        self.albums = []
        self.index = ""
        self.token = ""
        self.headers = {"User-Agent": "hhhcli"}
        self.params = {"limit": "100"}
        self.main()

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
        self.token = rj["access_token"]
        self.headers = {"Authorization": f"bearer {self.token}", "User-Agent": "hhhcli"}

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

    def pingYoutube(self, thread):
        isVideo = True
        ydl = youtube_dl.YoutubeDL({"simulate": True, "quiet": True, "forcethumbnail": True})
        with ydl:
            try:
                result = ydl.extract_info(thread.url, download=False, ie_key="Youtube")
                thread.url = result["webpage_url"]
                thread.image = result["thumbnails"][-1]["url"]
            except Exception as e:
                isVideo = False
        return isVideo

    def configureVideo(self, thread):
        isVideo = self.pingYoutube(thread)
        if isVideo:
            self.videos.append(thread)

    def parseRequest(self, response):
        children = response["data"]["children"]
        self.index = children[-1]["data"]["name"]
        for child in children:
            if child["data"]["ups"] >= 10:
                thread = parser(child).parse()
                if thread.tag == "FRESH":
                    self.tracks.append(thread)
                elif thread.tag == "FRESH VIDEO":
                    self.configureVideo(thread)
                elif thread.tag == "FRESH ALBUM":
                    self.albums.append(thread)

    def main(self):
        # We call three times because Reddit search api only returns data the first three times
        # When I looked up why this happens it seems that the number of results has a cap.
        # Supposedly this is around 1,000 returned results.
        # I suspect this isn't true. I think instead you are only allowed to search up to 1,000
        # posts back - starting with the most recent post.
        for i in range(3):
            response = self.requestPosts()
            self.parseRequest(response)
            # We update the parameters after performing a search so that we can start a search after the index.
            # The index in this case is the "name" of the last post returned.
            self.params = {"limit": "100", "after": self.index}


@app.route("/")
@app.route("/index")
def main():
    print("Creating new request")
    newRequest = redditRequest()
    print("Request retrieved")
    if __name__ == "__main__":
        pass
    else:
        return render_template(
            "base.html",
            videos=newRequest.videos,
            tracks=newRequest.tracks,
            albums=newRequest.albums,
            zip=zip,
        )

if __name__ == "__main__":
    main()
    thread = "https://www.youtube.com/watch?v=yGYuDtF5AnE"
