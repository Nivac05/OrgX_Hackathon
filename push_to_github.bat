@echo off
git init
git add .
git commit -m "Upload everything"
git remote add origin https://github.com/Nivac05/OrgX_Hackathon.git
git branch -M main
git push -u origin main --force
