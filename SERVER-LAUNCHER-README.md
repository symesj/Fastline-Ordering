# 🚀 Fastline Ordering Server Launcher

This project includes several easy ways to start your servers with a single click!

## 📁 Available Launchers

### 🚀 **Main Launcher** (Recommended)
**File:** `🚀-start-servers.bat`
- **Usage:** Double-click the file
- **Features:** 
  - ✅ Checks for Python and Node.js
  - 🧹 Cleans up existing processes
  - 🎨 Colorful console output
  - ⏰ Auto-closes after 10 seconds
  - 📱 Opens separate windows for each server

### 🛑 **Server Stopper**
**File:** `🛑-stop-servers.bat`
- **Usage:** Double-click to stop all servers
- **Features:**
  - 🔍 Finds and stops all Python/Flask processes
  - 🔍 Finds and stops all Node.js/Next.js processes
  - ✅ Confirms when servers are stopped

### 📎 **Desktop Shortcuts** 
**Files:** 
- `🚀 Start Servers.lnk` (in project folder)
- `Fastline Ordering Servers.lnk` (on desktop)
- **Usage:** Double-click like any other program
- **Features:** Runs the PowerShell version with a nice icon

## 🖥️ What Gets Started

When you run any launcher, it starts:

1. **🐍 Flask API Server**
   - Port: `5000`
   - URL: http://localhost:5000
   - Handles: WhatsApp integration, GHL sync, file uploads

2. **⚛️ Next.js Frontend**
   - Port: `3000` 
   - URL: http://localhost:3000
   - Handles: Web interface, unified inbox, dashboard

## 🔧 Alternative Launchers (Advanced)

### PowerShell Version
**File:** `start-servers.ps1`
```powershell
powershell -ExecutionPolicy Bypass -File ".\start-servers.ps1"
```

### VBScript Version (Windows Native)
**File:** `start-servers.vbs`
- Double-click for a dialog-based launcher
- Works on any Windows system

### Basic Batch File
**File:** `start-servers.bat`
- Simple version without fancy formatting

## ⚙️ Manual Commands (If you prefer)

### Start Flask Server
```bash
cd flask_app
python app_orders.py
```

### Start Next.js Server
```bash
cd ghl-custom-frontend
npm run dev
```

## 🛠️ Troubleshooting

### Python Not Found
1. Install Python from https://python.org
2. Make sure "Add to PATH" is checked during installation
3. Restart your computer
4. Test: Open Command Prompt and type `python --version`

### Node.js Not Found  
1. Install Node.js from https://nodejs.org
2. Choose the LTS version
3. Restart your computer
4. Test: Open Command Prompt and type `node --version`

### Port Already in Use
If you get "port already in use" errors:
1. Run the `🛑-stop-servers.bat` to clean up
2. Wait 10 seconds
3. Try starting again

### Permission Errors
If Windows blocks the scripts:
1. Right-click the file → Properties
2. Check "Unblock" at the bottom
3. Click Apply → OK

## 🎯 Quick Start Guide

1. **For first-time users:**
   - Double-click `🚀-start-servers.bat`
   - Wait for both server windows to open
   - Go to http://localhost:3000 in your browser

2. **For daily use:**
   - Use the desktop shortcut "Fastline Ordering Servers"
   - Or double-click `🚀-start-servers.bat`

3. **To stop servers:**
   - Close the server windows, OR
   - Double-click `🛑-stop-servers.bat`

## 🌟 Pro Tips

- 📌 Pin the batch files to your taskbar for even quicker access
- 🔄 Servers auto-restart if you make code changes
- 📱 Use the unified inbox at http://localhost:3000/conversations
- 🔍 Check server logs in their respective windows for debugging

---

**Happy Coding! 🎉**

*For technical support, check the server logs in the console windows.*