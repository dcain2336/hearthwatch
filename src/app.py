# app.py — the Hearthwatch demo web server.
# Pure Python standard library plus OpenCV: no web framework needed.
# Endpoints:
#   GET  /                  the single-page demo UI.
#   GET  /api/scenes        list the built-in synthetic test scenes.
#   POST /api/run           run the pipeline on a scene or upload,
#                            return events and an annotated video.
#   GET  /output/<file>     serve an annotated video produced by a run.
#   POST /api/acknowledge   acknowledge an open alert by index.
#   POST /api/false_alarm   mark an open alert a false alarm by index.
# Run with: python3 src/app.py  (serves on port 8772 by default).

import json
import os
import sys

# Import the HTTP server pieces from the standard library.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Import OpenCV for reading videos and drawing annotation boxes.
import cv2

# Import the pipeline and the agent from this same folder.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import HearthAgent
from sentinel import Sentinel

# Port the demo server listens on.
PORT = 8772
# Folder holding the synthetic test scenes (built by make_testset.py).
TESTSET_DIR = os.path.join(
    os.path.dirname(__file__), "..", "evaluation", "testset"
)
# Folder where annotated output videos are written.
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "demo", "output")
# Colours for annotation boxes, one per detection kind (BGR order).
BOX_COLORS = {
    "motion": (200, 200, 200),
    "presence": (0, 200, 0),
    "left_object": (200, 150, 0),
    "stove_glow": (0, 100, 255),
    "fall_like": (0, 0, 255),
}

# The agent from the most recent run, kept so the acknowledge and
# false-alarm buttons act on real alert state.
LAST_AGENT = {"agent": None}


# Run the pipeline and agent over a video file, writing an annotated
# copy with detection boxes drawn on every frame.
# Returns (events, output_filename).
def analyze_video(path):
    # Open the input video for frame-by-frame reading.
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    # Fresh pipeline and agent for this run.
    sentinel = Sentinel()
    agent = HearthAgent()
    # Prepare the annotated output video (same size and frame rate).
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_name = "annotated_" + os.path.basename(path)
    out_path = os.path.join(OUTPUT_DIR, out_name)
    fps = cap.get(cv2.CAP_PROP_FPS) or 10
    writer = cv2.VideoWriter(
        out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (640, 360)
    )
    # Process every frame, drawing boxes as we go.
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        detections = sentinel.process(frame)
        agent.observe(detections)
        # Draw one box and label per detection on this frame.
        for det in detections:
            color = BOX_COLORS.get(det.kind, (255, 255, 255))
            cv2.rectangle(
                frame,
                (det.x, det.y),
                (det.x + det.w, det.y + det.h),
                color,
                2,
            )
            cv2.putText(
                frame,
                det.kind,
                (det.x, max(15, det.y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )
        writer.write(frame)
    cap.release()
    writer.release()
    # Remember this run's agent for the alert buttons.
    LAST_AGENT["agent"] = agent
    return [e.to_dict() for e in agent.events], out_name


# The demo page: plain HTML with a scene picker, a run button, an
# event table, and alert buttons. No build step, no framework.
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Hearthwatch — home-safety vision agent</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:2em auto;padding:0 1em;color:#222}
h1{font-size:1.6em} .card{border:1px solid #ccc;border-radius:8px;padding:1em;margin:1em 0}
table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:.4em;text-align:left}
.tier-escalate{background:#fde2e2}.tier-notify{background:#fff3cd}.tier-log{background:#e8f5e9}
button{padding:.5em 1em;margin-right:.5em;cursor:pointer}
video{width:100%;background:#000}
.note{color:#555;font-size:.9em}
</style></head><body>
<h1>Hearthwatch — a home-safety vision agent</h1>
<p class="note">OpenCV 5 perception + an agent loop: vision output changes what the
system does next. Test scenes are <b>synthetic</b> (drawn with OpenCV), labelled
as such. No facial recognition: people are "person-like presence" only.</p>
<div class="card">
<label>Test scene: <select id="scene"></select></label>
<button onclick="runScene()">Run the agent</button>
<span id="status"></span>
</div>
<div class="card" id="videoCard" style="display:none">
<video id="vid" controls></video>
</div>
<div class="card" id="eventsCard" style="display:none">
<h2>Events</h2><table id="events"><tr><th>Kind</th><th>Tier</th><th>Score</th><th>Detail</th><th>State</th></tr></table>
<h2>Open alerts</h2><div id="alerts"></div>
</div>
<script>
async function loadScenes(){
  const r = await fetch('/api/scenes'); const scenes = await r.json();
  const sel = document.getElementById('scene');
  scenes.forEach(s => { const o = document.createElement('option'); o.value = s.file; o.textContent = s.file + ' — ' + (s.event || 'no event'); sel.appendChild(o); });
}
async function runScene(){
  const file = document.getElementById('scene').value;
  document.getElementById('status').textContent = 'Running…';
  const r = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({file})});
  const data = await r.json();
  document.getElementById('status').textContent = data.events.length + ' events';
  document.getElementById('vid').src = '/output/' + data.video;
  document.getElementById('videoCard').style.display = 'block';
  const tbl = document.getElementById('events');
  tbl.innerHTML = '<tr><th>Kind</th><th>Tier</th><th>Score</th><th>Detail</th><th>State</th></tr>';
  data.events.forEach(e => {
    const tr = document.createElement('tr'); tr.className = 'tier-' + e.tier;
    tr.innerHTML = '<td>'+e.kind+'</td><td>'+e.tier+'</td><td>'+e.score+'</td><td>'+e.detail+'</td><td>'+e.state+'</td>';
    tbl.appendChild(tr);
  });
  const alerts = document.getElementById('alerts');
  alerts.innerHTML = '';
  data.open_alerts.forEach((a, i) => {
    const d = document.createElement('div');
    d.innerHTML = '<b>'+a.kind+'</b> ('+a.tier+'): '+a.detail+' ';
    const ack = document.createElement('button'); ack.textContent = 'Acknowledge';
    ack.onclick = async () => { await postAction('/api/acknowledge', i); runScene(); };
    const fa = document.createElement('button'); fa.textContent = 'False alarm';
    fa.onclick = async () => { await postAction('/api/false_alarm', i); runScene(); };
    d.appendChild(ack); d.appendChild(fa); alerts.appendChild(d);
  });
  if (!data.open_alerts.length) alerts.textContent = 'None open.';
  document.getElementById('eventsCard').style.display = 'block';
}
async function postAction(url, i){
  await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({index: i})});
}
loadScenes();
</script></body></html>
"""


# The HTTP request handler: routes each request to the right logic.
class Handler(BaseHTTPRequestHandler):
    # Silence the default per-request log lines.
    def log_message(self, *args):
        pass

    # Helper: send a JSON response with the given object.
    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Helper: read a JSON request body (empty body becomes {}).
    def read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length) or b"{}")

    # Handle GET requests: the page, the scene list, output videos.
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/scenes":
            # List scenes from the manifest, if it exists.
            manifest = os.path.join(TESTSET_DIR, "manifest.json")
            scenes = []
            if os.path.exists(manifest):
                with open(manifest) as f:
                    scenes = json.load(f)
            self.send_json(scenes)
        elif path.startswith("/output/"):
            # Serve an annotated video file by name only (no paths).
            name = os.path.basename(path)
            fpath = os.path.join(OUTPUT_DIR, name)
            if not os.path.exists(fpath):
                self.send_response(404)
                self.end_headers()
                return
            with open(fpath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    # Handle POST requests: run, acknowledge, false alarm.
    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/run":
            data = self.read_json()
            # Only manifest-listed scene files may be run by name,
            # so a request cannot point the server at arbitrary files.
            name = os.path.basename(data.get("file", ""))
            vpath = os.path.join(TESTSET_DIR, name)
            if not os.path.exists(vpath):
                self.send_json({"error": "unknown scene"}, 400)
                return
            try:
                events, video = analyze_video(vpath)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 500)
                return
            agent = LAST_AGENT["agent"]
            self.send_json(
                {
                    "events": events,
                    "video": video,
                    "open_alerts": (
                        [e.to_dict() for e in agent.open_alerts]
                        if agent
                        else []
                    ),
                }
            )
        elif path in ("/api/acknowledge", "/api/false_alarm"):
            data = self.read_json()
            agent = LAST_AGENT["agent"]
            if agent is None:
                self.send_json({"error": "no run yet"}, 400)
                return
            index = int(data.get("index", -1))
            if path == "/api/acknowledge":
                ok = agent.acknowledge(index)
            else:
                ok = agent.mark_false_alarm(index)
            self.send_json({"ok": ok})
        else:
            self.send_response(404)
            self.end_headers()


# Start the server when this file is executed directly.
if __name__ == "__main__":
    # Allow the port to be overridden from the command line.
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Hearthwatch demo on http://127.0.0.1:{port}/")
    server.serve_forever()
