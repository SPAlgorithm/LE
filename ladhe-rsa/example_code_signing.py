"""
example_code_signing.py — Practical demo of using Ladhe
signatures for software release verification.

Scenario:
  Bob wants to release a binary that Alice can verify is
  genuinely from him, unmodified. No encryption needed —
  just proof of authorship and integrity.

Run:
    python example_code_signing.py
"""

import hashlib
from pathlib import Path

import ladhe_rsa as LR


def simulate_release_flow():
    # --- BOB'S SIDE (the publisher) ---
    print("=" * 60)
    print("  BOB: Setting up signing key (done once)")
    print("=" * 60)
    bob_pk, bob_sk = LR.keygen(up1=5)
    print(f"  Published public key:")
    print(f"    prime: {bob_pk.prime}")
    print(f"    h:     {bob_pk.h.hex()[:48]}...")
    print(f"  (Bob publishes these on his website / in his CA cert)")
    print(f"  NOTE: Ladhe one-time — Bob uses this key for ONE release,")
    print(f"        then generates a fresh key for the next.")
    print()

    # Bob builds some software
    software = b"#!/bin/sh\necho 'Hello from Bob'\n"
    software_hash = hashlib.sha256(software).digest()

    print("=" * 60)
    print("  BOB: Signing software release")
    print("=" * 60)
    print(f"  software bytes: {len(software)}")
    print(f"  sha256(software): {software_hash.hex()[:32]}...")
    signature = LR.sign(software_hash, bob_sk)
    print(f"  signature size: {len(signature.encode())} bytes")
    print()
    print("  Bob ships (software, signature, public_key) to the world.")
    print()

    # --- ATTACKER TRIES TO TAMPER ---
    print("=" * 60)
    print("  ATTACKER: Trying to swap in malicious software")
    print("=" * 60)
    malicious = b"#!/bin/sh\nrm -rf /\n"
    malicious_hash = hashlib.sha256(malicious).digest()
    ok = LR.verify(malicious_hash, signature, bob_pk)
    print(f"  malicious software with Bob's signature: verified = {ok}")
    print(f"  (expected False — signature binds to the original hash)")
    print()

    # --- ALICE'S SIDE (a user) ---
    print("=" * 60)
    print("  ALICE: Downloading and verifying the release")
    print("=" * 60)

    # Alice downloads the (hopefully genuine) software
    downloaded = software   # or `malicious` in a MITM scenario
    downloaded_hash = hashlib.sha256(downloaded).digest()
    print(f"  downloaded hash: {downloaded_hash.hex()[:32]}...")
    ok = LR.verify(downloaded_hash, signature, bob_pk)
    if ok:
        print("  ✓ Signature verifies — software is genuinely from Bob")
        print("  Alice can trust this binary.")
    else:
        print("  ✗ Signature FAILS — someone tampered with the download")
        print("  Alice should refuse to run this binary.")
    print()

    # --- Q: WHY WASN'T ENCRYPTION NEEDED? ---
    print("=" * 60)
    print("  WHY NO ENCRYPTION?")
    print("=" * 60)
    print("""
  Alice wasn't trying to hide the software from attackers —
  she was trying to verify it wasn't MODIFIED by attackers.

  Signatures solve the second problem. Encryption would have
  solved a different problem (confidentiality).

  Bob's software is PUBLIC — anyone can download it. The
  question isn't 'who can see it' but 'was it really made
  by Bob?'.

  This is the core use case for signatures:
    • Software releases (Apple, Microsoft, Linux distros)
    • TLS certificates (who owns this domain?)
    • Blockchain transactions (who authorized this transfer?)
    • Code signing for embedded devices (is this firmware genuine?)
    • Document signatures (did Bob really agree to this contract?)
""")


if __name__ == "__main__":
    simulate_release_flow()
