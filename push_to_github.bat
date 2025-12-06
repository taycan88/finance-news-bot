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
git commit -m "Sync fixes: 2h frequency and URL deduplication"

:: Push with force to ensure cloud matches local code exactly
git push -u origin main --force

echo.
echo Done!
pause
