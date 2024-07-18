document.addEventListener("DOMContentLoaded", function () {
	var tableBody = document.querySelector("#data-table tbody");
	var accountSelect = document.getElementById("accountSelect");
	var deleteSetButton = document.getElementById("deleteSetButton");
	deleteSetButton.disabled = true;

	function enableDeleteButton() {
		deleteSetButton.disabled = false;
	}

	function disableDeleteButton() {
		deleteSetButton.disabled = true;
	}

	function checkRowSelection() {
		var selectedRows = Array.from(
			tableBody.querySelectorAll(".row-select:checked")
		).map((checkbox) => {
			return checkbox.closest("tr").querySelector("td:nth-child(3)")
				.textContent; // Magic number
		});

		if (selectedRows.length > 0) {
			enableDeleteButton();
		} else {
			disableDeleteButton();
		}
	}

	function updateSliderValue(sliderId) {
		const slider = document.getElementById(sliderId);
		const valueSpan = document.getElementById(sliderId + "-value");
		valueSpan.textContent = slider.value;
	}

	function setRangeValues() {
		document.getElementById("min-profit").min = filterData.minProfit;
		document.getElementById("min-profit").max = filterData.maxProfit;
		document.getElementById("min-profit").value = filterData.minProfit;
		updateSliderValue("min-profit");

		document.getElementById("min-trades").min = filterData.minTrades;
		document.getElementById("min-trades").max = filterData.maxTrades;
		document.getElementById("min-trades").value = filterData.minTrades;
		updateSliderValue("min-trades");

		document.getElementById("max-drawdown").min = filterData.minDrawdown;
		document.getElementById("max-drawdown").max = filterData.maxDrawdown;
		document.getElementById("max-drawdown").value = filterData.minDrawdown;
		updateSliderValue("max-drawdown");

		document.getElementById("profit-factor").min = filterData.minProfitFactor;
		document.getElementById("profit-factor").max = filterData.maxProfitFactor;
		document.getElementById("profit-factor").value = filterData.minProfitFactor;
		updateSliderValue("profit-factor");

		document.getElementById("return-drawdown").min =
			filterData.minReturnOnDrawdown;
		document.getElementById("return-drawdown").max =
			filterData.maxReturnOnDrawdown;
		document.getElementById("return-drawdown").value =
			filterData.minReturnOnDrawdown;
		updateSliderValue("return-drawdown");

		document.getElementById("min-days-live").min = filterData.minDaysLive;
		document.getElementById("min-days-live").max = filterData.maxDaysLive;
		document.getElementById("min-days-live").value = filterData.minDaysLive;
		updateSliderValue("min-days-live");

		document.getElementById("avg-drawdown").min = filterData.minAvgDrawdown;
		document.getElementById("avg-drawdown").max = filterData.maxAvgDrawdown;
		document.getElementById("avg-drawdown").value = filterData.minAvgDrawdown;
		updateSliderValue("avg-drawdown");

		document.getElementById("win-rate").min = filterData.minWinRate;
		document.getElementById("win-rate").max = filterData.maxWinRate;
		document.getElementById("win-rate").value = filterData.avgWinRate;
		updateSliderValue("win-rate");
	}

	//setRangeValues();
	function setStatValues() {
		newData = calculateStatData();
		document.getElementById("selectedProfit").textContent = newData["profit"];
		document.getElementById("selectedMaxDrawdown").textContent =
			newData["maxDrawdown"];
		document.getElementById("selectedAvgDrawdown").textContent =
			newData["avgDrawdown"];
		document.getElementById("selectedSets").textContent = newData["sets"];
	}

	function updateGraphSets() {
		var setNames = Array.from(
			tableBody.querySelectorAll(".row-select:checked")
		).map((checkbox) => {
			return checkbox.closest("tr").querySelector("td:nth-child(2)")
				.textContent; // Magic number
		});

		if (setNames.length == 0) {
			var setNames = Array.from(
				tableBody.querySelectorAll(".row-select:not(:checked)")
			).map((checkbox) => {
				return checkbox.closest("tr").querySelector("td:nth-child(2)")
					.textContent; // Magic number
			});
		}

		var newGraphData = [];
		graphData.forEach(function (trace) {
			if (setNames.includes(trace.name)) {
				newGraphData.push(trace);
			}
		});
		var newEquityData = [];
		equityData.forEach(function (trace) {
			if (setNames.includes(trace.name)) {
				newEquityData.push(trace);
			}
		});

		Plotly.react("drawdownGraph", newGraphData, drawdownLayout);
		Plotly.react("equityGraph", newEquityData, equityLayout);
	}

	function calculateStatData() {
		var magicNumbers = Array.from(
			tableBody.querySelectorAll(".row-select:checked")
		).map((checkbox) => {
			return checkbox.closest("tr").querySelector("td:nth-child(3)")
				.textContent; // Magic number
		});

		if (magicNumbers.length == 0) {
			return {
				profit: accountProfit.toFixed(2),
				maxDrawdown: accountDrawdown.toFixed(2),
				avgDrawdown: accountAvgDrawdown.toFixed(2),
				sets: testSets,
			};
		}
		var selectedProfit = 0;
		var selectedMaxDrawdown = 0;
		var selectedAvgDrawdown = 0;
		setsData.forEach(function (set) {
			if (magicNumbers.includes(set["stats"].magic.toString())) {
				selectedProfit += set["stats"].profit;
				if (
					set["stats"].maxDrawdown != "-" &&
					set["stats"].avgDrawdown != "-"
				) {
					selectedMaxDrawdown += set["stats"].maxDrawdown;
					selectedAvgDrawdown += set["stats"].avgDrawdown;
				}
			}
		});
		return {
			profit: selectedProfit.toFixed(2),
			maxDrawdown: selectedMaxDrawdown.toFixed(2),
			avgDrawdown: selectedAvgDrawdown.toFixed(2),
			sets: magicNumbers.length,
		};
	}

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
			"magic",
			"profit",
			"trades",
			"maxDrawdown",
			"avgDrawdown",
			"profitFactor",
			"returnOnDrawdown",
			"minLotSize",
			"maxLotSize",
			"avgLotSize",
			"winRate",
			"wins",
			"losses",
			"minTradeTime",
			"maxTradeTime",
			"avgTradeTime",
			"daysLive",
		].forEach(function (key) {
			if (document.getElementById(key).checked) {
				document.getElementById(key + "Header").style.display = "";
				var cell = document.createElement("td");
				cell.textContent = stats[key];
				row.appendChild(cell);
			} else {
				document.getElementById(key + "Header").style.display = "none";
			}
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
	setRangeValues();
	setStatValues();

	var selectedRows = Array.from(
		tableBody.querySelectorAll(".row-select:checked")
	).map((checkbox) => {
		return checkbox.closest("tr").querySelector("td:nth-child(3)").textContent; // Magic number
	});

	function resetTable() {
		populateTable(setsData);
	}

	var columnToggles = document.querySelectorAll(".column-toggle");
	columnToggles.forEach(function (toggle) {
		toggle.addEventListener("change", resetTable);
	});

	function toggleFilters() {
		calculateStatData();
		filters = document.getElementById("filters-container");
		if (filters.style.display == "none") {
			filters.style.display = "";
		} else {
			filters.style.display = "none";
		}
	}

	document
		.getElementById("filterButton")
		.addEventListener("click", toggleFilters);

	function applyFilters() {
		var profitMin = parseInt(document.getElementById("profitRange").value);
		var profitMax = parseInt(document.getElementById("profitRange").max);
		var drawdownMin = parseInt(
			document.getElementById("maxDrawdownRange").value
		);
		var drawdownMax = parseInt(document.getElementById("maxDrawdownRange").max);
		var daysLiveMin = parseInt(document.getElementById("daysLiveRange").value);
		var daysLiveMax = parseInt(document.getElementById("daysLiveRange").max);
		var drawdownWindow = parseInt(
			document.getElementById("drawdownWindow").value
		);
		var equityWindow = parseInt(document.getElementById("equityWindow").value);

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
		updateGraphs(filteredData, drawdownWindow, equityWindow);
	}

	function resetFilters() {
		populateTable(setsData);
		updateGraphs(graphData, 10, 10);
		setRangeValues();
	}

	//document
	//	.getElementById("applyFilters")
	//	.addEventListener("click", applyFilters);

	//document
	//	.getElementById("resetFilters")
	//	.addEventListener("click", resetFilters);

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
				name: trace.name,
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

		Plotly.react("drawdownGraph", smoothedDrawdownTraces, drawdownLayout);
		Plotly.react("equityGraph", smoothedEquityTraces, equityLayout);
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

	var screenWidth = window.innerWidth;
	var newWidth = screenWidth - 350;

	var drawdownLayout = {
		title: "Drawdown",
		plot_bgcolor: "#222",
		paper_bgcolor: "#222",
		width: newWidth,
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
		width: newWidth,
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

	function onResize() {
		var screenWidth = window.innerWidth;
		var newWidth = screenWidth - 350;
		var updatedDawdownLayout = {
			title: "Drawdown",
			plot_bgcolor: "#222",
			paper_bgcolor: "#222",
			width: newWidth,
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

		var updatedEquityLayout = {
			title: "Equity",
			plot_bgcolor: "#222",
			paper_bgcolor: "#222",
			width: newWidth,
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
		Plotly.react("drawdownGraph", graphData, updatedDawdownLayout);
		Plotly.react("equityGraph", equityData, updatedEquityLayout);
	}

	window.addEventListener("resize", onResize);

	function deleteSet() {
		fetch("/delete-set", {
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
		setStatValues();
		updateGraphSets();
		checkRowSelection();
	});

	accountSelect.addEventListener("change", function () {
		var selectedRows = Array.from(
			tableBody.querySelectorAll(".row-select:checked")
		).map((checkbox) => {
			return checkbox.closest("tr").querySelector("td:nth-child(3)")
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
		checkRowSelection();
	});

	var tableBody = document.querySelector("#data-table tbody");
	var currentSortColumn = null;
	var isAscending = true;

	function sortTable(columnIndex, dataType) {
		var rows = Array.from(tableBody.rows);

		rows.sort(function (rowA, rowB) {
			var valueA = parseCellValue(
				rowA.cells[columnIndex].textContent,
				dataType
			);
			var valueB = parseCellValue(
				rowB.cells[columnIndex].textContent,
				dataType
			);

			if (isAscending) {
				return compareValues(valueA, valueB);
			} else {
				return compareValues(valueB, valueA);
			}
		});

		// Clear existing rows
		while (tableBody.firstChild) {
			tableBody.removeChild(tableBody.firstChild);
		}

		// Append sorted rows
		rows.forEach(function (row) {
			tableBody.appendChild(row);
		});

		// Toggle sort order
		isAscending = !isAscending;
		currentSortColumn = columnIndex;
	}

	function parseCellValue(value, dataType) {
		if (value === "-" || value === "") {
			if (dataType === "numeric") {
				return 0;
			} else {
				return "";
			}
		} else {
			if (dataType === "numeric") {
				return parseFloat(value);
			} else {
				return value;
			}
		}
	}

	function compareValues(valueA, valueB) {
		if (valueA < valueB) {
			return -1;
		} else if (valueA > valueB) {
			return 1;
		} else {
			return 0;
		}
	}

	// Add click event listeners to table headers
	var headers = document.querySelectorAll("#data-table th");
	headers.forEach(function (header, index) {
		header.addEventListener("click", function () {
			// Determine data type based on column index
			var dataType = "string"; // default to string
			if (
				index === 2 ||
				index === 3 ||
				index === 4 ||
				index === 5 ||
				index === 6 ||
				index === 7 ||
				index === 8 ||
				index === 9 ||
				index === 10 ||
				index === 11 ||
				index === 12 ||
				index === 13 ||
				index === 14 ||
				index === 15 ||
				index === 16 ||
				index === 17
			) {
				dataType = "numeric";
			}

			sortTable(index, dataType);
		});
	});
});
