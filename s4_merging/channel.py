"""The return trip to the sender, for real: the reply travels through a noisy channel and is checked by SHA-256.
A corrupted copy fails the hash and is resent, so noise on the way back costs time and cannot change the answer.
dist(t) gives the corruption probability at time t, rnd() gives a float in [0, 1)."""
import hashlib


def sha(msg):
    return hashlib.sha256(msg.encode()).hexdigest()


def corrupt(msg, rnd):
    """Always changes exactly one character."""
    i = int(rnd()*len(msg))
    return msg[:i] + ("x" if msg[i] != "x" else "y") + msg[i+1:]


def send_back(reply, dist, t, rnd, limit=100000):
    """Returns (the reply as received, number of resends)."""
    h = sha(reply)
    for tries in range(limit):
        got = corrupt(reply, rnd) if rnd() < dist(t + 1 + tries) else reply
        if sha(got) == h:
            return got, tries
    raise RuntimeError(f"no clean copy after {limit} sends")
