@echo off
echo --- Finance News Bot Helper ---
echo.
echo Pushing changes to GitHub...
echo.

git add .
git commit -m "Fix duplicate news by using URL as key"
git push

echo.
echo Done!
pause
