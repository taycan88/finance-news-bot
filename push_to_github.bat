@echo off
echo --- Finance News Bot Helper ---
echo.
echo Syncing and Pushing changes to GitHub...
echo.

:: Ensure git is initialized
if not exist .git (
    git init
    git branch -M main
    git remote add origin https://github.com/taycan88/finance-news-bot.git
)

:: Force rename branch to main just in case
git branch -M main

:: Add all files
git add .

:: Commit
git commit -m "Improve time filtering (last 2.5h) and robust date parsing"

:: Push with force to ensure cloud matches local code exactly
git push -u origin main --force

echo.
echo Done!
git add .
git commit -m "Fix GitHub Actions: Remove stateful commit and fix indentation"
git push

echo.
echo Fixed and Pushed!
pause
