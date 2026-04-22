# 📸 Photo Backup Feature - Quick Reference

## What Changed?

Your backup system now backs up **both the database AND all student photos** in a single ZIP file!

---

## 🎯 How to Use It

### Exporting a Backup (with Photos)
1. Go to **Settings → Backup** page
2. Click **"Export Database"** button
3. Wait for the ZIP file to download (`ssc_education_backup_YYYYMMDD_HHMMSS.zip`)
4. ✅ File contains:
   - Complete database
   - All student photos from media/student_photos/

### Importing from Backup (with Photos)
1. Go to **Settings → Backup** page
2. Click **"Choose File"** or drag & drop a ZIP backup
3. Click **"Import Database"** button
4. Confirm the import in the dialog
5. ✅ System will:
   - Backup current database
   - Backup current photos
   - Extract and restore all photos
   - Merge database data
   - Refresh automatically

---

## 📋 Supported File Types

### For Import:
- ✅ **ZIP backups** (.zip) - Contains database + photos (NEW!)
- ✅ **Raw database files** (.db, .sqlite, .sqlite3) - Old backups still work

### File Size Limits:
- Maximum: **500 MB** (increased from 100 MB for large photo collections)

---

## 🛡️ Safety Features

**Automatic Backups Before Import:**
- Current database backed up as: `database_backup_before_import_{timestamp}.db`
- Current photos backed up as: `student_photos_backup_{timestamp}/`

**Data Handling:**
- Import **merges** data (updates existing, adds new)
- Not a destructive operation
- Previous state always recoverable

---

## 📁 What's Inside a ZIP Backup

```
ssc_education_backup_20260422_143022.zip
│
├── database/
│   └── db.sqlite3  ← Complete database
│
└── media/
    └── student_photos/
        ├── passport_photo_xxxxx.jpg
        ├── Andhare-Vedant.P.jpg
        ├── Chavan-Adarsh.P.jpg
        └── ... (all student photos)
```

---

## ⚡ Key Benefits

| Feature | Before | Now |
|---------|--------|-----|
| **What's Backed Up** | Database only | Database + Photos ✨ |
| **File Format** | .db file | .zip archive |
| **Restore Photos** | Manual copy needed | Automatic ✨ |
| **Restore Data** | Replace all | Merge/Update ✨ |
| **File Size Limit** | 100 MB | 500 MB ✨ |
| **Backup Safety** | Manual action | Auto before import ✨ |

---

## 🔧 Files Modified

### Backend
- **`core/views.py`**
  - `export_database()` - Now creates ZIP with photos
  - `import_database()` - Now extracts and restores photos

### Frontend  
- **`templates/core/backup.html`**
  - Updated descriptions
  - Added ZIP file support

- **`static/core/backup.js`**
  - Updated file validation (ZIP support)
  - Updated messaging
  - Increased file size limit

---

## 💡 Example Scenarios

### Scenario 1: Moving to a New Installation
```
OLD System:
├── database.sqlite3
└── media/student_photos/ (500 photos)

BACKUP:
1. Click "Export Database"
2. Download: ssc_education_backup_20260422_143022.zip

NEW System:
1. Go to Backup page
2. Upload the ZIP file
3. All photos automatically restored! ✅
4. All data merged! ✅
```

### Scenario 2: Regular Data Backup
```
Monday: Export → ssc_education_backup_Monday.zip
Wednesday: Export → ssc_education_backup_Wednesday.zip
Friday: Export → ssc_education_backup_Friday.zip

(Each backup has full data + photos)
```

### Scenario 3: Using Old Backups
```
Have an old database file? 
→ Still works! Upload .db file
→ Data merges properly
→ Photos won't be restored (if not in backup)
```

---

## 🚀 Next Steps

1. **Test Export**: Click "Export Database" button to create a ZIP backup
2. **Verify ZIP**: Check that the downloaded file contains both database and photos
3. **Test Import**: Try importing the ZIP to ensure photos are restored
4. **Regular Backups**: Set a schedule to regularly export backups

---

## ❓ FAQ

**Q: Will importing a backup replace my current data?**
A: No! It merges data. Existing records are updated, new ones are added.

**Q: What if I have photos in a backup but not in the ZIP structure?**
A: They won't be restored, but the database will still import correctly.

**Q: Can I import old database backups (.db files)?**
A: Yes! Full backward compatibility. Photos won't be restored unless they're in a ZIP.

**Q: How do I recover if something goes wrong during import?**
A: A backup of your current data is created before import. Look for files like `database_backup_before_import_*.db` and `student_photos_backup_*/`

**Q: Is there a size limit?**
A: Max 500 MB per backup file (supports large photo collections).

---

**Version**: 2.0 (Photo Backup Support)
**Date**: April 22, 2026
