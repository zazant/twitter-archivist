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

## guide

1. archive user "pontifex" as "pope"<kbd><img src="https://user-images.githubusercontent.com/14267785/131233036-bb242866-6478-41cf-ad19-e6b72bd2137f.png"></kbd>
2. start server with "pope" and "dalai_lama" folders (this step is optional, you could view un-paginated chronological results through the html file)<br><kbd><img src="https://user-images.githubusercontent.com/14267785/131233037-7115f174-8f5a-4c86-9656-da244687e5d0.png"></kbd>
3. view archive<br><kbd><img width="640" src="https://user-images.githubusercontent.com/14267785/131233038-2c4a6657-fc7a-45d2-b77b-1092f12066be.png"></kbd>

---

## single twitter user

<kbd>
<img width="1425" alt="Screen Shot 2021-08-28 at 7 02 05 PM" src="https://user-images.githubusercontent.com/14267785/131233018-89a46b9a-6c5d-42b0-ac4a-208af193906f.png">
</kbd>

---

## combined view

<kbd>
<img width="647" alt="Screen Shot 2021-08-28 at 6 56 55 PM" src="https://user-images.githubusercontent.com/14267785/131233039-b77e9a95-6569-4bc2-a1c1-d644ef113372.png">
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





