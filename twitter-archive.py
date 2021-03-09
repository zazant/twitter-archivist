#!/usr/bin/env python3
import subprocess
import argparse
import sys
from pathlib import Path
from shutil import rmtree
import os
from os import path
import json
import urllib.request
import urllib.error
import re
import snscrape.twitter as twitter
import time
import pickle
from math import ceil
from random import shuffle

from mako.template import Template
from tqdm import tqdm
from bottle import route, run, template, static_file, redirect

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

def get_tweets(username, since=None, until=None, private=False, headers_file=None):
	if since:
		since = parse_datetime_arg(since)
	results = []
	try:
		private_headers = {}
		if private:
			if headers_file:
				try:
					with open(headers_file, "r") as f:
						private_headers = json.loads(f.read())
				except:
					print("headers_file opening failed")
			else:
				print("paste headers object:")
				lines = []
				while True:
					line = input()
					if line:
						lines.append(line)
					else:
						break
				text = '\n'.join(lines)
				private_headers = json.loads(text)
		a = twitter.TwitterUserScraper(username, until=until, private_headers=private_headers).get_items()
		i = 0
		for i, tweet in enumerate(a, start=1):
			tweet_json = json.loads(tweet.json())
			if since is not None and tweet.date < since:
				print(f'Exiting due to reaching older results than {since.strftime("%Y-%m-%d")}')
				break
			results.append(tweet_json)
			if i % 100 == 0:
				print(f'Scraping, {i} results so far')
		print(f'Done, found {i} results')
		return results
	except:
		print("error in get_tweets")
		return results


def archive(args):
	try:
		Path(args.name).mkdir(parents=True, exist_ok=False)
	except FileNotFoundError:
		sys.exit("error: parent directory not found")
	except FileExistsError:
		print("directory already exists, continuing")
	if Path(args.name + "/" + args.name + "_data.json").exists():
		sys.exit("error: " + args.name + "_data.json already exists")
	a = get_tweets(args.username, since=args.since, private=args.private, headers_file=args.headers_file)
	if (not a):
		rmtree(args.name)
		sys.exit("error: scraping failed")
	with open(args.name + "/" + args.name + "_data.json", "w") as f:
		json.dump(a, f, indent=4)
	if a[0] and "user" in a[0] and a[0]["user"]:
		with open(args.name + "/" + args.name + "_user_data.json", "w") as f:
			json.dump(a[0]["user"], f, indent=4)

	Path(args.name + "/photos").mkdir(exist_ok=True)

	compile_args = argparse.Namespace()
	compile_args.folder_name = [args.name]
	compile_args.alert = False
	compile_args.return_conversations = False
	compile_html(compile_args)

def update(args):
	for name in args.folder_name:
		print("----------------------")
		print(name)
		print("----------------------")
		private = False
		try:
			with open(name + "/" + name + "_user_data.json", "r") as f:
				temp_user = json.loads(f.read())
				if temp_user["protected"]:
					private = True
					print("protected user")
		except:
			private = False

		failed = False
		a = {}
		with open(name + "/" + name + "_data.json", "r") as f:
			a = json.loads(f.read())
			if not a or not a[0] or not "date" in a[0] or not "user" in a[0] or not "username" in a[0]["user"]:
				failed = True
			else:
				if not args.reverse:
					date = a[0]["date"].split("T")[0]
				else:
					date = a[-1]["date"].split("T")[0]
				username = a[0]["user"]["username"]
				print("date: " + date)
				if not args.reverse:
					tweets = get_tweets(username, since=date, private=private, headers_file=args.headers_file)
				else:
					tweets = get_tweets(username, until=date, private=private, headers_file=args.headers_file)
				if not tweets:
					failed = True
			if failed:
				print("no tweets found")
			else:
				if not args.reverse:
					for tweet in reversed(tweets):
						try:
							if not any(tweet["url"] == x["url"] for x in a):
								a.insert(0, tweet)
								print("added " + tweet["url"])
						except:
							print("failed tweet: " + tweet)
					if tweets and tweets[0] and "user" in tweets[0] and tweets[0]["user"]:
						with open(name + "/" + name + "_user_data.json", "w") as fdata:
							json.dump(tweets[0]["user"], fdata, indent=4)
				else:
					for tweet in tweets:
						try:
							if not any(tweet["url"] == x["url"] for x in a):
								a.append(tweet)
								print("added " + tweet["url"])
							else:
								print("skipping " + tweet["url"])
						except:
							print("failed tweet: " + tweet)

		with open(name + "/" + name + "_data.json", "w") as f:
			json.dump(a, f, indent=4)

		print("compiling html")

		compile_args = argparse.Namespace()
		compile_args.folder_name = [name]
		compile_args.alert = False
		compile_args.return_conversations = False
		compile_html(compile_args)

def compile_html(args):
	for name in args.folder_name:
		if args.alert:
			print("----------------------")
			print(name)
			print("----------------------")
		data_file = name + "/" + name + "_data.json"

		print("reading json")
		with open(data_file, 'r') as d:
			data_raw = d.read()

		data = json.loads(data_raw)

		urls = []

		conversations = {}

		linkpattern = re.compile(r'([A-Z]+)([0-9]+)')
		print("processing data")
		for d in tqdm(data):
			content = re.sub(r"http(s)?:\/\/t.co\/\S{10}", "", d["renderedContent"])
			other_l = re.findall(r'[a-zA-Z0-9]*\.?[a-zA-Z0-9-]+\.[a-zA-Z]{1,3}\b[-a-zA-Z0-9()@:%_\+.~#?&\/=]*\u2026?', content)
			for l in other_l:
				a = next((link for link in d["outlinks"] if l.replace("\u2026", "") in link), None)
				if a:
					content = content.replace(l, "<a href='" + a + "'>" + l.replace("\u2026", "...") + "</a>")
			d["renderedContent"] = content.replace("\n", "<br>")
			if d["quotedTweet"] != None:
				qcontent = re.sub(r"http(s)?:\/\/t.co\/\S{10}", "", d["quotedTweet"]["renderedContent"])
				other_l = re.findall(r'[a-zA-Z0-9]*\.?[a-zA-Z0-9-]+\.[a-zA-Z]{1,3}\b[-a-zA-Z0-9()@:%_\+.~#?&\/=]*\u2026?', qcontent)
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
				try:
					urllib.request.urlretrieve(d[0], d[1])
				except urllib.error.HTTPError:
					print(d[1] + " (" + d[0] + "): download failed")

		if not args.return_conversations:
			print("making html")
			with open(name + "/" + name + ".html", 'w') as out:
				out.write(Template(filename=(path.dirname(path.abspath(__file__)) + "/template.mako")).render(name=name, conversations=conversations.values(), pagination=None))
		else:
			return conversations

def server(args):
	cached_data = {}
	if path.exists(".cached_server_data") and not args.recache:
		print("loading cached data")
		cached_data = pickle.load(open(".cached_server_data", "rb"))

	if cached_data:
		print("using cached data. use --recache to recache data")
		modified_html_files = cached_data["modified_html_files"]
		conversations = cached_data["conversations"]
	else:
		print("----------------------")
		print("first time server setup. this might take a few minutes")
		compile_args = argparse.Namespace()
		conversations = {}
		compile_args.alert = True
		modified_html_files = {}
		print("processing html files")
		for name in args.folder_name:
			with open(name + "/" + name + ".html", 'r') as f:
				compile_args.folder_name = [name]
				compile_args.return_conversations = True
				conversations[name] = compile_html(compile_args)
				html = f.read()
			modified_html_files[name] = re.sub(r"(?<=img src=\")photos", "/accounts/" + name + "/photos", html)
		print("caching data")
		pickle.dump({
			"modified_html_files": modified_html_files,
			"conversations": conversations
		}, open(".cached_server_data", "wb"))


	@route('/')
	def index():
		return template("""
		<body style="margin: 0 auto; max-width:750px; font-family: -apple-system, system-ui, 'Segoe UI', Roboto, Helvetica, A;">
		<h1 style="margin: 8px 0">twitter-archive</h1>
		<hr>
		<main>
		  % for name in folder_names:
		  <a href="/accounts/{{name}}">{{name}}</a><br>
		  <hr>
		  % end
		</main>
		</body>
		""", folder_names=args.folder_name)

	@route("/accounts/<name>/<filepath:re:.*\.json>")
	def server_static(name, filepath):
		return static_file(name + "/" + filepath, root=os.getcwd())

	@route('/accounts/<name>/photos/<filepath:path>')
	@route('/accounts/<name>/<page:int>/photos/<filepath:path>')
	@route('/accounts/<name>/<page:int>/<sort>/photos/<filepath:path>')
	@route('/accounts/<name>/<page:int>/<sort>/<reverse:int>/photos/<filepath:path>')
	@route('/accounts/<name>/<page:int>/<sort>/<reverse:int>/<all_replies:int>/photos/<filepath:path>')
	@route('/accounts/<name>/<page:int>/<sort>/<reverse:int>/<all_replies:int>/<initiating_replies:int>/photos/<filepath:path>')
	def server_static(name, filepath, page=1, sort="date", reverse=0, all_replies=1, initiating_replies=1):
		return static_file(name + "/photos/" + filepath, root=os.getcwd())

	@route('/accounts/<name>')
	def index(name):
		if not args.pagination:
			return modified_html_files[name]
		else:
			redirect("/accounts/" + name + "/1")

	if args.pagination:
		@route('/accounts/<name>/<page:int>')
		@route('/accounts/<name>/<page:int>/<sort>')
		@route('/accounts/<name>/<page:int>/<sort>/<reverse:int>')
		@route('/accounts/<name>/<page:int>/<sort>/<reverse:int>/<all_replies:int>')
		@route('/accounts/<name>/<page:int>/<sort>/<reverse:int>/<all_replies:int>/<initiating_replies:int>')
		def index(name, page, sort="date", reverse=0, all_replies=1, initiating_replies=1):
			pagination = {
				"results": args.pagination,
				"page": page,
				"sort": sort,
				"reverse": reverse,
				"all-replies": all_replies,
				"initiating-replies": initiating_replies,
				"pages": ceil(len(conversations[name]) / args.pagination)
			}
			start_index = pagination["results"] * (pagination["page"] - 1)
			end_index = start_index + pagination["results"]
			conversations_page = []
			filtered_items = []
			if initiating_replies or all_replies:
				for conversation in conversations[name].values():
					if initiating_replies and "@" in conversation[0]["renderedContent"]:
						continue
					filtered_conversation = []
					if all_replies:
						for reply in conversation:
							if "@" not in reply["renderedContent"]:
								filtered_conversation.append(reply)
						if len(filtered_conversation) == 0:
							continue
					else:
						filtered_conversation = conversation
					filtered_items.append(filtered_conversation)
				pagination["pages"] = ceil(len(filtered_items) / args.pagination)
			else:
				filtered_items = conversations[name].values()

			if start_index < len(conversations[name]):
				if sort == "date":
					conversations_page = sorted(list(filtered_items), key=lambda x: x[0]["date"], reverse=not bool(reverse))[start_index:end_index]
				if sort == "thread-size":
					conversations_page = sorted(list(filtered_items), key=lambda x: len(x),
												reverse=not bool(reverse))[start_index:end_index]
				if sort == "likes":
					conversations_page = sorted(list(filtered_items), key=lambda x: x[0]["likeCount"],
												reverse=not bool(reverse))[start_index:end_index]
				if sort == "random":
					conversations_page = list(filtered_items)
					shuffle(conversations_page)
					conversations_page = conversations_page[start_index:end_index]
			return Template(filename=(path.dirname(path.abspath(__file__)) + "/template.mako")).render(name=name, conversations=conversations_page, pagination=pagination)

	run(host=args.ip, port=args.port)

parser = argparse.ArgumentParser(description="Twitter account archiver.")
subparsers = parser.add_subparsers(dest="mode", required=True, help="mode")

archive_parser = subparsers.add_parser("archive")
archive_parser.add_argument("name", type=str)
archive_parser.add_argument("username", type=str)
archive_parser.add_argument('--since', dest='since', type=parse_datetime_arg)
archive_parser.add_argument('--private', dest='private', action='store_true')
archive_parser.add_argument('--headers-file', default=None, type=str)
archive_parser.set_defaults(private=False)
archive_parser.set_defaults(func=archive)

update_parser = subparsers.add_parser("update")
update_parser.add_argument("folder_name", nargs="+", type=str)
update_parser.add_argument('--reverse', dest='reverse', action='store_true')
update_parser.add_argument('--headers-file', default=None, type=str)
update_parser.set_defaults(reverse=False)
update_parser.set_defaults(func=update)

compile_parser = subparsers.add_parser("compile")
compile_parser.add_argument("folder_name", nargs="+", type=str)
compile_parser.set_defaults(func=compile_html)
compile_parser.set_defaults(return_conversations=False)
compile_parser.set_defaults(alert=True)

server_parser = subparsers.add_parser("server")
server_parser.add_argument("folder_name", nargs="+", type=str)
server_parser.add_argument('--pagination', default=0, dest='pagination', type=int)
server_parser.add_argument('--port', default=8000, dest='port', type=int)
server_parser.add_argument('--ip', default="localhost", dest='ip', type=str)
server_parser.add_argument('--recache', dest='recache', action='store_true')
server_parser.set_defaults(recache=False)
server_parser.set_defaults(func=server)

args = parser.parse_args()
args.func(args)
