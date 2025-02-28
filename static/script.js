document.addEventListener("DOMContentLoaded", function () {
    const startDate = document.getElementById("start");
    const endDate = document.getElementById("end");
    const riskTolerance = document.getElementById("risk_tolerance");
    const riskValue = document.getElementById("riskValue");
    const resultsDiv = document.getElementById("results");

    // Loading message
    const loadingDiv = document.createElement("p");
    loadingDiv.id = "loadingMessage";
    loadingDiv.innerHTML = "⏳ <strong>Preparing portfolio...</strong>";
    loadingDiv.style.display = "none"; 
    loadingDiv.style.color = "#2c3e50"; 
    loadingDiv.style.fontSize = "1.2rem"; 
    loadingDiv.style.fontWeight = "bold";
    loadingDiv.style.textAlign = "center";
    resultsDiv.parentNode.insertBefore(loadingDiv, resultsDiv); 

    riskTolerance.addEventListener("input", function () {
        riskValue.textContent = this.value;
    });
});

document.getElementById('portfolioForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const stocks = document.getElementById('stocks').value;
    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;
    const funds = parseFloat(document.getElementById('funds').value);
    const riskTolerance = parseInt(document.getElementById('risk_tolerance').value);
    const resultsDiv = document.getElementById("results");
    const loadingMessage = document.getElementById("loadingMessage");

    if (!stocks || funds <= 0) {
        alert("Please enter valid stock tickers and investment amount.");
        return;
    }

    // Show loading message
    loadingMessage.style.display = "block";
    resultsDiv.innerHTML = "";

    try {
        const response = await fetch('/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stocks, start, end, funds, risk_tolerance: riskTolerance })
        });

        const result = await response.json();

        if (result.error) {
            alert(`Error: ${result.error}`);
        } else {
            displayResults(result);
        }
    } catch (error) {
        alert("An error occurred while optimizing the portfolio.");
    } finally {
        loadingMessage.style.display = "none";
    }
});

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    
    resultsDiv.innerHTML = `
        <h3 class="mt-3">Optimization Results</h3>
        <p><strong>Expected Annual Return:</strong> ${(data.performance.annual_return * 100).toFixed(2)}%</p>
        <p><strong>Annual Volatility:</strong> ${(data.performance.annual_volatility * 100).toFixed(2)}%</p>
        <p><strong>Sharpe Ratio:</strong> ${data.performance.sharpe_ratio.toFixed(2)}</p>
        <h4>Allocation:</h4>
        <ul>
            ${Object.entries(data.allocation).map(([stock, shares]) => `<li>${stock}: ${shares} shares</li>`).join('')}
        </ul>
        <p><strong>Remaining Funds:</strong> $${data.leftover_funds.toFixed(2)}</p>
        <div id="pieChart"></div>
        <div id="priceChart"></div>
    `;

    // Render Pie Chart
    Plotly.newPlot('pieChart', JSON.parse(data.pie_chart));

    // Render Price History Line Chart
    Plotly.newPlot('priceChart', JSON.parse(data.price_chart));
}

