# Privacy Policy for LeSecure

**Effective Date:** May 9, 2026
**Last Updated:** May 9, 2026

This Privacy Policy describes how LeSecure AI Inc ("we," "us," or "our") collects, uses, and shares information when you use the **LeSecure** mobile application (the "App") on iOS.

We respect your privacy and have designed LeSecure to collect as little personal information as possible. Most of your game data stays on your device and is never transmitted.

---

## 1. Information We Collect

### 1.1 Information You Provide

- **Player names** you enter for gameplay are stored locally on your device only. We do not transmit or store your names on our servers.
- **In-App Purchase confirmations** are handled by Apple via StoreKit. We receive only a confirmation that you upgraded to LeSecure Pro; we do not see your payment details, billing address, or Apple ID.

### 1.2 Information Collected Automatically

When you use **online multiplayer** features, we collect:

- A randomly generated session ID for matchmaking
- Game moves and game state during your active session
- Anonymous Firebase user ID (no personal information attached)
- Approximate connection timing for synchronization

When **advertisements** are displayed (free version only), Google AdMob may automatically collect device identifiers and usage data — see Section 4.

### 1.3 Information We Do NOT Collect

- We do **not** collect your real name, email address, phone number, or any contact information.
- We do **not** access your contacts, photos, microphone, camera, or precise GPS location.
- We do **not** sell, rent, or trade your data to third parties.
- We do **not** track you across other apps or websites.

---

## 2. How We Use Information

We use the information we (or our service providers) collect to:

- Provide game functionality (PenTacToe, BrainTaire, and related single-player and multiplayer modes)
- Save your progress and preferences locally on your device
- Synchronize moves between players in **Online** and **Same WiFi** modes
- Display advertisements (free version only) and process Pro upgrades
- Diagnose crashes and improve the App

---

## 3. Local Storage on Your Device

LeSecure stores the following data only on your device using Apple's `UserDefaults` API:

- Game preferences (board pattern, marble color, difficulty level, sound on/off, etc.)
- Saved games for resume functionality
- Your Pro upgrade status (cached from StoreKit)
- Game statistics (games played, wins per pattern, best scores)
- Player names you've entered

This data never leaves your device unless you explicitly delete the app or restore from a device backup. To clear all local data, delete the App from your device.

---

## 4. Advertising — Google AdMob

LeSecure displays advertisements provided by **Google AdMob** to support the free version of the App. When ads are served, AdMob may automatically collect:

- Advertising identifier (IDFA on iOS, if you grant App Tracking permission)
- IP address and approximate location derived from it
- Device model, operating system version, and language
- App interactions related to ads (ad views, clicks)
- Crash and performance diagnostics for advertising SDKs

Google uses this information to deliver relevant advertisements, measure ad performance, prevent fraud, and improve their services.

**Opt-out and controls:**

- Google's Privacy Policy: <https://policies.google.com/privacy>
- Google Ad Settings: <https://myadcenter.google.com>
- AdMob and AdSense disclosures: <https://support.google.com/admob/answer/6128543>
- iOS users can disable ad tracking in **Settings → Privacy & Security → Tracking** (deny App Tracking Transparency prompt) or enable **Limit Ad Tracking** in older iOS versions.

**Pro upgrade:** If you purchase LeSecure Pro via In-App Purchase, all advertisements are removed and no advertising data is collected by AdMob during your sessions.

---

## 5. Online Multiplayer — Google Firebase

When you play in **Online** mode, the App uses **Google Firebase** services (Authentication and Realtime Database) to:

- Create an anonymous session for matchmaking with another player
- Synchronize game moves between you and your opponent in real time
- Disconnect cleanly when a player leaves the session

Firebase may collect:

- An anonymous Firebase user ID (no personal information attached)
- IP address (used for routing the connection only, not stored)
- Game move data and session state during your active session only

Game session data is automatically deleted when the session ends or after a short inactivity timeout. We do not retain past game records on our servers.

For more about Firebase data practices, see: <https://firebase.google.com/support/privacy>

---

## 6. Local Network Play — Same WiFi

When you use **Same WiFi** mode, the App uses Apple's MultipeerConnectivity framework to discover and connect to other devices on your local network. No data leaves your local network when using this mode — game moves are sent peer-to-peer between devices on the same WiFi router.

iOS will prompt you for **Local Network** permission the first time you use this feature. You can revoke this permission anytime in **Settings → LeSecure → Local Network**.

---

## 7. In-App Purchases (StoreKit)

The Pro upgrade is processed by Apple via Apple's StoreKit framework. Apple handles all payment information; we receive only a transaction record from Apple confirming the upgrade purchase. We do not see, store, or process your payment method, billing address, or Apple ID.

For Apple's privacy practices regarding purchases, see: <https://www.apple.com/legal/privacy/>

---

## 8. Children's Privacy (COPPA)

LeSecure is rated suitable for ages 4 and up and is intended for general audiences. We do **not knowingly collect** personally identifiable information from children under 13.

If you are a parent or guardian and believe your child under 13 has provided personal information through the App, please contact us at the email address below and we will promptly remove it.

---

## 9. Your Rights (GDPR / CCPA / Other Jurisdictions)

If you are a resident of the European Economic Area (EEA), the United Kingdom, California, or another jurisdiction with data protection laws, you may have the following rights:

- **Access**: Request what data we hold about you
- **Deletion**: Request deletion of your data
- **Opt-out of personalized ads**: Use iOS App Tracking settings or Google Ads Settings (linked above)
- **Portability**: Request a copy of your data in machine-readable format

Since LeSecure does not collect personally identifiable information directly, your data primarily exists in three places:

1. **Apple's device-local storage** — cleared by deleting the App from your device
2. **Google AdMob** — manage via Google Ads Settings (linked in Section 4)
3. **Firebase** — automatically cleared when your online session ends

To exercise additional rights or ask questions, contact us using the information below.

---

## 10. Data Security

We use industry-standard technical and organizational measures to protect data in transit (TLS/HTTPS for all Firebase connections). However, no method of internet transmission or electronic storage is 100% secure, and we cannot guarantee absolute security.

---

## 11. Third-Party Services Summary

For transparency, here is the complete list of third-party services LeSecure integrates with:

| Service | Purpose | Data Shared | Provider |
|---|---|---|---|
| Google AdMob | Display ads (free version) | Device ID, IP, ad interactions | Google LLC |
| Google Firebase | Online multiplayer matchmaking | Anonymous user ID, game state | Google LLC |
| Apple StoreKit | In-App Purchases | Purchase confirmation only | Apple Inc |
| Apple MultipeerConnectivity | LAN multiplayer | None — local network only | Apple Inc |

---

## 12. Changes to This Privacy Policy

We may update this Privacy Policy from time to time. The "Last Updated" date at the top of this document will reflect the most recent version. Material changes will be communicated via an in-app notice or App Store update release notes.

Continued use of the App after changes are posted constitutes acceptance of the updated Privacy Policy.

---

## 13. Contact Us

If you have questions about this Privacy Policy or our data practices, please contact:

**LeSecure AI Inc**
Email: [your-contact-email@domain.com]
Website: [your-website-or-github-page]

---

*This Privacy Policy was last reviewed on May 9, 2026.*
