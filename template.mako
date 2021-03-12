<!DOCTYPE HTML>
<html>
<head>
	<title>${name}</title>
	<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
</head>
<style>
.container {
    white-space: nowrap;
    width: 100%;
	padding-top: 8px;
    overflow: scroll
}
.media {
    max-height: 351px;
    width: auto;
    height: auto;
    border: 1px solid lightgrey;
}
.container>.media {
    height: 351px;
}
.container>.media:nth-child(1) {
    border-radius: 7px 0 0 7px;
}
.container>.media:nth-last-child(1) {
    border-radius: 0 7px 7px 0;
}
.container>.media:only-child {
    height: auto !important;
    border-radius: 7px !important;
    max-width: 99%;
}
a {
	text-decoration: none;
	//color: black;
}
* {
	font-family: -apple-system, system-ui, "Segoe UI", Roboto, Helvetica, A;
}
body {
	max-width: 624px;
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
	margin: 0.5em 20px 0;
	## padding: 0.5em;
    padding: 10px;
    border-top: 1px dashed grey;
	border-bottom: 1px dashed grey;
    overflow: scroll
}
.conversation {
    padding: 10px;
    margin: 5px;
    border-radius: 5px;
    box-shadow: 0px 0.7px 1px 0.8px lightgray;
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
	<hr style="margin-top: 0">
	<div id="input-container">
		<div>
			<input type="checkbox" id="checkbox1" class="checkbox" checked>hide initiating replies
			<input type="checkbox" id="checkbox2" class="checkbox" checked>hide all replies
		</div>
		<div>
			<input type="checkbox" id="checkbox3" class="checkbox-other">reverse
			<select name="sort" id="sort" onchange="refresh_sort()">
				<option value="date">date</option>
				<option value="thread_size">thread size</option>
				<option value="like_amount">like amount</option>
				<option value="random">random</option>
			</select>
		</div>
	</div>
	<hr style="margin-bottom: 6px">
	<div id="loading">
		loading...
	</div>
	<main style="display: none">
	%for value in conversations:
	<div class="conversation">
	%for d in value:
		<div title="${d["date"]} likes:${d["likeCount"]}" date="${d["date"]}" like-count="${d["likeCount"]}" class="tweet">
			<div class="separator">· · ·</div>
			<div class="tweet-text">${d["renderedContent"]}</div>
			%if not d["media"] is None:
            <div class="container">
                %for i in d["media"]:
                %if i["type"] == "photo":
                <img src="${i["fullUrl"]}" class="media">
                %endif
                %if i["type"] == "video":
                <video controls class="media">
                    <source src="${i["variants"][0]["url"]}">
                </video>
                %endif
                %if i["type"] == "gif":
                <video loop autoplay class="media">
                    <source src="${i["variants"][0]["url"]}">
                </video>
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
                    <img src="${i["fullUrl"]}" class="media">
					%endif
					%if i["type"] == "video":
                    <video controls class="media">
                        <source src="${i["variants"][0]["url"]}">
                    </video>
					%endif
					%if i["type"] == "gif":
                    <video loop autoplay class="media">
                        <source src="${i["variants"][0]["url"]}">
                    </video>
					%endif
					%endfor
				</div>
				%endif
			</div>
			%endif
		</div>
	%endfor
## 	<hr>
	</div>
	%endfor
	</main>
    %if pagination:
        <hr>
        <div style="display: flex; justify-content: space-between">
        %if pagination['page'] - 1 > 0:
                <a href="/accounts/${name}/${max(pagination['page'] - 1, 1)}/${pagination['sort']}/${pagination['reverse']}">previous</a>
        %else:
            <div style="color: grey">previous</div>
        %endif
        %if pagination['page'] + 1 <= pagination['pages']:
            <a href="/accounts/${name}/${min(pagination['page'] + 1, pagination['pages'])}/${pagination['sort']}/${pagination['reverse']}">next</a>
        %else:
            <div style="color: grey">next</div>
        %endif
        </div>
        <hr style="border: 1px dashed grey; border-bottom: none">
        <div style="margin-bottom: 8px; text-align: center">
        %for i in range(1, pagination["page"]):
            %if i != 1:
                ·
            %endif
            <a href="/accounts/${name}/${i}/${pagination['sort']}/${pagination['reverse']}">${i}</a>
        %endfor
        %if pagination["page"] != 1:
             ·
        %endif
        ${pagination["page"]}
        %for i in range(pagination["page"] + 1, pagination["pages"] + 1):
             · <a href="/accounts/${name}/${i}/${pagination['sort']}/${pagination['reverse']}">${i}</a>
        %endfor
        </div>
    %endif
</body>
<script>
%if not pagination:
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

	document.querySelector("#checkbox3").addEventListener('click', event => {
		document.querySelector("main").style.flexDirection = document.querySelector("#checkbox3").checked ? "column-reverse" : "column"
	})

	refresh();
	document.querySelector("#title-container-links").innerHTML =
        "<span>" + document.querySelectorAll(".tweet").length + " tweets</span> · " + document.querySelector("#title-container-links").innerHTML;

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
%else:
    document.querySelectorAll(".conversation").forEach(conversation => {
        conversation.querySelector(".separator").style.display = "none";
    })
    function refresh_sort() {
        reverse = document.querySelector("#checkbox3").checked ? 1 : 0
        if (document.querySelector("#sort").value == "date") {
            window.location.href = "/accounts/${name}/${pagination['page']}/date/" + reverse
        } else if (document.querySelector("#sort").value == "thread_size") {
            window.location.href = "/accounts/${name}/${pagination['page']}/thread-size/" + reverse
        } else if (document.querySelector("#sort").value == "like_amount") {
            window.location.href = "/accounts/${name}/${pagination['page']}/likes/" + reverse
        } else {
            window.location.href = "/accounts/${name}/${pagination['page']}/random/" + reverse
        }
    }

    document.querySelectorAll("[type=checkbox]").forEach(checkbox => {
        checkbox.addEventListener('click', event => {
            let checked1 = document.getElementById('checkbox1').checked;
            let checked2 = document.getElementById('checkbox2').checked;
            let checked3 = document.getElementById('checkbox3').checked;
            if (checked2) {
                document.getElementById('checkbox1').checked = true;
                document.getElementById('checkbox1').disabled = true;
                checked1 = true
            } else {
                document.getElementById('checkbox1').disabled = false;
            }
            window.location.href = "/accounts/${name}/${pagination['page']}/${pagination['sort']}/" + (checked3 ? 1 : 0) + "/" + (checked2 ? 1 : 0) + "/" + (checked1 ? 1 : 0)
        })
    })

    document.querySelector("#checkbox1").checked = ${pagination["initiating-replies"]};
    document.querySelector("#checkbox2").checked = ${pagination["all-replies"]};
    document.querySelector("#checkbox3").checked = ${pagination["reverse"]};
    if (document.querySelector("#checkbox2").checked) {
        document.getElementById('checkbox1').checked = true;
        document.getElementById('checkbox1').disabled = true;
    } else {
        document.getElementById('checkbox1').disabled = false;
    }
    if ("${pagination["sort"]}" === "date") {
        document.querySelector("#sort").value = "date";
    } else if ("${pagination["sort"]}" === "thread-size") {
        document.querySelector("#sort").value = "thread_size";
    } else if ("${pagination["sort"]}" === "likes") {
        document.querySelector("#sort").value = "like_amount";
    } else {
        document.querySelector("#sort").value = "random";
    }
    document.querySelector("#title-container-links").innerHTML = "<a href='/'>home</a> · " + document.querySelector("#title-container-links").innerHTML
%endif
document.querySelectorAll(".tweet-text").forEach(div => {
    if (div.innerText === "") {
        if (div.parentElement.querySelector(".container")) {
            div.parentElement.querySelector(".container").style.paddingTop = "0";
        }
    }
})

Array.from(document.querySelectorAll(".container"))
        .filter(container => container.children.length === 1)
        .forEach(container => {
            //container.children[0].style.maxHeight = "100%";
            //container.children[0].style.maxWidth = "100%";
            //container.children[0].style.height = "auto";
            //container.children[0].style.width = "auto";
        })

document.querySelector("#loading").style.display = "none";
document.querySelector("main").style.display = "flex";
</script>
</html>
