"""Stella: সময় যাচাই ও শাশ্বত ভূমিকার সুরক্ষিত ভান্ডার।"""
import base64
import hashlib
import hmac
import ssl
import time
import urllib.request
from email.utils import parsedate_to_datetime

_BLOB = "".join([
    "Pa<)eKj|@<V5RxrO_>aIU6tO#S@mhw7!r>+ExYkqFYw*nkd_x+{Cbgx4E^<x",
    "d@}O2*C-~eD#<DFe@xKjLIKy7p*h2?U)6z6Qol|g78Ke~fjoJFn%6_$AciSw",
    "_dZ^Na6!6;V<VJ_h05ERi^yW)!Z8YgX_WuTzi=QiJf=y<2z7S+qcjGhl5@Hg",
    "13YT?9MP_bkr!G3NjG4ZN@q8wfkB;wD3nt95eLGnq7yq7HZ|Fk%>K(o>}wGE",
    "h`BMVMcvouXd?-J@tmvKLJ{$Ha+TnwG+u7}guL2HU2m6-BVxqk@SItRXeSJ@",
    "J&q6&sqvUteV-TE1cI@8UZy%G>IQ*5LY!3W>twEsGNB1?Cp}ys_~Fg)rmyd7",
    "a86;iCUcq~!8FyaOM$&$N)-`G*_M*1_QIx_MN-r`1LaD~xHT@u#R%K_W^32I",
    "C68uOJFB3xC`Xm()Dc+Q6V#D~YbO)DR_Ov>24=hV24Db`0O}(4An%7zqeWCH",
    "SAUV6Mn6=s#+i1!iDsa%w$Dx<2a0v0YS)gVVhf)a1)uw@CPK@;&(2k|863Dj",
    "B16A)kvuunP9v_hH6nLD!;w1LwRnrQ0~c?n!QB^r({ASptAzk;F%8G|)KMSQ",
    "A=dlrqxRSqgvZ>}zB&O}(vjbaUikk%quThMe8J;Ie;0^l<N",
])

def _p0():
    a = bytes.fromhex("238d01c70f298aff22d856547af9ce10afee28cfd6c55daa74e286a9e0276be1")
    b = bytes(x ^ y for x, y in zip(bytes.fromhex("801e1ea2a61b0be843a422bc6671b307b4168c9d9129a93b3498a9be424f8284"),
                                    hashlib.sha256("467e16210643".encode()).digest()))
    c = bytes((v - 37 * k) % 256 for k, v in enumerate([158, 125, 4, 122, 0, 233, 61, 139, 10, 197, 0, 212, 82, 115, 222, 186, 216, 84, 215, 195, 112, 216, 68, 120, 43, 54, 140, 152, 118, 86, 171, 143]))
    return bytes(x ^ y ^ z for x, y, z in zip(a, b, c))

def _p1():
    a = bytes.fromhex("65fc6bbf25371350bdda1eeff6411f3d5f0a9db5526723bc7b412b4cbcc718a4")
    b = bytes(x ^ y for x, y in zip(bytes.fromhex("c20b9104b8c35d6e112d64c3cdbe5ea0c11d50b15f953812fc8edf76dcb26a2b"),
                                    hashlib.sha256("ddf47d4da2d4".encode()).digest()))
    c = bytes((v - 37 * k) % 256 for k, v in enumerate([176, 100, 138, 149, 53, 195, 48, 150, 230, 69, 166, 183, 231, 193, 49, 82, 213, 142, 209, 190, 112, 161, 75, 227, 33, 120, 119, 217, 95, 189, 57, 65]))
    return bytes(x ^ y ^ z for x, y, z in zip(a, b, c))

def _p2():
    a = bytes.fromhex("f5032efce7bd4b8ac4c86bbbe884c2766d00a6bd90f7e55b99b02d2ffef4c90f")
    b = bytes(x ^ y for x, y in zip(bytes.fromhex("7283a9a13afd30c71bfa7225f4ea002ba6672fd297201bf1823c5ea06f5748ee"),
                                    hashlib.sha256("292ab1b2714f".encode()).digest()))
    c = bytes((v - 37 * k) % 256 for k, v in enumerate([80, 154, 159, 89, 15, 192, 111, 189, 50, 121, 0, 94, 232, 245, 81, 188, 115, 2, 218, 107, 13, 49, 208, 79, 130, 2, 44, 40, 63, 160, 53, 47]))
    return bytes(x ^ y ^ z for x, y, z in zip(a, b, c))


def _kdf(secret, salt):
    k = hashlib.pbkdf2_hmac("sha256", secret, salt, 60000, 64)
    return k[:32], k[32:]


def _stream(key, nonce, n):
    out = bytearray()
    c = 0
    while len(out) < n:
        out += hmac.new(key, nonce + c.to_bytes(8, "big"), hashlib.sha256).digest()
        c += 1
    return bytes(out[:n])


def _unseal(blob, secret):
    salt, nonce, ct, tag = blob[:16], blob[16:32], blob[32:-32], blob[-32:]
    ek, mk = _kdf(secret, salt)
    if not hmac.compare_digest(tag, hmac.new(mk, salt + nonce + ct, hashlib.sha256).digest()):
        raise ValueError("bad")
    return bytes(a ^ b for a, b in zip(ct, _stream(ek, nonce, len(ct))))


_cache = {"net": None, "mono": None, "checked": 0.0}
_HOSTS = ("https://www.google.com", "https://www.cloudflare.com",
          "https://www.microsoft.com", "https://www.apple.com")


def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _fetch(url, ctx):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=3, context=ctx) as r:
        return parsedate_to_datetime(r.headers.get("Date")).timestamp()


def secure_now():
    """ইন্টারনেট থেকে যাচাই করা আসল সময় (ফোনের ঘড়ি নয়)। যাচাই না হলে None।"""
    mono = time.monotonic()
    if _cache["net"] is not None and mono - _cache["checked"] < 600:
        return _cache["net"] + (mono - _cache["mono"])
    if _cache["net"] is None and _cache["checked"] and mono - _cache["checked"] < 20:
        return None  # সম্প্রতি ব্যর্থ হয়েছে, বারবার নেট চেষ্টা নয়
    ctx = _ctx()
    got = []
    for h in _HOSTS:
        try:
            got.append(_fetch(h, ctx))
        except Exception:
            continue
        if len(got) == 2:
            break
    _cache["checked"] = mono
    if len(got) == 2 and abs(got[0] - got[1]) < 300:
        _cache["net"], _cache["mono"] = min(got), time.monotonic()
        return _cache["net"]
    if _cache["net"] is not None:  # আগে যাচাই হয়েছিল: মনোটোনিক ঘড়ি দিয়ে এগিয়ে নেওয়া
        return _cache["net"] + (mono - _cache["mono"])
    return None


def get_foreword():
    """শুধু সময় হলে stella.py এটাকে ডাকে; তিন স্তর খুলে লেখা ফেরত দেয়।"""
    try:
        data = base64.b85decode(_BLOB)
        for p in (_p2, _p1, _p0):
            data = _unseal(data, p())
        return data.decode("utf-8")
    except Exception:
        return None
