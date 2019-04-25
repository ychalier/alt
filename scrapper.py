import random
import praw
import sys
import re

class Entry:

    regexes = ["v=([a-zA-Z0-9_-]{11})", "tu\.be/([a-zA-Z0-9_-]{11})"]

    def __init__(self, submission):
        self.id = submission.id
        self.title = submission.title
        self.score = submission.score
        self.flair = submission.link_flair_text
        self.video_id = None
        for pattern in self.regexes:
            match = re.search(pattern, submission.url)
            if match is not None:
                self.video_id = match.group(1)
                break
    def search(self, query):
        if query is None:
            return True
        return query.lower() in (self.title + str(self.flair)).lower()

    def is_valid(self):
        return self.title is not None and self.video_id is not None

    def to_tsv(self):
        attributes = [self.title, self.score, self.flair, self.video_id]
        return "\t".join(map(str, attributes)).replace("None", "")

class Scrapper:

    subreddit_name = "Frenchaltmusic"

    def __init__(self, client_id, client_secret, user_agent):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent

    def scrap(self, limit):
        reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
        )
        subreddit = reddit.subreddit(self.subreddit_name)
        entries = []
        for submission in subreddit.new(limit=limit):
            entry = Entry(submission)
            if entry.is_valid():
                entries.append(entry)
        return entries

class DiscJockey:

    base_url = "https://www.youtube.com/embed?playlist="
    limit = 50  # imposed by YouTube

    def __init__(self):
        pass

    def get_playlist(self, entries, query=None, shuffle=True):
        selection = [e.video_id for e in entries if e.search(query)]
        if shuffle:
            random.shuffle(selection)
        return self.base_url + ",".join(selection[:self.limit])

def export(filename, entries):
    with open(filename, "w") as file:
        for entry in entries:
            file.write("{}\n".format(entry.to_tsv()))

if __name__ == "__main__":
    with open("credentials.txt") as file:
        credentials = [line.strip() for line in file.readlines()]
    client_id, client_secret, user_agent = credentials[:3]
    scrapper = Scrapper(client_id, client_secret, user_agent)
    entries = scrapper.scrap(None)
    export("entries.tsv", entries)
    dj = DiscJockey()
    if len(sys.argv) == 2:
        print(dj.get_playlist(entries, query=sys.argv[1]))
    else:
        print(dj.get_playlist(entries))
