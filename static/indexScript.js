// script.js

document.addEventListener("DOMContentLoaded", function () {
	var tableBody = document.querySelector("#data-table tbody");

	// Iterate over each object in the data array
	accounts.forEach(function (object) {
		// Create a new row for each object
		var row = document.createElement("tr");

		var cell = document.createElement("td");
		cell.textContent = object;
		row.appendChild(cell);

		var buttonCell = document.createElement("td");
		var button = document.createElement("button");
		button.textContent = "View";
		button.id = "add-chart-btn";
		button.addEventListener("click", function () {
			window.location.href = "/" + object; // Redirect to /object
		});
		buttonCell.appendChild(button);
		row.appendChild(buttonCell);
		// Append the row to the table body
		tableBody.appendChild(row);
	});
});
