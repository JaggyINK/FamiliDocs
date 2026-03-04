@echo off
echo ========================================
echo   FamiliDocs - Creation de l'executable
echo   Version Desktop Native (sans navigateur)
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate

REM Installer les dependances si necessaire
echo [1/4] Verification des dependances...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installation de PyInstaller...
    pip install pyinstaller
)
pip show customtkinter >nul 2>&1
if %errorlevel% neq 0 (
    echo Installation de CustomTkinter...
    pip install customtkinter
)
pip show pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo Installation de Pillow...
    pip install pillow
)

REM Nettoyer les anciennes builds
echo [2/4] Nettoyage des anciennes builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Construire l'executable
echo [3/4] Construction de l'executable...
echo.
pyinstaller --onefile --windowed ^
    --name "FamiliDocs" ^
    --add-data "app/templates;app/templates" ^
    --add-data "app/static;app/static" ^
    --hidden-import flask ^
    --hidden-import flask_login ^
    --hidden-import flask_sqlalchemy ^
    --hidden-import flask_wtf ^
    --hidden-import sqlalchemy ^
    --hidden-import sqlalchemy.sql.default_comparator ^
    --hidden-import sqlalchemy.ext.baked ^
    --hidden-import sqlalchemy.pool ^
    --hidden-import werkzeug ^
    --hidden-import werkzeug.security ^
    --hidden-import jinja2 ^
    --hidden-import bcrypt ^
    --hidden-import email_validator ^
    --hidden-import wtforms ^
    --hidden-import cryptography ^
    --hidden-import cryptography.fernet ^
    --hidden-import dotenv ^
    --hidden-import schedule ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import app ^
    --hidden-import app.models ^
    --hidden-import app.models.user ^
    --hidden-import app.models.document ^
    --hidden-import app.models.folder ^
    --hidden-import app.models.task ^
    --hidden-import app.models.family ^
    --hidden-import app.models.notification ^
    --hidden-import app.models.permission ^
    --hidden-import app.models.log ^
    --hidden-import app.models.tag ^
    --hidden-import app.models.message ^
    --hidden-import app.models.document_version ^
    --hidden-import app.services.encryption_service ^
    --hidden-import app.services.scheduler_service ^
    --hidden-import app.services.notification_service ^
    --hidden-import app.services.document_service ^
    --hidden-import app.services.backup_service ^
    --hidden-import app.services.permission_service ^
    --hidden-import app.services.auth_service ^
    --hidden-import app.services.search_service ^
    --collect-all customtkinter ^
    desktop_app.py

echo.
echo [4/4] Verification...
if exist "dist\FamiliDocs.exe" (
    echo.
    echo ========================================
    echo   BUILD REUSSI !
    echo ========================================
    echo.
    echo   L'executable se trouve dans:
    echo   dist\FamiliDocs.exe
    echo.
    echo   C'est une APPLICATION DESKTOP NATIVE
    echo   [pas de navigateur, fenetre autonome]
    echo.
    echo   Les donnees seront stockees dans:
    echo   %%USERPROFILE%%\.familidocs
    echo.
    echo ========================================
    echo.
    pause
    exit /b 0
)

echo.
echo ========================================
echo   ERREUR lors de la creation
echo ========================================
echo   Verifiez les messages ci-dessus.
echo.
pause
exit /b 1
