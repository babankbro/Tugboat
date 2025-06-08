#!/usr/bin/env python3
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import timedelta, datetime
import pandas as pd
from read_data import *
from initialize_data import initialize_data, print_all_objects
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.travel_helper import *
from CodeVS.components.solution import Solution

import pandas as pd
import json
import webbrowser
import os
from pathlib import Path

import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import timedelta, datetime
import pandas as pd
from read_data import *
from initialize_data import initialize_data, print_all_objects
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.travel_helper import *
from CodeVS.components.solution import Solution



def create_timeline_html(csv_data, output_file="tugboat_timeline.html"):
    """Create HTML timeline from CSV data"""
    

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Tugboat Operations Timeline</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(45deg, #3498db, #8e44ad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            font-size: 12px;
        }
        
        .filter-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .filter-btn.active {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }
        
        .timeline-container {
            position: relative;
            overflow-x: auto;
            background: white;
            border-radius: 10px;
            padding: 40px 20px 60px 20px;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .timeline {
            position: relative;
            min-width: 1400px;
            height: 800px;
        }
        
        .timeline-axis {
            position: absolute;
            bottom: 40px;
            left: 0;
            right: 0;
            height: 40px;
            border-top: 2px solid #34495e;
        }
        
        .axis-label {
            position: absolute;
            bottom: -35px;
            transform: translateX(-50%);
            font-size: 10px;
            color: #7f8c8d;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .task-bar {
            position: absolute;
            height: 28px;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            padding: 0 8px;
            font-size: 11px;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            overflow: hidden;
            white-space: nowrap;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .task-bar:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            z-index: 10;
            height: 32px;
            margin-top: -2px;
        }
        
        /* Task Type Colors */
        .task-bar.start { background: linear-gradient(45deg, #27ae60, #229954); }
        .task-bar.barge { background: linear-gradient(45deg, #3498db, #2980b9); }
        .task-bar.crane { background: linear-gradient(45deg, #e67e22, #d35400); }
        .task-bar.travel { background: linear-gradient(45deg, #9b59b6, #8e44ad); }
        .task-bar.appointment { background: linear-gradient(45deg, #e74c3c, #c0392b); }
        .task-bar.loader { background: linear-gradient(45deg, #f39c12, #e67e22); }
        .task-bar.customer { background: linear-gradient(45deg, #1abc9c, #16a085); }
        .task-bar.change { background: linear-gradient(45deg, #34495e, #2c3e50); }
        .task-bar.carrier { background: linear-gradient(45deg, #8e44ad, #732d91); }
        
        /* Tugboat-specific styling */
        .task-bar.tbs1 { border-left: 4px solid #ff6b6b; }
        .task-bar.tbr1 { border-left: 4px solid #4ecdc4; }
        
        .tooltip {
            position: absolute;
            background: rgba(44, 62, 80, 0.95);
            color: white;
            padding: 15px;
            border-radius: 10px;
            display: none;
            z-index: 1000;
            max-width: 350px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            font-size: 12px;
            line-height: 1.4;
        }
        
        .legend {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(5px);
            font-size: 12px;
        }
        
        .legend-color {
            width: 18px;
            height: 18px;
            border-radius: 9px;
            flex-shrink: 0;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            opacity: 0.9;
            font-size: 0.8em;
        }
        
        .tugboat-info {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .tugboat-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 15px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            font-size: 12px;
        }
        
        .tugboat-badge.tbs1 { border-left: 4px solid #ff6b6b; }
        .tugboat-badge.tbr1 { border-left: 4px solid #4ecdc4; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚢 Enhanced Tugboat Operations Timeline</h1>
        
        <div class="tugboat-info">
            <div class="tugboat-badge tbs1">🚢 TBS1 - Sea Tugboat</div>
            <div class="tugboat-badge tbr1">🛥️ TBR1 - River Tugboat</div>
        </div>
        
        <div class="controls">
            <button class="filter-btn active" onclick="filterTasks('all')">All Operations</button>
            <button class="filter-btn" onclick="filterTasks('tbs1')">TBS1 Only</button>
            <button class="filter-btn" onclick="filterTasks('tbr1')">TBR1 Only</button>
            <button class="filter-btn" onclick="filterTasks('trip-1')">Trip 1</button>
            <button class="filter-btn" onclick="filterTasks('trip-2')">Trip 2</button>
            <button class="filter-btn" onclick="filterTasks('barge')">Barge Ops</button>
            <button class="filter-btn" onclick="filterTasks('crane')">Crane Ops</button>
            <button class="filter-btn" onclick="filterTasks('travel')">Travel</button>
            <button class="filter-btn" onclick="filterTasks('customer')">Customer</button>
        </div>
        
        <div class="timeline-container">
            <div class="timeline" id="timeline">
                <div class="timeline-axis" id="axis"></div>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #27ae60, #229954);"></div>
                <span>Start Operations</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #3498db, #2980b9);"></div>
                <span>Barge Operations</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #e67e22, #d35400);"></div>
                <span>Crane Operations</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #9b59b6, #8e44ad);"></div>
                <span>Travel & Transport</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #e74c3c, #c0392b);"></div>
                <span>Appointments</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #f39c12, #e67e22);"></div>
                <span>Loading Operations</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #1abc9c, #16a085);"></div>
                <span>Customer Stations</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #34495e, #2c3e50);"></div>
                <span>Barge Changes</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(45deg, #8e44ad, #732d91);"></div>
                <span>Carrier Operations</span>
            </div>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalTasks">0</div>
                <div class="stat-label">Total Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalDuration">0</div>
                <div class="stat-label">Duration (hours)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalDistance">0</div>
                <div class="stat-label">Distance (km)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalLoad">0</div>
                <div class="stat-label">Total Load</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="tugboatCount">0</div>
                <div class="stat-label">Tugboats</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="tripCount">0</div>
                <div class="stat-label">Trips</div>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>

    <script>
        const rawData = `DATA_PLACEHOLDER`;
        
        let data = [];
        let currentFilter = 'all';
        
        function parseCSV(csvText) {
            const lines = csvText.trim().split('\\n');
            const headers = lines[0].split(',');
            
            return lines.slice(1).map(line => {
                const values = [];
                let current = '';
                let inQuotes = false;
                
                for (let i = 0; i < line.length; i++) {
                    const char = line[i];
                    if (char === '"') {
                        inQuotes = !inQuotes;
                    } else if (char === ',' && !inQuotes) {
                        values.push(current.trim());
                        current = '';
                    } else {
                        current += char;
                    }
                }
                values.push(current.trim());
                
                const obj = {};
                headers.forEach((header, index) => {
                    obj[header.trim()] = values[index] || '';
                });
                return obj;
            });
        }
        
        function getTaskType(type, name, id) {
            const typeStr = type.toLowerCase();
            const nameStr = name.toLowerCase();
            const idStr = id.toLowerCase();
            
            if (typeStr === 'start') return 'start';
            if (typeStr.includes('barge') || nameStr.includes('barge')) {
                if (typeStr.includes('change') || nameStr.includes('change')) return 'change';
                return 'barge';
            }
            if (typeStr.includes('crane') || nameStr.includes('crane')) return 'crane';
            if (typeStr.includes('loader') || nameStr.includes('loader')) return 'loader';
            if (typeStr.includes('customer') || nameStr.includes('customer') || nameStr.includes('station')) return 'customer';
            if (typeStr.includes('carrier') || nameStr.includes('carrier')) return 'carrier';
            if (typeStr.includes('sea-river') || typeStr.includes('travel') || nameStr.includes('travel')) return 'travel';
            if (typeStr.includes('appointment') || nameStr.includes('appointment') || nameStr.includes('pier')) return 'appointment';
            
            return 'other';
        }
        
        function createTimeline() {
            data = parseCSV(rawData);
            
            let minDate = new Date('2030-01-01');
            let maxDate = new Date('2020-01-01');
            
            data.forEach(item => {
                item.startDate = new Date(item.enter_datetime);
                item.endDate = new Date(item.exit_datetime);
                item.taskType = getTaskType(item.type, item.name, item.ID);
                item.tugboatClass = item.tugboat_id || 'unknown';
                
                if (item.startDate < minDate) minDate = item.startDate;
                if (item.endDate > maxDate) maxDate = item.endDate;
            });
            
            const timeline = document.getElementById('timeline');
            timeline.innerHTML = '<div class="timeline-axis" id="axis"></div>';
            
            const totalDuration = maxDate - minDate;
            
            // Create more axis labels for better precision
            const numLabels = 12;
            for (let i = 0; i <= numLabels; i++) {
                const time = new Date(minDate.getTime() + (totalDuration * i / numLabels));
                const label = document.createElement('div');
                label.className = 'axis-label';
                label.style.left = `${(i / numLabels) * 100}%`;
                const dateStr = time.toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
                const timeStr = time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                label.textContent = `${dateStr} ${timeStr}`;
                document.getElementById('axis').appendChild(label);
            }
            
            // Group tasks by tugboat and trip for better positioning
            const taskGroups = {};
            data.forEach((item, index) => {
                if (shouldShowTask(item)) {
                    const groupKey = `1`;
                    if (!taskGroups[groupKey]) taskGroups[groupKey] = [];
                    taskGroups[groupKey].push({...item, originalIndex: index});
                }
            });
            
            // Create task bars with better positioning
            let rowOffset = 0;
            Object.keys(taskGroups).forEach((groupKey, groupIndex) => {
                taskGroups[groupKey].forEach((item, itemIndex) => {
                    const bar = createTaskBar(item, minDate, totalDuration, rowOffset + itemIndex);
                    timeline.appendChild(bar);
                });
                rowOffset += taskGroups[groupKey].length + 1; // Add spacing between groups
            });
            
            updateStats();
        }
        
        function createTaskBar(item, minDate, totalDuration, rowIndex) {
            const bar = document.createElement('div');
            bar.className = `task-bar ${item.taskType} ${item.tugboatClass}`;
            
            const startOffset = (item.startDate - minDate) / totalDuration;
            const duration = Math.max((item.endDate - item.startDate) / totalDuration, 0.001);
            
            bar.style.left = `${startOffset * 100}%`;
            bar.style.width = `${Math.max(duration * 100, 0.3)}%`;
            bar.style.top = `${rowIndex * 32 + 20}px`;
            
            const taskName = item.name.length > 25 ? item.name.substring(0, 25) + '...' : item.name;
            bar.textContent = taskName;
            
            bar.addEventListener('mouseenter', (e) => showTooltip(e, item));
            bar.addEventListener('mouseleave', hideTooltip);
            
            return bar;
        }
        
        function shouldShowTask(item) {
            if (currentFilter === 'all') return true;
            if (currentFilter === 'tbs1') return item.tugboat_id === 'tbs1';
            if (currentFilter === 'tbr1') return item.tugboat_id === 'tbr1';
            if (currentFilter === 'trip-1') return item.order_trip === '1';
            if (currentFilter === 'trip-2') return item.order_trip === '2';
            if (currentFilter === 'barge') return item.taskType === 'barge' || item.taskType === 'change';
            if (currentFilter === 'crane') return item.taskType === 'crane';
            if (currentFilter === 'travel') return item.taskType === 'travel';
            if (currentFilter === 'customer') return item.taskType === 'customer' || item.taskType === 'loader';
            return true;
        }
        
        function showTooltip(e, item) {
            const tooltip = document.getElementById('tooltip');
            const duration = (item.endDate - item.startDate) / (1000 * 60 * 60);
            
            tooltip.innerHTML = `
                <strong>🚢 ${item.name}</strong><br>
                <strong>Type:</strong> ${item.type}<br>
                <strong>Tugboat:</strong> ${item.tugboat_id}<br>
                <strong>Start:</strong> ${item.startDate.toLocaleString()}<br>
                <strong>End:</strong> ${item.endDate.toLocaleString()}<br>
                <strong>Duration:</strong> ${duration.toFixed(2)} hours<br>
                <strong>Trip:</strong> ${item.order_trip}<br>
                <strong>Distance:</strong> ${parseFloat(item.distance || 0).toFixed(2)} km<br>
                <strong>Speed:</strong> ${parseFloat(item.speed || 0).toFixed(1)} km/h<br>
                <strong>Load:</strong> ${item.total_load} units<br>
                <strong>Barges:</strong> ${item.barge_ids}<br>
                <strong>ID:</strong> ${item.ID}
            `;
            
            tooltip.style.display = 'block';
            tooltip.style.left = e.pageX + 15 + 'px';
            tooltip.style.top = e.pageY - 10 + 'px';
        }
        
        function hideTooltip() {
            document.getElementById('tooltip').style.display = 'none';
        }
        
        function filterTasks(filter) {
            currentFilter = filter;
            
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            createTimeline();
        }
        
        function updateStats() {
            const visibleTasks = data.filter(shouldShowTask);
            const totalTasks = visibleTasks.length;
            const totalDuration = visibleTasks.reduce((sum, item) => {
                return sum + (item.endDate - item.startDate) / (1000 * 60 * 60);
            }, 0);
            const totalDistance = visibleTasks.reduce((sum, item) => {
                return sum + parseFloat(item.distance || 0);
            }, 0);
            const totalLoad = visibleTasks.reduce((sum, item) => {
                return sum + parseFloat(item.total_load || 0);
            }, 0);
            const tugboats = [...new Set(visibleTasks.map(item => item.tugboat_id))];
            const trips = [...new Set(visibleTasks.map(item => item.order_trip))];
            
            document.getElementById('totalTasks').textContent = totalTasks;
            document.getElementById('totalDuration').textContent = totalDuration.toFixed(1);
            document.getElementById('totalDistance').textContent = totalDistance.toFixed(1);
            document.getElementById('totalLoad').textContent = totalLoad.toLocaleString();
            document.getElementById('tugboatCount').textContent = tugboats.length;
            document.getElementById('tripCount').textContent = trips.length;
        }
        
        createTimeline();
    </script>
</body>
</html>          <strong>End:</strong> ${item.endDate.toLocaleString()}<br>
                <strong>Duration:</strong> ${duration.toFixed(2)} hours<br>
                <strong>Trip:</strong> ${item.order_trip}<br>
                <strong>Distance:</strong> ${parseFloat(item.distance || 0).toFixed(2)} km<br>
                <strong>Load:</strong> ${item.total_load} units<br>
                <strong>Barges:</strong> ${item.barge_ids}
            `;
            
            tooltip.style.display = 'block';
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY - 10 + 'px';
        }
        
        function hideTooltip() {
            document.getElementById('tooltip').style.display = 'none';
        }
        
        function filterTasks(filter) {
            currentFilter = filter;
            
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            createTimeline();
        }
        
        function updateStats() {
            const visibleTasks = data.filter(shouldShowTask);
            const totalTasks = visibleTasks.length;
            const totalDuration = visibleTasks.reduce((sum, item) => {
                return sum + (item.endDate - item.startDate) / (1000 * 60 * 60);
            }, 0);
            const totalDistance = visibleTasks.reduce((sum, item) => {
                return sum + parseFloat(item.distance || 0);
            }, 0);
            
            document.getElementById('totalTasks').textContent = totalTasks;
            document.getElementById('totalDuration').textContent = totalDuration.toFixed(1);
            document.getElementById('totalDistance').textContent = totalDistance.toFixed(1);
        }
        
        createTimeline();
    </script>
</body>
</html>     const tooltip = document.getElementById('tooltip');
            const duration = (item.endDate - item.startDate) / (1000 * 60 * 60);
            
            tooltip.innerHTML = `
                <strong>${item.name}</strong><br>
                <strong>Type:</strong> ${item.type}<br>
                <strong>Start:</strong> ${item.startDate.toLocaleString()}<br>
      '''

    # Replace placeholder with actual data
    escaped_csv = csv_data.replace('\n', '\\n').replace('`', '\\`').replace('\r', '')
    html_content = html_template.replace('DATA_PLACEHOLDER', escaped_csv)

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Timeline generated: {output_file}")
    return output_file

def save_csv_file(csv_data, filename="tugboat_data.csv"):
    """Save CSV data to file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(csv_data)
    print(f"✅ CSV saved: {filename}")
    return filename

def convert_to_json(csv_data, output_file="tugboat_data.json"):
    """Convert CSV to JSON format"""
    from io import StringIO
    
    # Parse CSV
    df = pd.read_csv(StringIO(csv_data))
    
    # Convert to JSON
    json_data = df.to_dict('records')
    
    # Save JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print(f"✅ JSON saved: {output_file}")
    return json_data

def analyze_data(csv_data):
    """Analyze the tugboat data"""
    from io import StringIO
    
    df = pd.read_csv(StringIO(csv_data))
    
    print("\n📊 DATA ANALYSIS")
    print("=" * 50)
    print(f"Total records: {len(df)}")
    print(f"Date range: {df['enter_datetime'].min()} to {df['exit_datetime'].max()}")
    print(f"Unique trips: {df['order_trip'].nunique()}")
    print(f"Task types: {df['type'].unique()}")
    print(f"Total distance: {df['distance'].sum():.2f} km")
    print(f"Average speed: {df['speed'].mean():.2f} km/h")
    
    # Trip summary
    print("\n🚢 TRIP SUMMARY")
    for trip in df['order_trip'].unique():
        trip_data = df[df['order_trip'] == trip]
        total_time = (pd.to_datetime(trip_data['exit_datetime']).max() - 
                     pd.to_datetime(trip_data['enter_datetime']).min()).total_seconds() / 3600
        print(f"Trip {trip}: {len(trip_data)} tasks, {total_time:.1f} hours")

def start_web_server(html_file, port=8000):
    """Start a simple web server to view the HTML file"""
    import http.server
    import socketserver
    import threading
    import time
    
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress log messages
    
    try:
        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            url = f"http://localhost:{port}/{html_file}"
            print(f"🌐 Server started at {url}")
            
            # Open browser
            webbrowser.open(url)
            
            print("Press Ctrl+C to stop the server...")
            try:
                while True:
                    time.sleep(0.2)
            except KeyboardInterrupt:
                httpd.shutdown()
                print("\n🛑 Server stopped")
                
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try port {port + 1}")
            start_web_server(html_file, port + 1)
        else:
            print(f"❌ Error starting server: {e}")

def main():
    data = initialize_data(carrier_df, station_df, order_df, tugboat_df, barge_df)
    TravelHelper()
    TravelHelper._set_data(TravelHelper._instance,  data)
    
    
    orders = data['orders']
    barges = data['barges']
    tugboats = data['tugboats']
    order = orders['o1']
    
    
    solution = Solution(data)
    
    vtugboat_df, vbarge_df = solution.generate_schedule()
    
    filtered_df = vtugboat_df[
                            ((vtugboat_df['tugboat_id'] == 'tbs1')) 
                           # &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
                             # & ((vtugboat_df['order_id'] == 'o1') )
                           # & (tugboat_df['order_trip'] == 1)
                            #& (tugboat_df['distance'] > 60)
                            #(tugboat_df['distance'] > 60)
                            #(vtugboat_df['name'].str.contains('ld1', case=False, na=False))
                            ]
    temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
                           'tugboat_id','distance', 'time', 'speed','order_trip',
                      # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
                      'total_load', 'barge_ids',
       #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
       #'tugboat_id', 'order_id', 'water_type'
       ]]
    
    #sort data on enter_datetime
    temp_df['enter_datetime'] = pd.to_datetime(temp_df['enter_datetime'])
    temp_df = temp_df.sort_values(by='enter_datetime')
    
    #print(temp_df.head(30))
    #temp_df = temp_df.head(5)
    
    CSV_DATA = temp_df.to_csv(index=False)
    print(CSV_DATA)
    print(len(temp_df))

    """Main function to process tugboat data"""
    print("🚢 TUGBOAT TIMELINE GENERATOR")
    print("=" * 50)

    # Save CSV file
    csv_file = save_csv_file(CSV_DATA)
    
    # Analyze data
    analyze_data(CSV_DATA)
    
    # Convert to JSON
    json_data = convert_to_json(CSV_DATA)
    
    # Generate timeline HTML
    html_file = create_timeline_html(CSV_DATA)
    
    # Ask user if they want to start web server
    print(f"\n✨ Timeline visualization ready!")
    print(f"📄 HTML file: {html_file}")
    print(f"📊 CSV file: {csv_file}")
    print(f"📋 JSON file: tugboat_data.json")
    
    response = input("\n🌐 Start web server to view timeline? (y/n): ").lower()
    if response in ['y', 'yes']:
        start_web_server(html_file)

if __name__ == "__main__":
    main()

# USAGE EXAMPLES:
# ===============

# 1. Basic usage - run the script
# python process_tugboat_csv.py

# 2. Use as module
# from process_tugboat_csv import create_timeline_html, convert_to_json
# html_file = create_timeline_html(your_csv_data)
# json_data = convert_to_json(your_csv_data)

# 3. Process different data formats
# create_timeline_html(csv_string)           # From CSV string
# create_timeline_html(pd.read_csv('file'))  # From DataFrame
# create_timeline_html(json_data)            # From JSON data