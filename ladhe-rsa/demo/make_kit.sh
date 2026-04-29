#!/usr/bin/env bash
#
# make_kit.sh — Build a self-contained Ladhe verification kit.
#
# Output: ladhe_demo_kit.zip in the current directory, containing:
#   - verify.py           (zero-dep standalone verifier)
#   - ca.cert.pem         (the CA's cert, Ladhe-native JSON-in-PEM)
#   - alice.cert.pem      (Alice's cert, Ladhe-native)
#   - ca.x509.pem         (the CA's cert, X.509 DER-in-PEM, openssl-parseable)
#   - alice.x509.pem      (Alice's cert, X.509 DER-in-PEM)
#   - <doc>               (the document Alice signed)
#   - <doc>.sig           (Alice's signature on the document)
#   - README.txt          (instructions for the recipient)
#
# The X.509 PEM files require asn1crypto on the BUILDER's machine
# (pip install asn1crypto). Recipients only need openssl, which is
# already on every macOS/Linux/Windows box.
#
# Usage:
#     ./make_kit.sh                                # uses purchase_order.txt
#     ./make_kit.sh path/to/some_other_file.docx   # signs that file instead
#
# Prereq: ./setup.sh has been run at least once (creates ca/ alice/ bob/).

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LADHE="$(cd "$HERE/.." && pwd)"

# ---------------------------------------------------------------------
# Pick the document to sign (default: purchase_order.txt)
# ---------------------------------------------------------------------
DOC_SRC="${1:-$HERE/purchase_order.txt}"
if [[ ! -f "$DOC_SRC" ]]; then
    echo "ERROR: document not found: $DOC_SRC" >&2
    exit 1
fi
DOC_BASENAME="$(basename "$DOC_SRC")"

# ---------------------------------------------------------------------
# Make sure the demo PKI exists; bootstrap if missing
# ---------------------------------------------------------------------
if [[ ! -f "$HERE/ca/ca.cert.pem" || ! -f "$HERE/alice/alice.cert.pem" ]]; then
    echo ">> Demo PKI missing; running setup.sh first..."
    "$HERE/setup.sh"
fi

# ---------------------------------------------------------------------
# Sign the document with Alice's key (overwrite any old .sig)
# ---------------------------------------------------------------------
cp -f "$DOC_SRC" "$HERE/alice/$DOC_BASENAME"
rm -f "$HERE/alice/$DOC_BASENAME.sig"

cd "$LADHE"
python3 ladhe_cert_cli.py sign \
    --subject alice \
    --dir "$HERE/alice" \
    --doc "$HERE/alice/$DOC_BASENAME" \
    --sig "$HERE/alice/$DOC_BASENAME.sig"

# ---------------------------------------------------------------------
# Export X.509 PEM versions of both certs
# ---------------------------------------------------------------------
HAS_X509=1
if ! python3 -c "import asn1crypto" 2>/dev/null; then
    echo ""
    echo ">> WARNING: asn1crypto not installed; skipping X.509 export."
    echo ">>          To include openssl-parseable X.509 PEMs, run:"
    echo ">>              pip install asn1crypto"
    echo ""
    HAS_X509=0
fi

if [[ "$HAS_X509" == "1" ]]; then
    python3 ladhe_cert_cli.py export-x509 \
        --cert "$HERE/alice/alice.cert.pem" \
        --out  "$HERE/alice/alice.x509.pem" \
        --format pem >/dev/null
    python3 ladhe_cert_cli.py export-x509 \
        --cert "$HERE/ca/ca.cert.pem" \
        --out  "$HERE/ca/ca.x509.pem" \
        --format pem >/dev/null
    echo ">> Exported X.509 PEM versions of both certs."
fi

# ---------------------------------------------------------------------
# Stage the kit in a temp directory
# ---------------------------------------------------------------------
STAGE="$(mktemp -d -t ladhe_kit.XXXXXX)/ladhe_demo_kit"
mkdir -p "$STAGE"

cp "$LADHE/verify.py"                       "$STAGE/verify.py"
cp "$HERE/ca/ca.cert.pem"                   "$STAGE/ca.cert.pem"
cp "$HERE/alice/alice.cert.pem"             "$STAGE/alice.cert.pem"
cp "$HERE/alice/$DOC_BASENAME"              "$STAGE/$DOC_BASENAME"
cp "$HERE/alice/$DOC_BASENAME.sig"          "$STAGE/$DOC_BASENAME.sig"

if [[ "$HAS_X509" == "1" ]]; then
    cp "$HERE/ca/ca.x509.pem"          "$STAGE/ca.x509.pem"
    cp "$HERE/alice/alice.x509.pem"    "$STAGE/alice.x509.pem"
fi

# ---------------------------------------------------------------------
# Generate README.txt for the recipient
# ---------------------------------------------------------------------
if [[ "$HAS_X509" == "1" ]]; then
    X509_CONTENTS_BLOCK=$(cat <<-X509_BLOCK
	  ca.x509.pem            the CA's cert in standard X.509 PEM format
	  alice.x509.pem         Alice's cert in standard X.509 PEM format
X509_BLOCK
)
    X509_DEMO_BLOCK=$(cat <<-X509_BLOCK

	BONUS: STANDARD X.509 INTEROPERABILITY (uses openssl)
	------------------------------------------------------
	The two .x509.pem files are the SAME certificates, exported
	in standard X.509 v3 format (ASN.1 DER inside PEM). Any
	openssl on any machine can parse them:

	    openssl x509 -in alice.x509.pem -text -noout

	You will see fields like:

	    Signature Algorithm: 1.3.6.1.4.1.65644.1.1
	    Issuer: CN=Acme Quantum CA
	    Subject: CN=alice@acme.com
	    Public Key Algorithm: 1.3.6.1.4.1.65644.1.2

	The OID 1.3.6.1.4.1.65644.1.1 is registered with IANA to
	LeSecure (Private Enterprise Number 65644, April 2026).
	Openssl will print "Unable to load Public Key" because it
	does not yet have a provider plugin for Ladhe — that is
	the next engineering milestone. The cert STRUCTURE is fully
	X.509 v3 compliant, which is what this part of the demo
	is meant to show.

	Walk the ASN.1 tree if you are curious:

	    openssl asn1parse -in alice.x509.pem | head -30
X509_BLOCK
)
else
    X509_CONTENTS_BLOCK=""
    X509_DEMO_BLOCK=""
fi

cat > "$STAGE/README.txt" <<EOF
LADHE VERIFICATION KIT
======================

This bundle contains a digitally signed document and the tools to
verify it. The signature was produced with Ladhe, a one-time
hash-based signature scheme whose security reduces to SHA-256
preimage resistance (paper: https://zenodo.org/records/19888480).

CONTENTS
--------
  verify.py              standalone verifier (no installs needed)
  ca.cert.pem            the certificate authority's cert (Ladhe-native)
  alice.cert.pem         the signer's cert (Ladhe-native)
$X509_CONTENTS_BLOCK
  $DOC_BASENAME            the signed document
  $DOC_BASENAME.sig        Alice's signature on the document
  README.txt             this file

REQUIREMENTS
------------
  Python 3.9 or newer. That's it. No pip install. No virtualenv.
  (The optional X.509 demo at the end uses openssl, which is
   already on every Mac, Linux, and Windows machine.)

VERIFY EVERYTHING (the easy way)
---------------------------------
  cd ladhe_demo_kit
  python3 verify.py

  Expected last line: "All verifications passed."

ATTEMPT A TAMPER (the demo's punchline)
----------------------------------------
  1. Open  $DOC_BASENAME  in your editor.
  2. Change ANY single byte (one digit, one letter - anything).
  3. Save the file.
  4. Re-run:    python3 verify.py
  5. The signature check should now FAIL - that's the math
     catching the tampering.
  6. Restore the file from the original and verify again - passes.

EXPLICIT MODE (per-step)
------------------------
  python3 verify.py verify-cert alice.cert.pem ca.cert.pem
  python3 verify.py verify-doc  $DOC_BASENAME  $DOC_BASENAME.sig  alice.cert.pem
$X509_DEMO_BLOCK

QUESTIONS / FEEDBACK
--------------------
  spalgorithm@gmail.com

Thank you for taking the time to test this.
EOF

# ---------------------------------------------------------------------
# Bundle into a zip in the user's CWD
# ---------------------------------------------------------------------
KIT_NAME="${KIT_NAME:-ladhe_demo_kit.zip}"
OUT="$(pwd)/$KIT_NAME"
rm -f "$OUT"

(cd "$(dirname "$STAGE")" && zip -r -q "$OUT" "ladhe_demo_kit")

# Clean up the stage
rm -rf "$(dirname "$STAGE")"

echo ""
echo "==============================================="
echo "  Kit built: $OUT"
echo ""
echo "  Contents:"
unzip -l "$OUT" | sed 's/^/    /'
echo ""
echo "  To test locally:"
echo "    rm -rf /tmp/ladhe_kit_test && unzip -d /tmp/ladhe_kit_test \"$OUT\""
echo "    cd /tmp/ladhe_kit_test/ladhe_demo_kit && python3 verify.py"
echo "==============================================="
