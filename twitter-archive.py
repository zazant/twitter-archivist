#!python3
import subprocess
import argparse
import sys
from pathlib import Path
from shutil import rmtree
from os import path
import json
import urllib.request
import re
import snscrape.twitter as twitter

from mako.template import Template
from tqdm import tqdm

import datetime
def parse_datetime_arg(arg):
	for format in (
			"%Y-%m-%d %H:%M:%S %z",
			"%Y-%m-%d %H:%M:%S",
			"%Y-%m-%d %z",
			"%Y-%m-%d",
	):
		try:
			d = datetime.datetime.strptime(arg, format)
		except ValueError:
			continue
		else:
			if d.tzinfo is None:
				return d.replace(tzinfo=datetime.timezone.utc)
			return d
	# Try treating it as a unix timestamp
	try:
		d = datetime.datetime.fromtimestamp(int(arg), datetime.timezone.utc)
	except ValueError:
		pass
	else:
		return d
	raise argparse.ArgumentTypeError(f"Cannot parse {arg!r} into a datetime object")

def get_tweets(username, since_r=None):
	if since_r is not None:
		since = parse_datetime_arg(since_r)
	else:
		since = None
	results = []
	try:
		a = twitter.TwitterUserScraper(username).get_items()
		i = 0
		for i, tweet in enumerate(a, start=1):
			tweet_json = json.loads(tweet.json())
			if since is not None and tweet.date < since:
				print(f'Exiting due to reaching older results than {since_r}')
				break
			results.append(tweet_json)
			if i % 100 == 0:
				print(f'Scraping, {i} results so far')
		print(f'Done, found {i} results')
		return results
	except:
		return None


def archive(args):
	try:
		Path(args.name).mkdir(parents=True, exist_ok=False)
	except FileNotFoundError:
		sys.exit("error: parent directory not found")
	except FileExistsError:
		print("directory already exists, continuing")
	if Path(args.name + "/" + args.name + "_data.json").exists():
		sys.exit("error: " + args.name + "_data.json already exists")
	a = get_tweets(args.username)
	if (not a):
		rmtree(args.name)
		sys.exit("error: scraping failed")
	with open(args.name + "/" + args.name + "_data.json", "w") as f:
		json.dump(a, f, indent=4)
	Path(args.name + "/photos").mkdir(exist_ok=True)

	compile_args = argparse.Namespace()
	compile_args.folder_name = [args.name]
	compile_html(compile_args)

def update(args):
	for name in args.folder_name:
		print("----------------------")
		print(name)
		print("----------------------")
		failed = False
		a = {}
		with open(name + "/" + name + "_data.json", "r") as f:
			a = json.loads(f.read())
			if not a or not a[0] or not "date" in a[0] or not "user" in a[0] or not "username" in a[0]["user"]:
				failed = True
			else:
				date = a[0]["date"].split("T")[0]
				username = a[0]["user"]["username"]
				print("date: " + date)
				tweets = get_tweets(username, since_r=date)
				if not tweets:
					failed = True
			if failed:
				print("scraping_failed")
				continue
			for tweet in reversed(tweets):
				try:
					if not any(tweet["url"] == x["url"] for x in a):
						a.insert(0, tweet)
						print("added " + tweet["url"])
					else:
						print("skipping " + tweet["url"])
				except:
					print("failed tweet: " + tweet)
		with open(name + "/" + name + "_data.json", "w") as f:
			json.dump(a, f, indent=4)

		compile_args = argparse.Namespace()
		compile_args.folder_name = [name]
		compile_html(compile_args)

def compile_html(args):
	for name in args.folder_name:
		data_file = name + "/" + name + "_data.json"

		print("reading json")
		with open(data_file, 'r') as d:
			data_raw = d.read()

		data = json.loads(data_raw)

		urls = []

		conversations = {}

		linkpattern = re.compile(r'([A-Z]+)([0-9]+)')
		print("processing data")
		for d in data:
			content = re.sub(r"http(s)?:\/\/t.co\/\S{10}", "", d["renderedContent"])
			other_l = re.findall(r'[a-zA-Z0-9]*\.?[a-zA-Z0-9]+\.[a-zA-Z]{1,3}\b[-a-zA-Z0-9()@:%_\+.~#?&\/=]*\u2026?', content)
			for l in other_l:
				a = next((link for link in d["outlinks"] if l.replace("\u2026", "") in link), None)
				if a:
					content = content.replace(l, "<a href='" + a + "'>" + l.replace("\u2026", "...") + "</a>")
			d["renderedContent"] = content
			if d["quotedTweet"] != None:
				qcontent = re.sub(r"http(s)?:\/\/t.co\/\S{10}", "", d["quotedTweet"]["renderedContent"])
				other_l = re.findall(r'[a-zA-Z]+\.[a-zA-Z]{1,3}\b[-a-zA-Z0-9()@:%_\+.~#?&\/=]*\u2026?', qcontent)
				for l in other_l:
					a = next((link for link in d["quotedTweet"]["outlinks"] if l.replace("\u2026", "") in link), None)
					if a != None:
						qcontent = qcontent.replace(l, "<a href='" + a + "'>" + l.replace("\u2026", "...") + "</a>")
				d["quotedTweet"]["renderedContent"] = qcontent
			if d["conversationId"] not in conversations:
				conversations[d["conversationId"]] = [d]
			else:
				conversations[d["conversationId"]].insert(0, d)
			if d["media"]:
				for i in d["media"]:
					if i["type"] == "photo":
						f = name + "/photos/" + i["fullUrl"].split('/')[-1].split('&')[0].replace("?format=",".")
						if not path.exists(f):
							urls.append((i["fullUrl"], f))
						i["fullUrl"] = f.split("/", 1)[1]
					if i["type"] == "video":
						url = next(video for video in i["variants"] if video["bitrate"])["url"]
						f = name + "/photos/" + url.split('/')[-1].split('?')[0]
						if not path.exists(f):
							urls.append((url, f))
						i["variants"][0]["url"] = f.split("/", 1)[1]
					if i["type"] == "gif":
						url = next(video for video in i["variants"])["url"]
						f = name + "/photos/" + url.split('/')[-1]
						if not path.exists(f):
							urls.append((url, f))
						i["variants"][0]["url"] = f.split("/", 1)[1]
			if d["quotedTweet"] and d["quotedTweet"]["media"]:
				for i in d["quotedTweet"]["media"]:
					if i["type"] == "photo":
						f = name + "/photos/" + i["fullUrl"].split('/')[-1].split('&')[0].replace("?format=",".")
						if not path.exists(f):
							urls.append((i["fullUrl"], f))
						i["fullUrl"] = f.split("/", 1)[1]
					if i["type"] == "video":
						url = next(video for video in i["variants"] if video["bitrate"])["url"]
						f = name + "/photos/" + url.split('/')[-1].split('?')[0]
						if not path.exists(f):
							urls.append((url, f))
						i["variants"][0]["url"] = f.split("/", 1)[1]
					if i["type"] == "gif":
						url = next(video for video in i["variants"])["url"]
						f = name + "/photos/" + url.split('/')[-1]
						if not path.exists(f):
							urls.append((url, f))
						i["variants"][0]["url"] = f.split("/", 1)[1]

		if urls:
			print("downloading images")
			t = tqdm(urls)
			for d in t:
				t.set_description(d[1])
				urllib.request.urlretrieve(d[0], d[1])
				
		print("making html")
		with open(name + "/" + name + ".html", 'w') as out:
			out.write(Template(filename=(path.dirname(path.abspath(__file__)) + "/template.mako")).render(name=name, conversations=conversations))

parser = argparse.ArgumentParser(description="Twitter account archiver.")
subparsers = parser.add_subparsers(dest="mode", required=True, help="mode")

archive_parser = subparsers.add_parser("archive")
archive_parser.add_argument("name", type=str)
archive_parser.add_argument("username", type=str)
archive_parser.set_defaults(func=archive)

update_parser = subparsers.add_parser("update")
update_parser.add_argument("folder_name", nargs="+", type=str)
update_parser.set_defaults(func=update)

compile_parser = subparsers.add_parser("compile")
compile_parser.add_argument("folder_name", nargs="+", type=str)
compile_parser.set_defaults(func=compile_html)

args = parser.parse_args()
args.func(args)
