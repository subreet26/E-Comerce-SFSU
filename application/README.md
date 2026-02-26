# Local Setup

# Go to front end folder
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

# Please go to application/pages/views.py
## then enter your about me information
### Add image into static/images/team
#### Then replace views.py with your image