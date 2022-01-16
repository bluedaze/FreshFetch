class Tokenizer:
    def __init__(self, child):
        self.thread = self.spawn_thread()
        self.construct_token(child)
        self.pos = 0
        self.char = ""

    def spawn_thread(self):
        thread = {
            "reddit_id": "",
            "tag": "",
            "url": "",
            "image": "",
            "name": "",
            "tokens": [],
            "comments": [],
            "text": "",
            "ytid": "",
            "ups": 0,
            "ts": "",
        }
        return thread

    def construct_token(self, child):
        self.thread["text"] = child["data"]["title"]
        self.thread["url"] = child["data"]["url"]
        self.thread["reddit_id"] = child["data"]["id"]
        self.thread["ups"] = int(child["data"]["ups"])
        self.thread["ts"] = child["data"]["created_utc"]
        self.thread[
            "reddit_url"
        ] = f"https://www.reddit.com{child['data']['permalink']}"

    def sanitize(self):
        # There are some characters that look weird,
        # or are harder to parse. So we replace those.
        if "&amp;" in self.thread["text"]:
            self.thread["text"] = self.thread["text"].replace("&amp;", "&")
        if "–" in self.thread["text"]:
            self.thread["text"] = self.thread["text"].replace("–", "-")
        if "—" in self.thread["text"]:
            self.thread["text"] = self.thread["text"].replace("—", "-")

    def get_id(self):
        result = ""
        while self.char.isalnum() and self.pos < len(self.thread["text"]):
            result += self.char
            self.next_char()
        self.thread["tokens"].append(result)

    def peek(self):
        if self.pos < len(self.thread["text"]):
            try:
                next_char = self.thread["text"][self.pos + 1]
                return next_char
            except:
                return None

    def add_token(self, result):
        self.thread["tokens"].append(result)
        self.next_char()

    def next_char(self):
        self.pos += 1
        if self.pos < len(self.thread["text"]):
            self.char = self.thread["text"][self.pos]

    def create_token(self):
        if self.char.isalnum():
            self.get_id()
        elif self.char.isspace():
            self.add_token(self.char)
        elif self.char:
            self.add_token(self.char)
        else:
            self.next_char()

    def parse_text(self):
        self.sanitize()
        self.char = self.thread["text"][self.pos]
        while self.pos < len(self.thread["text"]):
            self.create_token()
        return self.thread


class Parser:
    def __init__(self, child):
        self.thread = Tokenizer(child).parse_text()
        self.tokens = self.thread["tokens"]
        self.pos = 0
        self.currentToken = self.thread["tokens"][self.pos]

    def parse_parens(self):
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

    def next_token(self):
        next_token = ""
        if self.pos < len(self.tokens):
            next_token = self.tokens[self.pos + 1]
        return next_token

    def parse_square_brackets(self):
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

    def get_name(self):
        stop_chars = ["(", "["]
        while self.pos < len(self.tokens):
            if self.currentToken in stop_chars:
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

    def contain_alpha_num(self):
        if any(char.isalnum() for char in self.currentToken):
            return True
        else:
            return False

    def parse_tokens(self):
        if self.currentToken == "[":
            self.parse_square_brackets()
        elif self.currentToken == "(":
            self.parse_parens()
        elif self.currentToken.isalnum():
            self.get_name()
        elif self.currentToken.isspace():
            self.advance()
        elif self.contain_alpha_num():
            self.get_name()
        else:
            self.get_name()

    def parse(self):
        while self.pos < len(self.tokens):
            self.parse_tokens()
        return self.thread
