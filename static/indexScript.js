// script.js

document.addEventListener("DOMContentLoaded", function () {
	var tableBody = document.querySelector("#data-table tbody");

	// Iterate over each object in the data array
	accounts.forEach(function (object) {
		// Create a new row for each object
		var row = document.createElement("tr");

		var cell = document.createElement("td");
		cell.textContent = object.login;
		row.appendChild(cell);

		var cell = document.createElement("td");
		cell.textContent = object.type;
		row.appendChild(cell);

		var cell = document.createElement("td");
		cell.textContent = object.status;
		row.appendChild(cell);

		var buttonCell = document.createElement("td");
		var button = document.createElement("button");
		button.textContent = "View";
		button.id = "add-chart-btn";
		if (object.status != "tracking") button.disabled = true;
		button.addEventListener("click", function () {
			window.location.href = "/" + object.login; // Redirect to /object
		});
		buttonCell.appendChild(button);
		row.appendChild(buttonCell);
		// Append the row to the table body
		tableBody.appendChild(row);
	});
});
