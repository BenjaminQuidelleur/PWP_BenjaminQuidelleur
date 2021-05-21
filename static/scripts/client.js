function GetArtists() {
	var row = "";
	$.get("http://127.0.0.1:5000/api/artists/", function(data, status) {
		var artists = data["items"]; //information from response body
		for (var i in artists) {
			//loop through artists and format them to table rows.
			row =
				row +
				"<tr id=" +
				i.unique_name +
				"><td id=" +
				i.unique_name +
				"A>" +
				artists[i].unique_name +
				"</td><td id=" +
				i["name"] +
				"A>" +
				artists[i].name
				"</td>"
				;
		}
		//Get questions table by id and set the content to include all question rows.
		document.getElementById("artists").innerHTML = '<table id="qlist" border=1  width="440">' + row + "</table>";
		row = ""; //Clean row variable after table content is set.
	});
}

function GetChoreography() {
	var row = "";
	$.get("http://127.0.0.1:5000/api/choreographies/", function(data, status) {
		var choreographies = data["items"]; //information from response body
		for (var i in choreographies) {
			//loop through artists and format them to table rows.
			row =
				row +
				"<tr id=" +
				i.name +
				"><td id=" +
				i.name +
				"A>" +
				choreographies[i].name +
				"</td><td id=" +
				i["description"] +
				"A>" +
				choreographies[i].description
				"</td>"
				;
		}
		//Get questions table by id and set the content to include all question rows.
		document.getElementById("choreographies").innerHTML = '<table id="qlist" border=1  width="440">' + row + "</table>";
		row = ""; //Clean row variable after table content is set.
	});
}

function addAlbum() {
	//input fields from which the author and question are taken.
	var name = document.getElementById("chore_name").value;
	var description = document.getElementById("chore_description").value;


	$.ajax({
		//ajax for POST
		url: "http://127.0.0.1:5000/api/questions/",
		contentType: "application/json",
		type: "POST",
		data: '{ "question":"' + question + '", "author":"' + author + '" }', //body
		success: function() {
			GetQuestions(); //again update the table with new question.
			document.getElementById("error").innerHTML = "";
		},
		error: function(jqxhr) {
			var error = JSON.parse(jqxhr.responseText);
			document.getElementById("error").innerHTML = error.message;
		}
	});
}

function EditArtist() {
	//Author and answer are on input fields for editing. Get values from them
	var chore_n = document.getElementById("artist_name_old").value;
	var name = document.getElementById("artist_name").value;
	var unique_name = document.getElementById("artist_unique").value;

	$.ajax({
		//Lets use ajax for PUT method
		url: "http://127.0.0.1:5000/api/artists/" + chore_n +"/" ,
		contentType: "application/json",
		type: "PUT",
		data: '{ "name":"' + name + '", "unique_name":"' + unique_name + '" }', //body
		success: function(data) {
			//when PUT is successfull, do this
			console.log("Updated!");
			location.reload();
			return false;
		},
		error: function(jqxhr) {
			var error = JSON.parse(jqxhr.responseText);
			document.getElementById("error").innerHTML = error.message;
		}
	});
}

function DeleteChoreography() {
	var chore_n = document.getElementById("chore_name_old").value;
	

	$.ajax({
		//ajax  for DELETE
		url: "http://127.0.0.1:5000/api/choreographies/" + chore_n +"/",
		type: "DELETE",
		success: function() {
			console.log("Deleted!");
			location.reload();
			return false;
		}
	});
}