"""Verify a raw extract file against the hash computed in the browser.

The browser computes a djb2-style hash over every line except SOURCE and
CHECK lines (joined with '\n'), using UTF-16 code units. Python's ord() on
BMP characters gives the same values.
"""
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().split("\n")
body = [l for l in lines if l and not l.startswith(("SOURCE|", "CHECK|"))]
text = "\n".join(body)
h = 5381
for ch in text:
    h = (h * 33 + ord(ch)) % 1000000007
expected = None
for l in lines:
    if l.startswith("CHECK|"):
        expected = int(l.split("hash=")[1].split("|")[0])
print(path, "computed", h, "expected", expected,
      "OK" if h == expected else "MISMATCH")
