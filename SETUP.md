# 🚀 Quick Setup & Run Guide (Windows 10 & 11)

Ek click ya single command me pura project (Backend + Frontend) install aur run karne ka tarika:

---

## ⚡ Step 1: Run Kaise Kare (How to Run)

### 👉 Tarika 1: Double-Click (Sabse Aasan)
Project folder me jakar **`setup.bat`** file par double-click karein.

---

### 👉 Tarika 2: PowerShell Me Run Karein
PowerShell open karein aur ye command run karein:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1
```

---

## 🤖 Ye Script Automatically Kya Karega:
1. **Python 3.12** check karega (agar nahi hai toh auto-install karega).
2. **Node.js LTS** check karega (agar nahi hai toh auto-install karega).
3. **Backend:** Python virtual environment banayega, requirements install karega, aur database seed karega.
4. **Frontend:** React/Vite dependencies install karega.
5. **Launch:** Backend (`:8000`) aur Frontend (`:5173`) dono start karke browser automatically open kar dega.

---

## 🌐 Live URLs & Links

| Service | URL |
| :--- | :--- |
| **Frontend UI** | [http://localhost:5173](http://localhost:5173) |
| **Backend API** | [http://localhost:8000](http://localhost:8000) |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 🔑 Demo Login Credentials

- **Super Admin:** `admin@credverify.demo` / `admin123`
- **Institution Admin:** `instadmin@demo-institute.edu` / `instadmin123`

---

## ⚙️ Optional Commands

- **Sirf setup karna ho (server start na karna ho):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1 -SetupOnly
  ```

- **Sab kuch naye se clean install karna ho:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1 -ForceReinstall
  ```
