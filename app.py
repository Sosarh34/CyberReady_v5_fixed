from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import json
import hmac
from pathlib import Path
from functools import wraps
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cyberready.db"

app = Flask(__name__)
app.secret_key = os.environ.get("CYBERREADY_SECRET_KEY", "CyberReady_Local_Demo_2026")
ADMIN_PASSWORD = os.environ.get("CYBERREADY_ADMIN_PASSWORD", "CR-Admin-2026!Secure")

CATEGORIES = {
    "Phishing & Email Security": "Phishing",
    "Passwords & MFA": "Passwords",
    "Social Engineering": "Social Engineering",
    "Device & USB Security": "Device Security",
    "Data Protection & Safe Browsing": "Data & Browsing",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation TEXT NOT NULL,
        difficulty TEXT NOT NULL DEFAULT 'Medium',
        mode TEXT NOT NULL DEFAULT 'challenge',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        department TEXT NOT NULL,
        mode TEXT NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        percentage REAL NOT NULL,
        category_scores TEXT,
        completed_at TEXT NOT NULL
    );
    """)
    count = conn.execute("SELECT COUNT(*) FROM questions WHERE mode='challenge'").fetchone()[0]
    if count == 0:
        seed_challenge_questions(conn)
    phish_count = conn.execute("SELECT COUNT(*) FROM questions WHERE mode='phish'").fetchone()[0]
    if phish_count == 0:
        seed_phish_questions(conn)
    conn.commit()
    conn.close()


def seed_challenge_questions(conn):
    # The original 25-question Cyber Challenge bank.
    questions = [
        ("Phishing & Email Security", "You receive an email that appears to be from HR saying: “URGENT: Salary Account Verification Required.” It asks you to click a link within 30 minutes to prevent payment delays. What should you do?", "Click the link immediately because salary is involved", "Reply to the email asking whether it is genuine", "Contact HR through a known official channel to verify the request", "Forward the email to your colleagues", "C", "Urgency and requests for sensitive information are common phishing indicators. Verify through an independent, trusted channel.", "Easy"),
        ("Phishing & Email Security", "You receive a message saying your Microsoft 365 account will be suspended unless you log in using a provided link. The link uses a strange domain. What is the biggest warning sign?", "The message contains the Microsoft logo", "The link does not appear to be an official Microsoft domain", "Microsoft 365 accounts can be suspended", "The message asks you to log in", "B", "Attackers create fake login pages that look legitimate. Check the actual domain and use trusted bookmarks or official sites.", "Easy"),
        ("Phishing & Email Security", "A colleague sends you an unexpected email with an attachment named “Invoice — Please Open Immediately.” The file is executable. What should you do?", "Open it to see what it contains", "Download it and scan it later", "Verify with the colleague through another channel and report it if suspicious", "Forward it to IT without saying anything", "C", "Unexpected attachments, especially executable files, can contain malware. Verify unexpected files before opening them.", "Medium"),
        ("Phishing & Email Security", "You receive a WhatsApp message from someone claiming to be your CEO: “I’m in a meeting. I need you to urgently purchase gift cards and send me the codes.” What should you do?", "Do it because it is your CEO", "Ask for the CEO’s personal identification", "Verify the request using an established company communication channel", "Send the codes but ask for reimbursement later", "C", "Attackers impersonate executives to pressure employees into unauthorized payments or disclosures. Verify unusual requests independently.", "Medium"),
        ("Phishing & Email Security", "You accidentally click a suspicious link in an email but immediately close the page. What should you do next?", "Ignore it because nothing happened", "Delete the email and continue working", "Report the incident according to company procedure and follow IT/security instructions", "Restart your computer and assume everything is fine", "C", "Closing the page does not guarantee that nothing happened. Prompt reporting allows the organization to investigate.", "Medium"),
        ("Passwords & MFA", "Your company requires a strong password for email, but you use the same password on social media. What is the biggest problem?", "Strong passwords should only contain numbers", "Your social media account could be hacked", "A compromised password could be used to access multiple accounts", "You should change your password every day", "C", "Password reuse creates a domino effect: a compromised password can be tried against other accounts.", "Easy"),
        ("Passwords & MFA", "You receive an unexpected Microsoft Authenticator/MFA approval request even though you are not trying to log in. What should you do?", "Approve it so the notification disappears", "Ignore it", "Deny it and report the suspicious login attempt", "Turn off MFA", "C", "Unexpected MFA requests can indicate that someone has your password and is attempting to access your account.", "Easy"),
        ("Passwords & MFA", "A colleague says: “I’m having trouble accessing the system. Just give me your login details so I can finish this quickly.” What should you do?", "Give them the password because they are a colleague", "Give them the password but change it later", "Refuse and direct them to the appropriate support process", "Give them the password if they promise not to share it", "C", "Credentials should never be shared. Proper access controls should give employees their own accounts.", "Easy"),
        ("Passwords & MFA", "You have several work accounts and struggle to remember all your passwords. Which is the safest option?", "Save them in your phone’s Notes app", "Use the same password everywhere", "Use an approved password manager", "Write them on a note under your keyboard", "C", "An approved password manager can securely store unique passwords and reduce unsafe password reuse.", "Easy"),
        ("Passwords & MFA", "Which password practice provides the strongest protection?", "Davina123", "Password2026!", "A unique, long password/passphrase combined with MFA", "Your birthday plus your surname", "C", "Length, uniqueness and MFA significantly improve account security. Personal information should not be used in passwords.", "Easy"),
        ("Social Engineering", "Someone calls claiming to be from your company’s IT department and says: “We detected malware. Give me your password so I can fix it.” What should you do?", "Give them the password because they are IT", "Ask them to email first and then provide it", "Refuse to provide credentials and verify the caller through an official channel", "Give them the password if they know your employee number", "C", "Legitimate IT staff should not require your password. Attackers use authority and urgency to manipulate employees.", "Easy"),
        ("Social Engineering", "Someone you do not recognize enters your office behind an employee and says: “I forgot my access card. Can you let me through?” What should you do?", "Hold the door open", "Let them in because they appear friendly", "Ask them to follow the organization’s visitor/access procedure", "Ignore them", "C", "Tailgating is a physical social-engineering technique. Follow access-control procedures even when someone appears trustworthy.", "Easy"),
        ("Social Engineering", "You receive a message: “Congratulations! You’ve won ₦500,000. Send your BVN and bank details to claim your prize.” What is the most appropriate response?", "Send the information quickly", "Ask them to send the money first", "Treat it as suspicious and do not provide sensitive information", "Forward it to friends", "C", "Unexpected prizes and requests for sensitive information are common social-engineering tactics.", "Easy"),
        ("Social Engineering", "Someone calls claiming to conduct a survey about your company. They ask what antivirus you use, how many employees you have, and what email system you use. What should you do?", "Answer because none of the information is a password", "Provide only the antivirus information", "Avoid disclosing internal information unless the request is authorized", "Give them false information", "C", "Information that seems harmless can help attackers understand an organization’s technology and structure.", "Medium"),
        ("Social Engineering", "Your manager sends: “I’m travelling and can’t access the payment system. Transfer ₦300,000 to this account immediately. I’ll explain later.” What should you do?", "Transfer the money immediately", "Verify the request using the organization’s established payment-verification process", "Ask another employee to transfer it", "Transfer half first", "B", "Business email compromise and executive impersonation can cause financial losses. Financial requests should follow verification procedures.", "Medium"),
        ("Device & USB Security", "You find a USB drive in the office parking lot labelled “CONFIDENTIAL — STAFF SALARY.” What should you do?", "Plug it into your computer to identify the owner", "Give it to a colleague", "Report it to IT/security personnel without connecting it", "Plug it into a personal computer instead", "C", "Unknown USB devices can contain malware. Never connect unknown removable media to organizational systems.", "Easy"),
        ("Device & USB Security", "You need to leave your desk for 15 minutes. What should you do?", "Leave your laptop unlocked because you’ll return soon", "Lock your computer before leaving", "Turn off the monitor only", "Ask a colleague to watch it", "B", "Locking an unattended device prevents someone nearby from using your active session.", "Easy"),
        ("Device & USB Security", "A coworker asks you to install a browser extension that is not approved by your organization because “it makes work faster.” What should you do?", "Install it immediately", "Install it only on your personal laptop", "Use the approved software process and verify the extension first", "Ask them to install it for you", "C", "Unapproved extensions can access browsing data or introduce malicious code. Use approved software and review requirements.", "Medium"),
        ("Device & USB Security", "Your laptop is connected to the company network when you notice a new USB device you do not recognize. What is the safest response?", "Open it to see what it contains", "Copy its files to a safe folder", "Do not connect or open it and report the device if it is already attached", "Plug it into another computer", "C", "Unknown removable media can be a malware delivery method. Report suspicious devices instead of investigating them yourself.", "Easy"),
        ("Device & USB Security", "Your computer displays an official notification that an important security update is available. What should you do?", "Ignore it permanently", "Install it according to company procedures", "Disable future notifications", "Download an unofficial version from a random website", "B", "Security updates often address vulnerabilities that attackers could exploit.", "Easy"),
        ("Data Protection & Safe Browsing", "You need to send a spreadsheet containing customer information to an external partner. What should you do first?", "Send it through your personal email", "Upload it to any free file-sharing website", "Confirm authorization and use the organization’s approved secure sharing method", "Send it through your personal WhatsApp account", "C", "Sensitive information should only be shared when authorized and through approved secure channels.", "Medium"),
        ("Data Protection & Safe Browsing", "You find the official software vendor website and another site offering a “free cracked version” with premium features unlocked. Which should you use?", "The free cracked version", "The official vendor website", "Whichever website downloads faster", "Both", "B", "Unofficial or pirated software can contain malware, backdoors or unwanted programs.", "Easy"),
        ("Data Protection & Safe Browsing", "You accidentally send a confidential company document to the wrong email address. What should you do?", "Delete the sent email and forget about it", "Immediately report the incident according to company procedures", "Ask the recipient to delete it and do nothing else", "Pretend it did not happen", "B", "Accidental disclosure can still be a security incident. Prompt reporting gives the organization a chance to contain it.", "Medium"),
        ("Data Protection & Safe Browsing", "You visit a website and your browser displays: “Your connection is not private.” What should you do?", "Continue anyway because the website looks legitimate", "Enter your password quickly", "Leave the site and verify that you are using the correct website address", "Disable the browser warning", "C", "Browser security warnings can indicate certificate, configuration or connection problems. Do not ignore them for sensitive services.", "Easy"),
        ("Data Protection & Safe Browsing", "You need to share a company document with a colleague. Which is safest?", "Set it to “Anyone with the link can edit”", "Use the organization’s approved cloud platform and give only the necessary access", "Upload it to your personal cloud account", "Post the document in a public group", "B", "Least privilege reduces unauthorized access and accidental modification.", "Medium"),
    ]
    now = datetime.now().isoformat(timespec="seconds")
    conn.executemany("""
        INSERT INTO questions
        (category, question, option_a, option_b, option_c, option_d,
         correct_answer, explanation, difficulty, mode, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'challenge', ?)
    """, [q + (now,) for q in questions])


def seed_phish_questions(conn):
    phish = [
        ("Email", "FROM: payroll@payr0ll-update.com\nSUBJECT: URGENT — Salary Account Verification\n\nYour salary payment is on hold. Verify your bank details within 30 minutes or your payment may be delayed.\n\n[ VERIFY NOW ]", "The sender domain contains a suspicious spelling", "The email mentions salary", "The message uses a greeting", "The email is short", "A", "The domain payr0ll-update.com uses a zero in place of the expected spelling and is not an obvious official payroll domain. Verify through a trusted channel instead of clicking the link.", "Easy"),
        ("Email", "FROM: it-support@micr0soft-security.com\nSUBJECT: Microsoft 365 password expires today\n\nYour mailbox will be disabled unless you confirm your password immediately.\n\n[ KEEP MY ACCOUNT ]", "It says Microsoft 365", "The sender domain is not an official Microsoft domain", "It uses a button", "It says password", "B", "The sender domain is a major red flag. Attackers commonly imitate trusted brands with lookalike domains.", "Easy"),
        ("WhatsApp", "FROM: Unknown number\n\nCEO: I’m in a meeting and need you to buy ₦200,000 worth of gift cards. Send the codes here when done. Please don’t call because I’m busy.", "The person uses WhatsApp", "The request is urgent and asks for gift-card codes", "The message has no emoji", "The sender says they are busy", "B", "Urgency, secrecy and an unusual financial request are classic executive-impersonation signals. Verify through a known company channel.", "Easy"),
        ("Email", "FROM: recruitment@company-careers.com\nSUBJECT: Final interview document\n\nPlease open the attached .exe file to view your interview schedule. We need it opened today.", "It concerns recruitment", "The attachment is an executable file", "The email has a subject line", "The sender mentions an interview", "B", "Executable attachments are high risk, especially when unexpected. Verify the message and use the organization’s approved reporting process.", "Easy"),
        ("SMS", "Your bank account will be blocked today. Confirm your BVN and PIN at: hxxps://secure-bank-verification.example", "It says your account will be blocked", "It asks for a PIN and uses an unsolicited link", "It uses the word secure", "It is an SMS", "B", "Requests for PINs and sensitive credentials through unsolicited links are strong phishing indicators. Use the bank’s official app or known website instead.", "Easy"),
        ("Email", "FROM: benefits@company.com\nSUBJECT: Staff bonus — action required\n\nWe have credited your bonus. To release it, sign in to your account using the link below.\n\nThe link displayed is: company.com\nBut hovering reveals: login-company-bonus.example", "The email is about a bonus", "The visible link and actual destination do not match", "It contains a subject line", "It comes from a company-looking address", "B", "A mismatched link destination is a strong phishing clue. Never rely only on the text displayed for a link.", "Medium"),
        ("Email", "FROM: ceo.office@company.com\nSUBJECT: Need a quick favour\n\nI’m travelling. Please send me the employee list with phone numbers and home addresses. I need it for a meeting in 10 minutes.", "The request is for employee personal information", "The message says meeting", "The sender uses a company-looking address", "It is only one paragraph", "A", "A request for sensitive personal information combined with urgency should be independently verified before disclosure.", "Medium"),
        ("WhatsApp", "FROM: HR Updates\n\nCongratulations! You have been selected for a staff welfare payment. Send your BVN, NIN and bank login details to this number to receive ₦150,000 today.", "It mentions staff welfare", "It asks for extremely sensitive credentials and identity information", "It uses a money amount", "It comes through WhatsApp", "B", "BVN, NIN and especially bank login details should not be sent through an unsolicited message. Treat this as suspicious and report it.", "Easy"),
    ]
    now = datetime.now().isoformat(timespec="seconds")
    conn.executemany("""
        INSERT INTO questions
        (category, question, option_a, option_b, option_c, option_d,
         correct_answer, explanation, difficulty, mode, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'phish', ?)
    """, [q + (now,) for q in phish])


def get_questions(mode="challenge"):
    conn = get_db()
    rows = conn.execute("SELECT * FROM questions WHERE mode=? ORDER BY id", (mode,)).fetchall()
    conn.close()
    return rows


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    employee_id = request.form.get("employee_id", "").strip()
    department = request.form.get("department", "").strip()
    mode = request.form.get("mode", "challenge")
    if not employee_id or not department:
        flash("Please enter your employee ID and department.")
        return redirect(url_for("index"))
    if mode not in ("challenge", "phish"):
        mode = "challenge"
    questions = get_questions(mode)
    if not questions:
        flash("This challenge has no questions yet.")
        return redirect(url_for("index"))

    # Keep the assessment short: 10 questions per attempt.
    if mode == "challenge":
        # Pick two questions from each threat category where possible.
        selected = []
        seen_categories = []
        for q in questions:
            if q["category"] not in seen_categories:
                seen_categories.append(q["category"])
        for category in seen_categories:
            category_rows = [q for q in questions if q["category"] == category]
            selected.extend(category_rows[:2])
        questions = selected[:10]
    else:
        questions = questions[:10]

    session.clear()
    session["employee_id"] = employee_id
    session["department"] = department
    session["mode"] = mode
    session["question_ids"] = [q["id"] for q in questions]
    session["current"] = 0
    session["answers"] = {}
    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    if "question_ids" not in session:
        return redirect(url_for("index"))
    ids = session["question_ids"]
    current = session["current"]
    if current >= len(ids):
        return redirect(url_for("result"))
    conn = get_db()
    q = conn.execute("SELECT * FROM questions WHERE id=?", (ids[current],)).fetchone()
    conn.close()
    return render_template("quiz.html", q=q, number=current+1, total=len(ids), mode=session["mode"])


@app.route("/answer", methods=["POST"])
def answer():
    if "question_ids" not in session:
        return redirect(url_for("index"))

    try:
        qid = int(request.form["question_id"])
        answer_value = request.form["answer"]
    except (KeyError, ValueError):
        flash("Please select an answer and try again.")
        return redirect(url_for("quiz"))

    conn = get_db()
    q = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    conn.close()

    if not q:
        flash("Question not found. Please restart the challenge.")
        return redirect(url_for("index"))

    session.setdefault("answers", {})
    session["answers"][str(qid)] = answer_value
    session.modified = True

    is_correct = answer_value == q["correct_answer"]
    session["current"] = session.get("current", 0) + 1

    # After the final answer, save the assessment immediately and show results.
    if session["current"] >= len(session["question_ids"]):
        ids = session["question_ids"]
        answers = session.get("answers", {})
        conn = get_db()
        placeholders = ",".join(["?"] * len(ids))
        questions = conn.execute(
            f"SELECT * FROM questions WHERE id IN ({placeholders})", ids
        ).fetchall()

        score = sum(
            1 for item in questions
            if answers.get(str(item["id"])) == item["correct_answer"]
        )
        total = len(questions)
        percentage = round((score / total) * 100) if total else 0

        category_scores = {}
        for item in questions:
            cat = CATEGORIES.get(item["category"], item["category"])
            category_scores.setdefault(cat, [0, 0])
            category_scores[cat][1] += 1
            if answers.get(str(item["id"])) == item["correct_answer"]:
                category_scores[cat][0] += 1

        completed_at = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute("""
            INSERT INTO results
            (employee_id, department, mode, score, total, percentage,
             category_scores, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["employee_id"], session["department"], session["mode"],
            score, total, percentage, json.dumps(category_scores), completed_at
        ))
        result_id = cur.lastrowid
        conn.commit()
        conn.close()

        session["last_result_id"] = result_id

        # Clear quiz state but keep the result ID so /result can display it.
        session.pop("question_ids", None)
        session.pop("current", None)
        session.pop("answers", None)

        return redirect(url_for("result"))

    return render_template(
        "feedback.html",
        q=q,
        selected=answer_value,
        is_correct=is_correct,
        number=session["current"],
        total=len(session["question_ids"]),
        mode=session["mode"]
    )


@app.route("/result")
def result():
    result_id = session.get("last_result_id")
    if result_id:
        conn = get_db()
        saved = conn.execute("SELECT * FROM results WHERE id=?", (result_id,)).fetchone()
        conn.close()
        if saved:
            category_scores = json.loads(saved["category_scores"] or "{}")
            percentage = saved["percentage"]
            if percentage >= 90:
                badge, message = "Cyber Gen Z", "Outstanding! Your cyber instincts are strong."
            elif percentage >= 70:
                badge, message = "Cyber Ready", "Good job! A few areas could still use attention."
            elif percentage >= 50:
                badge, message = "Cyber Apprentice", "You have a foundation, but there are important knowledge gaps."
            else:
                badge, message = "Security Rookie", "Time for a little cyber-upgrade. Review the learning points and try again."
            return render_template("result.html", score=saved["score"], total=saved["total"],
                                   percentage=percentage, category_scores=category_scores,
                                   badge=badge, message=message, employee_id=saved["employee_id"],
                                   department=saved["department"], mode=saved["mode"], result_id=result_id)

    return redirect(url_for("index"))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if hmac.compare_digest(password, ADMIN_PASSWORD):
            session["is_admin"] = True
            return redirect(url_for("admin"))
        flash("Incorrect administrator password.")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    conn = get_db()
    questions = conn.execute("SELECT * FROM questions ORDER BY id").fetchall()
    results = conn.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", questions=questions, results=results)


@app.route("/admin/delete/<int:qid>", methods=["POST"])
@admin_required
def delete_question(qid):
    conn = get_db()
    conn.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/edit/<int:qid>", methods=["GET", "POST"])
@admin_required
def edit_question(qid):
    conn = get_db()
    q = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    if not q:
        conn.close()
        return "Question not found", 404
    if request.method == "POST":
        fields = (
            request.form["category"], request.form["question"],
            request.form["option_a"], request.form["option_b"],
            request.form["option_c"], request.form["option_d"],
            request.form["correct_answer"], request.form["explanation"],
            request.form["difficulty"], request.form.get("mode", "challenge")
        )
        conn.execute("""
            UPDATE questions SET category=?, question=?, option_a=?, option_b=?,
            option_c=?, option_d=?, correct_answer=?, explanation=?, difficulty=?, mode=?
            WHERE id=?
        """, fields + (qid,))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))
    conn.close()
    return render_template("edit_question.html", q=q)


@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def add_question():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO questions
            (category, question, option_a, option_b, option_c, option_d,
             correct_answer, explanation, difficulty, mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["category"], request.form["question"],
            request.form["option_a"], request.form["option_b"],
            request.form["option_c"], request.form["option_d"],
            request.form["correct_answer"], request.form["explanation"],
            request.form["difficulty"], request.form.get("mode", "challenge"),
            datetime.now().isoformat(timespec="seconds")
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))
    return render_template("edit_question.html", q=None)


# Initialize the local database whenever the application starts.
init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
