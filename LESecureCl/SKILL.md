---
name: LESecureCl
description: "LESecure Cloud Skills — encrypt or decrypt data using the LESecure API with layered locks (pin, password, MFA, time lock). Use this skill whenever the user mentions LESecure, LESecureCl, LESecure Cloud, layered encryption, multi-lock encryption, or wants to protect data with combinations of pin codes, passwords, phone-based MFA, or time-based access windows. Also trigger when the user wants to decrypt LESecure-encrypted data."
---

# LESecureCl — LESecure Cloud Skills

Encrypt and decrypt **plain text data only** through the LESecure REST API. The API supports layered security "locks" that can be combined for defense-in-depth protection.

## ROUTING RULES (MANDATORY)

- **LESecure Cloud is for PlainText ONLY.** Never use the cloud API for files or folders.
- **If the user wants to encrypt/decrypt files or folders**, always redirect to **LESecureLocal** (the desktop tool). Inform the user: "File/folder encryption is only supported via LESecure Local (desktop). Let me use that instead."
- **If the user wants to encrypt/decrypt plain text**, ask them: "Would you like to use **LESecure Cloud** (API) or **LESecure Local** (desktop)?" and proceed accordingly.

## API Basics

- **Endpoint**: `https://api.lesecure.ai/exec`
- **Method**: POST
- **Auth**: Bearer token in the Authorization header
- **Content-Type**: `application/json`
- **Body**: `{"args": [<array of CLI-style arguments>]}`

The user must provide their API key each time. Ask for it if not provided.

## Date & Time Rules (MANDATORY)

All date/time handling for this skill follows these rules — no exceptions, no need for the user to restate them:

1. **Always use EST/EDT (America/New_York)** to calculate and send dates. The LESecure server interprets `-l` and `-r` in EST/EDT. Never use UTC, never convert.
2. **Start time (`-l`) = current EST + 2 minutes** by default. This buffer prevents the "date must be in future" error caused by clock drift between the client and server.
3. **End time (`-r`) = start time + the user's requested duration** (e.g., "for next 10 min" means `-r` is start + 10 min, so 12 minutes from "now" in absolute terms).
4. **Standard commands** for computing times:
   - Start (`-l`): `TZ=America/New_York date -v+2M "+%Y/%m/%d %H:%M"`
   - End (`-r`) for N minutes: `TZ=America/New_York date -v+$((2+N))M "+%Y/%m/%d %H:%M"`
   - End (`-r`) for N hours: `TZ=America/New_York date -v+2M -v+${N}H "+%Y/%m/%d %H:%M"`
5. **Always display the window back to the user in EDT/EST** so they know when they can decrypt.

## Available Locks

LESecure supports four lock types that can be combined freely:

| Flag | Lock Type | Value | Example |
|------|-----------|-------|---------|
| `-1` | Pin/Code | Numeric string | `"1122"` |
| `-w` | Password | Passphrase string | `"mypasscode"` |
| `-2` | MFA | Phone number (E.164) | `"+19199870623"` |
| `-l` | Time lock start | Date/time `YYYY/MM/DD HH:MM` | `"2026/04/12 17:41"` |
| `-r` | Time lock end | Date/time `YYYY/MM/DD HH:MM` | `"2027/04/12 17:36"` |

Time locks (`-l` and `-r`) are used together to define an access window during which decryption is allowed.

## Operations

### Encrypt (`-e`)

Use `-e` followed by the data to encrypt.

### Decrypt (`-d`)

Use `-d` followed by the encrypted data to decrypt. The same locks used during encryption must be provided for decryption.

## Output Flags

| Flag | Purpose |
|------|---------|
| `--PlainText` | Output as plain text |

Always include `--PlainText` for readable output.

## Building the curl Command

Construct the args array by mapping user requirements to flags. Order within the array doesn't matter, but group related flags and their values together for readability.

**Encrypt with pin lock only:**
```bash
curl -s https://api.lesecure.ai/exec \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"args":["-e","<DATA>","-1","<PIN>","--PlainText"]}'
```

**Encrypt with all locks:**
```bash
curl -s https://api.lesecure.ai/exec \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"args":["-e","<DATA>","-w","<PASSWORD>","-1","<PIN>","-2","<PHONE>","-l","<START_DATE>","-r","<END_DATE>","--PlainText"]}'
```

**Decrypt:**
```bash
curl -s https://api.lesecure.ai/exec \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"args":["-d","<ENCRYPTED_DATA>","-1","<PIN>","--PlainText"]}'
```

## Workflow

1. **Gather inputs from the user:**
   - The data to encrypt or decrypt
   - Which locks to apply (pin, password, MFA, time window)
   - The values for each lock
   - Their API key
   - Always include `--PlainText`

2. **Build the args array** with the appropriate flags and values.

3. **Execute the curl command** via Bash and return the result to the user.

4. **If decrypting**, remind the user they need the same lock values that were used during encryption.

## Important Notes

- Phone numbers for MFA (`-2`) should be in E.164 format (e.g., `+19199870623`).
- Time lock dates use the format `YYYY/MM/DD HH:MM`. See the "Date & Time Rules" section above — always EST/EDT, always +2 min buffer on start.
- Time locks require both `-l` (start) and `-r` (end) to define the access window.
- The API key is sensitive -- never log it or include it in output shown to the user.
- If the API returns an error, show the response to the user and help them troubleshoot (common issues: wrong lock values for decryption, expired time window, invalid API key).
