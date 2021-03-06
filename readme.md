# twitter-archive

makes a nice looking html webpage from a twitter user with sorting options. saves images, videos, threads, and qts, too

uses snscrape, so it will break if twitter changes something and messes with that...

requirements: `mako, tqdm, python 3 (python 3.9 used), snscrape (must be installed and executable through your shell)`

	usage: twitter-archive.py [-h] {archive,update,compile} ...

	--------

	archive: twitter-archive.py archive [-h] name username
	
	makes a folder called "name" and scrapes the twitter user with the handle "username" into it.
	"name" is also used in the title of the html page.

	---
	
	update: twitter-archive.py update [-h] folder_name [folder_name ...]
	
	updates existing archive folder with new tweets.
	
	--- 

	compile: twitter-archive.py compile [-h] folder_name [folder_name ...]

	compiles changes to html template into folder name.

---

![1](../extra/screenshots/1.png)

---

![2](../extra/screenshots/2.png)

---

![3](../extra/screenshots/3.png)

---

![4](../extra/screenshots/4.png)
