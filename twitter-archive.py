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

from mako.template import Template
from tqdm import tqdm

def archive(args):
	try:
		Path(args.name).mkdir(parents=True, exist_ok=False)
	except FileNotFoundError:
		sys.exit("error: parent directory not found")
	except FileExistsError:
		print("directory already exists, continuing")
	if Path(args.name + "/" + args.name + "_data.json").exists():
		sys.exit("error: " + args.name + "_data.json already exists")
	with open(args.name + "/" + args.name + "_data_raw", "w") as f:
		if (subprocess.call(["snscrape", "--jsonl", "--progress", "twitter-user", args.username], stdout=f) != 0):
			rmtree(args.name)
			sys.exit("error: scraping failed")
	raw_file_data = None
	file_data = []
	with open(args.name + "/" + args.name + "_data_raw", "r") as f:
		raw_file_data = f.readlines()
	for i, line in enumerate(raw_file_data):
		if (i == 0):
			line = "[" + line
		if (i != len(raw_file_data) - 1):
			line = line.rstrip("\n") + ",\n"
		if (i == len(raw_file_data) - 1):
			line = line.rstrip("\n") + "]"
		file_data.append(line)
	with open(args.name + "/" + args.name + "_data.json", "w") as f:
		f.writelines(file_data)
	Path.unlink(Path(args.name + "/" + args.name + "_data_raw"))
	Path(args.name + "/photos").mkdir(exist_ok=True)
	compile_html({"folder_name": [args.name]})

def update(args):
	for name in args.folder_name:
		print("----------------------")
		print(name)
		print("----------------------")
		failed = False
		a = {}
		with open(name + "/" + name + "_data.json", "r") as f:
			a = json.loads(f.read())
			with open(name + "/temp.json", "w") as temp:
				if not a or not a[0] or not "date" in a[0] or not "user" in a[0] or not "username" in a[0]["user"]:
					failed = True
				else:
					date = a[0]["date"].split("T")[0]
					username = a[0]["user"]["username"]
					print("date: " + date)
					try:
						print(" ".join(["snscrape", "--jsonl", "--progress", "--since", date, "twitter-user", username]))
						if (subprocess.call(["snscrape", "--jsonl", "--progress", "--since", date, "twitter-user", username], stdout=temp) != 0):
							failed = True
					except:
						failed = True
			if failed:
				Path(name + "/temp.json").unlink(missing_ok=True)
				print("scraping_failed")
				continue
			for line in reversed(open(name + "/temp.json", "r").readlines()):
				try:
					json_line = json.loads(line)
					if not any(json_line["url"] == x["url"] for x in a):
						a.insert(0, json_line)
						print("added " + json_line["url"])
					else:
						print("skipping " + json_line["url"])
				except:
					print("failed line: " + line)
		Path(name + "/temp.json").unlink(missing_ok=True)
		with open(name + "/" + name + "_data.json", "w") as f:
			json.dump(a, f)
		compile_html({"folder_name": [name]})

def compile_html(args):
	for name in args["folder_name"]:
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
