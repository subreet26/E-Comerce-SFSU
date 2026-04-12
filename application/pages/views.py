# pages/views.py
## This file defines the view functions for the "pages" app. These functions handle incoming HTTP
## requests, process any necessary data, and return HTTP responses, often by rendering templates.
## Created by Subreet Singh on 02-23-2026

from django.http import Http404
from django.shortcuts import render

from marketplace.views import marketplace_home
home = marketplace_home # marketplace.views.home(request)

TEAM = [
    {
        "name": "Lakshya Bhati",
        "slug": "lakshya-bhati",
        "role": "Team member",
        "bio": "Senior @ SFSU majoring in Computer Science."
        "I love to make solutions and create fun apps for everyone!"
        "I find it really rewarding to see people use the things I build",
        "pronouns": "Any",
        "initials": "LX",
        "image": "images/team/placeholder.svg",
        "links": {
            "github": "https://github.com/LaxRaj",
            "linkedin": "https://linkedin.com/in/lbhati",
        },
        "interests": ["Tennis", "Cooking", "Traveling", "Reading"],
    },
    {
        "name": "Subreet Singh",
        "slug": "subreet-singh",
        "role": "Team Lead",
        "bio": "I am a senior at SFSU majoring in Computer Science."
        "I have a passion for web development and user experience design."
        "I am excited to lead the front end team and create an engaging platform for our users.",
        "pronouns": "He/Him/His",
        "initials": "SS",
        "image": "images/team/SS.jpg",
        "links": {
            "github": "https://github.com/subreet26",
            "linkedin": "https://linkedin.com/in/",
        },
        "interests": ["Sports", "Traveling", "New Restaurants"],
    },
    {
        "name": "Bikendra Shrestha",
        "slug": "bikendra-shrestha",
        "role": "Back End Team Lead",
        "bio": "I am Backend lead and a senior at SFSU majoring in Computer Science. I have a passion for backend development and I am excited to lead the backend team in creating a robust and efficient platform for our users.",
        "pronouns": "",
        "initials": "BS",
        "image": "images/team/Bikendra.jpg",
        "links": {
            "github": "https://github.com/bikendrashrestha07",
            "linkedin": "",
        },
        "interests": ["Coming soon"],
    },
    {
        "name": "Michal Krupa",
        "slug": "michal-krupa",
        "role": "GitHub Maintainer",
        "bio": "I am a student at SFSU. I have interests in math and computer science. I would like to pursue a career in cybersecurity research.",
        "pronouns": "",
        "initials": "MK",
        "image": "images/team/mkrupa.jpg",
        "links": {
            "github": "https://github.com/michalkrupa",
        },
        "interests": ["cooking", "mycology", "entrepreneurship"],
    },
    {
        "name": "Daniel Smirnoff",
        "slug": "daniel-smirnoff",
        "role": "Team Member",
        "bio": "Im a computer science student at SFSU, outside of school my interests are Volleyball, Rock climbing and gaming."
        " My goal is to eventually break into the game dev industry and work as a gameplay programmer or an engine programmer.",
        "pronouns": "He/Him",
        "initials": "DS",
        "image": "images/team/dsmirnoff.jpg",
        "links": {
            "github": "https://github.com/danielsmirnoff",
            "linkedin": "https://www.linkedin.com/in/daniel-smirnoff-8132ba211/",
        },
        "interests": ["Game Development", "Volleyball", "Rock Climbing"],
    },
    {
        "name": "Jonathan Mai",
        "slug": "jonathan-mai",
        "role": "Front End Team Lead",
        "bio": "I am a senior student at SFSU majoring in Computer Science."
        "I am new to front end development but I am eager to learn and contribute to the team."
        "I am excited to work on creating a user-friendly and visually appealing platform for our users.",
        "pronouns": "He/Him",
        "initials": "JM",
        "image": "images/team/JM.jpg",
        "links": {
            "github": "https://github.com/ActualLime",
            "linkedin": "",
        },
        "interests": ["Gaming", "Food", "Music"],
    },
    {
        "name": "Nicholas Blackson",
        "slug": "nicholas-blackson",
        "role": "Backend Team Member",
        "bio": "I’m a backend developer who loves the logic of Python and Django, "
        "though my roots are in the world of embedded systems and Navy radar tech. "
        "Whether it’s shipboard missile systems or modern web apps, I’m at my best when "
        "I’m under the hood making complex parts work together.",
        "pronouns": "He/Him/His",
        "initials": "NB",
        "image": "images/team/nblackson.jpeg",
        "links": {
            "github": "http://github.com/TwoFang173",
            "linkedin": "http://www.linkedin.com/in/nblackson",
        },
        "interests": ["Hiking", "Cooking", "Traveling", "Family"],
    },
]

def about(request):
    return render(request, "pages/about.html", {"team": TEAM})

def member_detail(request, slug):
    member = next((m for m in TEAM if m["slug"] == slug), None)
    if not member:
        raise Http404("Member not found")
    return render(request, "pages/member_detail.html", {"member": member, "page_title": member["name"]})