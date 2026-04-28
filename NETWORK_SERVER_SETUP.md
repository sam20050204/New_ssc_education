# 🌐 Network Server Setup Guide - SSC Education Project

## Overview
This guide will help you run the Django project as a network server so that other devices on the same network can access it.

---

## ✅ Server Information

**Server Machine IP Address:** `192.168.29.47`  
**Network Port:** `8000`  
**Full Server URL:** `http://192.168.29.47:8000`

---

## 🚀 Step 1: Configuration (Already Done!)

Your `.env` file has been configured with:
- `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.29.47,192.168.29.*`
- This allows connections from:
  - Localhost (the server machine itself)
  - Your server IP (192.168.29.47)
  - Any device on your network (192.168.29.*)

---

## 📋 Step 2: Start the Django Development Server

Open PowerShell in your project directory and run:

```powershell
cd e:\Projects\New_ssc_education
python manage.py runserver 0.0.0.0:8000
```

**Important:** Use `0.0.0.0` instead of `localhost` - this makes the server listen on ALL network interfaces.

### Expected Output:
```
System check identified no issues (0 silenced).
April 28, 2026 - 12:00:00
Django version 6.0.1, using settings 'Project.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

---

## 🔌 Step 3: Allow Firewall Access (Windows)

### Option A: Temporary (Just for Testing)
Run PowerShell as Administrator and execute:

```powershell
netsh advfirewall firewall add rule name="Django Port 8000" dir=in action=allow protocol=tcp localport=8000
```

### Option B: Windows Defender Firewall GUI
1. Open **Windows Defender Firewall** → **Allow an app through firewall**
2. Click **Change settings** (requires admin)
3. Click **Allow another app**
4. Browse to your Python installation (usually `C:\Users\[Username]\AppData\Local\Programs\Python\Python314\python.exe`)
5. Select it and click **Add**
6. Make sure port **8000** is allowed

### Option C: Use Another Approach
If using a specific Python virtual environment:
```powershell
# Allow Python.exe through firewall
netsh advfirewall firewall add rule name="Python Django Server" dir=in action=allow program="C:\path\to\python.exe" enable=yes
```

---

## 💻 Step 4: Access from Other Devices on Network

Once the server is running, other devices can access it using:

### From Web Browser:
```
http://192.168.29.47:8000
```

### From Command Line (Windows):
```powershell
# Test connectivity
ping 192.168.29.47

# Access via curl
curl http://192.168.29.47:8000
```

### From Other Devices:
1. **Windows PC:** Open browser → Enter `http://192.168.29.47:8000`
2. **Mac:** Open browser → Enter `http://192.168.29.47:8000`
3. **Mobile (Android/iOS):** Open browser → Enter `http://192.168.29.47:8000`
4. **Linux:** `curl http://192.168.29.47:8000` or open browser

---

## 🔍 Step 5: Troubleshooting

### ❌ Problem: "Connection refused" from other device

**Solution 1: Check firewall is allowing port 8000**
```powershell
# Check if port 8000 is listening
netstat -ano | findstr ":8000"
```

**Solution 2: Verify server is running**
- Check the PowerShell window on your server machine
- You should see "Starting development server at http://0.0.0.0:8000/"

**Solution 3: Check network connectivity**
```powershell
# Ping server from another device
ping 192.168.29.47
```

### ❌ Problem: Server says "Invalid HTTP_HOST header"

**Solution:** This means ALLOWED_HOSTS isn't configured correctly
- Check your `.env` file includes: `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.29.47,192.168.29.*`
- Restart the Django server

### ❌ Problem: Changed IP Address (DHCP)

If your server got a new IP:
1. Run `ipconfig` again to find new IP
2. Update `.env` file with new IP
3. Update `ALLOWED_HOSTS`
4. Restart server

---

## 🛡️ Production Deployment (Not Development)

For actual production deployment, use a production server like:

```powershell
# Install Gunicorn (if not already installed)
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 Project.wsgi:application
```

Or use Windows Service installer:
```powershell
# Install NSSM (Non-Sucking Service Manager)
# Then run Django as Windows Service
```

---

## 📊 Network Diagram

```
┌─────────────────────────────────────────────┐
│     Your Server (192.168.29.47)             │
│     ┌────────────────────────────────────┐  │
│     │  Django App (Port 8000)             │  │
│     │  - New Admission                    │  │
│     │  - Enquiries                        │  │
│     │  - Admitted Students                │  │
│     │  - Fee Tracking                     │  │
│     └────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
            ▲              ▲              ▲
            │              │              │
    ┌───────┴──┐   ┌───────┴──┐  ┌───────┴──┐
    │ Device 1 │   │ Device 2 │  │ Device 3 │
    │ (Mobile) │   │ (Tablet) │  │   (PC)   │
    └──────────┘   └──────────┘  └──────────┘
    
    All devices access: http://192.168.29.47:8000
```

---

## ⚠️ Important Notes

1. **Development Only:** This setup is for development/testing on a local network
2. **Security:** Don't use this in production with sensitive data
3. **Network Required:** All devices must be on same WiFi/network as server
4. **Port 8000:** Make sure nothing else is using this port
5. **Server Must Be Running:** Keep the PowerShell window open while users are accessing

---

## 🎯 Quick Start Checklist

- [ ] Server IP is `192.168.29.47` ✓
- [ ] `.env` file is configured ✓
- [ ] Firewall allows port 8000
- [ ] Run: `python manage.py runserver 0.0.0.0:8000`
- [ ] Test from another device: `http://192.168.29.47:8000`
- [ ] Everything working? Share this URL with your network users!

---

## 📞 Still Having Issues?

1. Check server is running (PowerShell window visible)
2. Verify firewall allows port 8000
3. Confirm device is on same network (same WiFi)
4. Try accessing from browser on server machine first: `http://localhost:8000`
5. Check ALLOWED_HOSTS in `.env` includes your IP

---

**Last Updated:** April 28, 2026  
**Project:** New SSC Education System
