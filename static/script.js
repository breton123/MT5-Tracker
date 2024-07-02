// script.js

document.addEventListener("DOMContentLoaded", function () {
	var tableBody = document.querySelector("#data-table tbody");

	// Iterate over each object in the data array
	setsData.forEach(function (object) {
		// Create a new row for each object
		var row = document.createElement("tr");

		var stats = object.stats;
		Object.keys(stats).forEach(function (key, index) {
			var cell = document.createElement("td");
			if (index == 0) cell.textContent = stats["setName"];
			if (index == 1) cell.textContent = stats["strategy"];
			if (index == 2) cell.textContent = stats["magic"];
			if (index == 3) cell.textContent = stats["profit"];
			if (index == 4) cell.textContent = stats["trades"];
			if (index == 5) cell.textContent = stats["maxDrawdown"];
			if (index == 6) cell.textContent = stats["profitFactor"];
			if (index == 7) cell.textContent = stats["returnOnDrawdown"];
			if (index == 8) cell.textContent = stats["daysLive"];
			row.appendChild(cell);
		});

		// Append the row to the table body
		tableBody.appendChild(row);
	});
});

var drawdownLayout = {
	title: "Drawdown",
	plot_bgcolor: "#222", // Background color
	paper_bgcolor: "#222", // Plot area background color
	width: 1400,
	height: 800,
	font: {
		color: "#fff", // Font color
	},
	xaxis: {
		title: "Time",
		color: "#fff", // Axis label color
		gridcolor: "#444", // Grid line color
	},
	yaxis: {
		title: "Drawdown",
		color: "#fff", // Axis label color
		gridcolor: "#444", // Grid line color
	},
};

var equityLayout = {
	title: "Equity",
	plot_bgcolor: "#222", // Background color
	paper_bgcolor: "#222", // Plot area background color
	width: 1400,
	height: 800,
	font: {
		color: "#fff", // Font color
	},
	xaxis: {
		title: "Time",
		color: "#fff", // Axis label color
		gridcolor: "#444", // Grid line color
	},
	yaxis: {
		title: "Equity",
		color: "#fff", // Axis label color
		gridcolor: "#444", // Grid line color
	},
};

Plotly.newPlot("drawdownGraph", graphData, drawdownLayout);
Plotly.newPlot("equityGraph", equityData, equityLayout);
