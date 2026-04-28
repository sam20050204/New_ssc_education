#!/usr/bin/env python
"""
Quick Server Launcher
Runs Django on all network interfaces for local network access
"""

import os
import sys
import subprocess

def main():
    print("\n" + "="*60)
    print(" 🚀 SSC Education - Network Server Launcher")
    print("="*60)
    print()
    
    # Change to project directory
    project_dir = r"e:\Projects\New_ssc_education"
    os.chdir(project_dir)
    
    print(f"📁 Project Directory: {project_dir}")
    print(f"🌐 Server IP: 192.168.29.47")
    print(f"🔌 Port: 8000")
    print()
    print("📱 Access from any device on network:")
    print("   ➜ http://192.168.29.47:8000")
    print()
    print("-" * 60)
    print(" ⚠️  Make sure firewall allows port 8000!")
    print(" ℹ️  Press CTRL+C to stop the server")
    print("-" * 60)
    print()
    
    # Run server on all interfaces
    cmd = [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
