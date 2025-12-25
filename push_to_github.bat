@echo off
echo --- Guardando cambios locales ---
git add .
git commit -m "Update from local PC"
echo.
echo --- Bajando cambios desde GitHub (Sincronizando) ---
git pull --rebase --autostash
echo.
echo --- Subiendo cambios finales ---
git push
echo.
echo --- Completado! ---
pause
