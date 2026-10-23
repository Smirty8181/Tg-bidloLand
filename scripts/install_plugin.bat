@echo off
chcp 65001 >nul
echo.
echo === Установка BydloBridge на сервер ===
echo.
echo 1. Открой файловый менеджер:
echo    https://mgr.hosting-minecraft.pro/server/09390ef6/files#/plugins
echo.
echo 2. Нажми "Загрузить" и выбери файл:
echo    %~dp0..\plugin\build\libs\BydloBridge-1.0.0.jar
echo.
echo 3. Создай папку plugins\BydloBridge и файл config.yml:
echo    %~dp0BydloBridge\config.yml
echo.
echo 4. Перезапусти сервер (кнопка Рестарт в панели)
echo.
echo JAR также доступен по URL туннеля:
python "%~dp0print_plugin_install.py"
pause
