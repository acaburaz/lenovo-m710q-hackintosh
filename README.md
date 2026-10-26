# Lenovo ThinkCentre M710q Tiny – macOS Sequoia (OpenCore)

OpenCore EFI and step-by-step notes for running **macOS Sequoia 15.8.1** (and Ventura 13.7.8) on a
Lenovo ThinkCentre **M710q Tiny** with an Intel **i5-7400T / HD Graphics 630**. The whole install
was done headless through a **PiKVM** (virtual USB drive + keyboard/mouse + HDMI capture), so
there are also notes on driving a Hackintosh install over a KVM.

> Status (2026-10-26): Sequoia 15.8.1 boots from the internal SSD with full graphics
> acceleration (Metal 3), Ethernet, USB, Bluetooth and Wi-Fi (itlwm + HeliPort).
> Audio layout and a proper USB map not configured yet.

## Hardware

| Part | Model | Status |
|---|---|---|
| Machine | ThinkCentre M710q Tiny, type 10MR, BIOS M1AKT36A | |
| CPU | Intel Core i5-7400T (Kaby Lake, 4C/4T) | ✅ |
| iGPU | Intel HD Graphics 630 (`8086:5912`) | ✅ native, Metal 3, 1080p |
| RAM | 8 GB DDR4-2400 | ✅ |
| Storage | Kingston A400 240 GB SATA | ✅ |
| Ethernet | Intel I219-V | ✅ IntelMausi |
| Wi-Fi | Intel Wireless 8265 (`8086:24FD`) | ✅ itlwm 2.3.0 + HeliPort app (no AirDrop/Continuity) |
| Bluetooth | Intel 8265 BT (`8087:0A2B`, internal USB) | ✅ IntelBluetoothFirmware 2.4.0 + IntelBTPatcher + BlueToolFixup |
| Audio | Realtek (AppleALC loaded) | ⏳ no `layout-id` chosen yet |
| Video out | DisplayPort only (no HDMI) | ✅ via DP→HDMI adapter, see connector patch |

## EFI contents

* OpenCore **1.0.8**
* Kexts: Lilu 1.7.2, VirtualSMC 1.3.8 (+SMCProcessor, SMCSuperIO), WhateverGreen 1.7.1,
  AppleALC 1.9.8, IntelMausi 1.0.8, USBToolBox 1.2.0 + UTBDefault (generic map – make your own),
  itlwm 2.3.0, BlueToolFixup 2.7.2 (from BrcmPatchRAM), IntelBTPatcher + IntelBluetoothFirmware 2.4.0
* ACPI: Dortania prebuilt `SSDT-PLUG-DRTNIA`, `SSDT-EC-USBX-DESKTOP` (no AWAC needed on 200-series)
* Drivers: OpenRuntime, OpenHfsPlus, ResetNvramEntry
* SMBIOS **iMac19,1** (Sequoia) / iMac18,1 (Ventura)

The `EFI/` folder in this repo contains **placeholder serials**. Before use, generate your own
SystemSerialNumber / MLB / SystemUUID for iMac19,1 (macserial or GenSMBIOS), and set ROM to your
Ethernet MAC – or put them in `smbios.json` and rebuild (see below).

### Key config choices

| Setting | Value | Why |
|---|---|---|
| `AAPL,ig-platform-id` | `00001259` (0x59120000) | HD 630 desktop with display. **No Coffee Lake spoof needed on Sequoia** – Sequoia's `AppleIntelKBLGraphics*` still match `0x5912`. |
| `framebuffer-con0..2-type` | `00080000` (HDMI) | DP→HDMI adapter. Without it the screen goes black as soon as WhateverGreen takes over. Remove if you use DisplayPort directly. |
| `framebuffer-stolenmem` / `fbmem` | `00003001` / `00009000` | Lenovo DVMT pre-alloc is small. |
| boot-args | `-v keepsyms=1 debug=0x100 igfxonln=1` | `igfxonln=1` forces displays online (helps capture cards/adapters). Drop `-v`/`debug` once stable. |
| `AppleXcpmCfgLock` | true | CFG Lock can't be disabled in the Lenovo BIOS menu. |
| `DisableIoMapper` | true | Instead of disabling VT-d. |
| `prev-lang:kbd` | `en-US:0` | ⚠️ OpenCore's `Sample.plist` ships `ru-RU:252` – the installer comes up in Russian otherwise. |
| `bluetoothExternalDongleFailed` = `00`, `bluetoothInternalControllerInfo` = 14 × `00` | NVRAM Add (+Delete) | Required by BlueToolFixup for Intel Bluetooth. Without them the controller shows `Address: NULL`, `State: Off`. |

## Wi-Fi and Bluetooth (Intel 8265)

* **Wi-Fi:** OpenIntelWireless has no AirportItlwm build for Sequoia (latest: Sonoma 14.4), so this
  uses **itlwm.kext**. The card appears as an extra Ethernet port (`en1`); join networks with the
  **[HeliPort](https://github.com/OpenIntelWireless/HeliPort)** menu-bar app (tick *Launch at
  Login*). Copy HeliPort to /Applications – its DMG asks you to accept its BSD-3 license.
* **Tested and not working: AirportItlwm v2.3.0 *Sonoma 14.4* build on Sequoia 15.8.1**
  (`build_efi.py ... --airportitlwm`). OpenCore refuses it at boot with
  `OC: Prelinked injection AirportItlwm.kext - Invalid Parameter` – Sequoia's IO80211Family
  (1200.13.1) no longer matches what the Sonoma build links against. Nothing crashes; there is just
  no Wi-Fi. Stay on itlwm until OpenIntelWireless ships a Sequoia build.
* **Bluetooth:** `BlueToolFixup` (Lilu plugin from BrcmPatchRAM) + `IntelBTPatcher` +
  `IntelBluetoothFirmware`. Do **not** add `IntelBluetoothInjector` on macOS 12+. Set the two
  NVRAM variables above. macOS then reports the controller as `THIRD_PARTY_DONGLE` – that's fine.

## BIOS

Defaults on this unit were already correct: **CSM disabled, Boot mode UEFI only, Secure Boot
disabled**. Nothing else changed.

## Install path that worked

1. **Build the EFI** (Windows/macOS/Linux, Python 3):
   ```bash
   scripts/fetch.sh ~/m710q              # downloads exact versions into ~/m710q/{dl,x}
   python3 scripts/build_efi.py ~/m710q ventura      # for the first install
   python3 scripts/build_efi.py ~/m710q sequoia      # final config
   ```
2. **Install Ventura first** from a Ventura recovery image
   (`macrecovery.py -b Mac-4B682C642B45593E -m 00000000000000000 download`) with the `ventura`
   EFI. Erase the SATA disk as APFS / GUID in Disk Utility → Reinstall macOS Ventura.
3. Copy the **`sequoia` EFI (iMac19,1)** to the internal disk's EFI partition and reboot.
   Software Update now offers Sequoia.
4. **Upgrade to Sequoia with `-igfxvesa` added** (`build_efi.py ... sequoia --upgrade`, or add the
   boot-arg temporarily). See the pitfall below.
5. After Sequoia reaches the desktop, remove `-igfxvesa` again → full acceleration.

## Pitfalls we hit (and fixes)

* **Black screen right after the kernel starts (installer/Recovery):** DP→HDMI adapter + default DP
  connector types. Fix: connector type patch to HDMI (`00080000`) for con0–con2.
* **Ventura → Sequoia upgrade hangs or boot-loops (black screen with native KBL, kernel panics /
  instant resets with a Coffee Lake spoof):** the Sequoia installer/recovery stage did not get
  through with HD 630 acceleration on this machine. **Fix: boot the installer stages with
  `-igfxvesa`.** The upgrade then finished in two reboots. Afterwards the normal native KBL config
  (no spoof, no `-igfxvesa`) boots Sequoia with Metal 3.
* **After a failed upgrade, "Macintosh HD" keeps booting Recovery (`-bsdmgroot`)** – that's the
  update still pending. Reset NVRAM, then boot Macintosh HD with `-igfxvesa` to let it finish.
* **OpenCore picker auto-boots its own USB entry and hangs ("Timeout")** after an NVRAM reset (no
  default set). Set `Misc.Boot.Timeout` to 0 while debugging, or pick the entry manually.
* **Panic text scrolls away on a 720p capture.** Grab frames several times per second (see
  `pikvm/fastcap.sh`) to catch it, or rely on the shutdown log: launchd `removing service ...
  PETRIFIED` lines mean an orderly reboot (installer progress), not a crash.

## Doing it through a PiKVM

* M710q has no HDMI out → **DP→HDMI adapter** into the PiKVM HDMI input.
* Build a GPT/FAT32 image containing `EFI/` + `com.apple.recovery.boot/` and attach it as
  **Flash** (not CD-ROM) via the Drive menu / `msd` API. The Lenovo lists it as
  "PiKVM Flash Drive" in the **F12** boot menu.
* Keep the MSD image **read-write** if you want OpenCore logs (`Misc.Debug.Target = 67`) written
  back to it – very handy for debugging boot loops from the PiKVM side.
* macOS can't mount a read-only FAT MSD (`failed to mount`) – copy files over SSH instead.
* Ctrl+Alt+Del from the PiKVM resets the machine while OpenCore/firmware is running; once macOS
  hangs you need the power button (or wired ATX).
* After the install, present the PiKVM as a plain keyboard/mouse and drop the virtual drive
  (`/etc/kvmd/override.yaml`, then `systemctl restart kvmd-otg kvmd`):
  ```yaml
  otg:
      manufacturer: Generic
      product: USB Keyboard and Mouse
      devices:
          msd:
              start: false
  kvmd:
      msd:
          type: disabled
  ```
  macOS then shows "Generic – USB Keyboard and Mouse" and no external disk.
* OpenCore default entry: SIP blocks `bless --setBoot`, so select *Macintosh HD* in the picker
  and press **Ctrl+Enter** once (`AllowSetDefault` is enabled).
* `pikvm/` has the small helpers used here (run on the PiKVM as root, they use the local
  `kvmd` unix socket, which accepts root without a password):
  * `k.sh` – `key F12`, `combo ControlLeft,AltLeft,Delete`, `click X Y`, `text "..."`, `snap`
    (click coordinates assume the capture resolution set inside the script)
  * `keep.py` – keeps the video streamer running so snapshots work without a browser open
  * `online.py` – prints whether the HDMI source has a signal
  * `fastcap.sh` – boots the selected OpenCore entry and captures ~3 frames/s until reboot

## Credits / licenses

OpenCore, Lilu, VirtualSMC, WhateverGreen, AppleALC, IntelMausi (acidanthera, BSD-3-Clause),
USBToolBox (dhinakg), itlwm / IntelBluetoothFirmware / HeliPort (OpenIntelWireless, zxystd), BrcmPatchRAM (acidanthera), ACPI tables from the Dortania guides. Follow the
[Dortania OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/) for the
background on every setting above.

macOS is licensed by Apple for use on Apple-branded hardware only. This repository is
documentation of a personal experiment; use at your own risk.
