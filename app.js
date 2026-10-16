const cameraState = document.querySelector("#connection-state");
const connectionLabel = document.querySelector("#connection-label");
const cameraMessage = document.querySelector("#camera-message");
const startButton = document.querySelector("#start-button");
const stopButton = document.querySelector("#stop-button");
const videoFeed = document.querySelector("#video-feed");
const videoPlaceholder = document.querySelector("#video-placeholder");
const detectionList = document.querySelector("#detection-list");
const markerCount = document.querySelector("#marker-count");
let startPending = false;

function setCameraState(running, message, starting = false) {
  const wasRunning = cameraState.dataset.state === "on";
  cameraState.dataset.state = running ? "on" : starting ? "starting" : "off";
  connectionLabel.textContent = running
    ? "Camera connected"
    : starting
      ? "Connecting camera"
      : "Camera offline";
  cameraMessage.textContent = message;
  startButton.disabled = running || startPending;
  stopButton.disabled = !running && !starting;

  if (running && !wasRunning) {
    videoFeed.src = `/video_feed?t=${Date.now()}`;
    videoFeed.hidden = false;
  } else if (!running) {
    videoFeed.removeAttribute("src");
    videoFeed.hidden = true;
    videoPlaceholder.hidden = false;
    document.querySelector("#frame-size").textContent = "AWAITING CAMERA";
    document.querySelector("#fps-value").textContent = "0.0 FPS";
    renderDetections([]);
  }
}

function renderDetections(detections) {
  markerCount.textContent = String(detections.length);
  detectionList.replaceChildren();
  if (detections.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const icon = document.createElement("span");
    icon.className = "empty-target";
    icon.textContent = "◎";
    const text = document.createElement("span");
    text.textContent = "No markers detected yet";
    empty.append(icon, text);
    detectionList.append(empty);
    return;
  }

  for (const detection of detections) {
    const row = document.createElement("article");
    row.className = "detection-row";
    const id = document.createElement("span");
    id.className = "detection-id";
    id.textContent = `ID ${detection.marker_id}`;
    const position = document.createElement("span");
    position.className = "detection-position";
    position.textContent = `X ${detection.center_x} · Y ${detection.center_y}`;
    const size = document.createElement("span");
    size.className = "detection-size";
    size.textContent = `${detection.side_pixels} px`;
    row.append(id, position, size);
    detectionList.append(row);
  }
}

async function refreshStatus() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not read camera status.");
    const status = await response.json();
    setCameraState(status.running, status.message, status.starting);
    if (status.running && status.frame_width > 0) {
      document.querySelector("#frame-size").textContent =
        `${status.frame_width} × ${status.frame_height}`;
      document.querySelector("#fps-value").textContent = `${status.fps.toFixed(1)} FPS`;
      videoPlaceholder.hidden = true;
    }
    renderDetections(status.detections ?? []);
  } catch (error) {
    cameraState.dataset.state = "off";
    connectionLabel.textContent = "Service unavailable";
    cameraMessage.textContent = error.message;
  }
}

startButton.addEventListener("click", async () => {
  startPending = true;
  setCameraState(false, "Opening camera and waiting for the first frame.", true);
  try {
    const response = await fetch("/api/camera/start", { method: "POST" });
    const result = await response.json();
    startPending = false;
    setCameraState(result.running, result.message, result.starting);
  } catch {
    startPending = false;
    setCameraState(false, "Could not reach the camera service. Refresh and try again.");
  }
});

stopButton.addEventListener("click", async () => {
  stopButton.disabled = true;
  try {
    const response = await fetch("/api/camera/stop", { method: "POST" });
    const result = await response.json();
    setCameraState(result.running, result.message);
  } catch {
    cameraMessage.textContent = "Could not stop the camera service.";
  }
});

document.querySelector("#marker-button").addEventListener("click", () => {
  const input = document.querySelector("#marker-id");
  const markerId = Number(input.value);
  const message = document.querySelector("#marker-message");
  if (!Number.isInteger(markerId) || markerId < 0 || markerId > 49) {
    message.textContent = "Choose a marker ID from 0 to 49.";
    return;
  }

  const image = document.querySelector("#marker-image");
  image.src = `/api/marker/${markerId}.png?t=${Date.now()}`;
  image.alt = `Printable ArUco test marker, ID ${markerId}`;
  message.textContent = `Marker ${markerId} · 4×4 dictionary`;
});

videoFeed.addEventListener("load", () => {
  videoPlaceholder.hidden = true;
});

videoFeed.addEventListener("error", () => {
  videoPlaceholder.hidden = false;
});

refreshStatus();
window.setInterval(refreshStatus, 500);
