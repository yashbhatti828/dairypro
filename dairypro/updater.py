"""
Baba Nanak Dairy — Auto Updater
Downloads latest code from GitHub, replaces .py files only.
dairy_data/ is NEVER touched.
"""
import urllib.request, zipfile, os, shutil, sys, json
from datetime import datetime

# ── CONFIG — change this to your GitHub repo URL after uploading ─────────────
GITHUB_ZIP_URL = "https://github.com/YOUR_USERNAME/dairypro/archive/refs/heads/main.zip"
VERSION_URL    = "https://raw.githubusercontent.com/YOUR_USERNAME/dairypro/main/version.json"
LOCAL_VERSION  = "version.json"
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR  = os.path.join(SCRIPT_DIR, "backup")
TEMP_ZIP    = os.path.join(SCRIPT_DIR, "_update_temp.zip")
TEMP_EXTRACT= os.path.join(SCRIPT_DIR, "_update_temp_dir")

# Files/folders that should NEVER be touched by updater
PROTECTED = {"dairy_data", "UPDATE.bat", "RUN.bat"}

def get_local_version():
    path = os.path.join(SCRIPT_DIR, LOCAL_VERSION)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f).get("version","0.0")
    return "0.0"

def get_remote_version():
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=10) as r:
            return json.loads(r.read()).get("version","0.0")
    except Exception as ex:
        print(f"  [!] Could not check remote version: {ex}")
        return None

def backup_current():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk = os.path.join(BACKUP_DIR, f"backup_{ts}")
    os.makedirs(bk, exist_ok=True)
    for item in os.listdir(SCRIPT_DIR):
        if item in PROTECTED or item.startswith("_") or item == "backup":
            continue
        src = os.path.join(SCRIPT_DIR, item)
        dst = os.path.join(bk, item)
        try:
            if os.path.isdir(src): shutil.copytree(src, dst)
            else:                  shutil.copy2(src, dst)
        except: pass
    print(f"  Backup saved → backup/{os.path.basename(bk)}")
    return bk

def download_zip():
    print("  Downloading latest version...")
    try:
        urllib.request.urlretrieve(GITHUB_ZIP_URL, TEMP_ZIP)
        print("  Download complete.")
        return True
    except Exception as ex:
        print(f"  [ERROR] Download failed: {ex}")
        return False

def apply_update():
    print("  Extracting update...")
    os.makedirs(TEMP_EXTRACT, exist_ok=True)
    with zipfile.ZipFile(TEMP_ZIP, "r") as z:
        z.extractall(TEMP_EXTRACT)

    # GitHub zips extract into a subfolder like "dairypro-main/"
    extracted_root = None
    for item in os.listdir(TEMP_EXTRACT):
        full = os.path.join(TEMP_EXTRACT, item)
        if os.path.isdir(full):
            extracted_root = full
            break
    if not extracted_root:
        print("  [ERROR] Could not find extracted folder.")
        return False

    updated = 0
    skipped = 0

    # Walk all files in extracted zip
    for root, dirs, files in os.walk(extracted_root):
        # Skip dairy_data if somehow in zip
        dirs[:] = [d for d in dirs if d not in PROTECTED]
        for fname in files:
            src_file = os.path.join(root, fname)
            # Relative path inside zip
            rel = os.path.relpath(src_file, extracted_root)
            dst_file = os.path.join(SCRIPT_DIR, rel)

            # Never overwrite protected files/folders
            parts = rel.replace("\\","/").split("/")
            if parts[0] in PROTECTED:
                skipped += 1
                continue

            # Only copy .py files and version.json
            if not (fname.endswith(".py") or fname == "version.json"):
                skipped += 1
                continue

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            updated += 1

    print(f"  Updated {updated} files, skipped {skipped}.")
    return True

def cleanup():
    try:
        if os.path.exists(TEMP_ZIP):    os.remove(TEMP_ZIP)
        if os.path.exists(TEMP_EXTRACT):shutil.rmtree(TEMP_EXTRACT)
    except: pass

def main():
    print(f"  Current version : {get_local_version()}")

    # Check if GitHub URL is configured
    if "yashbhatti828" in GITHUB_ZIP_URL:
        print()
        print("  ╔══════════════════════════════════════════════════════╗")
        print("  ║  Updater not configured yet.                         ║")
        print("  ║                                                      ║")
        print("  ║  Steps to enable auto-update:                       ║")
        print("  ║  1. Create a free account at github.com             ║")
        print("  ║  2. Upload your dairypro folder as a repository     ║")
        print("  ║  3. Open updater.py and replace YOUR_USERNAME       ║")
        print("  ║     with your actual GitHub username                ║")
        print("  ║  4. Run UPDATE.bat again                            ║")
        print("  ╚══════════════════════════════════════════════════════╝")
        print()
        print("  For now you can still manually replace .py files.")
        return

    remote = get_remote_version()
    if remote is None:
        print("  Could not reach server. Check internet connection.")
        return

    print(f"  Latest version  : {remote}")

    local = get_local_version()
    if local == remote:
        print()
        print("  ✓ Already up to date! No update needed.")
        return

    print(f"\n  New version available: {local} → {remote}")
    ans = input("  Update now? (y/n): ").strip().lower()
    if ans != "y":
        print("  Update cancelled.")
        return

    print("\n  Step 1/3 — Backing up current files...")
    backup_current()

    print("  Step 2/3 — Downloading update...")
    if not download_zip():
        cleanup(); return

    print("  Step 3/3 — Applying update...")
    if apply_update():
        cleanup()
        new_ver = get_local_version()
        print()
        print(f"  ✓ Update complete! Version {new_ver}")
        print("  Your dairy_data/ is untouched — all data safe.")
        print()
        print("  Restart the app (run RUN.bat) to use the new version.")
    else:
        cleanup()
        print("  [ERROR] Update failed. Your files are unchanged.")
        print("  Backup is saved in the backup/ folder.")

if __name__ == "__main__":
    main()
