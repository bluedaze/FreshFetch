import requests
import requests.auth
from flask import Flask
from flask import render_template
import time
from credentials import CLIENT_ID, SECRET_TOKEN

app = Flask(__name__)

class Post:
    def __init__(self):
        self.post_id = ""
        self.tag = ""
        self.url = ""
        self.image = ""
        self.name = ""
        self.tokens = []
        self.comments = []
        self.feat = []


class Tokenizer:
    def __init__(self, child):
        self.url = child["data"]["url"]
        self.pos = 0
        self.text = child["data"]["title"]
        self.char = ""
        self.post = Post()
        self.tokens = []
        self.parseText()

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

    def qmOperator(self):
        position = self.pos
        result = ""
        result += self.char
        if self.peek() == "v":
            self.nextChar()
            result += self.char
            if self.peek() == "=":
                self.nextChar()
                result += self.char
                self.addToken(self.char)
            else:
                self.pos == position
        else:
            self.addToken(self.char)

    def slashOperator(self):
        self.nextChar()

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
        elif self.char == "/":
            self.slashOperator()
        elif self.char == "?":
            self.qmOperator()
        elif self.char:
            self.addToken(self.char)
        else:
            self.nextChar()

    def parseText(self):
        self.normalizeCharacters()
        self.char = self.text[self.pos]
        while self.pos < len(self.text):
            self.createToken()


class parser:
    def __init__(self, child):
        tokens = Tokenizer(child)
        self.url = child["data"]["url"]
        self.post = Post()
        self.name = ""
        self.tokens = tokens.tokens
        self.pos = 0
        self.currentToken = self.tokens[self.pos]
        self.mainLoop()

    def getVideo(self):
        pass

    def parseParens(self):
        comment = ""
        while self.currentToken != ")":
            if self.currentToken.isalnum():
                comment += self.currentToken
                self.advance()
            elif self.currentToken.isspace():
                comment += self.currentToken
                self.advance()
            else:
                comment += self.currentToken
                self.advance()
        self.post.comments.append(comment)
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
        while self.currentToken != "]":
            if self.currentToken.lower() == "fresh":
                tag += self.currentToken.upper()
                self.advance()
            elif self.currentToken.isspace():
                tag += self.currentToken.upper()
                self.advance()
            elif self.currentToken.lower() == "video":
                tag += self.currentToken.upper()
                self.advance()
            elif self.currentToken.lower() == "album":
                tag += self.currentToken.upper()
                self.advance()
            else:
                self.advance()
        self.post.tag = tag
        self.advance()

    def getName(self):
        stopChars = ["(", "["]
        while self.pos < len(self.tokens):
            if self.currentToken.isalnum():
                self.name += self.currentToken
                self.advance()
            elif self.currentToken.isspace():
                self.name += self.currentToken
                self.advance()
            elif self.currentToken in stopChars:
                self.name = self.name.rstrip()
                break
            else:
                self.name += self.currentToken
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

    def getThumbnail(self):
        urls = ["maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg", "default.jpg"]
        image = ""
        for url in urls:
            image = f"https://i.ytimg.com/vi/{self.post.post_id}/{url}"
            r = requests.get(image)
            if r.status_code == 200:
                break
            elif r.status_code == 404:
                time.sleep(0.5)
        self.post.image = image

    def checkForYoutubeLink(self):
        ytid = None
        if self.url[0:32] == "https://www.youtube.com/watch?v=":
            ytid = self.url[32:43]
        elif self.url[0:30] == "https://m.youtube.com/watch?v=":
            ytid = self.url[30:41]
        elif self.url[0:28] == "https://youtube.com/watch?v=":
            ytid = self.url[28:39]
        elif self.url[0:16] == "https://youtu.be":
            ytid = self.url[17:28]
        else:
            pass
        self.post.post_id = ytid
        self.post.url = self.url

    def mainLoop(self):
        while self.pos < len(self.tokens):
            self.parseTokens()
        if self.post.tag.upper() == "FRESH VIDEO":
            self.checkForYoutubeLink()
            self.getThumbnail()
        self.post.name = self.name


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
        client_auth = requests.auth.HTTPBasicAuth(
            CLIENT_ID, SECRET_TOKEN
        )
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

    def parseRequest(self, response):
        children = response["data"]["children"]
        self.index = children[-1]["data"]["name"]
        for child in children:
            if child["data"]["ups"] >= 10:
                data = parser(child)
                if data.post.tag == "FRESH":
                    self.tracks.append(data.post)
                elif data.post.tag == "FRESH VIDEO":
                    self.videos.append(data.post)
                elif data.post.tag == "FRESH ALBUM":
                    self.albums.append(data.post)

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
@app.route('/index')
def main():
    newRequest = redditRequest()
    if __name__ == "__main__":
        pass
    else:
        return render_template(
            "base.html",
            videos=newRequest.videos,
            tracks=newRequest.tracks,
            albums=newRequest.albums,
            posts=newRequest.data,
            zip=zip,
        )

@app.route("/start")
def start():
    return render_template(
        "start.html"
    )

if __name__ == "__main__":
    main()
