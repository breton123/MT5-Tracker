document.addEventListener("DOMContentLoaded", function () {
	var profileInput = document.getElementById("profileSelect");
	var accountInput = document.getElementById("accountSelect");
	var profileNameInput = document.getElementById("profileNameInput");

	updateProfiles();
	updateProfileName();

	document
		.getElementById("accountSelect")
		.addEventListener("change", updateProfiles);

	document.getElementById("profileSelect").addEventListener("change", getSets);
	document
		.getElementById("profileNameInput")
		.addEventListener("change", updateProfileName);
	document
		.getElementById("profileSelect")
		.addEventListener("change", updateProfileName);

	function updateProfileName() {
		var profileNameInput = document.getElementById("profileNameInput");
		var profileNameInputlabel = document.getElementById(
			"profileNameInputLabel"
		);
		var profileName = document.getElementById("profileName").value;
		var profileInputValue = document.getElementById("profileSelect").value;
		if (profileInputValue == "New Profile") {
			profileNameInput.style.display = "";
			profileNameInputlabel.style.display = "";
		} else {
			profileNameInput.style.display = "none";
			profileNameInputlabel.style.display = "none";
		}
	}

	function updateProfiles() {
		var accountInputValue = parseInt(
			document.getElementById("accountSelect").value
		);
		profiles[accountInputValue].forEach(function (profile) {
			var newOption = document.createElement("option");
			newOption.value = profile;
			newOption.textContent = profile;
			profileInput.appendChild(newOption);
		});
	}

	function getSets() {
		var accountInputValue = parseInt(
			document.getElementById("accountSelect").value
		);
		var profileInputValue = document.getElementById("profileSelect").value;
		fetch(
			`http://127.0.0.1:5000/api/getProfileSets/${accountInputValue}/${profileInputValue}`
		)
			.then((response) => response.json())
			.then((data) => {
				console.log(data);
				updateSets(data);
			})
			.catch((error) => console.error("Error:", error));
	}

	function updateSets(sets) {
		table = document.getElementById("setsTableBody");
		table.innerHTML = "";
		sets.forEach(function (set) {
			var row = document.createElement("tr");
			var cell = document.createElement("td");
			cell.textContent = set.setName;
			row.appendChild(cell);
			var cell = document.createElement("td");
			cell.textContent = set.symbol;
			row.appendChild(cell);
			var cell = document.createElement("td");
			cell.textContent = set.magic;
			row.appendChild(cell);
			table.appendChild(row);
		});
	}
});
