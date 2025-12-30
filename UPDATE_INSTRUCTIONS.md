# Update Instructions for Clients

## Before Updating:
1. ✅ Stop the application
2. ✅ Backup your database: Run `backup_db.bat`
3. ✅ Note current version number

## Update Process:
1. Open command prompt in project folder
2. Run: `git pull origin main`
3. Run: `python manage.py migrate`
4. Restart application: `ssceducations.bat`

## If Something Goes Wrong:
1. Stop the application
2. Restore backup: `copy backups\db_backup_YYYYMMDD.sqlite3 db.sqlite3`
3. Contact support

## Safety Notes:
- ✅ Your data is safe - migrations only update database structure
- ✅ Student records, fees, receipts remain unchanged
- ✅ Photos and media files are not affected