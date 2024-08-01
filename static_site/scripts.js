async function fetchData() {
    try {
        const response = await fetch('https://baitfluentd.s3.amazonaws.com/summary.json');
        const data = await response.json();
        console.log('Fetched data:', data); // Log the fetched data to understand its structure
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

function updateLastUpdated(dateString) {
    document.getElementById('last-updated').textContent = dateString;
}

function updateTotalAlerts(data) {
    if (data && data.rule_description) {
        const totalAlerts = Object.values(data.rule_description).reduce((a, b) => a + b, 0);
        document.getElementById('total-alerts').textContent = totalAlerts;
    } else {
        console.error('Data for rule descriptions is missing or invalid.');
    }
}

function createPieChart(data, elementId, legendId) {
    if (!data) {
        console.error(`Data for ${elementId} is missing or invalid.`);
        return;
    }
    
    const width = 200, height = 200, margin = 20; // Reduced size
    const radius = Math.min(width, height) / 2 - margin;

    const svg = d3.select(elementId)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${width / 2},${height / 2})`);

    const color = d3.scaleOrdinal()
        .domain(Object.keys(data))
        .range(d3.schemeCategory10);

    const pie = d3.pie()
        .value(d => d[1]);

    const data_ready = pie(Object.entries(data));

    svg
        .selectAll('path')
        .data(data_ready)
        .enter()
        .append('path')
        .attr('d', d3.arc()
            .innerRadius(0)
            .outerRadius(radius)
        )
        .attr('fill', d => color(d.data[0]))
        .attr('stroke', '#d3d3d3')  // Lighter border color
        .style('stroke-width', '1px')  // Thinner border
        .style('opacity', 0.7);

    const legend = d3.select(legendId);
    legend.selectAll('div')
        .data(data_ready)
        .enter()
        .append('div')
        .attr('class', 'legend-item')
        .html(d => `
            <div class="legend-color" style="background-color: ${color(d.data[0])};"></div>
            <div>${d.data[0]}: ${d.data[1]}</div>
        `);
}

function populateTable(data, elementId) {
    if (!data) {
        console.error(`Data for ${elementId} is missing or invalid.`);
        return;
    }

    const tbody = document.getElementById(elementId);
    tbody.innerHTML = '';
    const sortedData = Object.entries(data).sort((a, b) => b[1] - a[1]);
    sortedData.slice(0, 10).forEach(([key, value]) => {
        const row = document.createElement('tr');
        const keyCell = document.createElement('td');
        keyCell.textContent = key;
        const valueCell = document.createElement('td');
        valueCell.textContent = value;
        row.appendChild(keyCell);
        row.appendChild(valueCell);
        tbody.appendChild(row);
    });
}

fetchData().then(data => {
    if (!data) {
        console.error('No data received');
        return;
    }

    updateLastUpdated(data.last_updated);
    updateTotalAlerts(data);
    createPieChart(sortData(data.rule_level), '#rule-level-chart', '#rule-level-legend');
    createPieChart(sortData(data.agent_name), '#agent-name-chart', '#agent-name-legend');
    populateTable(data.rule_description, 'rule-description-table');
    populateTable(data.geo_location, 'geo-location-table');
}).catch(error => console.error('Error loading data:', error));

function sortData(data) {
    if (!data) return {};
    return Object.fromEntries(Object.entries(data).sort((a, b) => b[1] - a[1]));
}
