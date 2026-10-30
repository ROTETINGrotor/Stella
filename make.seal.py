"""বিল্ডের সময় চলে: stella.py ও eternal.py-র ফিঙ্গারপ্রিন্ট _seal.py-তে লেখে।"""
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ("stella.py", "eternal.py")


def fingerprint(base):
    h = hashlib.sha256()
    for name in FILES:
        with open(os.path.join(base, name), "rb") as f:
            data = f.read().replace(b"\r\n", b"\n")
        h.update(hashlib.sha256(data).digest())
    return h.hexdigest()


if __name__ == "__main__":
    with open(os.path.join(HERE, "_seal.py"), "w") as f:
        f.write(f'SEAL = "{fingerprint(HERE)}"\n')
    print("sealed")
