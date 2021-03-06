<!DOCTYPE HTML>
<html>
<head>
	<title>${name}</title>
	<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
</head>
<style>
.container {
	display: flex;
	max-height: 500px;
	padding-top: 8px;
}
img {
	max-width: 100%;
	max-height: 300px;
}
video {
	max-width: 100%;
	max-height: 300px;
	padding: 0;
}
.media {
	max-width: 100%;
	max-height: 100%;
	max-height: 300px;
}
a {
	text-decoration: none;
	//color: black;
}
* {
	font-family: -apple-system, system-ui, "Segoe UI", Roboto, Helvetica, A;
}
body {
	max-width: 750px;
	margin: 0 auto;
}
h1 {
	margin: 8px 0;
}
.quote {
	border-top: 1px dashed grey;
	border-bottom: 1px dashed grey
}
#title-container {
	display: flex;
	justify-content: space-between;
	align-items: center
}
.tweet-text {
	word-wrap: break-word;
}
#title-container-links > * {
  color: grey
}
.quoted-tweet {
	margin: 0.5em 20px;
	padding: 0.5em;
	border-top: 1px dashed grey;
	border-bottom: 1px dashed grey;
}
.conversation {
	
}
/*.tweet {
	margin: 0.5em 0;
}*/
.separator {
	text-align: center;
	color: grey;
	height: 22px;
	line-height: 22px;
}
main {
	display: flex;
	flex-direction: column
}
#input-container {
	display: flex;
	justify-content: space-between
}
</style>
<body>
	<div id="title-container">
		<h1>${name}</h1>
		<div id="title-container-links">
			<a href="${name}_data.json">json</a>
		</div>
	</div>
	<hr>
	<div id="input-container">
		<div>
			<input type="checkbox" id="checkbox1" class="checkbox" checked>hide initiating replies</input>
			<input type="checkbox" id="checkbox2" class="checkbox" checked>hide all replies</input>
		</div>
		<div>
			<input type="checkbox" id="checkbox3" class="checkbox-other">reverse</input>
			<select name="sort" id="sort" onchange="refresh_sort()">
				<option value="date">date</option>
				<option value="thread_size">thread size</option>
				<option value="like_amount">like amount</option>
				<option value="random">random</option>
			</select>
		</div>
	</div>
	<hr>
	<div id="loading">
		loading...
	</div>
	<main style="display: none">
	%for conversationId, value in conversations.items():
	<div class="conversation">
	%for d in value:
		<div title="${d["date"]} likes:${d["likeCount"]}" date="${d["date"]}" like-count="${d["likeCount"]}" class="tweet">
			<div class="separator">· · ·</div>
			<div class="tweet-text">${d["renderedContent"]}</div>
			%if not d["media"] is None:
			<div class="container">
				%for i in d["media"]:
				%if i["type"] == "photo":
				<div id="image">
					<img src="${i["fullUrl"]}">
				</div>
				%endif
				%if i["type"] == "video":
				<div class="media video">
					<video controls>
						<source src="${i["variants"][0]["url"]}">
					</video>
				</div>
				%endif
				%if i["type"] == "gif":
				<div class="media video">
					<video loop autoplay>
						<source src="${i["variants"][0]["url"]}">
					</video>
				</div>
				%endif
				%endfor
			</div>
			%endif
			%if not d["quotedTweet"] is None:
			<div class="quoted-tweet">
				<div class="tweet-text">${d["quotedTweet"]["renderedContent"]}</div>
				%if not d["quotedTweet"]["media"] is None:
				<div class="container">
					%for i in d["quotedTweet"]["media"]:
					%if i["type"] == "photo":
					<div class="media image">
						<img src="${i["fullUrl"]}">
					</div>
					%endif
					%if i["type"] == "video":
					<div class="media video">
						<video controls>
							<source src="${i["variants"][0]["url"]}">
						</video>
					</div>
					%endif
					%if i["type"] == "gif":
					<div class="media video">
						<video loop autoplay>
							<source src="${i["variants"][0]["url"]}">
						</video>
					</div>
					%endif
					%endfor
				</div>
				%endif
			</div>
			%endif
		</div>
	%endfor
	<hr>
	</div>
	%endfor
	</main>
</body>
<script>
	function refresh() {
		let checked1 = document.getElementById('checkbox1').checked;
		let checked2 = document.getElementById('checkbox2').checked;
		if (checked2) {
			document.getElementById('checkbox1').checked = true;
			document.getElementById('checkbox1').disabled = true;
			checked1 = true
		} else {
			document.getElementById('checkbox1').disabled = false;
		}
		document.querySelectorAll(".conversation").forEach(conversation => {
			conversation.querySelector(".separator").style.display = "none";
			divs = conversation.querySelectorAll(".tweet")
			if (checked1 && divs[0].querySelector(".tweet-text").innerText.includes("@"))
				conversation.style.display = "none"
			else if (divs[0].innerText.includes("@"))
				conversation.style.display = "initial"
				
			for (let i = 0; i < divs.length; i++) {
				if (divs[i].querySelector(".tweet-text").innerText.includes("@")) {
					if (checked2) {
						divs[i].style.display = "none"
					} else {
						divs[i].style.display = "block"
					}
				}
			}
		})
	}
	
	document.querySelectorAll(".tweet-text").forEach(div => {
		if (div.innerText === "") {
			if (div.parentElement.querySelector(".container")) {
				div.parentElement.querySelector(".container").style.paddingTop = "0";
			}
		}
	})
	document.querySelector("#checkbox3").addEventListener('click', event => {
		document.querySelector("main").style.flexDirection = document.querySelector("#checkbox3").checked ? "column-reverse" : "column"
	})
	
	refresh();
	document.querySelector("#loading").style.display = "none";
	document.querySelector("main").style.display = "flex";
	
	function shuffle(array) {
		var currentIndex = array.length, temporaryValue, randomIndex;
		// While there remain elements to shuffle...
		while (0 !== currentIndex) {
			// Pick a remaining element...
			randomIndex = Math.floor(Math.random() * currentIndex);
			currentIndex -= 1;
			// And swap it with the current element.
			temporaryValue = array[currentIndex];
			array[currentIndex] = array[randomIndex];
			array[randomIndex] = temporaryValue;
		}
		return array;
	}
	
	function refresh_sort() {
		var toSort = document.querySelector('main').children;
		toSort = Array.prototype.slice.call(toSort, 0);
		if (document.querySelector("#sort").value == "date") {
			toSort.sort(function(a, b) {
				var aord = new Date(a.querySelectorAll(".tweet")[0].getAttribute("date"));
				var bord = new Date(b.querySelectorAll(".tweet")[0].getAttribute("date"));
				return bord - aord;
			});
		} else if (document.querySelector("#sort").value == "thread_size")  {
			toSort.sort(function(a, b) {
				var aord = a.querySelectorAll(".tweet").length;
				var bord = b.querySelectorAll(".tweet").length;
				return bord - aord;
			});
		} else if (document.querySelector("#sort").value == "like_amount") {
			toSort.sort(function(a, b) {
				var aord = a.querySelectorAll(".tweet")[0].getAttribute("like-count");
				var bord = b.querySelectorAll(".tweet")[0].getAttribute("like-count");
				return bord - aord
			});
		} else {
			shuffle(toSort)
		}
		var parent = document.querySelector('main');
		parent.innerHTML = "";
		
		for(var i = 0, l = toSort.length; i < l; i++) {
			parent.appendChild(toSort[i]);
		}
	}
	document.querySelectorAll('.checkbox').forEach(checkbox => {
		checkbox.addEventListener('click', event => {
			refresh();
		})
	})
</script>
</html>
