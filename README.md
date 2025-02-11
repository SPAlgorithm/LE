# 🔒 Ladhe’s Encryption Utility (LE)

Experience the next generation of **data security** with **Ladhe’s Encryption Utility (LE)**—a **cutting-edge, quantum-safe encryption tool** designed for **Mac terminals**. Built with advanced features and unparalleled encryption power, **LE** ensures your sensitive data remains **protected** from modern and future threats.

---

## ✨ Key Features

### 🔑 Advanced Encryption Capabilities
- **Symmetric Key Generation**: Secure **AES-like** encryption. _(Licensed version)_
- **Asymmetric Key Generation**: **RSA-style** encryption for enhanced security. _(Licensed version)_
- **Versatile Encryption Options**: Encrypt **plaintext, pipelined text, and entire files**. _(Licensed version)_
- **Flexible Decryption**: Decrypt data encrypted with **symmetric or asymmetric** keys. _(Licensed version)_

### 🗂 File & Folder Encryption
- **Encrypt/Decrypt Files & Folders**: Apply strong encryption to both files and directories.
- **Recursive Folder Encryption**: Encrypt entire directories with **subfolder support**.
- **Trio Mode**: Use **Force, Clean, and Recursive** encryption in a single command.

### 🔄 Force & Clean Mode
- **Force Mode**: Overwrites existing encrypted files.
- **Clean Mode**: Restores **.leXXX** files to their **original** format upon decryption.

### 🔑 Password , Time-Lock Security , Geo Location Security
- **Password Encryption**: Encrypt files with a **secure password file**.
- **Time-Lock Encryption**:
  - 🔹 **Decrypt only before** a specified date.
  - 🔹 **Decrypt only after** a specified date.
  - 🔹 **Decrypt within** a date range.
- **Geo Location Encryption**: Encrypt files with a **Geo Location file**.


### 🛡 Additional Features
- **Metadata & File Info**: Retrieve **detailed encryption metadata**.
- **Auto-Generated Comments**: LE **embeds encryption details** into file properties.
- **Tamper Detection**: _(Licensed version)_ Prevents **date manipulation** using online validation.
- **File Size Limit**:
  - ⚡ **Beta Version**: Supports **up to 4MB**.
  - 🚀 **Licensed Version**: Supports **up to 100MB**.

- **Files Limit in Folder**:
  - ⚡ **Beta Version**: Supports **up to 2000 Files**.
  - 🚀 **Licensed Version**: Supports **up to 100,000 Files**.

---

## 📂 Supported File Extensions

LE currently supports encryption for the following file types:

| **Category**        | **File Extensions**                         |
|---------------------|-------------------------------------------|
| **Text Files**      | `txt`, `rtf`, `csv`, `log`, `json`, `xml`  |
| **Programming**     | `java`, `c`, `vb`, `cs`, `php`, `py`, `sql` |
| **Web Files**       | `html`, `htm`, `js`, `aspx`, `xhtml`        |
| **Apple Development** | `storyboard`, `swift`, `xib`            |
| **Miscellaneous**   | `asp`, `class`, `m`, `h`                   |

💡 **Need support for additional file types?** Contact **spalgorithm@gmail.com**.

---

## 🎯 Why Choose LE?

🚀 **Ladhe’s Encryption Utility (LE)** is at the **forefront of post-quantum cryptography**, ensuring **future-proof** security for your sensitive data.

- 🔹 **Lightweight** & **Efficient** terminal-based encryption.
- 🔹 **Protects against modern and quantum-based attacks**.
- 🔹 **Advanced encryption** with **password & time-lock** security.
- 🔹 **Beta Version** available for free, with **Licensed Version** offering extended features.

🔒 **Secure your files today with LE!** If you find it meets your needs, request a **licensed copy** to unlock even more powerful features.

---

# LE Encryption & Decryption Commands

## 🔹 Install Steps:

1. **Clone the repository** or **download the zip**:
   ```bash
   git clone https://github.com/SPAlgorithm/LE.git
   ```
   Or download the zip and extract it.

2. **Install LE**:
   - Tap on **LE.dmg** and copy/move **LE** to a local folder.

3. **Setup LE**:
   ```bash
   ./LE –setup
   ```
   Or:
   ```bash
   ./LE -s
   ```
   This will create a `cer.le` certificate.

4. **Encrypt a test file**:
   ```bash
   echo Testing > example.txt
   ./LE -e example.txt -j
   ```
   You should see **example.letxt** in the folder.

---

## 🔹 Create a Password Encryption File

1. **Create a password file**:
   ```bash
   echo TestingPassword > pass.txt
   ```
   This password file now contains the password `"TestingPassword"`.

2. **Encrypt the password file**:
   ```bash
   ./LE -e pass.txt -q -j
   ```
   The password file (pass.letxt) is now encrypted and can be used for encrypting files or folders.

3. **Decrypt the password file**:
   ```bash
   ./LE -d pass.letxt -j -w TestingPassword
   ```
   To decrypt a password file, the user must **know the password** stored inside the password file.

---

## 🔹 Create a Location Encryption File

1. **Create a location file**:
   ```bash
   echo "35.8538,-78.686,2000,43.2381,-72.5786,4000" > location.txt
   ```
   This password file now contains the array of geo locations `"Lattitude,Longitude,Distance to allow decrypt in meters"`.

2. **Encrypt the location file**:
   ```bash
   ./LE -e location.csv -v -j
   ```
   The location file (location.letxt) is now encrypted and can be used for geo location encrypting files or folders.

3. **Decrypt the location file**:
   ```bash
   ./LE -d location.lecsv -j 
   ```
   To decrypt a password file, the user must **know the password** stored inside the password file.

---

# LE Encryption & Decryption Workflows

## 🔹 1. Basic Encryption & Decryption
### 🔹 Encrypt & Decrypt a File
**Encrypt:**
```bash
./LE -e example.txt -j
```
**Decrypt:**
```bash
./LE -d example.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder
**Encrypt:**
```bash
./LE -e my_folder -j
```
**Decrypt:**
```bash
./LE -d my_folder -j
```

---

## 🔹 2. Encryption & Decryption with Password Protection
### 🔹 Encrypt & Decrypt a File with a Password
**Encrypt:**
```bash
./LE -e example.txt -w pass.letxt -j
```
**Decrypt:**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Password
**Encrypt:**
```bash
./LE -e my_folder -w pass.letxt -j
```
**Decrypt:**
```bash
./LE -d my_folder -w pass.letxt -j
```

---

## 🔹 3. Encryption & Decryption with Time Lock
### 🔹 Encrypt & Decrypt a File Until a Specific Date
**Encrypt (available for decryption after this date):**
```bash
./LE -e example.txt -t "2025/01/31 19:10" -j
```
**Decrypt (after the specified date):**
```bash
./LE -d example.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder Until a Specific Date
**Encrypt (available for decryption after this date):**
```bash
./LE -e my_folder -t "2025/01/31 19:10" -j
```
**Decrypt (after the specified date):**
```bash
./LE -d my_folder -j
```

### 🔹 Encrypt & Decrypt a File From a Specific Date
**Encrypt (only decryptable after this date):**
```bash
./LE -e example.txt -l "2025/01/31 19:10" -j
```
**Decrypt (after the specified date):**
```bash
./LE -d example.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder From a Specific Date
**Encrypt (only decryptable after this date):**
```bash
./LE -e my_folder -l "2025/01/31 19:10" -j
```
**Decrypt (after the specified date):**
```bash
./LE -d my_folder -j
```

### 🔹 Encrypt & Decrypt a File with a Date Range
**Encrypt (only decryptable between the specified dates):**
```bash
./LE -e example.txt -l "2025/01/31 19:10" -r "2026/02/01 14:10" -j
```
**Decrypt (within the allowed date range):**
```bash
./LE -d example.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Date Range
**Encrypt (only decryptable between the specified dates):**
```bash
./LE -e my_folder -l "2025/01/31 19:10" -r "2026/02/01 14:10" -j
```
**Decrypt (within the allowed date range):**
```bash
./LE -d my_folder -j
```

---

## 🔹 4. Encryption & Decryption with Password & Time Lock
### 🔹 Encrypt & Decrypt a File with a Password Until a Specific Date
**Encrypt (only decryptable after this date with a password):**
```bash
./LE -e example.txt -w pass.letxt -t "2025/01/31 19:10" -j
```
**Decrypt (with password after the specified date):**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Password Until a Specific Date
**Encrypt (only decryptable after this date with a password):**
```bash
./LE -e my_folder -w pass.letxt -t "2025/01/31 19:10" -j
```
**Decrypt (with password after the specified date):**
```bash
./LE -d my_folder -w pass.letxt -j
```

---

## 🔹 5. Encryption & Decryption with Geo Location Protection
### 🔹 Encrypt & Decrypt a File with a Geo Location
**Encrypt:**
```bash
./LE -e example.txt -b location.lecsv -j
```
**Decrypt:**
```bash
./LE -d example.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Geo Location
**Encrypt:**
```bash
./LE -e my_folder -b location.lecsv -j
```
**Decrypt:**
```bash
./LE -d my_folder -j
```

---

### 🔹 Encrypt & Decrypt a File with a Geo Location and password 
**Encrypt:**
```bash
./LE -e example.txt -b location.lecsv -w pass.letxt  -j
```
**Decrypt:**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Geo Location and password 
**Encrypt:**
```bash
./LE -e my_folder -b location.lecsv -w pass.letxt -j
```
**Decrypt:**
```bash
./LE -d my_folder -w pass.letxt -j
```

---

---

### 🔹 Encrypt & Decrypt a File with a Time Lock, Geo Location and password 
**Encrypt:**
```bash
./LE -e example.txt -b location.lecsv -w pass.letxt  -j
```
**Decrypt:**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Geo Location and password 
**Encrypt:**
```bash
./LE -e my_folder -b location.lecsv -w pass.letxt -j
```
**Decrypt:**
```bash
./LE -d my_folder -w pass.letxt -j
```

---

### 🔹 Encrypt & Decrypt a File Until a Specific Date with a Geo Location and password 
**Encrypt (available for decryption after this date):**
```bash
./LE -e example.txt -t "2025/03/31 19:10" -b location.lecsv -w pass.letxt -j
```
**Decrypt (after the specified date):**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder Until a Specific Date with a Geo Location and password
**Encrypt (available for decryption after this date):**
```bash
./LE -e my_folder -t "2025/03/31 19:10" -b location.lecsv -w pass.letxt -j
```
**Decrypt (after the specified date):**
```bash
./LE -d my_folder -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a File From a Specific Date with a Geo Location and password
**Encrypt (only decryptable after this date):**
```bash
./LE -e example.txt -l "2025/02/20 19:10" -b location.lecsv -w pass.letxt -j
```
**Decrypt (after the specified date):**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder From a Specific Date with a Geo Location and password
**Encrypt (only decryptable after this date):**
```bash
./LE -e my_folder -l "2025/02/20 19:10" -b location.lecsv -w pass.letxt -j
```
**Decrypt (after the specified date):**
```bash
./LE -d my_folder -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a File with a Date Range with a Geo Location and password
**Encrypt (only decryptable between the specified dates):**
```bash
./LE -e example.txt -l "2025/02/20 19:10" -r "2026/02/01 14:10" -b location.lecsv -w pass.letxt -j
```
**Decrypt (within the allowed date range):**
```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Date Range with a Geo Location and password
**Encrypt (only decryptable between the specified dates):**
```bash
./LE -e my_folder -l "2025/02/20 19:10" -r "2026/02/01 14:10" -b location.lecsv -w pass.letxt -j
```
**Decrypt (within the allowed date range):**
```bash
./LE -d my_folder -w pass.letxt -j
```

---
