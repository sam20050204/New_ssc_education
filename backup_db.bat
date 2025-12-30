@echo off
echo Creating database backup...
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
copy db.sqlite3 "backups\db_backup_%timestamp%.sqlite3"
echo Backup created: db_backup_%timestamp%.sqlite3
pause