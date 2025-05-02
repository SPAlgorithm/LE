# 🔒 LE detailed readme ...

## 🔹 Verify Phone number for MFA

1. **Register Phone number for OTP**:

```bash
./LE -2 "+1XXXXXXXXXX" -5
```
   This will send you OTP to your phone number.

2. **Verify OTP from valid phone number**:

Lets say your received OTP - 597349

```bash
./LE -6 597349
```

If otp is correct, LE will be able to send OTP for MFA.

---

## 🔹 Create a PasswordKey Encryption File

1. **Create a PasswordKey file**:

```bash
echo TestingPassword > pass.txt
```
   This PasswordKey file now contains the password `"TestingPassword"`.

2. **Encrypt the PasswordKey file**:

**The PasswordKey file needs to be encrypted/decrypted with 4 digit pin or  MFA enabled.**

```bash
./LE -e pass.txt -q -j -1 1234
```
   The PasswordKey file (pass.letxt) is now encrypted with pin 1234 and can be used for encrypting files or folders.

```bash
./LE -e pass.txt -q -j -1 1234 -2 "+1XXXXXXXXX,+1YYYYYYYYYY"
```

The PasswordKey file (pass.letxt) is now encrypted with pin 1234 and MFA where you will provide a valid phone
number (with +Country Code) where static otp can be send at the time of decrypting and can be used for encrypting files
or folders. 

**Note: Please make sure that you have enabled messages app on your Mac.**

**Either Pin or MFA should be enabled for PasswordKey/LocationKey file**

3. **Decrypt the PasswordKey file**:

Only MFA/OTP

```bash
./LE -d pass.letxt -j -w TestingPassword -3 "123456"
```

Only Pin

```bash
./LE -d pass.letxt -j -w TestingPassword -1 1234
```

To decrypt a PasswordKey file, the user must **know the password** stored inside the password file.

To get OTP to your configured phone:

Only MFA/OTP

```bash
./LE -4 pass.letxt 
```

Only Pin

```bash
./LE -4 pass.letxt -1 1234 
```

Use that OTP to decrypt :

Pin and MFA/OTP

```bash
./LE -d pass.letxt  -j -w TestingPassword -1 1234 -3 "123456"
```

To decrypt a PasswordKey file, the user must **know the password** stored inside the PasswordKey file.

**Either Pin or MFA should be enabled for PasswordKey/Location file**

---

## 🔹 Create a Location Key Encryption File

1. **Create a location key file**:

**Location key files needs to be encrypted/decrypted with 4 digit pin.**

If you know Latitude,Longitude and distance in meters:

```bash
echo "35.8538,-78.686,2000" > location.csv
```

```bash
echo "38.1233,-88.249,100" >> location.csv
```

   This location key file now contains the array of geo locations `"Lattitude,Longitude,Distance to allow decrypt in meters".
**One Geo Location point per line.**

If you don'know Latitude and Longitude but have address:

You can build location key file using precise Geo Points and distance using LE. You can append Geo location into location
file and build accurate location file.

```bash
./LE -x "1 Infinite Loop. Cupertino, CA 95014 United States" -m 100 >> location.csv
```

```bash
./LE -x "1560 Broadway, Manhattan, NY 10036 usa" -m 500 >> location.csv
```
    
Location.csv will contain 2 Geo Location points now if valid addresses are provided.

**To get current address**

```bash
./LE -7 
```

**To find distance of address from current location**

```bash
./LE -x "1 Infinite Loop. Cupertino, CA 95014 United States" -8  >> location.csv
```

**To find distance of address in FILE (address.txt) from current location**

```bash
echo "1560 Broadway, Manhattan, NY 10036 usa" >> address.txt
```

```bash
echo "1 Infinite Loop. Cupertino, CA 95014 United States" >> address.txt
```

```bash
./LE -9 "address.txt" -8  >> location.csv
```

**To remove comments '# lines' from (location.csv)**

```bash
./LE --LocationFileClean location.csv
```

- **Geo Locations Limit**:

  - ⚡ **Beta Version**: Supports **up to 5 Geo Locations**.
  - 🚀 **Licensed Version**: Supports **up to 100 Geo Locations**.


2. **Encrypt the location key file**:

**Without encrypted geo location point.**

```bash
./LE -e location.csv -v -1 1234 -j
```

The location key file (location.lecsv) is now encrypted with pin 1234 and can be used for geo location encrypting files or folders.It does not include current location, only geo points you specified. 
   
**With encrypted geo location point and custom distance.**

To add current location of enryption and distance of 200 meters to your list 

```bash
./LE -e location.csv -v -1 1234 -g -m 200 -j
```

To Encrypt location key file with pin and MFA :

Without current Geo Location:

Only MFA/OTP

```bash
./LE -e location.csv -v -j -2 "+1XXXXXXXXX,+1YYYYYYYYYY"
```

Pin and MFA/OTP
```bash
./LE -e location.csv -v -1 1234 -j -2 "+1XXXXXXXXX,+1YYYYYYYYYY"
```

With current Geo Location:

```bash
./LE -e location.csv -v -1 1234 -j -2 "+1XXXXXXXXX,+1YYYYYYYYYY" -g -m 200
```

The location key file (location.lecsv) is now encrypted with pin 1234 and can be used for geo location encrypting files or folders.It will add current geo location and distance of 200 meters.

**Either Pin or MFA should be enabled for PasswordKey/LocationKey file**

**Get Info on encrypted location key file**

```bash
./LE -i location.lecsv 
```

3. **Decrypt the location file**:

```bash
./LE -d location.lecsv -j -1 1234
```

You will need a valid pin to decrypt location file.

To get OTP to your configured phone:

```bash
./LE -4 location.lecsv -1 1234 
```

Use that OTP to decrypt :

```bash
./LE -d location.lecsv -j -1 1234 -3 "123456"
```

You will need a valid pin and static OTP (123456) send to valid phone number you provided to decrypt location key file.

**Note: Please make sure that you have enabled locations and messages app on your Mac.**

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

**Encrypt with Pin:**

```bash
./LE -e example.txt -j  -1 1234
```

**Decrypt with Pin:**

```bash
./LE -d example.letxt -j -1 1234
```

**Encrypt with MFA/OTP:**

```bash
./LE -e example.txt -j  -1 1234 -2 "+1XXXXXXXXX,+1YYYYYYYYYY"
```

**Decrypt with MFA/OTP:**

To get OTP to your configured phone:

```bash
./LE -4 example.letxt -1 1234 
```

Use that OTP to decrypt :

```bash
./LE -d example.letxt -j -1 1234 -3 "123456"
```

### 🔹 Encrypt & Decrypt a Folder

**Encrypt with Pin:**

```bash
./LE -e my_folder -j -1 1234
```

**Decrypt with Pin:**

```bash
./LE -d my_folder -j -1 1234
```

**Encrypt with MFA/OTP:**

```bash
./LE -e my_folder -j  -1 1234 -2 "+1XXXXXXXXX,+1YYYYYYYYYY"
```

**Decrypt with MFA/OTP:**

To get OTP to your configured phone:

```bash
./LE -4 my_folder -1 1234 
```

Use that OTP to decrypt :

```bash
./LE -d my_folder -j -1 1234 -3 "123456"
```

---

## 🔹 2. Encryption & Decryption with PasswordKey Protection
### 🔹 Encrypt & Decrypt a File with a PasswordKey

**Encrypt:**

```bash
./LE -e example.txt -w pass.letxt -j
```

**Decrypt:**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a PasswordKey

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

## 🔹 4. Encryption & Decryption with PasswordKey & Time Lock
### 🔹 Encrypt & Decrypt a File with a PasswordKey Until a Specific Date

**Encrypt (only decryptable after this date with a PasswordKey):**

```bash
./LE -e example.txt -w pass.letxt -t "2025/01/31 19:10" -j
```

**Decrypt (with PasswordKey after the specified date):**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a PasswordKey Until a Specific Date

**Encrypt (only decryptable after this date with a PasswordKey):**

```bash
./LE -e my_folder -w pass.letxt -t "2025/01/31 19:10" -j
```

**Decrypt (with PasswordKey after the specified date):**

```bash
./LE -d my_folder -w pass.letxt -j
```

---

## 🔹 5. Encryption & Decryption with Geo Location Protection
### 🔹 Encrypt & Decrypt a File with a Geo Location Key

**Encrypt:**

```bash
./LE -e example.txt -b location.lecsv -j
```

**Decrypt:**

```bash
./LE -d example.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Geo Location Key

**Encrypt:**

```bash
./LE -e my_folder -b location.lecsv -j
```

**Decrypt:**

```bash
./LE -d my_folder -j
```

---

### 🔹 Encrypt & Decrypt a File with a Geo LocationKey and PasswordKey 

**Encrypt:**

```bash
./LE -e example.txt -b location.lecsv -w pass.letxt  -j
```

**Decrypt:**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Geo LocationKey and PasswordKey 

**Encrypt:**

```bash
./LE -e my_folder -b location.lecsv -w pass.letxt -j
```

**Decrypt:**

```bash
./LE -d my_folder -w pass.letxt -j
```

---

### 🔹 Encrypt & Decrypt a File with a Time Lock, Geo LocationKey and PasswordKey 

**Encrypt:**

```bash
./LE -e example.txt -t "2025/03/31 19:10" -b location.lecsv -w pass.letxt  -j
```

**Decrypt:**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Geo LocationKey and PasswordKey 

**Encrypt:**

```bash
./LE -e my_folder -b location.lecsv -w pass.letxt -j
```

**Decrypt:**

```bash
./LE -d my_folder -w pass.letxt -j
```

---

### 🔹 Encrypt & Decrypt a File Until a Specific Date with a Geo LocationKey and PasswordKey 

**Encrypt (available for decryption after this date):**

```bash
./LE -e example.txt -t "2025/03/31 19:10" -b location.lecsv -w pass.letxt -j
```

**Decrypt (after the specified date):**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder Until a Specific Date with a Geo LocationKey and PasswordKey

**Encrypt (available for decryption after this date):**

```bash
./LE -e my_folder -t "2025/03/31 19:10" -b location.lecsv -w pass.letxt -j
```

**Decrypt (after the specified date):**

```bash
./LE -d my_folder -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a File From a Specific Date with a Geo LocationKey and PasswordKey

**Encrypt (only decryptable after this date):**

```bash
./LE -e example.txt -l "2025/02/20 19:10" -b location.lecsv -w pass.letxt -j
```

**Decrypt (after the specified date):**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder From a Specific Date with a Geo LocationKey and PasswordKey

**Encrypt (only decryptable after this date):**

```bash
./LE -e my_folder -l "2025/02/20 19:10" -b location.lecsv -w pass.letxt -j
```

**Decrypt (after the specified date):**

```bash
./LE -d my_folder -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a File with a Date Range with a Geo LocationKey and PasswordKey

**Encrypt (only decryptable between the specified dates):**

```bash
./LE -e example.txt -l "2025/02/20 19:10" -r "2026/02/01 14:10" -b location.lecsv -w pass.letxt -j
```

**Decrypt (within the allowed date range):**

```bash
./LE -d example.letxt -w pass.letxt -j
```

### 🔹 Encrypt & Decrypt a Folder with a Date Range with a Geo LocationKey and PasswordKey
**Encrypt (only decryptable between the specified dates):**

```bash
./LE -e my_folder -l "2025/02/20 19:10" -r "2026/02/01 14:10" -b location.lecsv -w pass.letxt -j
```

**Decrypt (within the allowed date range):**

```bash
./LE -d my_folder -w pass.letxt -j
```

---

### 🔹 Encrypt & Decrypt a File with a Date Range with a Geo LocationKey , 4 digit pin , MFA and PasswordKey

**Encrypt (only decryptable between the specified dates):**

```bash
./LE -e example.txt -l "2025/02/20 19:10" -r "2026/02/01 14:10" -b location.lecsv -w pass.letxt -1 1234 -2 "+1XXXXXXXXX,+1YYYYYYYYYY" -j
```

**Decrypt (within the allowed date range):**

To get OTP to your configured phone:

```bash
./LE -4 example.letxt -1 1234 
```

Use that OTP to decrypt :

```bash
./LE -d example.letxt -w pass.letxt -j -1 1234 -3 "123456"
```

### 🔹 Encrypt & Decrypt a Folder with a Date Range with a Geo LocationKey , 4 digit pin , MFA and PasswordKey
**Encrypt (only decryptable between the specified dates):**

```bash
./LE -e my_folder -l "2025/02/20 19:10" -r "2026/02/01 14:10" -b location.lecsv -w pass.letxt -1 1234 -2 "+1XXXXXXXXX,+1YYYYYYYYYY" -j
```

**Decrypt (within the allowed date range):**

To get OTP to your configured phone:

```bash
./LE -4 my_folder -1 1234 
```

Use that OTP to decrypt :

```bash
./LE -d my_folder -w pass.letxt -1 1234 -3 "123456" -j 
```

---

## 🔹 6. Get Info on encrypted file and folders
### 🔹 Info on a File 

**GetInfo File:**

```bash
./LE -i example.letxt
```

**GetInfo Folder:**

```bash
./LE -i my_folder -j
```

---
7. **Repair LE**:

```bash
./LE --repair
   ```
Or:

```bash
./LE -y
```

