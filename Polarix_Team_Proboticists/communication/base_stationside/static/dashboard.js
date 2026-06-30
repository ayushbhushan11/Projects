const HOST = window.location.host;
const WS_URL = "ws://" + HOST + "/ws/dashboard";

// --- DEBUG LOGGER ---
function log(msg) { console.log(`[DASHBOARD] ${msg}`); }

// --- DOM ELEMENTS (Safe Select) ---
// We use a helper so if an ID is wrong, it warns us instead of crashing
function get(id) {
    const el = document.getElementById(id);
    if (!el) console.warn(`⚠️ MISSING HTML ELEMENT: #${id}`);
    return el;
}

const elStatusText = get("status-text");
const elStatusLight = get("status-light");
const elRssi = get("rssi-value");
const elLinkQuality = get("link-quality-value");
const elBatteryPct = get("battery-percentage");
const elBatteryBar = get("battery-level");
const elTemp = get("temperature-value");

const elSignalBars = [
    get("rssi-bar-1"), get("rssi-bar-2"), 
    get("rssi-bar-3"), get("rssi-bar-4")
];

// --- WEBSOCKET ---
function connect() {
    log("Connecting to " + WS_URL);
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        log("✅ CONNECTED");
        if(elStatusText) {
            elStatusText.innerText = "ONLINE";
            elStatusText.style.color = "#66fcf1"; // Cyan
        }
        if(elStatusLight) elStatusLight.className = "w-2 h-2 bg-cyan-400 rounded-full mr-2 shadow-[0_0_10px_#66fcf1]";
    };

    ws.onclose = () => {
        log("❌ DISCONNECTED");
        if(elStatusText) {
            elStatusText.innerText = "OFFLINE";
            elStatusText.style.color = "gray";
        }
        if(elStatusLight) elStatusLight.className = "w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse";
        setTimeout(connect, 2000);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            // LOGGING TO SEE IF DATA ARRIVES
            // Remove the '//' below if you want to see every packet in console
            // console.log("Packet:", data); 

            if (data.topic === "telemetry") {
                console.log("⚡ GOT TELEMETRY:", data); // Check Console for this!
                handleTelemetry(data);
            } 
        } catch (e) {
            console.error("JSON Error:", e);
        }
    };
}

function handleTelemetry(data) {
    // 1. UPDATE TEXT VALUES (Only if element exists)
    if (elRssi) elRssi.innerText = data.rssi;
    if (elLinkQuality) elLinkQuality.innerText = data.link_quality;
    if (elBatteryPct) elBatteryPct.innerText = data.battery + "%";
    if (elTemp) elTemp.innerText = data.temperature;

    // 2. UPDATE BATTERY BAR
    if (elBatteryBar) {
        elBatteryBar.style.width = data.battery + "%";
    }

    // 3. UPDATE SIGNAL BARS
    const rssi = data.rssi;
    // -85 is weak, -50 is strong
    updateSignalBar(0, rssi > -85);
    updateSignalBar(1, rssi > -75);
    updateSignalBar(2, rssi > -65);
    updateSignalBar(3, rssi > -50);
}

function updateSignalBar(index, isActive) {
    const bar = elSignalBars[index];
    if (!bar) return;
    
    if (isActive) {
        bar.style.backgroundColor = "#66fcf1"; // Cyan
        bar.style.boxShadow = "0 0 5px #66fcf1";
    } else {
        bar.style.backgroundColor = "#333"; // Dark Grey
        bar.style.boxShadow = "none";
    }
}

// Start
connect();
