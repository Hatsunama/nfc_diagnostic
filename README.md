# NFC Diagnostic

An Android app for testing NFC between two phones, without a merchant terminal.

## Modes

- **Test card mode:** emulates non-payment AID `F0010203040506`, returning `NFC_OK` plus status `9000`.
- **Read diagnostic test card:** selects that AID on the other phone. Success returns 8 bytes and status `9000`.
- **Payment discovery only:** sends SELECT PPSE (`2PAY.SYS.DDF01`) to the other phone's default payment service. Displays and logs response length and status only.

Payment discovery stops after SELECT PPSE. It does not select individual payment applications, read card records, request payment cryptograms, or initiate a charge. Success confirms initial payment discovery, not that a merchant payment will succeed. Close-range success cannot rule out reduced antenna range or intermittent damage.

## Build on Windows

Requires Python 3, JDK 17 with `java`, `javac`, `jar`, and `keytool` on PATH, Android SDK Platform 36, and Build Tools 36.0.0. Set `ANDROID_HOME` or `ANDROID_SDK_ROOT` for a custom SDK location; otherwise the script uses `%LOCALAPPDATA%/Android/Sdk`.

```powershell
python build.py
adb -s PHONE_SERIAL install -r nfc-diagnostic.apk
```

Approve the phone's installation prompt if shown. The script generates all Java sources/resources and a local development signing key. The keystore password is `android`; this is not production signing. Retain the key for updates; a different key requires uninstalling the previous app.

## Test two phones

Enable NFC, unlock both phones, and align their NFC antennas back to back. Open the app on both phones. Choose **Test card mode** on one and **Read diagnostic test card** on the other. Reverse roles to test both directions.

For payment discovery, close the diagnostic app on the phone being tested and leave its normal wallet configured. Choose **Payment discovery only** on the reader phone. Test only devices you own or have permission to test.

```powershell
adb -s CARD_PHONE shell am start -n lab.nfc/.Main --es mode card
adb -s READER_PHONE shell am start -n lab.nfc/.Main --es mode reader
adb -s READER_PHONE logcat -d -s NFCLab:I '*:S'
```

The `reader` shortcut defaults to payment discovery. Choose the diagnostic-card button for the non-payment test. Keep the reader activity visible; it keeps the screen awake. Separate and re-tap the phones if switching modes does not trigger discovery.

`9000` means success; `6A82` means the selected application was not found, but still demonstrates an NFC response. No detection or a timeout alone does not establish hardware damage.

Exit or force-stop the app when finished to release reader mode:

```powershell
adb -s PHONE_SERIAL shell am force-stop lab.nfc
```

## Source and privacy

`build.py` contains the complete app source and build steps. Generated files, APKs, signing keys, and device logs are excluded from Git. The app requests only NFC permission and has no network permission. Payment response contents are neither displayed nor logged.
