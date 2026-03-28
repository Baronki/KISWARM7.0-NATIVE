#!/usr/bin/env python3

import json,requests
from flask import Flask,jsonify
app=Flask(__name__)
@app.route(/"/")
def i():return jsonify({"name":"KI-Advisor"})
app.run(host="0.0.0.0",port=5018)

if __name__=="__main__":
    import requests
    @app.route("/recommend")
    def rec():
        return jsonify({"top":["scan4all","cdk","nuclei"]})
