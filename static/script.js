document.addEventListener("DOMContentLoaded", function () {
	var tableBody = document.querySelector("#data-table tbody");
	var accountSelect = document.getElementById("accountSelect");

	function setRangeValues() {
		document.getElementById("profitRange").min = filterData.minProfit;
		document.getElementById("profitRange").max = filterData.maxProfit;
		document.getElementById("profitRange").value = filterData.minProfit;
		document.getElementById("tradesRange").min = filterData.minTrades;
		document.getElementById("tradesRange").max = filterData.maxTrades;
		document.getElementById("tradesRange").value = filterData.minTrades;
		document.getElementById("maxDrawdownRange").min = filterData.minDrawdown;
		document.getElementById("maxDrawdownRange").max = filterData.maxDrawdown;
		document.getElementById("maxDrawdownRange").value = filterData.minDrawdown;
		document.getElementById("profitFactorRange").min =
			filterData.minProfitFactor;
		document.getElementById("profitFactorRange").max =
			filterData.maxProfitFactor;
		document.getElementById("profitFactorRange").value =
			filterData.minProfitFactor;
		document.getElementById("returnOnDrawdownRange").min =
			filterData.minReturnOnDrawdown;
		document.getElementById("returnOnDrawdownRange").max =
			filterData.maxReturnOnDrawdown;
		document.getElementById("returnOnDrawdownRange").value =
			filterData.minReturnOnDrawdown;
		document.getElementById("daysLiveRange").min = filterData.minDaysLive;
		document.getElementById("daysLiveRange").max = filterData.maxDaysLive;
		document.getElementById("daysLiveRange").value = filterData.minDaysLive;
	}

	setRangeValues();

	function createTableRow(stats) {
		var row = document.createElement("tr");
		row.classList.add("selectable-row");
		var checkboxCell = document.createElement("td");
		var checkbox = document.createElement("input");
		checkbox.type = "checkbox";
		checkbox.className = "row-select";
		checkbox.style.display = "none"; // Hide the checkbox
		checkboxCell.appendChild(checkbox);
		row.appendChild(checkbox);
		[
			"setName",
			"strategy",
			"magic",
			"profit",
			"trades",
			"maxDrawdown",
			"profitFactor",
			"returnOnDrawdown",
			"daysLive",
		].forEach(function (key) {
			var cell = document.createElement("td");
			cell.textContent = stats[key];
			row.appendChild(cell);
		});
		return row;
	}

	function populateTable(filteredData) {
		tableBody.innerHTML = ""; // Clear existing rows
		filteredData.forEach(function (object) {
			var row = createTableRow(object.stats);
			tableBody.appendChild(row);
		});
	}

	populateTable(setsData);

	function applyFilters() {
		var profitMin = parseInt(document.getElementById("profitRange").value);
		var profitMax = parseInt(document.getElementById("profitRange").max);
		var drawdownMin = parseInt(
			document.getElementById("maxDrawdownRange").value
		);
		var drawdownMax = parseInt(document.getElementById("maxDrawdownRange").max);
		var daysLiveMin = parseInt(document.getElementById("daysLiveRange").value);
		var daysLiveMax = parseInt(document.getElementById("daysLiveRange").max);

		function parseDrawdown(drawdown) {
			return drawdown === "-" ? 0 : parseInt(drawdown);
		}

		var filteredData = setsData.filter(function (object) {
			var stats = object.stats;
			var maxDrawdown = parseDrawdown(stats.maxDrawdown);
			return (
				stats.profit >= profitMin &&
				stats.profit <= profitMax &&
				maxDrawdown >= drawdownMin &&
				maxDrawdown <= drawdownMax &&
				stats.daysLive >= daysLiveMin &&
				stats.daysLive <= daysLiveMax
			);
		});

		console.log(filteredData);
		populateTable(filteredData);
		updateGraphs(filteredData, 3, 3);
	}

	function resetFilters() {
		populateTable(setsData);
		updateGraphs(graphData, 3, 3);
		setRangeValues();
	}

	document
		.getElementById("applyFilters")
		.addEventListener("click", applyFilters);

	function updateGraphs(filteredData, drawdownWindow, equityWindow) {
		var filteredGraphData = graphData.filter(function (trace) {
			return filteredData.some(function (set) {
				return set.stats.setName === trace.name;
			});
		});

		var filteredEquityData = equityData.filter(function (trace) {
			return filteredData.some(function (set) {
				return set.stats.setName === trace.name;
			});
		});

		var smoothedDrawdownTraces = filteredGraphData.map((trace) => {
			var smoothedYData = movingAverage(trace.y, drawdownWindow);
			var adjustedXData = trace.x.slice(drawdownWindow - 1);

			return {
				x: adjustedXData,
				y: smoothedYData,
				mode: "lines",
				name: trace.name + " (Smoothed)",
				line: { shape: "spline" }, // Spline interpolation
			};
		});

		var smoothedEquityTraces = filteredEquityData.map((trace) => {
			var smoothedYData = movingAverage(trace.y, equityWindow);
			var adjustedXData = trace.x.slice(equityWindow - 1);

			return {
				x: adjustedXData,
				y: smoothedYData,
				mode: "lines",
				name: trace.name + " (Smoothed)",
				line: { shape: "spline" }, // Spline interpolation
			};
		});

		var allDrawdownTraces = [...filteredGraphData, ...smoothedDrawdownTraces];
		var allEquityTraces = [...filteredEquityData, ...smoothedEquityTraces];

		Plotly.react("drawdownGraph", allDrawdownTraces, drawdownLayout);
		Plotly.react("equityGraph", allEquityTraces, equityLayout);
	}

	function movingAverage(data, windowSize) {
		let result = [];
		for (let i = 0; i < data.length - windowSize + 1; i++) {
			let sum = 0;
			for (let j = 0; j < windowSize; j++) {
				sum += data[i + j];
			}
			result.push(sum / windowSize);
		}
		return result;
	}

	var drawdownLayout = {
		title: "Drawdown",
		plot_bgcolor: "#222",
		paper_bgcolor: "#222",
		width: 1400,
		height: 800,
		font: {
			color: "#fff",
		},
		xaxis: {
			title: "Time",
			color: "#fff",
			gridcolor: "#444",
		},
		yaxis: {
			title: "Drawdown",
			color: "#fff",
			gridcolor: "#444",
		},
	};

	var equityLayout = {
		title: "Equity",
		plot_bgcolor: "#222",
		paper_bgcolor: "#222",
		width: 1400,
		height: 800,
		font: {
			color: "#fff",
		},
		xaxis: {
			title: "Time",
			color: "#fff",
			gridcolor: "#444",
		},
		yaxis: {
			title: "Equity",
			color: "#fff",
			gridcolor: "#444",
		},
	};

	Plotly.newPlot("drawdownGraph", graphData, drawdownLayout);
	Plotly.newPlot("equityGraph", equityData, equityLayout);

	accounts.forEach((account) => {
		var option = document.createElement("option");
		option.value = account;
		option.textContent = account;
		accountSelect.appendChild(option);
	});

	tableBody.addEventListener("click", function (event) {
		var row = event.target.closest("tr");
		if (row) {
			row.classList.toggle("selected");
			var checkbox = row.querySelector(".row-select");
			checkbox.checked = !checkbox.checked;
			var selected =
				tableBody.querySelectorAll(".row-select:checked").length > 0;
			accountSelect.disabled = !selected;
		}
	});

	accountSelect.addEventListener("change", function () {
		var selectedRows = Array.from(
			tableBody.querySelectorAll(".row-select:checked")
		).map((checkbox) => {
			return checkbox.closest("tr").querySelector("td:nth-child(4)")
				.textContent; // Magic number
		});

		var selectedAccount = accountSelect.value;

		if (selectedAccount && selectedRows.length > 0) {
			fetch("/copy-to-account", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					account: selectedAccount,
					magicNumbers: selectedRows,
				}),
			})
				.then((response) => response.json())
				.then((data) => {
					console.log("Success:", data);
				})
				.catch((error) => {
					console.error("Error:", error);
				});
		}

		accountSelect.value = "";
		tableBody
			.querySelectorAll(".row-select:checked")
			.forEach((checkbox) => (checkbox.checked = false));
		tableBody
			.querySelectorAll("tr.selected")
			.forEach((row) => row.classList.remove("selected"));
		accountSelect.disabled = true;
	});
});
