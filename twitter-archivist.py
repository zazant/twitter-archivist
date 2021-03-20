#!/usr/bin/env python3
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
import pickle
from math import ceil
from random import shuffle
import datetime
from shutil import copyfile
import logging

from mako.template import Template
from tqdm import tqdm
from bottle import route, run, template, static_file, redirect, request

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# function from snscrape, originally
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


def parse_folder_name(folder_name):
	if folder_name[-1] == "/":
		folder_name = folder_name[0:-1]
	if folder_name[0] == "/":
		parsed_folder_name = folder_name
		name = folder_name.split("/")[-1]
	else:
		parsed_folder_name = os.getcwd() + "/" + folder_name + "/"
		name = [s for s in parsed_folder_name.split("/") if s != ""][-1]

	return parsed_folder_name, name


def get_tweets(username, since=None, until=None, private=False, headers_file=None, input_headers=True):
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
					logging.warning("headers_file opening failed")
			elif input_headers:
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
			else:
				logging.warning("private account with no headers given, skipping")
				return
		a = twitter.TwitterUserScraper(username, until=until, private_headers=private_headers).get_items()
		i = 0
		for i, tweet in enumerate(a, start=1):
			tweet_json = json.loads(tweet.json())
			if since is not None and tweet.date < since:
				logging.info(f'Exiting due to reaching older results than {since.strftime("%Y-%m-%d")}')
				break
			results.append(tweet_json)
			if i % 100 == 0:
				logging.info(f'Scraping, {i} results so far')
		logging.info(f'Done, found {i} results')
		return results
	except:
		logging.warning("error in get_tweets")
		return results


def archive(args):
	parsed_folder_name, name = parse_folder_name(args.name)
	try:
		Path(parsed_folder_name).mkdir(parents=True, exist_ok=False)
	except FileNotFoundError:
		sys.exit("error: parent directory not found")
	except FileExistsError:
		logging.warning("directory already exists, continuing")
	if Path(args.name + "/" + args.name + "_data.json").exists():
		sys.exit("error: " + args.name + "_data.json already exists")
	a = get_tweets(args.username, since=args.since, private=args.private, headers_file=args.headers_file)
	if (not a):
		rmtree(args.name)
		sys.exit("error: scraping failed")
	with open(parsed_folder_name + name + "_data.json", "w") as f:
		json.dump(a, f, indent=4)
	if a[0] and "user" in a[0] and a[0]["user"]:
		with open(parsed_folder_name + name + "_user_data.json", "w") as f:
			json.dump(a[0]["user"], f, indent=4)

	Path(parsed_folder_name + "photos").mkdir(exist_ok=True)

	compile_args = argparse.Namespace()
	compile_args.folder_name = [args.name]
	compile_args.alert = False
	compile_args.return_conversations = False
	compile_html(compile_args)


def update(args):
	for folder_name in args.folder_name:
		parsed_folder_name, name = parse_folder_name(folder_name)
		logging.info("----------------------")
		logging.info(name)
		logging.info("----------------------")
		if "input_headers" not in args:
			args.input_headers = True
		private = False
		try:
			with open(parsed_folder_name + name + "_user_data.json", "r") as f:
				temp_user = json.loads(f.read())
				if temp_user["protected"]:
					private = True
					logging.info("protected user")
		except:
			private = False


		failed = False
		a = {}
		with open(parsed_folder_name + name + "_data.json", "r") as f:
			a = json.loads(f.read())
			if not a or not a[0] or not "date" in a[0] or not "user" in a[0] or not "username" in a[0]["user"]:
				failed = True
			else:
				if not args.reverse:
					date = a[0]["date"].split("T")[0]
				else:
					date = a[-1]["date"].split("T")[0]
				username = a[0]["user"]["username"]
				logging.info("date: " + date)
				try:
					if not args.reverse:
						tweets = get_tweets(username, since=date, private=private, headers_file=args.headers_file, input_headers=args.input_headers)
					else:
						tweets = get_tweets(username, until=date, private=private, headers_file=args.headers_file, input_headers=args.input_headers)
				except:
					failed = True
				if not tweets:
					failed = True
			if failed:
				logging.warning("no tweets found")
				break
			else:
				if not args.reverse:
					for tweet in reversed(tweets):
						try:
							if not any(tweet["url"] == x["url"] for x in a):
								a.insert(0, tweet)
								logging.info("added " + tweet["url"])
						except:
							logging.warning("failed tweet: " + tweet)
					if tweets and tweets[0] and "user" in tweets[0] and tweets[0]["user"]:
						with open(parsed_folder_name + name + "_user_data.json", "w") as fdata:
							json.dump(tweets[0]["user"], fdata, indent=4)
				else:
					for tweet in tweets:
						try:
							if not any(tweet["url"] == x["url"] for x in a):
								a.append(tweet)
								logging.info("added " + tweet["url"])
							else:
								logging.info("skipping " + tweet["url"])
						except:
							logging.warning("failed tweet: " + tweet)

		if not failed:
			try:
				logging.info("making a backup file before update (" + name + "_data_backup.json)")
				copyfile(parsed_folder_name + name + "_data.json", parsed_folder_name + name + "_data_backup.json")
			except:
				logging.warning("failed to make backup")

			with open(parsed_folder_name + name + "_data.json", "w") as f:
				json.dump(a, f, indent=4)

			try:
				logging.info("json dump successful, removing backup file")
				os.remove(parsed_folder_name + name + "_data_backup.json")
			except:
				logging.warning("removing backup file failed")
		else:
			return

		logging.info("compiling html")

		compile_args = argparse.Namespace()
		compile_args.folder_name = [folder_name]
		compile_args.alert = False
		if not args.return_conversations:
			compile_args.return_conversations = False
			compile_html(compile_args)
		else:
			compile_args.return_conversations = True
			return compile_html(compile_args)


def compile_html(args):
	for folder_name in args.folder_name:
		parsed_folder_name, name = parse_folder_name(folder_name)
		if args.alert:
			logging.info("----------------------")
			logging.info(name)
			logging.info("----------------------")
		data_file = parsed_folder_name + name + "_data.json"

		logging.info("reading json")
		with open(data_file, 'r') as d:
			data_raw = d.read()

		data = json.loads(data_raw)

		urls = []

		conversations = {}

		logging.info("processing data")
		for d in tqdm(data):
			content = re.sub(r"http(s)?://t.co/\S{10}", "", d["renderedContent"])
			other_l = re.findall(r'[a-zA-Z0-9]*\.?[a-zA-Z0-9-]+\.[a-zA-Z]{1,3}\b[-a-zA-Z0-9()@:%_+.~#?&/=]*\u2026?', content)
			for l in other_l:
				a = next((link for link in d["outlinks"] if l.replace("\u2026", "") in link), None)
				if a:
					content = content.replace(l, "<a href='" + a + "'>" + l.replace("\u2026", "...") + "</a>")
			d["renderedContent"] = content.replace("\n", "<br>")
			if d["quotedTweet"] != None:
				qcontent = re.sub(r"http(s)?://t.co/\S{10}", "", d["quotedTweet"]["renderedContent"])
				other_l = re.findall(r'[a-zA-Z0-9]*\.?[a-zA-Z0-9-]+\.[a-zA-Z]{1,3}\b[-a-zA-Z0-9()@:%_+.~#?&/=]*\u2026?', qcontent)
				for l in other_l:
					a = next((link for link in d["quotedTweet"]["outlinks"] if l.replace("\u2026", "") in link), None)
					if a != None:
						qcontent = qcontent.replace(l, "<a href='" + a + "'>" + l.replace("\u2026", "...") + "</a>")
				d["quotedTweet"]["renderedContent"] = qcontent.replace("\n", "<br>")
			if d["conversationId"] not in conversations:
				conversations[d["conversationId"]] = [d]
			else:
				conversations[d["conversationId"]].insert(0, d)
			if d["media"]:
				for i in d["media"]:
					if i["type"] == "photo":
						f = "photos/" + i["fullUrl"].split('/')[-1].split('&')[0].replace("?format=",".")
						if not path.exists(parsed_folder_name + f):
							urls.append((i["fullUrl"], parsed_folder_name + f))
						i["fullUrl"] = f
					if i["type"] == "video":
						url = next(video for video in i["variants"] if video["bitrate"])["url"]
						f = "photos/" + url.split('/')[-1].split('?')[0]
						if not path.exists(parsed_folder_name + f):
							urls.append((url, parsed_folder_name + f))
						i["variants"][0]["url"] = f
					if i["type"] == "gif":
						url = next(video for video in i["variants"])["url"]
						f = "photos/" + url.split('/')[-1]
						if not path.exists(parsed_folder_name + f):
							urls.append((url, parsed_folder_name + f))
						i["variants"][0]["url"] = f
			if d["quotedTweet"] and d["quotedTweet"]["media"]:
				for i in d["quotedTweet"]["media"]:
					if i["type"] == "photo":
						f = "photos/" + i["fullUrl"].split('/')[-1].split('&')[0].replace("?format=",".")
						if not path.exists(parsed_folder_name + f):
							urls.append((i["fullUrl"], parsed_folder_name + f))
						i["fullUrl"] = f
					if i["type"] == "video":
						url = next(video for video in i["variants"] if video["bitrate"])["url"]
						f = "photos/" + url.split('/')[-1].split('?')[0]
						if not path.exists(parsed_folder_name + f):
							urls.append((url, parsed_folder_name + f))
						i["variants"][0]["url"] = f
					if i["type"] == "gif":
						url = next(video for video in i["variants"])["url"]
						f = "photos/" + url.split('/')[-1]
						if not path.exists(parsed_folder_name + f):
							urls.append((url, parsed_folder_name + f))
						i["variants"][0]["url"] = f

		if urls:
			logging.info("downloading images")
			t = tqdm(urls)
			for d in t:
				t.set_description(d[1])
				try:
					urllib.request.urlretrieve(d[0], d[1])
				except urllib.error.HTTPError:
					logging.info(d[1] + " (" + d[0] + "): download failed")

		if not args.return_conversations:
			logging.info("making html")
			with open(parsed_folder_name + name + ".html", 'w') as out:
				out.write(Template(filename=(path.dirname(path.abspath(__file__)) + "/template.mako")).render(name=name, conversations=conversations.values(), pagination=None))
		else:
			return conversations, len(data), data[0]["date"]


def server(args):
	cached_data = {}
	if path.exists(".cached_server_data") and args.cache:
		logging.info("loading cached data")
		cached_data = pickle.load(open(".cached_server_data", "rb"))

	conversations = {}
	latest_dates = {}
	tweet_amount = {}
	modified_html_files = {}
	names = {}

	def refresh(conversations, modified_html_files):
		compile_args = argparse.Namespace()
		compile_args.alert = True
		logging.info("processing html files")
		for folder_name in args.folder_name:
			parsed_folder_name, name = parse_folder_name(folder_name)
			try:
				with open(parsed_folder_name + name + "_user_data.json", "r") as r:
					username = json.loads(r.read())["username"]
			except FileNotFoundError:
				username = name
			names[name] = parsed_folder_name, name, username
			with open(parsed_folder_name + name + ".html", 'r') as f:
				compile_args.folder_name = [folder_name]
				compile_args.return_conversations = True
				conversations[name], tweet_amount[name], latest_dates[name] = compile_html(compile_args)
				html = f.read()
			modified_html_files[name] = re.sub(r"(?<=img src=\")photos", "/accounts/" + name + "/photos", html)
		logging.info("caching data")
		pickle.dump({
			"modified_html_files": modified_html_files,
			"conversations": conversations,
			"tweet_amount": tweet_amount,
			"latest_dates": latest_dates,
			"names": names
		}, open(os.getcwd() + "/.cached_server_data", "wb"))

	def update_request(conversations):
		update_args = argparse.Namespace()
		update_args.return_conversations = True
		update_args.reverse = False
		update_args.input_headers = False
		update_args.headers_file = args.headers_file
		for folder_name in args.folder_name:
			parsed_folder_name, name = parse_folder_name(folder_name)
			with open(parsed_folder_name + name + ".html", 'r') as f:
				update_args.folder_name = [folder_name]
				update_data = update(update_args)
				if update_data:
					conversations[name], tweet_amount[name], latest_dates[name] = update_data
				else:
					continue
		logging.info("caching data")
		pickle.dump({
			"modified_html_files": modified_html_files,
			"conversations": conversations
		}, open(os.getcwd() + "/.cached_server_data", "wb"))

	if cached_data:
		logging.info("loaded")
		modified_html_files = cached_data["modified_html_files"]
		conversations = cached_data["conversations"]
		tweet_amount = cached_data["tweet_amount"]
		latest_dates = cached_data["latest_dates"]
		for folder_name in args.folder_name:
			parsed_folder_name, name = parse_folder_name(folder_name)
			names[name] = parsed_folder_name
	else:
		refresh(conversations, modified_html_files)

	@route('/')
	def index():
		# account_info = {}
		updated = {}
		folder_names = []
		for folder_name in args.folder_name:
			parsed_folder_name, name = parse_folder_name(folder_name)
			updated[name] = datetime.datetime.strptime(latest_dates[name], "%Y-%m-%dT%H:%M:%S+00:00")\
				.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None).strftime("%A %m/%d/%Y at %-I:%M %p")
			folder_names.append((parsed_folder_name, name))
		folder_names = sorted(folder_names, key=lambda x: datetime.datetime.strptime(updated[x[1]], "%A %m/%d/%Y at %I:%M %p"), reverse=True)
		# 	with open(parsed_folder_name + name + "_user_data.json", "r") as r:
		# 		account_info[name] = json.loads(r.read())
		for parsed_folder_name, name in folder_names:
			updated[name] = updated[name].replace(datetime.datetime.now().strftime("%A %m/%d/%Y"), "Today")\
				.replace((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%A %m/%d/%Y"), "Yesterday")
		return template("""
		<head><title>twitter-archivist</title></head>
		<body style="margin: 0 auto; max-width:624px; font-family: -apple-system, system-ui, 'Segoe UI', Roboto, Helvetica, A;">
		<div style="display: flex; justify-content: space-between; align-items: center">
			<h1 style="margin: 8px 0">twitter-archivist</h1>
			<div style="color: grey">
				<a style="cursor: pointer" onclick="refresh()" id="refresh">refresh</a> · 
				<a style="cursor: pointer" onclick="update()" id="update">update</a>
			</div>
		</div>

		<script type="text/javascript">
			function refresh() {
				document.querySelector("#refresh").innerText = "."
				setInterval(function() {
					if (document.querySelector("#refresh").innerText === ".")
						document.querySelector("#refresh").innerText = ".."
					else if (document.querySelector("#refresh").innerText === "..")
						document.querySelector("#refresh").innerText = "..."
					else
						document.querySelector("#refresh").innerText = "."
				}, 500)
				var xhr = new XMLHttpRequest();
				xhr.onreadystatechange = function () {
					if (xhr.readyState === 4) {
						window.location.reload(false);
						//alert(xhr.response);
					}
				}
				xhr.open('get', '/refresh', true);
				xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
				xhr.send();
			}

			function update() {
				document.querySelector("#update").innerText = "."
				setInterval(function() {
					if (document.querySelector("#update").innerText === ".")
						document.querySelector("#update").innerText = ".."
					else if (document.querySelector("#update").innerText === "..")
						document.querySelector("#update").innerText = "..."
					else
						document.querySelector("#update").innerText = "."
				}, 500)
				var xhr = new XMLHttpRequest();
				xhr.onreadystatechange = function () {
					if (xhr.readyState === 4) {
						window.location.reload(false);
						//alert(xhr.response);
					}
				}
				xhr.open('get', '/update', true);
				xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
				xhr.send();
			}
		</script>
		<hr style="margin-top: 0">
		<a href="/combined" style="text-decoration: none; padding: 10px; line-height: 22px">combined feed</a>
		<hr>
		<main>
			% for parsed_folder_name, name in folder_names:
			<div style="padding: 10px;margin: 10px 5px; border-radius: 5px; box-shadow: 0px 0.7px 1px 0.8px lightgray;">
				<a href="/accounts/{{name}}" style="text-decoration: none">{{name}}</a> <i style="color: grey">· {{updated[name]}} · {{tweet_amount[name]}} tweets</i><br>
			</div>
			% end
		</main>
		</body>
		""", folder_names=folder_names, updated=updated, tweet_amount=tweet_amount)

	@route('/refresh')
	def index():
		refresh(conversations, modified_html_files)
		return "refreshed"

	@route('/update')
	def index():
		update_request(conversations)
		return "updated"

	@route('/combined')
	def index():
		redirect("/combined/1")

	@route('/combined/<page:int>')
	def index(page):
		sort = request.query["sort"] if "sort" in request.query else "date"
		reverse = int(request.query["reverse"]) if "reverse" in request.query else 0
		all_replies = int(request.query["all-replies"]) if "all-replies" in request.query else 1
		initiating_replies = int(request.query["initiating-replies"]) if "initiating-replies" in request.query else 1
		conversations_merged = {}
		for n in conversations.keys():
			conversations_merged.update(conversations[n])
		pagination = {
			"results": args.pagination,
			"page": page,
			"sort": sort,
			"reverse": reverse,
			"all-replies": all_replies,
			"initiating-replies": initiating_replies,
		}
		start_index = pagination["results"] * (pagination["page"] - 1)
		end_index = start_index + pagination["results"]
		conversations_page = []
		filtered_items = []
		if initiating_replies or all_replies:
			for conversation in conversations_merged.values():
				if initiating_replies and len(conversation[0]["renderedContent"]) >= 1 and conversation[0]["renderedContent"][0] == '@':
					continue
				filtered_conversation = []
				if all_replies:
					for reply in conversation:
						if len(reply["renderedContent"]) >= 1 and reply["renderedContent"][0] == '@':
							continue
						else:
							filtered_conversation.append(reply)
					if len(filtered_conversation) == 0:
						continue
				else:
					filtered_conversation = conversation
				filtered_items.append(filtered_conversation)
			pagination["pages"] = ceil(len(filtered_items) / args.pagination)
		else:
			filtered_items = conversations_merged.values()

		pagination["pages"] = ceil(len(filtered_items) / args.pagination)
		if pagination["page"] > pagination["pages"]:
			redirect("/combined/" + str(pagination["pages"]))

		if start_index < len(conversations_merged):
			if sort == "date":
				conversations_page = sorted(list(filtered_items), key=lambda x: x[0]["date"],
											reverse=not bool(reverse))[start_index:end_index]
			if sort == "thread-size":
				conversations_page = sorted(list(filtered_items), key=lambda x: len(x),
											reverse=not bool(reverse))[start_index:end_index]
			if sort == "like-amount":
				conversations_page = sorted(list(filtered_items), key=lambda x: x[0]["likeCount"],
											reverse=not bool(reverse))[start_index:end_index]
			if sort == "random":
				conversations_page = list(filtered_items)
				shuffle(conversations_page)
				conversations_page = conversations_page[start_index:end_index]
		return Template(filename=(path.dirname(path.abspath(__file__)) + "/template.mako")).render(name="combined",
																								   conversations=conversations_page,
																								   pagination=pagination,
																								   combined=True,
																								   combined_names=names)

	# noinspection PyUnresolvedReferences
	@route("/accounts/<name>/<filepath:re:.*\.json>")
	def server_static(name, filepath):
		return static_file(names[name][0] + filepath, root="/")

	# noinspection PyUnresolvedReferences
	@route('/accounts/<name>/photos/<filepath:path>')
	@route('/accounts/<name>/<page:int>/photos/<filepath:path>')
	def server_static(name, filepath):
		return static_file(names[name][0] + "photos/" + filepath, root="/")

	@route('/accounts/<name>')
	def index(name):
		if not args.pagination:
			return modified_html_files[name]
		else:
			redirect("/accounts/" + name + "/1")

	if args.pagination:
		# noinspection PyUnresolvedReferences
		@route('/accounts/<name>/<page:int>')
		def index(name, page):
			sort = request.query["sort"] if "sort" in request.query else "date"
			reverse = int(request.query["reverse"]) if "reverse" in request.query else 0
			all_replies = int(request.query["all-replies"]) if "all-replies" in request.query else 1
			initiating_replies = int(request.query["initiating-replies"]) if "initiating-replies" in request.query else 1
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
					if initiating_replies and len(conversation[0]["renderedContent"]) >= 1 and conversation[0]["renderedContent"][0] == '@':
						continue
					filtered_conversation = []
					if all_replies:
						for reply in conversation:
							if len(reply["renderedContent"]) >= 1 and reply["renderedContent"][0] == '@':
								continue
							else:
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
				if sort == "like-amount":
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
update_parser.set_defaults(return_conversations=False)
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
server_parser.add_argument('--cache', dest='cache', action='store_true')
server_parser.add_argument('--headers-file', default=None, type=str)
server_parser.set_defaults(cache=False)
server_parser.set_defaults(func=server)

args = parser.parse_args()
args.func(args)
