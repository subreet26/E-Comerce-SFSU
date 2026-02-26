# Local Setup

# Go to dev branch
git checkout dev
git pull

# Go to front end team pages branch
git checkout feature/frontend-team-pages

# Go to front end app folder
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

# Visit the website
http://127.0.0.1:8000/

# Please go to 
application/pages/views.py
## then enter your about me information

# Add image into 
application/static/images/team/
## Then replace your image field in views.py to match the filename



