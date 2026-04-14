---
name: LESecureLocal
description: LESecure Local/On-Prem — encrypt and decrypt data, files, and folders using the LE desktop tool with layered locks (pin, password, MFA, time lock, geo-location).
triggers:
  - LESecure Local
  - LESecure Desktop
  - LESecure On-Prem
  - LE local
  - LE desktop
  - encrypt file
  - decrypt file
  - encrypt folder
  - decrypt folder
---

# LESecureLocal — LESecure Local / On-Prem Skills

Encrypt and decrypt **plain text, files, and folders** using the LE desktop binary. No API key is needed — everything runs locally.

## ROUTING RULES (MANDATORY)

- **Files and folders MUST always use LESecure Local.** Never use LESecure Cloud for file/folder encryption. If the user asks to encrypt files/folders via cloud, inform them: "File/folder encryption is only supported via LESecure Local (desktop)." and use this skill.
- **For plain text**, ask the user: "Would you like to use **LESecure Cloud** (API) or **LESecure Local** (desktop)?" and proceed accordingly.

## Binary Location

```
/Users/pankajladhe/Pankaj/2018/LETesting1/LE
```

Always use the full path when invoking LE.

## Date & Time Rules (MANDATORY)

All date/time handling for this skill follows these rules — no exceptions:

1. **Always use EST/EDT (America/New_York)** to calculate and send dates. The LE tool interprets `-l` and `-r` in EST/EDT.
2. **Start time (`-l`) = current EST + 2 minutes** by default. This buffer prevents the "date must be in future" error.
3. **End time (`-r`) = start time + the user's requested duration**.
4. **Standard commands** for computing times:
   - Start (`-l`): `TZ=America/New_York date -v+2M "+%Y/%m/%d %H:%M"`
   - End (`-r`) for N minutes: `TZ=America/New_York date -v+$((2+N))M "+%Y/%m/%d %H:%M"`
   - End (`-r`) for N hours: `TZ=America/New_York date -v+2M -v+${N}H "+%Y/%m/%d %H:%M"`
5. **Always display the window back to the user in EDT/EST**.

## Two Modes

### 1. PlainText Mode (`--PlainText` / `-p`)

Encrypt/decrypt inline strings. Wrap the string in triple single quotes.

```bash
# Encrypt
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -e '''<DATA>''' <LOCK_FLAGS> --PlainText

# Decrypt
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -d '''<ENCRYPTED_DATA>''' <LOCK_FLAGS> --PlainText
```

### 2. File / Folder Mode (`-j`)

Encrypt/decrypt files or entire folders. The `-j` flag combines **clean** (`-c`), **force** (`-z`), and **recursive** (`-n`).

```bash
# Encrypt a file or folder
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -e <FILE_OR_FOLDER> <LOCK_FLAGS> -j

# Decrypt a file or folder
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -d <FILE_OR_FOLDER> <LOCK_FLAGS> -j
```

**Important for file/folder mode:**
- Run the command from the directory containing the target, or provide the full path.
- Encrypted files get a `.le` prefix on the extension (e.g., `example.txt` becomes `example.letxt`); use the `.letxt` filename when decrypting.
- For folders, the individual files inside get the `.le` prefix on their extensions (e.g., `file.txt` → `file.letxt`). The folder name itself stays the same. Use the same folder name when decrypting.

## Available Locks

| Flag | Lock Type | Value | Example |
|------|-----------|-------|---------|
| `-1` | Pin/Code | Numeric string | `"1122"` |
| `-w` | Password | Password file (`.letxt`) or passphrase | `pass.letxt` |
| `-2` | MFA | Phone number (E.164) | `"+19199870623"` |
| `-3` | OTP | OTP code for decryption | `"123456"` |
| `-l` | Time lock start | `YYYY/MM/DD HH:MM` | `"2026/04/12 17:41"` |
| `-r` | Time lock end | `YYYY/MM/DD HH:MM` | `"2027/04/12 17:36"` |

### Additional Flags

| Flag | Purpose |
|------|---------|
| `-j` | Trio flag: force + clean + recursive (use for files/folders) |
| `-z` | Force — overwrite existing encrypted file |
| `-c` | Clean — remove source after encrypt/decrypt |
| `-n` | Recursive — process folders recursively |
| `-i` | Get info on an encrypted file |
| `-o` | Specify output file name |

## MFA Workflow

1. **Encrypt with MFA**: Use `-2 "+1XXXXXXXXXX"` to register the phone number.
2. **Decrypt with MFA**: First run decrypt with `-4 <encrypted_file>` to trigger OTP delivery, then run again with `-3 <OTP_CODE>`.

## Examples

### PlainText — Pin only
```bash
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -e '''hello world''' -1 "1234" --PlainText
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -d '''<ENCRYPTED>''' -1 "1234" --PlainText
```

### PlainText — All locks
```bash
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -e '''secret data''' -w pass.letxt -1 "1122" -2 "+19199870623" -l "2026/04/12 17:41" -r "2027/04/12 17:36" --PlainText
```

### File — Pin only
```bash
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -e /path/to/myfile.txt -1 "1234" -j
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -d /path/to/myfile.letxt -1 "1234" -j
```

### Folder — Pin + Password
```bash
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -e /path/to/my_folder -w pass.letxt -1 "1234" -j
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -d /path/to/my_folder -w pass.letxt -1 "1234" -j
```

### Get info on encrypted file
```bash
/Users/pankajladhe/Pankaj/2018/LETesting1/LE -i /path/to/myfile.letxt
```

## Workflow

1. **Determine the mode**: PlainText (`--PlainText`) for inline strings, or File/Folder (`-j`) for files and directories.
2. **Gather lock inputs**: Which locks to apply and their values.
3. **Build the command** with the appropriate flags.
4. **Execute via Bash** and return the result.
5. **For decryption**, remind the user they need the same lock values used during encryption.

## Important Notes

- No API key is needed — LE runs entirely locally.
- Phone numbers for MFA (`-2`) must be in E.164 format.
- Time lock dates use `YYYY/MM/DD HH:MM` format. Follow the Date & Time Rules above.
- Time locks require both `-l` (start) and `-r` (end).
- The password file (`.letxt`) should be an encrypted password file created with `LE -e pass.txt -q`.
- For geo-location locks, use `-v` with a location CSV file and `-0 LAT LON` or `-x 'Address'` for geo-point validation.
