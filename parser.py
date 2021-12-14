class Tokenizer:
    def __init__(self, child):
        self.thread = self.spawnThread()
        self.constructToken(child)
        self.pos = 0
        self.char = ""

    def spawnThread(self):
        thread = {"reddit_id": "",
                  "tag": "",
                  "url": "",
                  "image": "",
                  "name": "",
                  "tokens": [],
                  "comments": [],
                  "text": "",
                  "ytid": "",
                  "ups": "",
                  "time_posted": ""}
        return thread

    def constructToken(self, child):
        self.thread["text"] = child["data"]["title"]
        self.thread["url"] = child["data"]["url"]
        self.thread["reddit_id"] = child["data"]["id"]
        self.thread["ups"] = child["data"]["ups"]
        self.thread["time_posted"] = child["data"]["created_utc"]
        self.thread["reddit_url"] = f"https://www.reddit.com{child['data']['permalink']}"

    def sanitize(self):
        # There are some characters that look weird,
        # or are harder to parse. So we replace those.
        if "&amp;" in self.thread["text"]:
            self.thread["text"] = self.thread["text"].replace("&amp;", "&")
        if "–" in self.thread["text"]:
            self.thread["text"] = self.thread["text"].replace("–", "-")
        if "—" in self.thread["text"]:
            self.thread["text"] = self.thread["text"].replace("—", "-")

    def getID(self):
        result = ""
        while self.char.isalnum() and self.pos < len(self.thread["text"]):
            result += self.char
            self.nextChar()
        self.thread["tokens"].append(result)

    def peek(self):
        if self.pos < len(self.thread["text"]):
            try:
                nextChar = self.thread["text"][self.pos + 1]
                return nextChar
            except:
                return None

    def addToken(self, result):
        self.thread["tokens"].append(result)
        self.nextChar()

    def nextChar(self):
        self.pos += 1
        if self.pos < len(self.thread["text"]):
            self.char = self.thread["text"][self.pos]

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
        self.sanitize()
        self.char = self.thread["text"][self.pos]
        while self.pos < len(self.thread["text"]):
            self.createToken()
        return self.thread

class Parser:
    def __init__(self, child):
        self.thread = Tokenizer(child).parseText()
        self.tokens = self.thread["tokens"]
        self.pos = 0
        self.currentToken = self.thread["tokens"][self.pos]

    def parseParens(self):
        comment = ""
        while self.currentToken != ")":
            comment += self.currentToken
            self.advance()
        self.thread["comments"].append(comment)
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
        while self.currentToken != "]" and self.pos < len(self.tokens):
            if self.currentToken.lower() in keywords or self.currentToken.isspace():
                tag += self.currentToken.upper()
                self.advance()
            else:
                self.advance()
        self.thread["tag"] = tag
        self.advance()

    def getName(self):
        stopChars = ["(", "["]
        while self.pos < len(self.tokens):
            if self.currentToken in stopChars:
                self.thread["name"] = self.thread["name"].rstrip()
                break
            elif self.currentToken == "-":
                if self.thread["name"]:
                    self.thread["name"] += self.currentToken
                    self.advance()
                else:
                    self.advance()
            elif self.currentToken:
                self.thread["name"] += self.currentToken
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
        print(self.thread["name"])
        return self.thread