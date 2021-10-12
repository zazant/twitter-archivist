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
    overflow: auto
}
.media {
    border: 1px solid rgb(225, 225, 225);
    border-radius: 7px;
}
.container>a>.media, .container>.media {
    max-height: 200px;
}
.container>a:only-child>.media, .container>.media:only-child {
    max-height: 250px;
    border-radius: 7px;
    max-width: 99%;
}
a {
	text-decoration: none;
	//color: black;
}
/*
{
	font-family: -apple-system, system-ui, "Segoe UI", Roboto, Helvetica, A;
}
*/
body {
	max-width: 624px;
	margin: 0 auto;
	font-family: -apple-system, system-ui, "Segoe UI", Roboto, Helvetica, A;
}
h1 {
	margin: 8px 0;
}
hr {
    border-style: double;
    border-bottom: none;
    border-color: rgb(200, 200, 200)
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
    overflow: auto
}
.conversation {
    padding: 10px;
    margin: 5px;
    border-radius: 5px;
    box-shadow: 0px 0.7px 1px 0.8px lightgray;
}

.outer-heading {
    width: 100%;
    text-align: center;
    border-bottom: 1px dashed #000;
    line-height: 0.1em;
    margin: 15px 0;
}

.inner-heading {
    background: white;
    padding: 0 10px
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
img:hover {
    cursor: zoom-in
}
</style>
<body>
	<div id="title-container">
		<h1>${name}</h1>
        <div>
        
		<div id="title-container-links">
            %if not combined:
            <a href="${name}_data.json">json</a>
            %endif
            ·
            <a style="cursor: pointer" id="theme-button" onclick="changeTheme()">default</a>
        </div>
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
    <%
        import datetime
        today_shown = False
        yesterday_shown = False
        other_shown = False
    %>
	%for value in conversations:
    %if combined:
        <%
        calculated_name = next((combined_name[1] for combined_name in combined_names.values() if "user" in value[0] and combined_name[2] == value[0]["user"]["username"]), "none")

        updated_date = datetime.datetime.strptime(value[0]["date"], "%Y-%m-%dT%H:%M:%S+00:00")\
            .replace(tzinfo=datetime.timezone.utc).astimezone(tz=None).strftime("%A %m/%d/%Y at %-I:%M %p")
        updated_date = updated_date.replace(datetime.datetime.now().strftime("%A %m/%d/%Y"), "Today")\
            .replace((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%A %m/%d/%Y"), "Yesterday").lower()

        %>
    %if pagination["sort"] == "date" and not pagination["reverse"] and not today_shown and "today" in updated_date:
    <div class="outer-heading">
        <span class="inner-heading">today</span>
    </div>
    <% today_shown = True %>
    %endif
    %if pagination["sort"] == "date" and not pagination["reverse"] and not yesterday_shown and "yesterday" in updated_date:
    <div class="outer-heading">
        <span class="inner-heading">yesterday</span>
    </div>
    <% yesterday_shown = True %>
    %endif
    %if pagination["sort"] == "date" and not pagination["reverse"] and not other_shown and "today" not in updated_date and "yesterday" not in updated_date:
    <div class="outer-heading">
        <span class="inner-heading">other dates</span>
    </div>
    <% other_shown = True %>
    %endif
            <div style="display: flex; justify-content: space-between; color: lightgrey; padding: 4px 8px 2px; margin: 0 5px 2px; border-bottom: 1px dashed lightgrey">
                <div>${calculated_name}</div>
                <i>${updated_date.replace("today at", "").replace("yesterday at", "")}</i>
            </div>
    %endif
    <div class="conversation">
        %if combined:
        %endif
        <%
        def fixed_tag(tag):
            if combined:
                return "/accounts/" + calculated_name + "/" + tag
            else:
                return tag
    %>
    %for d in value:
		<div title="${datetime.datetime.strptime(d["date"], "%Y-%m-%dT%H:%M:%S+00:00").replace(tzinfo=datetime.timezone.utc).astimezone(tz=None).strftime("%A %m/%d/%Y at %-I:%M %p")} likes:${d["likeCount"]}" date="${d["date"]}" like-count="${d["likeCount"]}" class="tweet">
			<div class="separator">· · ·</div>
			<div class="tweet-text">${d["renderedContent"]}</div>
			%if not d["media"] is None:
            <div class="container">
                %for i in d["media"]:
                %if i["type"] == "photo":
                <a target="_blank" href="${fixed_tag(i['fullUrl'])}"><img src="${fixed_tag(i['fullUrl'])}" class="media"></a>
                %endif
                %if i["type"] == "video":
                <video controls class="media">
                    <source src="${fixed_tag(i["variants"][0]["url"])}">
                </video>
                %endif
                %if i["type"] == "gif":
                <video loop autoplay class="media">
                    <source src="${fixed_tag(i["variants"][0]["url"])}">
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
                    <a target="_blank" href="${fixed_tag(i['fullUrl'])}"><img src="${fixed_tag(i["fullUrl"])}" class="media"></a>
					%endif
					%if i["type"] == "video":
                    <video controls class="media">
                        <source src="${fixed_tag(i["variants"][0]["url"])}">
                    </video>
					%endif
					%if i["type"] == "gif":
                    <video loop autoplay class="media">
                        <source src="${fixed_tag(i["variants"][0]["url"])}">
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
	<a href="javascript:void(0)" onclick="window.location='${"/accounts/" if not combined else "/"}${name}/${max(pagination['page'] - 1, 1)}'+window.location.search;">previous</a>
        %else:
            <div style="color: grey">previous</div>
        %endif
        %if pagination['page'] + 1 <= pagination['pages']:
	<a href="javascript:void(0)" onclick="window.location='${"/accounts/" if not combined else "/"}${name}/${min(pagination['page'] + 1, pagination['pages'])}'+window.location.search;">next</a>
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
	    <a href="javascript:void(0)" onclick="window.location='${"/accounts/" if not combined else "/"}${name}/${i}'+window.location.search;">${i}</a>
        %endfor
        %if pagination["page"] != 1:
             ·
        %endif
        ${pagination["page"]}
        %for i in range(pagination["page"] + 1, pagination["pages"] + 1):
	· <a href="javascript:void(0)" onclick="window.location='${"/accounts/" if not combined else "/"}${name}/${i}'+window.location.search;">${i}</a>
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
        let reverse = document.querySelector("#checkbox3").checked ? 1 : 0
        let url = new URL(window.location.origin + "/" + "${("" if combined else "accounts/")}" + "${name}" + "/1")
        url.search = (new URL(window.location)).searchParams
        url.searchParams.set("reverse", reverse)
        if (document.querySelector("#sort").value == "date") {
            url.searchParams.set("sort", "date")
            window.location.href = url
        } else if (document.querySelector("#sort").value == "thread_size") {
            url.searchParams.set("sort", "thread-size")
            window.location.href = url
        } else if (document.querySelector("#sort").value == "like_amount") {
            url.searchParams.set("sort", "like-amount")
            window.location.href = url
        } else {
            url.searchParams.set("sort", "random")
            window.location.href = url
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
            let url = new URL(window.location.origin + "/" + "${("" if combined else "accounts/")}" + "${name}" + "/1")
            url.search = (new URL(window.location)).searchParams
            if (checked3 || url.searchParams.has("reverse"))
                url.searchParams.set("reverse", checked3 ? 1 : 0)
            if (!checked2 || url.searchParams.has("all-replies"))
                url.searchParams.set("all-replies", checked2 ? 1 : 0)
            if (!checked1 || url.searchParams.has("initiating-replies"))
                url.searchParams.set("initiating-replies", checked1 ? 1 : 0)
            window.location.href = url
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
    } else if ("${pagination["sort"]}" === "like-amount") {
        document.querySelector("#sort").value = "like_amount";
    } else {
        document.querySelector("#sort").value = "random";
    }

    %if not combined:
    document.querySelector("#title-container-links").innerHTML = "<a href='/'>home</a> · " + document.querySelector("#title-container-links").innerHTML
    %else:
    document.querySelector("#title-container-links").innerHTML = "<a href='/'>home</a>" + document.querySelector("#title-container-links").innerHTML
    %endif
%endif
document.querySelectorAll(".tweet-text").forEach(div => {
    if (div.innerText.trim() === "") {
        if (div.parentElement.querySelector(".container")) {
            div.parentElement.querySelector(".container").style.paddingTop = "4.25px";
        }
    }
})

document.querySelector("#loading").style.display = "none";
document.querySelector("main").style.display = "flex";

themeValue = 0

function changeTheme() {
    themeValue ++;
    if (themeValue > 2) {
        themeValue = 0;
    }
    localStorage.setItem('themeValue', themeValue);
    if (themeValue == 0) {
        document.body.style.backgroundColor = "white";
        document.body.style.color = "black"
        document.body.style.fontFamily = "-apple-system, system-ui, \"Segoe UI\", Roboto, Helvetica, A";
        document.querySelector("#theme-button").text = "default"
        document.querySelectorAll(".conversation").forEach(c => {
            c.style.boxShadow = "0px 0.7px 1px 0.8px lightgray"
            c.style.borderRadius = "5px"
            c.style.border = "unset"
        });
        document.querySelectorAll(".media").forEach(c => {
            c.style.borderRadius = "7px"
            c.style.border = "1px solid rgb(225, 225, 225)"
        });
        document.querySelectorAll("hr").forEach(c => c.style.display = "block")
    } else if (themeValue == 1) {
        document.body.style.backgroundColor = "black";
        document.body.style.fontFamily = "Times New Roman";
        document.body.style.color = "white";
        document.querySelectorAll(".conversation").forEach(c => {
            c.style.boxShadow = "unset"
            c.style.borderRadius = 0
            c.style.border = "1px solid white"
        });
        document.querySelectorAll(".media").forEach(c => {
            c.style.borderRadius = 0
            c.style.border = "1px solid lime"
        });
        document.querySelector("#theme-button").text = "black"
    } else if (themeValue == 2) {
        document.body.style.backgroundColor = "white";
        document.body.style.color = "black";
        document.querySelectorAll(".conversation").forEach(c => {
            c.style.border = "1px solid lightgrey"
        });
        document.querySelector("#theme-button").text = "white"
        ## document.querySelectorAll("hr").forEach(c => c.style.display = "none")
        document.querySelectorAll(".media").forEach(c => {
            c.style.borderRadius = 0
            c.style.border = "1px solid lightgrey"
        });
    }
}

function loadTheme() {
    if (localStorage && localStorage.getItem('themeValue')) {
        var storedTheme = parseInt(localStorage.getItem('themeValue'));
        for (let i = 0; i < storedTheme; i++) {
            changeTheme()
        }
    }
}

loadTheme()

## var imgHeight;
## var imgWidth;

## function findHHandWW() {
##     imgHeight = this.height;
##     imgWidth = this.width;
##     return true;
## }

## function showImage(imgPath) {
##     var myImage = new Image();
##     myImage.name = imgPath;
##     myImage.onload = findHHandWW;
##     myImage.src = imgPath;
## }

## document.querySelectorAll(".container").forEach(c => {
##     if (!c.querySelector("video")) {
##         let maxHeight = 50
##         console.log(maxHeight)
##         c.querySelectorAll("img").forEach(d => {
##             imgHeight = d.naturalHeight
##             if (imgHeight > maxHeight)
##                 maxHeight = imgHeight
##         })
##         if (maxHeight > 351) {
##             maxHeight = 351
##         }
##         c.querySelectorAll("img").forEach(d => {
##             d.style.height = maxHeight.toString() + "px"
##         })
##     }
## })
</script>
</html>
