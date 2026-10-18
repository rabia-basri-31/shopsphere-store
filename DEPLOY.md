# Deploying to Render (free tier)

This gets you a **public URL** a recruiter can click — no MySQL install,
no Python setup on their side.

---

## What you need first

1. This project pushed to GitHub ✅ (already done)
2. A free [Render](https://render.com) account
3. A GitHub account (you have this)

---

## Option A — the Blueprint (recommended, easiest)

Render reads `render.yaml` and sets up the app *and* the database for you.

1. Push this project to GitHub so `render.yaml` is there:

   ```bash
   git add .
   git commit -m "Add Render deployment config"
   git push
   ```

2. Go to <https://render.com> → sign in with GitHub

3. Click **New +** → **Blueprint**

4. Pick the repository `ecommerce-web-app`

5. Render shows you everything it will create. Review, then **Apply**

6. Wait ~2 minutes. When it finishes you get a URL like:

   ```
   https://ecommerce-web-app.onrender.com
   ```

### Load the sample data

Render creates an empty database. To fill it with the 6 categories and
12 products, open the **Shell** tab of your web service on Render and run:

```bash
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD $DB_NAME < database/schema.sql
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD $DB_NAME < database/seed.sql
```

Then create yourself an admin account:

```bash
python admin_setup.py
```

---

## Option B — manual setup

If you would rather click through it yourself:

1. **New +** → **Web Service** → connect the repo
2. Fill in:

   | Field | Value |
   |---|---|
   | Runtime | Python |
   | Build command | `pip install -r requirements.txt` |
   | Start command | `gunicorn app:app` |

3. **New +** → **Database** → MySQL → Free
4. Copy its connection details into **Environment**:

   ```
   DB_HOST     = (from Render)
   DB_PORT     = (from Render)
   DB_USER     = (from Render)
   DB_PASSWORD = (from Render)
   DB_NAME     = ecommerce_db
   SECRET_KEY  = any long random string
   FLASK_DEBUG = false
   ```

---

## Things that will trip you up

| Problem | Why | Fix |
|---|---|---|
| Login works but you get logged out on refresh | Secret key changed between requests | Set a **fixed** `SECRET_KEY`, not a random one per boot |
| "This site can't provide a secure connection" loop | Flask thinks it is on http | Already handled — `ProxyFix` is enabled when debug is off |
| Blank page / 500 on every route | `DB_NAME` mismatch | Check the Database tab name matches exactly |
| It works, then dies a few days later | Render's free MySQL expires after **30 days** | Fine for a demo. Delete it when you're done, or point `DB_HOST` at your own server |
| `gunicorn: command not found` | Requirements not installed | Check the build log; make sure `gunicorn` is in `requirements.txt` |

---

## ⚠️ Security before you deploy

**Turn debug OFF.** `FLASK_DEBUG=false` in production — otherwise anyone can
read your source code through the debugger.

**Never commit your `.env`.** Render supplies real values as environment
variables instead, which is exactly how it should work. Verify with:

```bash
git ls-files | Select-String "^\.env$"
```

If that prints nothing, you're safe.

---

## ⚠️ gunicorn does not run on Windows

You cannot test the exact production command on your own PC:

```
ModuleNotFoundError: No module named 'fcntl'
```

`fcntl` is a Linux-only module, so gunicorn only boots on Linux. That is
why Render works and `gunicorn app:app` fails at home. Locally just use:

```bash
python app.py
```

The code path is identical apart from the server in front of it.

---

## Turning the demo off afterwards

The public site will still be live after you delete the Render service, but
anyone who finds the URL can create an account and place test orders. If that
matters to you:

- Delete the service and the database on Render when the interview is over
- Change the demo passwords afterwards

Remember the database is deleted too, so download anything you want to keep
first.