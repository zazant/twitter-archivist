#!python3
import subprocess
import argparse
import sys
from pathlib import Path
from shutil import rmtree
from compile import compile
import os
import json

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
	class Namespace:
		def __init__(self, **kwargs):
			self.__dict__.update(kwargs)
	compile(Namespace(folder_name=[args.name]))

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
		class Namespace:
			def __init__(self, **kwargs):
				self.__dict__.update(kwargs)
		compile(Namespace(folder_name=[name]))

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
compile_parser.set_defaults(func=compile)

args = parser.parse_args()
args.func(args)
