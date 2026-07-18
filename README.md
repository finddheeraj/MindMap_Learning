# Learning Hub

A personal learning website for organizing learning topics into visual mind maps
with notes and videos.

> **Status: OAuth/cloud-storage migration — milestone 4 complete.** Topic CRUD, search, sort, and the
> responsive landing page are implemented (Phase 1). The interactive,
> persisted Mind Elixir mind map per topic is implemented (Phase 2).
> Node details / rich notes (Phase 3) and polish/export (Phase 4) are
> not yet built.

---

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy (Flask-SQLAlchemy), SQLite
- **Frontend:** Bootstrap 5, Bootstrap Icons, Vanilla JavaScript
- **Mind map:** Mind Elixir 5.14.0 (vendored locally in `static/vendor/mind-elixir/`,
  not loaded from a CDN - see note below)
- **Rich text (Phase 3):** Quill

---

## Project Structure

```
learning_hub/
├── app.py                  # App factory + entry point (python app.py)
├── config.py                # Config classes (dev/prod), DB path
├── extensions.py             # Shared `db` (SQLAlchemy) instance
├── requirements.txt
├── README.md
├── database/
│   └── learning_hub.db      # SQLite file (auto-created on first run)
├── models/
│   ├── __init__.py          # Exposes all models
│   ├── topic.py               # Topic model
│   └── mind_map_node.py       # MindMapNode model (self-referential tree)
├── services/
│   ├── __init__.py
│   ├── topic_service.py       # Topic business logic / queries
│   └── mindmap_service.py     # Tree <-> Mind Elixir JSON conversion, upsert/save
├── routes/
│   ├── __init__.py
│   ├── topics.py               # Topic blueprint: index, create, edit, delete
│   └── mindmap.py              # Mind map blueprint: view page + autosave endpoint
├── templates/
│   ├── base.html             # Shared layout, navbar, flash messages
│   ├── index.html            # Landing page (topic table)
│   ├── topic_form.html       # Create/edit topic form
│   ├── mindmap.html           # Mind map page (Mind Elixir canvas)
│   └── errors/
│       ├── 404.html
│       └── 500.html
└── static/
    ├── css/style.css         # App styling (light theme, responsive)
    ├── js/main.js             # Delete-confirm modal, live search
    ├── js/mindmap.js          # Mind Elixir init + autosave (ES module)
    ├── vendor/mind-elixir/     # Mind Elixir's own MindElixir.js + MindElixir.css,
    │                           # vendored locally (see note below)
    └── images/                # (empty, for future use)
```

> **Why vendored instead of CDN?** Mind Elixir's actual CSS file is named
> `MindElixir.css` (not `style.css`), and its version moves quickly enough
> that a pinned CDN URL can 404 if the exact version is no longer current.
> Vendoring `MindElixir.js` and `MindElixir.css` directly (installed once
> via `npm install mind-elixir` and copied out of `node_modules`) means the
> app always serves exactly the files it was tested against, with no
> network dependency on a third-party CDN at runtime.

---

## Installation

### 1. Create and activate a virtual environment

```bash
cd learning_hub
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

The SQLite database and its tables are **created automatically** the first
time the app starts (see `create_app()` in `app.py`, which calls
`db.create_all()` inside an app context). There is no separate migration
step to run for Phase 1.

Visit **http://127.0.0.1:5000** in your browser.

## OAuth and Cloud Storage Migration

The project is being migrated incrementally so each release remains usable.
Milestone 1 establishes package boundaries for authentication (`auth/`), cloud
providers (`providers/`), storage (`storage/`), and shared utilities (`utils/`).
The current Topic and Mind Map behavior still uses SQLite exactly as before;
there are no cloud-storage reads or writes in this milestone.

### Google OAuth setup (milestone 2)

1. In Google Cloud Console, create an OAuth 2.0 **Web application** client.
2. Add `http://127.0.0.1:5000/auth/google/callback` to its authorized redirect URIs.
3. Set the client credentials before starting the application:

   ```powershell
   $env:GOOGLE_CLIENT_ID="your-google-client-id"
   $env:GOOGLE_CLIENT_SECRET="your-google-client-secret"
   python app.py
   ```

4. Open the app and select **Sign in with Google**. After consent, the app
   creates or updates a `user_mappings` row and saves the mapping identifier in
   the Flask session.

`Authlib` is required for this milestone; install the updated dependencies with
`pip install -r requirements.txt`. The existing startup schema creation creates
the new `user_mappings` table automatically, so no separate migration command
is required in this project.

The table includes a `drive_file_id` column for the later storage stages.

### Microsoft OAuth setup (milestone 3)

1. In Microsoft Entra admin center, create an app registration that supports
   the account types your deployment needs. For both work/school and personal
   Microsoft accounts, select the multi-tenant and personal-account option.
2. Add a **Web** redirect URI of
   `http://127.0.0.1:5000/auth/microsoft/callback`.
3. Create a client secret and set the values before starting the app:

   ```powershell
   $env:MICROSOFT_CLIENT_ID="your-microsoft-application-client-id"
   $env:MICROSOFT_CLIENT_SECRET="your-microsoft-client-secret"
   python app.py
   ```

4. The consent request uses OpenID Connect, Microsoft Graph `User.Read`, and
   `Files.ReadWrite.AppFolder`. The latter limits future OneDrive storage to
   the application's folder; no OneDrive read/write code runs in this
   milestone.

Both providers now use the same dynamic login and callback routes:
`/login/<provider>` and `/auth/<provider>/callback`. Google URLs remain
`/login/google` and `/auth/google/callback`, preserving the milestone-2
redirect URI.

### Encrypted refresh-token storage (milestone 4)

OAuth sign-in now requires a Fernet key to encrypt refresh tokens before they
are stored in `user_mappings.refresh_token`. Generate the key once and keep it
in your production secret manager; losing or changing the key without a
rotation plan makes existing stored tokens unreadable.

```powershell
$env:TOKEN_ENCRYPTION_KEY = (& .\venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

Set the same value every time the application starts, alongside the provider
credentials. The application refuses to begin either OAuth flow if this key is
missing or invalid. Refresh-token plaintext is never written to the database
or displayed in the user interface.

### Milestone 4 verification

1. Run `pip install -r requirements.txt`, activate the virtual environment, and run `python app.py` without OAuth credentials. Confirm the existing topic list, CRUD, and mind-map autosave still work.
2. Configure a provider but omit `TOKEN_ENCRYPTION_KEY`. Select that provider and confirm the app refuses login with a secure-token-storage message.
3. Generate and set `TOKEN_ENCRYPTION_KEY`, then complete a Google or Microsoft consent flow.
4. Inspect `database/learning_hub.db`. Confirm `user_mappings.refresh_token` has a value that does not equal the provider's plaintext refresh token.
5. Restart the application with the same key and sign in again. Confirm the mapping is reused and the application still functions.

---

## Features in Phase 1

- **Landing page** — responsive Bootstrap table of all topics, showing
  S.No, Topic (with description), Last Updated, and action buttons.
- **Add Topic** — button above the table opens a form to create a topic
  (name required, optional description).
- **Edit Topic** — inline pencil icon opens a pre-filled edit form.
- **Delete Topic** — trash icon opens a confirmation modal before deleting.
- **Search** — live (debounced) search box filters topics by name.
- **Sort** — click the "Topic" or "Last Updated" column headers to sort
  ascending/descending.
- **Validation & flash messages** — empty/invalid names are rejected with
  a clear error; successful actions show a dismissible success banner.
- **Responsive design** — the table collapses into stacked cards on phones;
  no horizontal scrolling on any screen size.
- **Custom error pages** — friendly 404 and 500 pages.

## Features in Phase 2

- **Launch Mind Map** — clicking the diagram icon on the landing page opens
  `/topic/<id>`, an interactive Mind Elixir canvas seeded with the topic's
  saved tree (or just the root node, named after the topic, on first visit).
- **Root node = Topic name** — the mind map's root node always starts as
  the topic's name; renaming the root node inside the mind map renames the
  topic everywhere (landing page included).
- **Unlimited nested children, siblings** — Mind Elixir's built-in
  drag-and-drop, right-click context menu, and keyboard shortcuts let you
  add children, add siblings, rename, delete, and drag nodes anywhere in
  the tree, with no depth limit.
- **Expand / collapse** — every node can be collapsed or expanded; the
  state persists across reloads.
- **Autosave** — every edit (add, rename, delete, move, collapse) fires a
  debounced save (~0.7s after you stop editing) to
  `POST /topic/<id>/mindmap/save`, which is shown live via a
  "Saving... / All changes saved / Save failed" indicator top-right.
- **Stable node identity** — nodes are matched between saves by the id
  Mind Elixir assigns them, so edits update existing rows instead of
  wiping and recreating the tree (important for Phase 3, when notes and
  videos get attached to specific nodes).
- **Cascade delete** — deleting a topic on the landing page also deletes
  its entire mind map.

The right-side node details panel (title/video/notes/completed checkbox)
is intentionally not wired up yet — that's Phase 3.

---

## Testing What You Have

1. Run `python app.py`.
2. Open the site — you should see an empty state with an "Add Topic" button.
3. Click **Add Topic**, create a topic (e.g. "Machine Learning").
4. Click the diagram icon in the **Launch Mind Map** column - you should
   land on `/topic/1` with a single root node named after your topic.
5. Try the mind map interactions:
   - Press `Tab` (or use the toolbar/context menu) to add a child node.
   - Press `Enter` to add a sibling node.
   - Double-click a node to rename it.
   - Drag a node onto another to reparent it.
   - Right-click a node for the full context menu (add child, add sibling,
     remove, etc).
   - Collapse/expand a branch using its `+`/`-` toggle.
6. Watch the top-right status indicator cycle "Saving..." → "All changes
   saved" after each edit.
7. Reload the page (`F5`) — your tree should reappear exactly as you left
   it, including collapsed/expanded state.
8. Go back to the landing page — "Last Updated" should reflect your most
   recent mind map edit.
9. Resize your browser (or open on a phone) — the mind map canvas should
   resize with the viewport, no horizontal scrolling on the page itself.

---

## What's Next

- **Phase 3:** Node details side panel — title, YouTube video URL, rich
  notes via Quill (`NodeNote` model), completed checkbox, and autosave.
- **Phase 4:** UI polish, deeper responsive refinement, subtle animations,
  and JSON export/import of a topic's mind map.
