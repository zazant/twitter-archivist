# twitter-archive

makes a nice looking html webpage from a twitter user with sorting options. saves images, videos, threads, and qts, too

uses snscrape, so it will break if twitter changes something and messes with that...

now includes a bottle based html server with pagination for viewing large twitter accounts

also -- the version of snscrape used here is modified by me to work with private twitter accounts. either paste a headers object when prompted or provide a json file from a request sent to the twitter api from your browser request logger

requirements: `mako, tqdm, requests, bs4, bottle, python >= 3.8`

	usage: twitter-archive.py [-h] {archive,update,compile,server} ...

	--------

	archive: twitter-archive.py archive [-h] name username
	
	makes a folder called "name" and scrapes the twitter user with the handle "username" into it. "name" is also used
    in the title of the html page.

	---
	
	update: twitter-archive.py update [-h] folder_name [folder_name ...]
	
	updates existing archive folder with new tweets.
	
	--- 

	compile: twitter-archive.py compile [-h] folder_name [folder_name ...]

	compiles changes to html template into folder name.

	--- 

    server: twitter-archive.py server [-h] [--pagination PAGINATION] --port PORT [--recache] folder_name [folder_name ...]

    runs server with folder names of twitter accounts. pagination is the amount of tweets to show on one page if that
    is something you want. port is defaulted to 8000

---

![1](../extra/screenshots/1.png)

---

![2](../extra/screenshots/2.png)

---

![3](../extra/screenshots/3.png)

---

![4](../extra/screenshots/4.png)
