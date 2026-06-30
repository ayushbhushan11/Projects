// ================= VIDEO RECORDING & SNAPSHOT LOGIC =================

const mediaRecorders = {};
const recordedChunks = {};

// --- 1. TAKE SNAPSHOT ---
function takeSnapshot(videoId) {
    const video = document.getElementById(videoId);
    if (!video) return console.error("Video not found:", videoId);

    // Create a canvas to capture the frame
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    // Convert to blob and upload
    canvas.toBlob(blob => {
        // Use a clean filename
        const filename = `${videoId}_snapshot.png`;
        uploadToServer(blob, filename);
        flashScreen(); // Visual feedback
    }, 'image/png');
}

// --- 2. TOGGLE RECORDING ---
function toggleRecording(videoId, btnId, index) {
    const video = document.getElementById(videoId);
    const btn = document.getElementById(btnId);
    const dot = document.getElementById(`rec-dot-${index}`);

    if (!mediaRecorders[videoId] || mediaRecorders[videoId].state === "inactive") {
        // START RECORDING
        const stream = video.srcObject;
        if (!stream) return alert("No video feed to record!");

        const recorder = new MediaRecorder(stream);
        mediaRecorders[videoId] = recorder;
        recordedChunks[videoId] = [];

        recorder.ondataavailable = (e) => {
            if (e.data.size > 0) recordedChunks[videoId].push(e.data);
        };

        recorder.onstop = () => {
            const blob = new Blob(recordedChunks[videoId], { type: "video/webm" });
            const filename = `${videoId}_clip.webm`;
            uploadToServer(blob, filename);
        };

        recorder.start();
        
        // Update UI
        btn.classList.add("recording");
        if(dot) dot.style.display = "block";
        console.log(`Started recording ${videoId}`);

    } else {
        // STOP RECORDING
        mediaRecorders[videoId].stop();
        
        // Update UI
        btn.classList.remove("recording");
        if(dot) dot.style.display = "none";
        console.log(`Stopped recording ${videoId}`);
    }
}

// --- 3. UPLOAD TO PYTHON SERVER ---
function uploadToServer(blob, filename) {
    const formData = new FormData();
    formData.append("file", blob, filename);

    // Show "Saving..." status (Optional)
    const statusText = document.getElementById("status-text");
    const originalText = statusText ? statusText.innerText : "";
    if(statusText) statusText.innerText = "SAVING...";

    // --- FIX: MUST BE /upload_media TO MATCH SERVER ---
    fetch("/upload_media", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log(`✅ Uploaded ${filename}`);
            if(statusText) statusText.innerText = "SAVED";
        } else {
            console.error("❌ Upload failed: Server returned " + response.status);
            if(statusText) statusText.innerText = "ERROR";
        }
        setTimeout(() => { if(statusText) statusText.innerText = originalText; }, 2000);
    })
    .catch(error => console.error("Network error:", error));
}

// --- VISUAL FLASH EFFECT ---
function flashScreen() {
    const flash = document.createElement("div");
    flash.style.position = "fixed";
    flash.style.inset = "0";
    flash.style.background = "white";
    flash.style.opacity = "0.5";
    flash.style.zIndex = "9999";
    flash.style.pointerEvents = "none";
    document.body.appendChild(flash);
    setTimeout(() => flash.remove(), 100);
}
