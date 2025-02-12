# 📂 Folder Sync - One-Way Folder Synchronization

## 📌 Overview
**Folder Sync** is a Python program that **synchronizes two folders** by ensuring that the `replica` folder is always an **exact copy** of the `source` folder.  
It performs **one-way synchronization**, meaning changes in the `source` will be reflected in `replica`, but modifications in `replica` will not affect `source`.

### 🔧 Features:
✅ **One-way synchronization** (Source → Replica)  
✅ **File creation, modification, and deletion tracking**  
✅ **Efficient file comparison** using **file size, modification time, and MD5 checksum**  
✅ **Automated logging** to both **console** and **log file**  
✅ **Handles missing paths** (creates `replica` and `log` file automatically)  
✅ **Periodic execution** at user-defined intervals  
✅ **Command-line argument support** for flexibility  

---

## 🚀 Installation & Usage

### 📌 **1. Prerequisites**
- **Python 3.x** installed on your system
- Works on **Windows, macOS, and Linux**
- No external dependencies are required

### 📌 **2. Clone the Repository**
```bash
git clone https://github.com/Gaz1l/folder_sync.git
cd folder_sync
```
### 📌3. Run the Program
```bash
python folder_sync.py --source "/path/to/source" --replica "/path/to/replica" --log "sync.log" --interval {interval_time_in_seconds}
```
--- 

## 📝 Notes
-Do not modify the replica folder manually. Any changes will be overwritten during the next sync.<br>
-The program only removes files/directories from replica if they no longer exist in source.<br>
-If replica or log file does not exist, the program will create them automatically.<br>

## 👨‍💻 Author
Abel Gazil<br>
GitHub: Gaz1l<br>
Email: abelgazil@gmail.com<br>
