#!/bin/bash
sudo apt-get update
sudo apt-get install -y ffmpeg
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
source venv/bin/activate
pip install -r requirements.txt
