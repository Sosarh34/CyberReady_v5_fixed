# CyberReady? v2

A local Flask + SQLite security-awareness quiz/game MVP for the capstone project.

## What is new in v2
- Working Cyber Challenge (25 scenarios)
- Working Spot the Phish mode (8 simulated email/SMS/WhatsApp missions)
- Results are saved reliably to SQLite and can be viewed again after completion
- Assessment Dashboard shows attempts and scores
- Result page identifies employee ID, department, mode, score and threat-zone performance
- Question bank remains editable through the local admin page

## Run on Windows
1. Install Python 3.14.x.
2. Extract the ZIP.
3. Run `setup.bat` once.
4. Run `start.bat`.
5. Open `http://127.0.0.1:5000` in Edge.

## Important capstone note
This is a local development MVP. The Flask debug server and admin page are intentionally not production-hardened. Later stages should include authentication/authorization, CSRF protection, secure secret management, input validation, secure headers, debug-off deployment, and testing with Nmap/OWASP ZAP in the lab.


## v3 stability fixes
- setup.bat/start.bat now always run from the project folder.
- Database initializes on app startup.
- Final answers save the assessment and redirect directly to Results.
- Invalid answer submissions are handled cleanly.


## Polished interaction update
This version keeps the core MVP intentionally lightweight: a polished, workplace-appropriate interactive quiz rather than a full game. It adds:
- clearer visual hierarchy and category cues
- subtle hover/selection/progress animations
- medium-intensity correct/incorrect feedback cards
- rotating friendly feedback phrases
- emoji reactions (with no external sound required)
- improved results presentation
- Spot the Phish remains a focused message-identification mode


## v5 design/security changes
- Cyber Challenge reduced to 10 concise questions per attempt.
- Spot the Phish reduced to 10 missions and changed from multiple-choice to clickable message zones.
- Staff quiz access is separate from administrator access.
- Admin area requires a separate administrator password.
- Default local demo admin password: `CR-Admin-2026!Secure`
- For stronger deployment security, set `CYBERREADY_ADMIN_PASSWORD` as an environment variable instead of relying on the demo default.
