# Database & Photos Backup Enhancements

## Summary
The backup system has been enhanced to automatically backup both the database AND all student photos together when exporting, and restore both when importing.

---

## Changes Made

### 1. **Backend Changes** (`core/views.py`)

#### Export Function (Lines 2018-2064)
- **Before**: Exported only the SQLite database file (.db)
- **After**: Creates a ZIP archive containing:
  - Database file (in `database/` folder)
  - All student photos (from `media/student_photos/`)
- **Filename**: `ssc_education_backup_{timestamp}.zip`
- **Benefits**: Single file backup with all data

#### Import Function (Lines 2066-2235)
- **Before**: Accepted only raw database files (.db, .sqlite, .sqlite3)
- **After**: 
  - Accepts both ZIP backups and raw database files
  - Automatically extracts and restores photos from ZIP files
  - Creates backup of current photos before importing
  - Merges/updates data instead of replacing
- **File Size Limit**: Increased from 100 MB to 500 MB (to accommodate photos)
- **Features**:
  - Backup of current database before import
  - Backup of current photos before import
  - Automatic photo extraction and restoration from ZIP
  - Safe merge operation with transaction support

---

### 2. **Frontend Changes** (`templates/core/backup.html`)

#### Export Section
- Updated "What will be exported" to include:
  - ✅ **📸 All student photos** (new)
  - Database file
  - All other records
- Updated "File Format" from SQLite (.db) to Compressed ZIP Archive (.zip)

#### Import Section
- Updated warning text from "replace all current data" to "merge and update your existing data"
- Updated "Supported Files" to:
  - ZIP backups (.zip) - with database + photos
  - Raw database files (.db, .sqlite, .sqlite3)
- Updated file input `accept` attribute to include `.zip`
- Updated max file size from 100 MB to 500 MB

---

### 3. **JavaScript Changes** (`static/core/backup.js`)

#### File Validation
- Added `.zip` to valid file extensions
- Increased max file size validation from 100 MB to 500 MB

#### Export Messages
- Updated loading message: "⏳ Exporting database..." → "⏳ Exporting database and photos..."
- Updated success message: "Database exported successfully!" → "Database and photos exported successfully!"
- Updated default filename: `database_backup.db` → `ssc_education_backup.zip`

#### Import Validation
- Added `application/zip` to valid MIME types

---

## How It Works

### Exporting Backup
1. User clicks "Export Database" button
2. System creates ZIP file containing:
   - Database file
   - All student photos from media/student_photos folder
3. ZIP is downloaded as `ssc_education_backup_{timestamp}.zip`

### Importing Backup
1. User selects a ZIP backup file
2. System detects it's a ZIP file
3. Performs these steps:
   - Creates backup of current database: `database_backup_before_import_{timestamp}.db`
   - Creates backup of current photos: `student_photos_backup_{timestamp}/`
   - Extracts database from ZIP
   - Extracts all photos from ZIP and restores them to `media/student_photos/`
   - Merges database data (inserts new records, updates existing ones)
   - Returns success message

---

## Backup Strategy

### What Gets Backed Up
✅ **Database**: All student records, fees, courses, enquiries, etc.
✅ **Photos**: All student passport photos from media/student_photos folder
✅ **Safe**: Automatic backups of current data before any import

### Restore Features
- **Merge, Not Replace**: Existing records are updated, new ones are added
- **Photo Restoration**: Photos are extracted and placed back in correct location
- **Rollback Safety**: Previous database and photos backed up before any changes

---

## File Structure in ZIP Archive

```
ssc_education_backup_YYYYMMDD_HHMMSS.zip
├── database/
│   └── db.sqlite3
└── media/
    └── student_photos/
        ├── passport_photo_xxxxx.jpg
        ├── Andhare-Vedant.P.jpg
        ├── Chavan-Adarsh.P.jpg
        └── ... (all student photos)
```

---

## Backward Compatibility

✅ **Still Supports Old Database Files**: If users have old `.db` backups, they can still import them (photos won't be restored, but database will merge)

---

## Technical Details

### Imports Used
- `zipfile`: For creating and extracting ZIP archives
- `tempfile`: For safe temporary file handling
- `io.BytesIO`: For in-memory ZIP creation
- `shutil`: For file/folder operations

### Transaction Safety
- Uses `transaction.atomic()` for safe database operations
- Proper cleanup of temporary files
- Backup of current state before any changes

---

## Testing Recommendations

1. **Export Test**: 
   - Click "Export Database"
   - Verify ZIP file is created with photos and database

2. **Import Test (ZIP)**:
   - Upload the ZIP backup
   - Verify photos are restored
   - Verify data is merged correctly

3. **Import Test (Old .db file)**:
   - Upload an old database file
   - Verify it still works (backward compatibility)

4. **File Size Test**:
   - Try uploading a large ZIP (up to 500 MB)

---

## Future Enhancements

Possible improvements:
- Add progress bar for large backup exports
- Allow selective photo backup (exclude some photos)
- Scheduled automatic backups
- Cloud storage integration
- Backup version history

---

**Date**: April 22, 2026
**Version**: 2.0 (with photo support)
