# twitter-archivist

makes a nice looking html webpage from a twitter user with sorting options. saves images, videos, threads, and qts, too

uses snscrape, so it will break if twitter changes something and messes with that...

now includes a bottle based html server with pagination for viewing large twitter accounts

also -- the version of snscrape used here is modified by me to work with private twitter accounts. either paste a headers object when prompted or provide a json file from a request sent to the twitter api from your browser request logger

requirements: `mako, tqdm, requests, bs4, bottle, python >= 3.8`

	usage: twitter-archivist.py [-h] {archive,update,compile,server} ...

	--------

	archive: twitter-archivist.py archive [-h] [--since SINCE] [--private] [--headers-file HEADERS_FILE] name username
	
	makes a folder called "name" and scrapes the twitter user with the handle "username" into it. "name" is also used
    in the title of the html page.

	---
	
	update: twitter-archivist.py update [-h] [--reverse] [--headers-file HEADERS_FILE] folder_name [folder_name ...]
	
	updates existing archive folder with new tweets.
	
	--- 

	compile: twitter-archivist.py compile [-h] folder_name [folder_name ...]

	compiles changes to html template into folder name.

	--- 

    server: twitter-archivist.py server [-h] [--pagination PAGINATION] --port PORT [--cache] folder_name [folder_name ...]

    runs server with folder names of twitter accounts. pagination is the amount of tweets to show on one page if that
    is something you want. port is defaulted to 8000

---

## guide - archiving @pontifex and @dalailama

1. create new folder for users that you want to archive inside the twitter-archivist directory (or elsewhere)

	```c
	mkdir users
	cd users
	```

3. archive user @pontifex as "pope"

	```c
	python3 ../twitter-archivist.py archive pope pontifex
	```

3. archive user @dalailama as "dalai_lama"

	```c
	python3 ../twitter-archivist.py archive dalai_lama dalailama
	```

3. start server with "pope" and "dalai_lama" folders (this step is optional, you could view un-paginated chronological results through the html files)

	```c
	python3 ../twitter-archivist.py server *
	```

5. view archive at [localhost:8000](http://localhost:8000)

<kbd><img width="640" src="https://user-images.githubusercontent.com/14267785/131233038-2c4a6657-fc7a-45d2-b77b-1092f12066be.png"></kbd>

---

## single twitter user

<kbd>
<img width="1425" alt="Screen Shot 2021-08-28 at 7 02 05 PM" src="https://user-images.githubusercontent.com/14267785/131233018-89a46b9a-6c5d-42b0-ac4a-208af193906f.png">
</kbd>

---

## combined view

<kbd>
<img width="998" alt="Screen Shot 2021-09-05 at 12 48 20 PM" src="https://user-images.githubusercontent.com/14267785/132134788-f0a113a9-53e8-4a9b-99a1-a168ccff4e27.png">
</kbd>

---

## view & sort by likes

<kbd>
<img width="716" alt="Screen Shot 2021-08-28 at 6 57 13 PM" src="https://user-images.githubusercontent.com/14267785/131233027-fb221f5f-bbdf-445e-a51e-5fc0e1aa3395.png">
</kbd>
<kbd>
<img width="315" alt="Screen Shot 2021-08-28 at 6 58 03 PM" src="https://user-images.githubusercontent.com/14267785/131233029-74ae043c-726c-4af5-a313-d65f8302cc5f.png">
</kbd>

---

## view videos

<kbd>
<img width="671" alt="Screen Shot 2021-08-28 at 6 58 31 PM" src="https://user-images.githubusercontent.com/14267785/131233031-e28afe95-ef62-4aea-be05-3d80299b83d4.png">
</kbd>

---

## pagination

<kbd>
<img width="685" alt="Screen Shot 2021-08-28 at 6 58 52 PM" src="https://user-images.githubusercontent.com/14267785/131233033-5076fbbd-740b-461e-81d7-30d6febc9f31.png">
</kbd>





