"""Build OpenCore EFI for Lenovo ThinkCentre M710q (i5-7400T, HD 630).

usage: build_efi.py ROOT [profile] [--upgrade]
  ventura      iMac18,1, native KBL framebuffer           -> ROOT/EFI
  sequoia      iMac19,1, native KBL framebuffer           -> ROOT/EFI-sequoia   (recommended)
  sequoia-cfl  iMac19,1, iGPU spoofed as CFL UHD 630      -> ROOT/EFI-sequoia-cfl (not needed, see README)
  --upgrade    add -igfxvesa so the Ventura -> Sequoia installer stage does not hang on a black screen
  --airportitlwm  use AirportItlwm (native Wi-Fi menu) instead of itlwm + HeliPort
                  (the Sonoma 14.4 build does NOT load on Sequoia 15.8.1, see README)

ROOT must contain the extracted downloads (see scripts/fetch.sh) and may contain
smbios.json with your own generated identifiers (never commit it):
  {"iMac18,1": {"SystemSerialNumber": "...", "MLB": "...", "SystemUUID": "..."},
   "iMac19,1": {...}, "ROM": "<ethernet MAC, 12 hex digits>"}
"""
import json, plistlib, shutil, sys
from pathlib import Path

args = [a for a in sys.argv[1:] if not a.startswith("--")]
ROOT = Path(args[0])
PROFILE = args[1] if len(args) > 1 else "sequoia"
UPGRADE = "--upgrade" in sys.argv
AIRPORT = "--airportitlwm" in sys.argv
X = ROOT / "x"
OC = X / "OpenCore-1.0.8-RELEASE"
OUT = ROOT / {"ventura": "EFI", "sequoia": "EFI-sequoia", "sequoia-cfl": "EFI-sequoia-cfl"}[PROFILE]

# Placeholders keep the config valid; generate real values with macserial / GenSMBIOS.
PLACEHOLDER = {"SystemSerialNumber": "W00000000001", "MLB": "M0000000000000001",
               "SystemUUID": "00000000-0000-0000-0000-000000000000"}
local = ROOT / "smbios.json"
SMBIOS = json.loads(local.read_text()) if local.exists() else {}
MODEL = "iMac18,1" if PROFILE == "ventura" else "iMac19,1"

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "BOOT").mkdir(parents=True)
oc = OUT / "OC"
for d in ["ACPI", "Drivers", "Kexts", "Resources", "Tools"]:
    (oc / d).mkdir(parents=True)

shutil.copy(OC / "X64/EFI/BOOT/BOOTx64.efi", OUT / "BOOT")
shutil.copy(OC / "X64/EFI/OC/OpenCore.efi", oc)
shutil.copy(OC / "X64/EFI/OC/Tools/OpenShell.efi", oc / "Tools")

drivers = ["OpenRuntime.efi", "OpenHfsPlus.efi", "ResetNvramEntry.efi"]
for d in drivers:
    shutil.copy(OC / "X64/EFI/OC/Drivers" / d, oc / "Drivers")

ssdts = ["SSDT-PLUG-DRTNIA.aml", "SSDT-EC-USBX-DESKTOP.aml"]
for s in ssdts:
    shutil.copy(ROOT / "dl" / s, oc / "ACPI")

# (bundle, source dir, has executable) -- load order matters
kexts = [
    ("Lilu.kext", X / "Lilu-1.7.2-RELEASE", True),
    ("VirtualSMC.kext", X / "VirtualSMC-1.3.8-RELEASE/Kexts", True),
    ("SMCProcessor.kext", X / "VirtualSMC-1.3.8-RELEASE/Kexts", True),
    ("SMCSuperIO.kext", X / "VirtualSMC-1.3.8-RELEASE/Kexts", True),
    ("WhateverGreen.kext", X / "WhateverGreen-1.7.1-RELEASE", True),
    ("AppleALC.kext", X / "AppleALC-1.9.8-RELEASE", True),
    ("IntelMausi.kext", X / "IntelMausi-1.0.8-RELEASE", True),
    ("USBToolBox.kext", X / "USBToolBox-1.2.0-RELEASE", True),
    ("UTBDefault.kext", X / "USBToolBox-1.2.0-RELEASE", False),
    # Intel Wireless 8265: Wi-Fi via itlwm (+ HeliPort app) or, experimental on Sequoia,
    # AirportItlwm (Sonoma 14.4 build, native Wi-Fi menu). Never both. Bluetooth for macOS 12+.
    ("AirportItlwm.kext", X / "AirportItlwm_v2.3.0_stable_Sonoma14.4", True) if AIRPORT
    else ("itlwm.kext", X / "itlwm_v2.3.0_stable.kext", True),
    ("BlueToolFixup.kext", X / "BrcmPatchRAM-2.7.2-RELEASE", True),
    ("IntelBTPatcher.kext", X / "IntelBluetooth-v2.4.0", True),
    ("IntelBluetoothFirmware.kext", X / "IntelBluetooth-v2.4.0", True),
]
for k, src, _ in kexts:
    shutil.copytree(src / k, oc / "Kexts" / k)

p = plistlib.load(open(OC / "Docs/Sample.plist", "rb"))

# ACPI
p["ACPI"]["Add"] = [{"Comment": s, "Enabled": True, "Path": s} for s in ssdts]
p["ACPI"]["Delete"] = []
p["ACPI"]["Patch"] = []

# Booter (Kaby Lake desktop)
p["Booter"]["MmioWhitelist"] = []
p["Booter"]["Patch"] = []
p["Booter"]["Quirks"].update({
    "AvoidRuntimeDefrag": True, "DevirtualiseMmio": False, "EnableSafeModeSlide": True,
    "EnableWriteUnprotector": True, "ProvideCustomSlide": True, "RebuildAppleMemoryMap": False,
    "SetupVirtualMap": True, "SyncRuntimePermissions": False, "ProtectUefiServices": False,
})

# DeviceProperties: HD 630 driving display, KBL 0x59120000 or CFL 0x3E9B0007 spoof
igpu_id = ({"AAPL,ig-platform-id": bytes.fromhex("07009B3E"), "device-id": bytes.fromhex("9B3E0000")}
           if PROFILE == "sequoia-cfl" else {"AAPL,ig-platform-id": bytes.fromhex("00001259")})
p["DeviceProperties"]["Add"] = {
    "PciRoot(0x0)/Pci(0x2,0x0)": {
        **igpu_id,
        "framebuffer-patch-enable": bytes.fromhex("01000000"),
        "framebuffer-stolenmem": bytes.fromhex("00003001"),
        "framebuffer-fbmem": bytes.fromhex("00009000"),
        # DP->HDMI adapter into PiKVM: present all connectors as HDMI
        **{f"framebuffer-con{i}-{k}": bytes.fromhex(v) for i in range(3)
           for k, v in (("enable", "01000000"), ("type", "00080000"))},
    },
}
p["DeviceProperties"]["Delete"] = {}

# Kernel
add = []
for k, _, has_exe in kexts:
    add.append({
        "Arch": "Any", "BundlePath": k, "Comment": k, "Enabled": True,
        "ExecutablePath": f"Contents/MacOS/{k[:-5]}" if has_exe else "",
        "MaxKernel": "", "MinKernel": "", "PlistPath": "Contents/Info.plist",
    })
p["Kernel"]["Add"] = add
p["Kernel"]["Block"] = []
p["Kernel"]["Patch"] = []
p["Kernel"]["Force"] = []
p["Kernel"]["Quirks"].update({
    "AppleCpuPmCfgLock": False, "AppleXcpmCfgLock": True, "DisableIoMapper": True,
    "DisableLinkeditJettison": True, "PanicNoKextDump": True, "PowerTimeoutKernelPanic": True,
    "XhciPortLimit": False,
})

# Misc
p["Misc"]["Boot"].update({"HideAuxiliary": False, "PickerMode": "Builtin", "ShowPicker": True, "Timeout": 10})
p["Misc"]["Debug"].update({"AppleDebug": True, "ApplePanic": True, "DisableWatchDog": True, "Target": 67})
p["Misc"]["Security"].update({
    "AllowSetDefault": True, "BlacklistAppleUpdate": True, "ScanPolicy": 0,
    "SecureBootModel": "Default", "Vault": "Optional",
})
p["Misc"]["Entries"] = []
p["Misc"]["Tools"] = [t for t in p["Misc"]["Tools"] if t["Path"] == "OpenShell.efi"]
for t in p["Misc"]["Tools"]:
    t["Enabled"] = True

# NVRAM
nv = p["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
nv["boot-args"] = "-v keepsyms=1 debug=0x100 igfxonln=1" + (" -igfxvesa" if UPGRADE else "")
nv["csr-active-config"] = bytes.fromhex("00000000")
nv["prev-lang:kbd"] = b"en-US:0"   # Sample.plist ships ru-RU:252
p["NVRAM"]["Delete"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"].append("prev-lang:kbd")
# Intel Bluetooth with BlueToolFixup (see BrcmPatchRAM README)
nv["bluetoothExternalDongleFailed"] = bytes.fromhex("00")
nv["bluetoothInternalControllerInfo"] = bytes(14)
p["NVRAM"]["Delete"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"] += [
    "bluetoothExternalDongleFailed", "bluetoothInternalControllerInfo"]
p["NVRAM"]["WriteFlash"] = True

# PlatformInfo
g = p["PlatformInfo"]["Generic"]
g.update({
    "SystemProductName": MODEL,
    **SMBIOS.get(MODEL, PLACEHOLDER),
    "ROM": bytes.fromhex(SMBIOS.get("ROM", "112233445566")),
})
p["PlatformInfo"]["UpdateSMBIOSMode"] = "Create"

# UEFI
p["UEFI"]["Drivers"] = [
    {"Arguments": "", "Comment": d, "Enabled": True, "HideVerbose": False, "LoadEarly": False, "Path": d}
    for d in drivers
]
p["UEFI"]["Quirks"]["RequestBootVarRouting"] = True

with open(oc / "config.plist", "wb") as f:
    plistlib.dump(p, f)
print("EFI built at", OUT)
