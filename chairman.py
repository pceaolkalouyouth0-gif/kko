#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           BOT MANAGEMENT SYSTEM - CHAIRMAN OS                    ║
║                   Version 4.0 - With Updates                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path("/root/clients")
CONFIG_FILE = Path("/root/bot-manager/clients.json")
BOT_REPO = "https://github.com/glen129/chairman.git"
BACKUP_DIR = Path("/root/backups")

# Files and folders to preserve during updates (sessions, configs, data)
PRESERVE_ITEMS = [
    "session",
    "auth_info",
    "auth_info_baileys",
    ".wwebjs_auth",
    "creds.json",
    "config.js",
    "config.json",
    ".env",
    "database",
    "database.json",
    "data",
    "store",
    "baileys_store.json",
    "baileys_store_multi.json",
    "sessions",
    "temp",
]

# Colors
class C:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def clear():
    os.system('clear')

def banner():
    clear()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════════════════╗
║{C.YELLOW}  ██████╗██╗  ██╗ █████╗ ██╗██████╗ ███╗   ███╗ █████╗ ███╗   ██╗ {C.CYAN}║
║{C.YELLOW} ██╔════╝██║  ██║██╔══██╗██║██╔══██╗████╗ ████║██╔══██╗████╗  ██║ {C.CYAN}║
║{C.YELLOW} ██║     ███████║███████║██║██████╔╝██╔████╔██║███████║██╔██╗ ██║ {C.CYAN}║
║{C.YELLOW} ██║     ██╔══██║██╔══██║██║██╔══██╗██║╚██╔╝██║██╔══██║██║╚██╗██║ {C.CYAN}║
║{C.YELLOW} ╚██████╗██║  ██║██║  ██║██║██║  ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║ {C.CYAN}║
║{C.YELLOW}  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ {C.CYAN}║
╠══════════════════════════════════════════════════════════════════╣
║{C.WHITE}              BOT MANAGEMENT SYSTEM v4.0                          {C.CYAN}║
╚══════════════════════════════════════════════════════════════════╝{C.END}
""")

def menu():
    print(f"""
{C.GREEN}┌────────────────────────────────────────────────────────────────┐
│                         MAIN MENU                              │
├────────────────────────────────────────────────────────────────┤{C.END}
│  {C.YELLOW}[1]{C.END}  👤 Add New Client (Setup + Run)                         │
│  {C.YELLOW}[2]{C.END}  📋 View All Clients                                     │
│  {C.YELLOW}[3]{C.END}  ▶️  Start Client (PM2 Background)                        │
│  {C.YELLOW}[4]{C.END}  ⏹️  Stop Client                                          │
│  {C.YELLOW}[5]{C.END}  🔄 Restart Client                                        │
│  {C.YELLOW}[6]{C.END}  ▶️  Start ALL Bots                                       │
│  {C.YELLOW}[7]{C.END}  ⏹️  Stop ALL Bots                                        │
│  {C.YELLOW}[8]{C.END}  📊 PM2 Status                                           │
│  {C.YELLOW}[9]{C.END}  📜 View Logs                                            │
│  {C.YELLOW}[10]{C.END} 🔧 Run Client Interactively (node index.js)             │
│  {C.YELLOW}[11]{C.END} 🗑️  Delete Client                                        │
│  {C.YELLOW}[12]{C.END} 💾 Backup Sessions                                      │
{C.GREEN}├────────────────────────────────────────────────────────────────┤{C.END}
│  {C.CYAN}[13]{C.END} 🔄 Update Single Client (Keep Session)                   │
│  {C.CYAN}[14]{C.END} 🔄 Update ALL Clients (Keep Sessions)                    │
│  {C.CYAN}[15]{C.END} 📥 Check for Updates                                     │
{C.GREEN}├────────────────────────────────────────────────────────────────┤{C.END}
│  {C.YELLOW}[0]{C.END}  🚪 Exit                                                 │
{C.GREEN}└────────────────────────────────────────────────────────────────┘{C.END}
""")

def load_clients():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"clients": []}

def save_clients(data):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_status(name):
    result = os.popen(f"pm2 jlist 2>/dev/null").read()
    try:
        processes = json.loads(result)
        for p in processes:
            if p.get('name') == name:
                return p.get('pm2_env', {}).get('status', 'unknown')
    except:
        pass
    return 'stopped'

def pause():
    input(f"\n{C.YELLOW}Press Enter to continue...{C.END}")

def select_client():
    data = load_clients()
    if not data['clients']:
        print(f"{C.YELLOW}No clients found. Add one first!{C.END}")
        return None
    
    print(f"\n{C.CYAN}Select a client:{C.END}\n")
    for i, client in enumerate(data['clients'], 1):
        status = get_status(client['username'])
        icon = "🟢" if status == "online" else "🔴"
        print(f"  [{i}] {icon} {client['username']}")
    print(f"  [0] Cancel")
    
    try:
        choice = int(input(f"\n{C.YELLOW}Enter number: {C.END}"))
        if choice == 0:
            return None
        if 1 <= choice <= len(data['clients']):
            return data['clients'][choice - 1]
    except:
        pass
    print(f"{C.RED}Invalid choice!{C.END}")
    return None

def get_local_version(client_dir):
    """Get local bot version from package.json or settings.js"""
    package_path = Path(client_dir) / "package.json"
    settings_path = Path(client_dir) / "settings.js"
    
    # Try package.json first
    if package_path.exists():
        try:
            with open(package_path, 'r') as f:
                data = json.load(f)
                return data.get('version', 'unknown')
        except:
            pass
    
    # Try settings.js
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
                import re
                match = re.search(r'version["\']?\s*[:=]\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        except:
            pass
    
    return 'unknown'

def get_remote_version():
    """Get latest version from GitHub"""
    import urllib.request
    try:
        # Try to get package.json from GitHub
        raw_url = BOT_REPO.replace('github.com', 'raw.githubusercontent.com').replace('.git', '') + '/main/package.json'
        with urllib.request.urlopen(raw_url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('version', 'unknown')
    except:
        try:
            # Try master branch
            raw_url = BOT_REPO.replace('github.com', 'raw.githubusercontent.com').replace('.git', '') + '/master/package.json'
            with urllib.request.urlopen(raw_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data.get('version', 'unknown')
        except:
            return 'unknown'

# ═══════════════════════════════════════════════════════════════
# UPDATE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def backup_preserved_items(client_dir, backup_path):
    """Backup session files and important data before update"""
    client_dir = Path(client_dir)
    backup_path = Path(backup_path)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    backed_up = []
    
    for item in PRESERVE_ITEMS:
        source = client_dir / item
        if source.exists():
            dest = backup_path / item
            try:
                if source.is_dir():
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
                backed_up.append(item)
            except Exception as e:
                print(f"  {C.YELLOW}⚠️ Could not backup {item}: {e}{C.END}")
    
    return backed_up

def restore_preserved_items(backup_path, client_dir):
    """Restore session files and important data after update"""
    backup_path = Path(backup_path)
    client_dir = Path(client_dir)
    
    restored = []
    
    for item in PRESERVE_ITEMS:
        source = backup_path / item
        if source.exists():
            dest = client_dir / item
            try:
                # Remove new version's file/folder if exists
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                
                # Restore from backup
                if source.is_dir():
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
                restored.append(item)
            except Exception as e:
                print(f"  {C.YELLOW}⚠️ Could not restore {item}: {e}{C.END}")
    
    return restored

def update_single_client(client, auto_restart=True):
    """Update a single client while preserving session"""
    username = client['username']
    client_dir = Path(client['directory'])
    
    print(f"\n{C.CYAN}{'═' * 60}{C.END}")
    print(f"{C.CYAN}  Updating: {username}{C.END}")
    print(f"{C.CYAN}{'═' * 60}{C.END}\n")
    
    # Check if directory exists
    if not client_dir.exists():
        print(f"{C.RED}❌ Client directory not found: {client_dir}{C.END}")
        return False
    
    # Get current version
    current_version = get_local_version(client_dir)
    print(f"  Current version: {C.YELLOW}{current_version}{C.END}")
    
    # Check if bot was running
    was_running = get_status(username) == 'online'
    
    # Step 1: Stop the bot if running
    if was_running:
        print(f"\n{C.YELLOW}[1/6] Stopping bot...{C.END}")
        os.system(f"pm2 stop {username} 2>/dev/null")
        print(f"  {C.GREEN}✅ Stopped{C.END}")
    else:
        print(f"\n{C.YELLOW}[1/6] Bot not running, skipping stop{C.END}")
    
    # Step 2: Backup session and important files
    print(f"\n{C.YELLOW}[2/6] Backing up session & data...{C.END}")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_backup = BACKUP_DIR / f"temp_update_{username}_{timestamp}"
    
    backed_up = backup_preserved_items(client_dir, temp_backup)
    if backed_up:
        print(f"  {C.GREEN}✅ Backed up: {', '.join(backed_up)}{C.END}")
    else:
        print(f"  {C.YELLOW}⚠️ No session files found to backup{C.END}")
    
    # Step 3: Create full backup (safety)
    print(f"\n{C.YELLOW}[3/6] Creating safety backup...{C.END}")
    safety_backup = BACKUP_DIR / f"full_backup_{username}_{timestamp}"
    try:
        shutil.copytree(client_dir, safety_backup)
        print(f"  {C.GREEN}✅ Full backup: {safety_backup}{C.END}")
    except Exception as e:
        print(f"  {C.YELLOW}⚠️ Could not create full backup: {e}{C.END}")
    
    # Step 4: Remove old files and clone fresh
    print(f"\n{C.YELLOW}[4/6] Downloading latest version...{C.END}")
    
    # Remove old directory
    try:
        shutil.rmtree(client_dir)
    except Exception as e:
        print(f"  {C.RED}❌ Could not remove old files: {e}{C.END}")
        # Restore from safety backup
        if safety_backup.exists():
            shutil.copytree(safety_backup, client_dir)
        return False
    
    # Clone fresh
    result = os.system(f"git clone {BOT_REPO} {client_dir} 2>&1")
    if result != 0:
        print(f"  {C.RED}❌ Clone failed! Restoring from backup...{C.END}")
        if safety_backup.exists():
            shutil.copytree(safety_backup, client_dir)
        return False
    print(f"  {C.GREEN}✅ Downloaded latest version{C.END}")
    
    # Step 5: Restore session and important files
    print(f"\n{C.YELLOW}[5/6] Restoring session & data...{C.END}")
    restored = restore_preserved_items(temp_backup, client_dir)
    if restored:
        print(f"  {C.GREEN}✅ Restored: {', '.join(restored)}{C.END}")
    else:
        print(f"  {C.YELLOW}⚠️ No files to restore{C.END}")
    
    # Step 6: Install dependencies
    print(f"\n{C.YELLOW}[6/6] Installing dependencies...{C.END}")
    result = os.system(f"cd {client_dir} && npm install 2>&1 | tail -5")
    if result != 0:
        print(f"  {C.YELLOW}⚠️ npm install had warnings (usually OK){C.END}")
    else:
        print(f"  {C.GREEN}✅ Dependencies installed{C.END}")
    
    # Get new version
    new_version = get_local_version(client_dir)
    
    # Clean up temp backup (keep safety backup for a while)
    try:
        shutil.rmtree(temp_backup)
    except:
        pass
    
    # Restart if was running
    if was_running and auto_restart:
        print(f"\n{C.CYAN}Restarting bot...{C.END}")
        os.system(f"pm2 start {client_dir}/index.js --name {username} --cwd {client_dir} 2>/dev/null")
        os.system("pm2 save 2>/dev/null")
        print(f"  {C.GREEN}✅ Bot restarted{C.END}")
    
    print(f"""
{C.GREEN}╔════════════════════════════════════════════════════════════════╗
║                    ✅ UPDATE COMPLETE!                         ║
╠════════════════════════════════════════════════════════════════╣{C.END}
║  Client    : {username:<50}║
║  Version   : {current_version} → {new_version:<43}║
║  Session   : {C.GREEN}Preserved ✅{C.END}                                        ║
║  Status    : {'Running 🟢' if was_running and auto_restart else 'Stopped 🔴':<50}║
{C.GREEN}╚════════════════════════════════════════════════════════════════╝{C.END}
""")
    
    return True

def update_client():
    """Update single client - menu option"""
    banner()
    print(f"\n{C.CYAN}══════════════════ UPDATE CLIENT ══════════════════{C.END}")
    print(f"{C.WHITE}This will update the bot code while keeping your session intact.{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    current_version = get_local_version(client['directory'])
    remote_version = get_remote_version()
    
    print(f"\n{C.CYAN}Version Info:{C.END}")
    print(f"  Current: {C.YELLOW}{current_version}{C.END}")
    print(f"  Latest:  {C.GREEN}{remote_version}{C.END}")
    
    if current_version == remote_version and current_version != 'unknown':
        print(f"\n{C.GREEN}✅ Already on latest version!{C.END}")
        force = input(f"\n{C.YELLOW}Force update anyway? (y/n): {C.END}")
        if force.lower() != 'y':
            pause()
            return
    
    print(f"""
{C.YELLOW}╔════════════════════════════════════════════════════════════════╗
║                      ⚠️  UPDATE WARNING                        ║
╠════════════════════════════════════════════════════════════════╣{C.END}
║  The following will be PRESERVED:                              ║
║  ✅ Session/Authentication (no re-scan needed)                 ║
║  ✅ Database files                                             ║
║  ✅ Config files (.env, config.js)                             ║
║                                                                ║
║  The following will be UPDATED:                                ║
║  🔄 All bot code files                                         ║
║  🔄 Commands                                                   ║
║  🔄 Dependencies (package.json)                                ║
{C.YELLOW}╚════════════════════════════════════════════════════════════════╝{C.END}
""")
    
    confirm = input(f"{C.YELLOW}Proceed with update? (yes/no): {C.END}")
    if confirm.lower() != 'yes':
        print(f"{C.YELLOW}Update cancelled.{C.END}")
        pause()
        return
    
    success = update_single_client(client)
    
    if success:
        print(f"{C.GREEN}✅ Update completed successfully!{C.END}")
    else:
        print(f"{C.RED}❌ Update failed! Check the errors above.{C.END}")
    
    pause()

def update_all_clients():
    """Update all clients - menu option"""
    banner()
    print(f"\n{C.CYAN}══════════════════ UPDATE ALL CLIENTS ══════════════════{C.END}")
    
    data = load_clients()
    
    if not data['clients']:
        print(f"{C.YELLOW}No clients found.{C.END}")
        pause()
        return
    
    remote_version = get_remote_version()
    print(f"\n{C.CYAN}Latest version available: {C.GREEN}{remote_version}{C.END}")
    print(f"\n{C.WHITE}Clients to update:{C.END}\n")
    
    for client in data['clients']:
        current = get_local_version(client['directory'])
        status = get_status(client['username'])
        icon = "🟢" if status == "online" else "🔴"
        print(f"  {icon} {client['username']}: v{current}")
    
    print(f"""
{C.YELLOW}╔════════════════════════════════════════════════════════════════╗
║                    ⚠️  BULK UPDATE WARNING                     ║
╠════════════════════════════════════════════════════════════════╣{C.END}
║  This will update ALL {len(data['clients']):>2} clients to the latest version.         ║
║                                                                ║
║  ✅ All sessions will be preserved                             ║
║  ✅ Running bots will be restarted automatically               ║
║  ✅ Safety backups will be created                             ║
{C.YELLOW}╚════════════════════════════════════════════════════════════════╝{C.END}
""")
    
    confirm = input(f"{C.RED}Type 'UPDATE ALL' to confirm: {C.END}")
    if confirm != 'UPDATE ALL':
        print(f"{C.YELLOW}Update cancelled.{C.END}")
        pause()
        return
    
    success_count = 0
    fail_count = 0
    
    for client in data['clients']:
        try:
            if update_single_client(client):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"{C.RED}❌ Error updating {client['username']}: {e}{C.END}")
            fail_count += 1
    
    print(f"""
{C.GREEN}╔════════════════════════════════════════════════════════════════╗
║                  BULK UPDATE COMPLETE                          ║
╠════════════════════════════════════════════════════════════════╣{C.END}
║  ✅ Successful: {success_count:<47}║
║  ❌ Failed:     {fail_count:<47}║
║  📊 Total:      {len(data['clients']):<47}║
{C.GREEN}╚════════════════════════════════════════════════════════════════╝{C.END}
""")
    
    os.system("pm2 save 2>/dev/null")
    pause()

def check_updates():
    """Check for available updates"""
    banner()
    print(f"\n{C.CYAN}══════════════════ CHECK FOR UPDATES ══════════════════{C.END}\n")
    
    print(f"{C.YELLOW}Checking GitHub for latest version...{C.END}\n")
    
    remote_version = get_remote_version()
    print(f"  Latest version on GitHub: {C.GREEN}{remote_version}{C.END}\n")
    
    data = load_clients()
    
    if not data['clients']:
        print(f"{C.YELLOW}No clients to check.{C.END}")
        pause()
        return
    
    print(f"{'Client':<20} {'Current':<15} {'Latest':<15} {'Status':<15}")
    print("─" * 65)
    
    updates_available = []
    
    for client in data['clients']:
        current = get_local_version(client['directory'])
        
        if current == remote_version:
            status = f"{C.GREEN}✅ Up to date{C.END}"
        elif current == 'unknown' or remote_version == 'unknown':
            status = f"{C.YELLOW}❓ Unknown{C.END}"
            updates_available.append(client)
        else:
            status = f"{C.RED}⬆️  Update available{C.END}"
            updates_available.append(client)
        
        print(f"{client['username']:<20} {current:<15} {remote_version:<15} {status}")
    
    print("─" * 65)
    
    if updates_available:
        print(f"\n{C.YELLOW}{len(updates_available)} client(s) can be updated.{C.END}")
        print(f"Use option [13] to update single client or [14] to update all.")
    else:
        print(f"\n{C.GREEN}All clients are up to date! ✅{C.END}")
    
    pause()

# ═══════════════════════════════════════════════════════════════
# EXISTING FUNCTIONS (unchanged)
# ═══════════════════════════════════════════════════════════════

def add_client():
    """Add new client - Clone, Install, Run node index.js"""
    banner()
    print(f"\n{C.GREEN}══════════════════ ADD NEW CLIENT ══════════════════{C.END}\n")
    
    username = input(f"{C.YELLOW}Enter client username: {C.END}").strip().lower()
    
    if not username or not username.isalnum():
        print(f"{C.RED}❌ Invalid username! Use letters and numbers only.{C.END}")
        pause()
        return
    
    data = load_clients()
    if any(c['username'] == username for c in data['clients']):
        print(f"{C.RED}❌ Client '{username}' already exists!{C.END}")
        pause()
        return
    
    client_dir = BASE_DIR / username
    
    print(f"\n{C.CYAN}[1/3] Cloning repository...{C.END}\n")
    print("─" * 60)
    
    if os.system(f"git clone {BOT_REPO} {client_dir}") != 0:
        print(f"\n{C.RED}❌ Clone failed!{C.END}")
        shutil.rmtree(client_dir, ignore_errors=True)
        pause()
        return
    
    print("\n" + "─" * 60)
    print(f"{C.GREEN}✅ Cloned!{C.END}\n")
    
    print(f"{C.CYAN}[2/3] Installing dependencies...{C.END}\n")
    print("─" * 60)
    
    if os.system(f"cd {client_dir} && npm install") != 0:
        print(f"\n{C.RED}❌ Install failed!{C.END}")
        pause()
        return
    
    print("\n" + "─" * 60)
    print(f"{C.GREEN}✅ Installed!{C.END}\n")
    
    # Save client
    client_info = {
        "username": username,
        "directory": str(client_dir),
        "created_at": datetime.now().isoformat()
    }
    data['clients'].append(client_info)
    save_clients(data)
    
    print(f"""
{C.GREEN}╔════════════════════════════════════════════════════════════════╗
║                  ✅ CLIENT SETUP COMPLETE!                     ║
╠════════════════════════════════════════════════════════════════╣{C.END}
║  Username  : {username:<50}║
║  Directory : /root/clients/{username:<35}║
{C.GREEN}╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  {C.WHITE}[3/3] RUNNING BOT - SCAN QR CODE NOW!{C.GREEN}                        ║
║                                                                ║
║  {C.WHITE}• Wait for QR code / Pairing code{C.GREEN}                           ║
║  {C.WHITE}• Open WhatsApp → Linked Devices → Link a Device{C.GREEN}            ║
║  {C.WHITE}• Scan QR or enter pairing code{C.GREEN}                             ║
║  {C.WHITE}• After connected, press Ctrl+C to exit{C.GREEN}                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝{C.END}
""")
    
    input(f"{C.YELLOW}Press Enter to start bot and see QR code...{C.END}")
    
    print(f"\n{C.CYAN}Starting: node index.js{C.END}")
    print(f"{C.YELLOW}(Press Ctrl+C after scanning QR and bot connects){C.END}\n")
    print("═" * 60 + "\n")
    
    # Run node index.js interactively
    os.system(f"cd {client_dir} && node index.js")
    
    print("\n" + "═" * 60)
    print(f"\n{C.GREEN}✅ Setup complete!{C.END}")
    print(f"{C.YELLOW}Use option [3] to start bot in background with PM2{C.END}")
    pause()

def view_clients():
    banner()
    print(f"\n{C.GREEN}══════════════════ ALL CLIENTS ══════════════════{C.END}\n")
    
    data = load_clients()
    
    if not data['clients']:
        print(f"{C.YELLOW}No clients yet. Use option [1] to add one.{C.END}")
        pause()
        return
    
    print(f"{'#':<4} {'Username':<20} {'Status':<12} {'Version':<12} {'Created':<12}")
    print("─" * 65)
    
    for i, client in enumerate(data['clients'], 1):
        status = get_status(client['username'])
        version = get_local_version(client['directory'])
        if status == 'online':
            st = f"{C.GREEN}● Online{C.END}"
        else:
            st = f"{C.RED}● Stopped{C.END}"
        created = client.get('created_at', '')[:10]
        print(f"{i:<4} {client['username']:<20} {st:<22} {version:<12} {created}")
    
    print("─" * 65)
    print(f"Total: {len(data['clients'])} clients")
    pause()

def start_client():
    banner()
    print(f"\n{C.GREEN}══════════════════ START CLIENT (PM2) ══════════════════{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    client_dir = client['directory']
    
    print(f"\n{C.CYAN}Starting {username} with PM2...{C.END}\n")
    
    os.system(f"pm2 start {client_dir}/index.js --name {username} --cwd {client_dir}")
    os.system("pm2 save 2>/dev/null")
    
    print(f"\n{C.GREEN}✅ {username} started in background!{C.END}")
    print(f"{C.YELLOW}Use 'pm2 logs {username}' or option [9] to view logs{C.END}")
    pause()

def stop_client():
    banner()
    print(f"\n{C.RED}══════════════════ STOP CLIENT ══════════════════{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    print(f"\n{C.CYAN}Stopping {username}...{C.END}")
    
    os.system(f"pm2 stop {username} 2>/dev/null")
    print(f"{C.GREEN}✅ {username} stopped!{C.END}")
    pause()

def restart_client():
    banner()
    print(f"\n{C.YELLOW}══════════════════ RESTART CLIENT ══════════════════{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    print(f"\n{C.CYAN}Restarting {username}...{C.END}")
    
    os.system(f"pm2 restart {username} 2>/dev/null")
    print(f"{C.GREEN}✅ {username} restarted!{C.END}")
    pause()

def start_all():
    banner()
    data = load_clients()
    
    if not data['clients']:
        print(f"{C.YELLOW}No clients found.{C.END}")
        pause()
        return
    
    print(f"\n{C.GREEN}══════════════════ START ALL BOTS ══════════════════{C.END}\n")
    
    for client in data['clients']:
        username = client['username']
        client_dir = client['directory']
        print(f"  Starting {username}...", end=" ", flush=True)
        
        status = get_status(username)
        if status == 'online':
            print(f"{C.YELLOW}already running{C.END}")
        else:
            os.system(f"pm2 start {client_dir}/index.js --name {username} --cwd {client_dir} 2>/dev/null")
            print(f"{C.GREEN}✅{C.END}")
    
    os.system("pm2 save 2>/dev/null")
    print(f"\n{C.GREEN}All bots started!{C.END}")
    pause()

def stop_all():
    banner()
    data = load_clients()
    
    if not data['clients']:
        print(f"{C.YELLOW}No clients found.{C.END}")
        pause()
        return
    
    confirm = input(f"{C.RED}Stop ALL bots? (yes/no): {C.END}")
    if confirm.lower() != 'yes':
        return
    
    print(f"\n{C.RED}══════════════════ STOPPING ALL ══════════════════{C.END}\n")
    
    for client in data['clients']:
        username = client['username']
        print(f"  Stopping {username}...", end=" ", flush=True)
        os.system(f"pm2 stop {username} 2>/dev/null")
        print(f"{C.GREEN}✅{C.END}")
    
    print(f"\n{C.GREEN}All bots stopped!{C.END}")
    pause()

def pm2_status():
    banner()
    print(f"\n{C.CYAN}══════════════════ PM2 STATUS ══════════════════{C.END}\n")
    os.system("pm2 status")
    pause()

def view_logs():
    banner()
    print(f"\n{C.CYAN}══════════════════ VIEW LOGS ══════════════════{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    print(f"\n{C.YELLOW}Showing logs for {username} (Ctrl+C to exit){C.END}\n")
    print("═" * 60)
    
    try:
        os.system(f"pm2 logs {username} --lines 100")
    except KeyboardInterrupt:
        pass

def run_interactive():
    """Run node index.js directly (for re-scanning QR)"""
    banner()
    print(f"\n{C.CYAN}══════════════════ RUN INTERACTIVELY ══════════════════{C.END}")
    print(f"{C.WHITE}Use this to re-scan QR code or debug{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    client_dir = client['directory']
    
    # Stop PM2 process first if running
    status = get_status(username)
    if status == 'online':
        print(f"\n{C.YELLOW}Stopping PM2 process first...{C.END}")
        os.system(f"pm2 stop {username} 2>/dev/null")
    
    print(f"""
{C.GREEN}════════════════════════════════════════════════════════════════
  Running: node index.js
  
  • QR code or pairing code will appear
  • Scan with WhatsApp → Linked Devices → Link a Device
  • Press Ctrl+C when done
════════════════════════════════════════════════════════════════{C.END}
""")
    
    input(f"{C.YELLOW}Press Enter to start...{C.END}")
    
    print("\n")
    os.system(f"cd {client_dir} && node index.js")
    
    print(f"\n{C.GREEN}Session ended.{C.END}")
    
    restart = input(f"\n{C.YELLOW}Start bot in background with PM2? (y/n): {C.END}")
    if restart.lower() == 'y':
        os.system(f"pm2 start {client_dir}/index.js --name {username} --cwd {client_dir}")
        os.system("pm2 save 2>/dev/null")
        print(f"{C.GREEN}✅ {username} running in background!{C.END}")
    
    pause()

def delete_client():
    banner()
    print(f"\n{C.RED}══════════════════ DELETE CLIENT ══════════════════{C.END}")
    
    client = select_client()
    if not client:
        pause()
        return
    
    username = client['username']
    
    confirm = input(f"\n{C.RED}Type '{username}' to confirm deletion: {C.END}")
    if confirm != username:
        print(f"{C.YELLOW}Cancelled.{C.END}")
        pause()
        return
    
    print(f"\n{C.CYAN}Deleting {username}...{C.END}")
    
    # Stop and delete from PM2
    os.system(f"pm2 stop {username} 2>/dev/null")
    os.system(f"pm2 delete {username} 2>/dev/null")
    
    # Remove directory
    client_dir = Path(client['directory'])
    if client_dir.exists():
        shutil.rmtree(client_dir)
    
    # Remove from config
    data = load_clients()
    data['clients'] = [c for c in data['clients'] if c['username'] != username]
    save_clients(data)
    
    print(f"{C.GREEN}✅ {username} deleted!{C.END}")
    pause()

def backup_sessions():
    banner()
    print(f"\n{C.CYAN}══════════════════ BACKUP SESSIONS ══════════════════{C.END}\n")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = BACKUP_DIR / f"sessions_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    data = load_clients()
    
    if not data['clients']:
        print(f"{C.YELLOW}No clients to backup.{C.END}")
        pause()
        return
    
    print(f"Backup location: {backup_dir}\n")
    
    for client in data['clients']:
        username = client['username']
        client_dir = Path(client['directory'])
        
        backed_up = backup_preserved_items(client_dir, backup_dir / username)
        
        if backed_up:
            print(f"  {C.GREEN}✅{C.END} {username} - {', '.join(backed_up)}")
        else:
            print(f"  {C.YELLOW}⚠️{C.END} {username} - no session found")
    
    # Backup config
    if CONFIG_FILE.exists():
        shutil.copy(CONFIG_FILE, backup_dir / "clients.json")
        print(f"  {C.GREEN}✅{C.END} clients.json")
    
    print(f"\n{C.GREEN}Backup complete: {backup_dir}{C.END}")
    pause()

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    # Setup
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check PM2
    if os.system("which pm2 > /dev/null 2>&1") != 0:
        print(f"{C.YELLOW}Installing PM2...{C.END}")
        os.system("npm install -g pm2")
    
    # Update PM2 if needed
    os.system("pm2 update > /dev/null 2>&1")
    
    actions = {
        '1': add_client,
        '2': view_clients,
        '3': start_client,
        '4': stop_client,
        '5': restart_client,
        '6': start_all,
        '7': stop_all,
        '8': pm2_status,
        '9': view_logs,
        '10': run_interactive,
        '11': delete_client,
        '12': backup_sessions,
        '13': update_client,
        '14': update_all_clients,
        '15': check_updates,
    }
    
    while True:
        banner()
        menu()
        
        try:
            choice = input(f"{C.CYAN}Select option: {C.END}").strip()
            
            if choice == '0':
                print(f"\n{C.GREEN}Goodbye! 👋{C.END}\n")
                sys.exit(0)
            elif choice in actions:
                actions[choice]()
            else:
                print(f"{C.RED}Invalid option!{C.END}")
                pause()
        except KeyboardInterrupt:
            print(f"\n{C.GREEN}Goodbye! 👋{C.END}\n")
            sys.exit(0)

if __name__ == "__main__":
    main()
