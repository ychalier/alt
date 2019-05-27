import random
import codecs
import praw
import json
import sys
import re
import os

path = "/home/ychalier/Downloads/alt/entries.tsv"

class Entry:

    regexes = ["v=([a-zA-Z0-9_-]{11})", "tu\.be/([a-zA-Z0-9_-]{11})"]

    def __init__(self, submission=None):
        if submission is not None:
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

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def search(self, query):
        if query is None or query == "":
            return True
        return query.lower() in (self.title + str(self.flair)).lower()

    def is_valid(self):
        return self.title is not None and self.video_id is not None

    def to_tsv(self):
        attributes = [self.id, self.title, self.score, self.flair, self.video_id]
        return "\t".join(map(str, attributes)).replace("None", "")

    def from_tsv(line):
        split = line.strip().split("\t")
        if len(split) == 5:
            entry = Entry()
            entry.id = split[0]
            entry.title = split[1]
            entry.score = int(split[2])
            entry.flair = split[3]
            entry.video_id = split[4]
            return entry


class Scraper:

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

    def update(self, entries):
        reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
        )
        for entry in entries:
            submission = reddit.submission(id=entry.id)
            entry.score = submission.score
        return entries

    def expand(self, entries, limit):
        new = self.scrap(limit)
        for entry in entries:
            if entry not in new:
                new.append(entry)
        return new


class DiscJockey:

    watch_url = "https://www.youtube.com/watch_videos?video_ids="
    embed_url = "https://www.youtube.com/embed?playlist="
    limit = 50  # imposed by YouTube

    def __init__(self):
        pass

    def get_playlist(self, entries, query="", sort="rand"):
        selection = [e for e in entries if e.search(query)]
        if sort == "rand":
            random.shuffle(selection)
        elif sort == "top":
            selection.sort(key=lambda e: -e.score)
        ids = ",".join([e.video_id for e in selection[:self.limit]])
        return {
            "watch": self.watch_url + ids,
            "embed": self.embed_url + ids
        }


def export(filename, entries):
    with codecs.open(filename, "w", "utf-8") as file:
        for entry in entries:
            file.write("{}\n".format(entry.to_tsv()))


def load(filename):
    entries = []
    with codecs.open(filename, "r", "utf-8") as file:
        for line in file.readlines():
            entry = Entry.from_tsv(line)
            if entry is not None:
                entries.append(entry)
    return entries


def gather(credentials):
    client_id, client_secret, user_agent = credentials[:3]
    scraper = Scraper(client_id, client_secret, user_agent)
    entries = []
    if os.path.isfile(path):
        entries = load(path)
        entries = scraper.update(entries)
    entries = scraper.expand(entries, None)
    export(path, entries)
    return entries


if __name__ == "__main__":
    with open("credentials.txt") as file:
        credentials = [line.strip() for line in file.readlines()]
    if len(sys.argv) not in [2, 3, 4]:
        exit()
    query = ""
    sort = "rand"
    if len(sys.argv) == 3:
        if sys.argv[2] in ["rand", "new", "top"]:
            sort = sys.argv[2]
        else:
            query = sys.argv[2]
    elif len(sys.argv) == 4:
        sort = sys.argv[2]
        query = sys.argv[3]
    if sys.argv[1] == "gather":
        gather(credentials)
    elif sys.argv[1] == "dj":
        dj = DiscJockey()
        entries = load(path)
        print(json.dumps(dj.get_playlist(entries, query=query, sort=sort)))
    else:
        print("Incorrect mode:  gather | dj")
