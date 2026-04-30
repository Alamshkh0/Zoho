# Redington Zoho CRM — Discovery Session App

A small Streamlit app to run **per-brand Zoho CRM discovery sessions** at Redington.
Multiple stakeholders fill in a structured form for each brand (AWS, Microsoft, Red Hat, …).
The admin downloads a merged **PDF / Word / CSV** requirements pack to hand to the Zoho services team.

---

## What's in this folder

| File | What it does |
|---|---|
| `app.py`         | The Streamlit app (form + admin dashboard) |
| `db.py`          | Supabase client + queries |
| `reports.py`     | Builds PDF / Word / CSV reports per brand |
| `suggestions.py` | Starter field library (parsed from REDHAT.xlsx + AWS.xlsx) |
| `config.py`      | Brand list, role list, env-var loading |
| `schema.sql`     | One-time DB setup — paste into Supabase SQL editor |
| `requirements.txt` | Python dependencies |
| `.env`           | Supabase URL/key + admin passcode (gitignored) |
| `.streamlit/config.toml` | App theme (Redington red) |

---

## ✅ One-time setup (you only do this once)

### 1. Create the database tables in Supabase
1. Open your Supabase project → **SQL Editor** → **New query**.
2. Open `schema.sql` from this folder, **copy the contents**, paste into the editor, click **Run**.
3. You should see *"Success. No rows returned."* That's it — the `contributors` and `responses` tables now exist.

### 2. Install Python dependencies (locally, to test before deploy)
```bash
cd "Discovery Session APP"
python3 -m pip install -r requirements.txt
```

### 3. Run it locally
```bash
streamlit run app.py
```
Your browser opens at `http://localhost:8501`. Try filling a session as 2 different contributors for the same brand to confirm everything works.

---

## 🚀 Deploying online (free)

Once it works locally:

1. **Push the folder to a GitHub repo** (don't commit `.env` — `.gitignore` already excludes it).
2. Go to **https://share.streamlit.io** → sign in with GitHub → **New app** → pick the repo and `app.py`.
3. Click **Advanced settings → Secrets** and paste:
   ```
   SUPABASE_URL = "https://xnfkuyvbzgbnyymznppg.supabase.co"
   SUPABASE_KEY = "<your anon key>"
   ADMIN_PASSCODE = "redington2026"
   ```
4. **Deploy**. After ~1 minute you get a public URL like `https://redington-discovery.streamlit.app` to share with brand leads.

---

## 🧭 How the app is used

### Brand contributor (PAM, BSM, PM, Pre-Sales, …)
1. Open the public link.
2. **🏁 Start** — pick brand, enter name/email/role.
3. **📝 Fill Discovery Form** — 8 tabs (People → Open Notes). Click **Load suggestions** in any field-builder tab to seed common fields, then edit/delete/add freely.
4. Click **Save & Submit** at the bottom. You can come back and edit anytime; multiple people can submit for the same brand.

### Admin (you)
1. Open the link → sidebar → **🔒 Admin Dashboard & Reports**.
2. Enter passcode (`redington2026`).
3. **Per-Brand Dashboard** — pick a brand, see all contributors, preview merged inputs, download **PDF / Word / CSV**.
4. **Cross-Brand Comparison** — single CSV with all brands side-by-side, ready for Excel pivots.

---

## 🧠 Design principles (worth keeping in mind as you customize)

- **Nothing is forced.** Every brand defines its own fields, workflow, dashboards, rules. The starter suggestions are just one click away — and one click to delete.
- **`questions.py` and `suggestions.py` are the "knobs."** Edit those files to add brands, roles, or change starter suggestions. No app-logic changes required.
- **Schema is intentionally simple** — two tables, JSON payload per section. Easy to evolve as needs grow.

---

## 🛠 Common tweaks

- **Add a brand:** edit `config.py` → `BRANDS` list. Done.
- **Add a role:** edit `config.py` → `ROLES` list.
- **Add a field type:** edit `config.py` → `FIELD_TYPES`.
- **Change the theme color:** edit `.streamlit/config.toml`.
- **Change starter suggestions:** edit `suggestions.py`.

---

## ❓ Troubleshooting

- **"Could not connect to database"** → Did you run `schema.sql` in Supabase? Did `.env` get the right URL/key?
- **Reports look empty** → Make sure contributors clicked **Save & Submit**, not just typed. Refresh the admin page.
- **Streamlit Cloud says module not found** → It auto-installs from `requirements.txt`. Push the file if you forgot.
- **SSL `self-signed certificate` error when running locally on Redington network** → This is your corporate proxy (Zscaler / BlueCoat etc.) intercepting HTTPS. Two options:
  1. **Easiest:** skip local testing and deploy straight to Streamlit Cloud (it runs outside your corp network and connects to Supabase fine).
  2. Or ask IT for the corporate root-CA `.pem`, then run `export SSL_CERT_FILE=/path/to/corp-ca.pem` before `streamlit run app.py`.
