const batteryLevel = document.getElementById("battery-level");
const batteryPercentage = document.getElementById("battery-percentage");
const rssiValue = document.getElementById("rssi-value");
const temperatureValue = document.getElementById("temperature-value");
const rssiBars = [
    document.getElementById("rssi-bar-1"),
    document.getElementById("rssi-bar-2"),
    document.getElementById("rssi-bar-3"),
    document.getElementById("rssi-bar-4"),
];

const linkQualityValue = document.getElementById("link-quality-value");
const cameraContainer = document.getElementById("camera-container");
const cameraItems = document.querySelectorAll(".camera-item");
const viewToggleButton = document.getElementById("view-toggle-btn");
const statusLight = document.getElementById("status-light");
const statusText = document.getElementById("status-text");

// Add these lines for the Gamepad Widget
const gamepadEventType = document.getElementById("gamepad-event-type");
const gamepadEventCode = document.getElementById("gamepad-event-code");
const gamepadEventState = document.getElementById("gamepad-event-state");