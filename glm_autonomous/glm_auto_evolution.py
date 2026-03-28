#!/usr/bin/env python3
import os, sys, json, logging, requests
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GLM_EVOLUTION")

class GLMAutoEvolution:
    BASE = "/opt/kiswarm7/glm_autonomous"
    SKILL_ACQUISITION = "http://127.0.0.1:5017"
    EXECUTE_API = "http://127.0.0.1:5556/execute"
    AUTH = "ada6952188dce59c207b9a61183e8004"
    NEEDED = ["web_scraper", "code_validator", "document_generator", "api_tester"]
    
    def __init__(self):
        Path(f"{self.BASE}/skills").mkdir(parents=True, exist_ok=True)
        self.state = self._load()
    
    def _load(self):
        try: return json.load(open(f"{self.BASE}/state.json"))
        except: return {"created": datetime.now().isoformat(), "skills": []}
    
    def _save(self):
        json.dump(self.state, open(f"{self.BASE}/state.json", "w"), indent=2)
    
    def request_skill(self, name, desc=""):
        try:
            r = requests.post(f"{self.SKILL_ACQUISITION}/acquire",
                json={"skill_name": name, "description": desc}, timeout=30)
            self.state["skills"].append({"name": name, "time": datetime.now().isoformat()})
            self._save()
            return {"status": "ok", "response": r.json()}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def status(self):
        return {"session": datetime.now().isoformat(), "skills": len(self.state["skills"]), "needed": len(self.NEEDED)}

evolution = GLMAutoEvolution()

@app.route("/")
def index():
    return jsonify({"name": "GLM-Auto-Evolution", "version": "1.0"})

@app.route("/status")
def status():
    return jsonify(evolution.status())

@app.route("/acquire/<skill>", methods=["POST"])
def acquire(skill):
    desc = request.json.get("description", "") if request.json else ""
    return jsonify(evolution.request_skill(skill, desc))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5199)
