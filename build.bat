@echo off
echo Сборка AI Video Clipper...
echo.

echo Очистка предыдущих сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo Установка зависимостей...
pip install -r requirements.txt

echo Сборка EXE файла...
pyinstaller --onefile --windowed --name "AI_Video_Clipper" --icon=icon.ico main.py

echo.
echo Готово! EXE файл находится в папке dist/
pause