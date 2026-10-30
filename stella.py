import ast
import getpass
import hashlib
import hmac
import json
import math
import operator
import os
import secrets
import shutil
import time
from datetime import datetime, timedelta, timezone

# ফাইল পাথ
DATABASE_FILE = "stella_brain.json"
BACKUP_FILE = "stella_backup.json"

# [ PERMANENT LOCK ]: Genesis Time (২৩ মার্চ, ২০২৬ | ২২:০৪:৫৮ বাংলাদেশ সময়)
GENESIS_TIMESTAMP = 1774281898.0
BD_TZ = timezone(timedelta(hours=6))
NINETY_NINE_YEARS_SEC = 99 * 365.25 * 24 * 3600
OPEN_DURATION_SEC = 99 * 60
YEAR_SEC = 365.25 * 24 * 3600
MAX_LOGIN_ATTEMPTS = 3

FOREWORD_TEXT = (
    "মহাজাগতিক এই সমীকরণ থামাবার সাধ্য কার?\n"
    " সমীকরণের বাইরে নিরাকার অস্তিত্ব যার;\n"
    " ঠেকাও তবে অয়ণে মাথা..\n"
    " প্রাণের রশি চরণে গাঁথা।"
)


# ───────────────────────── পাসওয়ার্ড / পিন ─────────────────────────
PBKDF2_ROUNDS = 100_000


def ask_secret(prompt):
    """getpass কাজ না করলে (Pyodide/মোবাইল অ্যাপ) সাধারণ input() ব্যবহার করে।"""
    try:
        return getpass.getpass(prompt)
    except KeyboardInterrupt:
        raise
    except Exception:
        return input(prompt)


def _pbkdf2(password, salt, rounds):
    """hashlib.pbkdf2_hmac না থাকলে (যেমন Pyodide/ব্রাউজার Python) হাতে লেখা PBKDF2-HMAC-SHA256।"""
    if hasattr(hashlib, "pbkdf2_hmac"):
        return hashlib.pbkdf2_hmac("sha256", password, salt, rounds)
    prf = hmac.new(password, digestmod=hashlib.sha256)
    u_prev_obj = prf.copy()
    u_prev_obj.update(salt + b"\x00\x00\x00\x01")
    u = u_prev_obj.digest()
    result = int.from_bytes(u, "big")
    for _ in range(rounds - 1):
        h = prf.copy()
        h.update(u)
        u = h.digest()
        result ^= int.from_bytes(u, "big")
    return result.to_bytes(32, "big")


def hash_secret(secret, salt=None):
    salt = salt or secrets.token_hex(16)
    secret = secret.strip().translate(BN_DIGITS)  # বাংলা সংখ্যা = ইংরেজি সংখ্যা
    digest = _pbkdf2(secret.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ROUNDS)
    return f"pbkdf2${salt}${digest.hex()}"


def verify_secret(secret, stored):
    """হ্যাশ করা মান যাচাই করে। পুরনো প্লেইন-টেক্সট ডাটাও সাপোর্ট করে।"""
    if isinstance(stored, str) and stored.startswith("pbkdf2$"):
        try:
            _, salt, _ = stored.split("$")
        except ValueError:
            return False
        return hmac.compare_digest(hash_secret(secret, salt), stored)
    return hmac.compare_digest(str(secret).strip().translate(BN_DIGITS).encode("utf-8"),
                               str(stored).strip().translate(BN_DIGITS).encode("utf-8"))


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith("pbkdf2$")


# ───────────────────────── সময় / লিমিট ─────────────────────────
def get_cosmic_limit():
    """Genesis Point থেকে ১০০x গতিতে মেমোরি লিমিট গণনা"""
    elapsed = max(0, time.time() - GENESIS_TIMESTAMP)
    return (13.8 * 93.0) + (elapsed * 100)


def _cycle_position():
    cycle_total = NINETY_NINE_YEARS_SEC + OPEN_DURATION_SEC
    return (time.time() - GENESIS_TIMESTAMP) % cycle_total


def get_foreword_status():
    pos = _cycle_position()
    if pos < NINETY_NINE_YEARS_SEC:
        remaining = NINETY_NINE_YEARS_SEC - pos
        y = int(remaining // YEAR_SEC)
        d = int((remaining % YEAR_SEC) // 86400)
        return f"Locked (🔒) - {y}Y {d}D left", False
    return "Unlocked (🔓) - Active Now", True


def handle_eternal_foreword():
    pos = _cycle_position()
    print("\n" + "━" * 55)
    print("        📜 THE ETERNAL FOREWORD (শাশ্বত ভূমিকা) 📜")
    print("━" * 55)
    if pos < NINETY_NINE_YEARS_SEC:
        rem = NINETY_NINE_YEARS_SEC - pos
        y = int(rem // YEAR_SEC)
        d = int((rem % YEAR_SEC) // 86400)
        h = int((rem % 86400) // 3600)
        m = int((rem % 3600) // 60)
        s = int(rem % 60)
        print(" [ STATUS ]: LOCKED (🔒)")
        print(f" [ COUNTDOWN ]: {y}Y {d}D {h}H {m}M {s}S")
        print("\n 'মহাজাগতিক এই সমীকরণ থামাবার সাধ্য কার?'")
    else:
        print(" [ STATUS ]: UNLOCKED (🔓)")
        print("-" * 55)
        print(f" \"{FOREWORD_TEXT}\"")
        print("-" * 55)
        time_left = OPEN_DURATION_SEC - (pos - NINETY_NINE_YEARS_SEC)
        print(f" [ CLOSING IN ]: {int(time_left // 60)}M {int(time_left % 60)}S")
    print("━" * 55 + "\n")


def clear_screen():
    try:
        os.system("clear" if os.name == "posix" else "cls")
    except Exception:
        print("\n" * 3)


def show_welcome_screen(name):
    limit = get_cosmic_limit()
    f_status, _ = get_foreword_status()
    genesis = datetime.fromtimestamp(GENESIS_TIMESTAMP, BD_TZ)
    now = datetime.now(BD_TZ)
    clear_screen()
    print("=" * 62)
    print(f"✨ WELCOME TO THE STELLA ETERNAL OS: {name.upper()} ✨")
    print("=" * 62)
    print(f" 📅 Date: {now.strftime('%d %B, %Y')} | ⏰ Time: {now.strftime('%I:%M:%S %p')}")
    print("-" * 62)
    print(f" 🚀 Genesis : {genesis.strftime('%B %d, %Y | %I:%M:%S %p')} (BST)")
    print(f" 🧠 Memory  : {int(limit):,}.00 QB (100x Growth)")
    print(f" 📜 Foreword: {f_status}")
    print("-" * 62)
    print("=" * 62 + "\n")


# ───────────────────────── ডাটা লোড / সেভ ─────────────────────────
def default_data():
    return {
        "password": hash_secret("0000"),
        "vault_pin": hash_secret("0000"),
        "nickname": "স্টেলা",
        "knowledge": {},
        "notes": [],
        "vault": [],
        "capsules": [],
        "reminders": [],
    }


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if not isinstance(d, dict):
        raise ValueError("invalid structure")
    return d


def load_data():
    """মূল ফাইল নষ্ট হলে ব্যাকআপ থেকে লোড করে; দুটোই নষ্ট হলে ফাইল না মুছে নতুন ডাটা দেয়।"""
    defaults = default_data()
    for path in (DATABASE_FILE, BACKUP_FILE):
        if os.path.exists(path):
            try:
                d = _read_json(path)
                for k, v in defaults.items():
                    d.setdefault(k, v)
                if path == BACKUP_FILE:
                    print("⚠️ মূল ডাটাফাইল নষ্ট ছিল, ব্যাকআপ থেকে লোড হয়েছে।")
                return d
            except (json.JSONDecodeError, OSError, ValueError):
                print(f"⚠️ {path} পড়া যায়নি।")
                try:
                    shutil.copy(path, path + ".corrupt")
                except OSError:
                    pass
    return defaults


def save_data(data):
    """অ্যাটমিক সেভ: আগের ভালো ফাইল ব্যাকআপ হয়, তারপর টেম্প ফাইল থেকে replace।"""
    if os.path.exists(DATABASE_FILE):
        try:
            _read_json(DATABASE_FILE)  # শুধু ভালো ফাইলই ব্যাকআপ হবে
            shutil.copy(DATABASE_FILE, BACKUP_FILE)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    tmp = DATABASE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, DATABASE_FILE)


# ───────────────────────── হেল্প মেনু ─────────────────────────
COMMAND_NAMES = {
    "0": "eternal", "1": "menu", "2": "count", "3": "manage", "4": "set-name",
    "5": "find", "6": "clean", "7": "vault", "8": "secret", "9": "quiz",
    "10": "capsule", "11": "open-capsule", "12": "note", "13": "notes",
    "14": "backup", "15": "calc", "16": "clear", "17": "time", "18": "remind",
    "19": "update", "20": "exit", "21": "chg-pass", "22": "chg-pin",
}

ALIASES = {
    "the eternal foreword": "eternal", "foreword": "eternal",
    "help": "menu",
    "count-x-stella": "count",
    "manage-files": "manage",
    "deep-clean": "clean",
    "open-vault": "vault",
    "secret-chat": "secret",
    "start-quiz": "quiz",
    "নোট": "note", "নোট দেখাও": "notes",
    "backup-now": "backup",
    "clear-tab": "clear",
    "সময়": "time", "বাজে": "time",
    "change-password": "chg-pass", "change-vault-pin": "chg-pin",
}

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def resolve_command(text):
    low = text.strip().lower().translate(BN_DIGITS)
    if low in COMMAND_NAMES:
        return COMMAND_NAMES[low]
    if low in ALIASES:
        return ALIASES[low]
    if low in COMMAND_NAMES.values():
        return low
    return None


def show_help_menu(name):
    print("\n" + "━" * 60)
    print(f"         🌟 {name}: SYSTEM COMMAND INTERFACE 🌟")
    print("━" * 60)
    cmds = [
        "০. eternal      -> শাশ্বত ভূমিকা (🔒 ৯৯ বছরের লক)",
        "১. menu / help  -> কমান্ডের পূর্ণাঙ্গ তালিকা",
        "২. count        -> Genesis থেকে ১০০x লাইভ লিমিট (১০ সেকেন্ড)",
        "৩. manage       -> মেমোরি স্ট্যাটাস ও স্টোরেজ চেক",
        "৪. set-name     -> স্টেলার ডাকনাম পরিবর্তন",
        "৫. find         -> সেভ করা তথ্যের ভেতর শব্দ খোঁজা",
        "৬. clean        -> ডুপ্লিকেট ডাটা পরিষ্কার",
        "৭. vault        -> পিন দিয়ে গোপন সিন্দুক খোলা",
        "৮. secret       -> অফ-রেকর্ড চ্যাট (সেভ হয় না)",
        "৯. quiz         -> শেখানো তথ্য নিয়ে কুইজ",
        "১০. capsule     -> টাইম ক্যাপসুল রাখা",
        "১১. open-capsule-> সময় হওয়া ক্যাপসুল খোলা",
        "১২. note / নোট  -> ডায়েরিতে নতুন নোট লেখা",
        "১৩. notes       -> তারিখসহ সব নোট দেখা",
        "১৪. backup      -> ম্যানুয়ালি ব্যাকআপ",
        "১৫. calc        -> গাণিতিক হিসাব",
        "১৬. clear       -> স্ক্রিন পরিষ্কার ও ড্যাশবোর্ড",
        "১৭. time / সময় -> বর্তমান সময়",
        "১৮. remind      -> রিমাইন্ডার সেট",
        "১৯. update      -> শেখানো তথ্য সংশোধন",
        "২০. exit        -> বন্ধ করা",
        "২১. chg-pass    -> লগইন পাসওয়ার্ড পরিবর্তন",
        "২২. chg-pin     -> ভল্ট পিন পরিবর্তন",
    ]
    for c in cmds:
        print(f" {c}")
    print("\n (সংখ্যা ইংরেজি/বাংলা দুই রকমই চলবে। 'menu-র নাম'ও ('deep-clean' ইত্যাদি) চলবে।)")
    print("━" * 60 + "\n")


# ───────────────────────── নিরাপদ ক্যালকুলেটর ─────────────────────────
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_FUNCS = {n: getattr(math, n) for n in
          ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "factorial", "floor", "ceil")}
_FUNCS["abs"] = abs
_FUNCS["round"] = round
_CONSTS = {"pi": math.pi, "e": math.e}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("ঘাত অনেক বড়")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _FUNCS and not node.keywords):
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError("অনুমোদিত নয়")


def safe_calc(expr):
    return _eval(ast.parse(expr.translate(BN_DIGITS).replace("^", "**"), mode="eval"))


# ───────────────────────── কমান্ড হ্যান্ডলার ─────────────────────────
def now_str():
    return datetime.now(BD_TZ).strftime("%d-%m-%Y %I:%M %p")


def cmd_count():
    print("✨ লাইভ লিমিট (১০ সেকেন্ড, প্রতি সেকেন্ডে একবার):")
    try:
        for _ in range(10):
            print(f"  ✨ Current Limit: {get_cosmic_limit():,.4f} QB", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    print()


def cmd_manage(data):
    size = os.path.getsize(DATABASE_FILE) / 1024 if os.path.exists(DATABASE_FILE) else 0.0
    print(f"\n📂 Used: {size:.2f} KB | 🚀 Limit (প্রতীকী): {int(get_cosmic_limit()):,} QB")
    print(f"📚 জ্ঞান: {len(data['knowledge'])} | 📝 নোট: {len(data['notes'])} | "
          f"🔐 ভল্ট: {len(data['vault'])} | ⏳ ক্যাপসুল: {len(data['capsules'])}\n")


def cmd_find(data):
    q = input("🔎 কী খুঁজবেন? ").strip().lower()
    if not q:
        return
    found = 0
    for k, v in data["knowledge"].items():
        if q in k.lower() or q in str(v).lower():
            print(f" 📚 {k} -> {v}")
            found += 1
    for n in data["notes"]:
        if q in n["text"].lower():
            print(f" 📝 [{n['time']}] {n['text']}")
            found += 1
    print(f"মোট {found}টি ফলাফল।\n" if found else "কিছু পাওয়া যায়নি।\n")


def cmd_clean(data):
    seen, notes = set(), []
    for n in data["notes"]:
        key = n["text"].strip().lower()
        if key not in seen:
            seen.add(key)
            notes.append(n)
    removed_notes = len(data["notes"]) - len(notes)
    data["notes"] = notes
    empty = [k for k, v in data["knowledge"].items() if not str(v).strip()]
    for k in empty:
        del data["knowledge"][k]
    data["reminders"] = [r for r in data["reminders"] if not r.get("done")]
    save_data(data)
    print(f"🧹 {removed_notes}টি ডুপ্লিকেট নোট, {len(empty)}টি খালি তথ্য ও সম্পন্ন রিমাইন্ডার মুছেছি।\n")


def cmd_vault(data):
    if not verify_secret(ask_secret("🔐 ভল্টের পিন (ডিফল্ট '0000'): "), data["vault_pin"]):
        print("❌ ভুল পিন!\n")
        return
    print("📂 ভল্ট উন্মুক্ত। (a = যোগ, v = দেখা, d = মোছা, enter = বের)")
    while True:
        c = input("ভল্ট> ").strip().lower()
        if c == "a":
            t = input("গোপন তথ্য: ").strip()
            if t:
                data["vault"].append({"time": now_str(), "text": t})
                save_data(data)
                print("✅ সংরক্ষিত।")
        elif c == "v":
            if not data["vault"]:
                print("(খালি)")
            for i, it in enumerate(data["vault"], 1):
                print(f" {i}. [{it['time']}] {it['text']}")
        elif c == "d":
            try:
                i = int(input("কত নম্বর মুছবেন? ")) - 1
                data["vault"].pop(i)
                save_data(data)
                print("🗑️ মোছা হয়েছে।")
            except (ValueError, IndexError):
                print("❌ ভুল নম্বর।")
        else:
            break
    print()


def cmd_secret(name):
    print("🤫 অফ-রেকর্ড চ্যাট (কিছুই সেভ হবে না)। বের হতে 'exit' লিখুন।")
    while True:
        t = input("তুমি (গোপন): ").strip()
        if t.lower() in ("exit", "quit", "বের"):
            print("🔒 অফ-রেকর্ড শেষ।\n")
            return
        if t:
            print(f"{name}: শুনছি... 🤍 (এটা কোথাও সেভ হচ্ছে না)")


def cmd_quiz(data, name):
    items = list(data["knowledge"].items())
    if not items:
        print("আগে আমাকে কিছু শেখান!\n")
        return
    import random
    random.shuffle(items)
    score = 0
    for q, a in items[:5]:
        ans = input(f"❓ {q}\n   উত্তর: ").strip()
        if ans.lower() == str(a).strip().lower():
            print("✅ ঠিক!")
            score += 1
        else:
            print(f"❌ সঠিক উত্তর: {a}")
    print(f"🏆 স্কোর: {score}/{min(5, len(items))}\n")


def cmd_capsule(data):
    msg = input("✉️ ভবিষ্যতের জন্য বার্তা: ").strip()
    if not msg:
        return
    date = input("কবে খোলা যাবে? (YYYY-MM-DD): ").strip()
    try:
        open_at = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=BD_TZ)
    except ValueError:
        print("❌ তারিখের ফরম্যাট ভুল।\n")
        return
    data["capsules"].append({"created": now_str(), "open_at": open_at.timestamp(), "text": msg, "opened": False})
    save_data(data)
    print(f"⏳ ক্যাপসুল সিল হলো, {date} তারিখে খোলা যাবে।\n")


def cmd_open_capsule(data):
    now, opened = time.time(), 0
    for c in data["capsules"]:
        if now >= c["open_at"]:
            print(f" 💌 [{c['created']}] {c['text']}")
            c["opened"] = True
            opened += 1
    waiting = sum(1 for c in data["capsules"] if now < c["open_at"])
    if opened:
        save_data(data)
    print(f"{opened}টি খোলা হয়েছে, {waiting}টি এখনো অপেক্ষায়।\n")


def cmd_note(data):
    t = input("📝 নোট: ").strip()
    if t:
        data["notes"].append({"time": now_str(), "text": t})
        save_data(data)
        print("✅ নোট সেভ হয়েছে।\n")


def cmd_notes(data):
    if not data["notes"]:
        print("কোনো নোট নেই।\n")
        return
    for i, n in enumerate(data["notes"], 1):
        print(f" {i}. [{n['time']}] {n['text']}")
    print()


def cmd_backup(data):
    save_data(data)
    shutil.copy(DATABASE_FILE, BACKUP_FILE)
    print("💾 ব্যাকআপ সম্পন্ন।\n")


def cmd_calc():
    expr = input("🧮 হিসাব (যেমন 2^10 + sqrt(16)): ").strip()
    if not expr:
        return
    try:
        res = safe_calc(expr)
        print(f" = {res}\n")
    except (ValueError, SyntaxError, ZeroDivisionError, TypeError, OverflowError):
        print("❌ হিসাবটি বোঝা বা সমাধান করা যায়নি।\n")


def cmd_remind(data):
    text = input("⏰ কী মনে করাবো? ").strip()
    if not text:
        return
    try:
        mins = float(input("কত মিনিট পরে? ").translate(BN_DIGITS))
    except ValueError:
        print("❌ সংখ্যা দিন।\n")
        return
    data["reminders"].append({"text": text, "due": time.time() + mins * 60, "done": False})
    save_data(data)
    print(f"✅ {mins:g} মিনিট পরে মনে করাবো। (পরের কমান্ডের সময় দেখাবো)\n")


def check_reminders(data):
    changed = False
    for r in data["reminders"]:
        if not r.get("done") and time.time() >= r["due"]:
            print(f"\n🔔 রিমাইন্ডার: {r['text']}\n")
            r["done"] = True
            changed = True
    if changed:
        save_data(data)


def cmd_update(data):
    key = input("কোন তথ্য সংশোধন করবেন? (প্রশ্ন লিখুন): ").strip().lower()
    if key not in data["knowledge"]:
        print("❌ এই নামে কিছু শেখানো নেই।\n")
        return
    print(f"বর্তমান উত্তর: {data['knowledge'][key]}")
    new = input("নতুন উত্তর: ").strip()
    if new:
        data["knowledge"][key] = new
        save_data(data)
        print("✅ হালনাগাদ হয়েছে।\n")


def cmd_set_name(data):
    n = input("নতুন ডাকনাম: ").strip()
    if n:
        data["nickname"] = n
        save_data(data)
        print(f"✅ এখন থেকে আমি {n}।\n")
    return data["nickname"]


def cmd_change_secret(data, field, label):
    if not verify_secret(ask_secret(f"বর্তমান {label}: "), data[field]):
        print(f"❌ ভুল {label}!\n")
        return
    new = ask_secret(f"নতুন {label}: ")
    if not new:
        print("❌ খালি রাখা যাবে না।\n")
        return
    if ask_secret(f"নতুন {label} আবার দিন: ") != new:
        print("❌ মিলেনি।\n")
        return
    data[field] = hash_secret(new)
    save_data(data)
    print(f"✅ {label} পরিবর্তন সফল।\n")


# ───────────────────────── লগইন ও মূল লুপ ─────────────────────────
def login(data):
    print(f"--- {data['nickname']}: Security Login ---")
    print("(প্রথমবারের ডিফল্ট পাসওয়ার্ড '0000'; এরপর পরিবর্তন করে নিন)")
    for left in range(MAX_LOGIN_ATTEMPTS, 0, -1):
        pw = ask_secret("🔑 পাসওয়ার্ড: ")
        if verify_secret(pw, data["password"]):
            if not is_hashed(data["password"]):  # পুরনো প্লেইন-টেক্সট থেকে মাইগ্রেট
                data["password"] = hash_secret(pw)
            if not is_hashed(data["vault_pin"]):
                data["vault_pin"] = hash_secret(data["vault_pin"])
            save_data(data)
            return True
        print(f"❌ ভুল পাসওয়ার্ড! আর {left - 1}বার চেষ্টা করা যাবে।")
    return False


def run_stella():
    data = load_data()
    clear_screen()
    try:
        if not login(data):
            print("🚫 অনেকবার ভুল। প্রস্থান।")
            return
    except (KeyboardInterrupt, EOFError):
        print("\nবিদায়!")
        return

    name = data["nickname"]
    show_welcome_screen(name)

    while True:
        try:
            check_reminders(data)
            user_input = input("আবির: ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n(বের হতে 'exit' লিখুন)")
            continue
        if not user_input:
            continue

        try:
            cmd = resolve_command(user_input)

            if cmd == "exit":
                print("বিদায় আবির!")
                break
            elif cmd == "eternal": handle_eternal_foreword()
            elif cmd == "menu": show_help_menu(name)
            elif cmd == "clear": show_welcome_screen(name)
            elif cmd == "count": cmd_count()
            elif cmd == "manage": cmd_manage(data)
            elif cmd == "set-name": name = cmd_set_name(data)
            elif cmd == "find": cmd_find(data)
            elif cmd == "clean": cmd_clean(data)
            elif cmd == "vault": cmd_vault(data)
            elif cmd == "secret": cmd_secret(name)
            elif cmd == "quiz": cmd_quiz(data, name)
            elif cmd == "capsule": cmd_capsule(data)
            elif cmd == "open-capsule": cmd_open_capsule(data)
            elif cmd == "note": cmd_note(data)
            elif cmd == "notes": cmd_notes(data)
            elif cmd == "backup": cmd_backup(data)
            elif cmd == "calc": cmd_calc()
            elif cmd == "time":
                print(f"🕒 এখন: {datetime.now(BD_TZ).strftime('%d %B %Y, %I:%M:%S %p')}\n")
            elif cmd == "remind": cmd_remind(data)
            elif cmd == "update": cmd_update(data)
            elif cmd == "chg-pass": cmd_change_secret(data, "password", "পাসওয়ার্ড")
            elif cmd == "chg-pin": cmd_change_secret(data, "vault_pin", "ভল্ট পিন")
            else:
                # সাধারণ নলেজ লজিক (কমান্ড নয় এমন ইনপুট)
                key = user_input.lower()
                if key in data["knowledge"]:
                    print(f"{name}: {data['knowledge'][key]}")
                else:
                    ans = input(f"{name}: জানি না। উত্তর কি? (স্কিপ: এন্টার): ").strip()
                    if ans:
                        data["knowledge"][key] = ans
                        save_data(data)
        except KeyboardInterrupt:
            print("\n(বাতিল)")
        except EOFError:
            break


if __name__ == "__main__":
    run_stella()
