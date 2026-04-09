# Application Folder

## Purpose
The purpose of this folder is to store all the source code and related files for your team's application. Source code MUST NOT be in any of folder. <strong>YOU HAVE BEEN WARNED</strong>

You are free to organize the contents of the folder as you see fit. But remember your team is graded on how you use Git. This does include the structure of your application. Points will be deducted from poorly structured application folders.

## Please use the rest of the README.md to store important information for your team's application.



# Local Setup

# Go to dev branch
git checkout dev
git pull

# If working on new feature
create new branch ex. feature/frontend/login

# Go to end app folder
cd application

# Vitualization 
python3 -m venv .venv

# Activate
source .venv/bin/activate

# MUST USE donwload exact versions
pip install -r requirements.txt

# Server
python manage.py migrate

# Server run local
python manage.py runserver

# Visit the local website
http://127.0.0.1:8000/

# Test code
please ensure your code is working locally

# push code
Please push code only to a feature branch
you are allowed to mess up a feature branch as much as you want

# merge code 
do a pr request from your feature branch into dev
2 people will need to test your code to verify it works

# Server changes
will only be done by leads



