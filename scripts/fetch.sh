#!/usr/bin/env bash
# Download the exact OpenCore / kext / SSDT versions this EFI was built and tested with.
# usage: scripts/fetch.sh WORKDIR   -> WORKDIR/dl (downloads), WORKDIR/x (extracted)
set -euo pipefail
W="${1:?usage: fetch.sh WORKDIR}"
mkdir -p "$W/dl" "$W/x"
cd "$W/dl"

urls=(
  https://github.com/acidanthera/OpenCorePkg/releases/download/1.0.8/OpenCore-1.0.8-RELEASE.zip
  https://github.com/acidanthera/Lilu/releases/download/1.7.2/Lilu-1.7.2-RELEASE.zip
  https://github.com/acidanthera/VirtualSMC/releases/download/1.3.8/VirtualSMC-1.3.8-RELEASE.zip
  https://github.com/acidanthera/WhateverGreen/releases/download/1.7.1/WhateverGreen-1.7.1-RELEASE.zip
  https://github.com/acidanthera/AppleALC/releases/download/1.9.8/AppleALC-1.9.8-RELEASE.zip
  https://github.com/acidanthera/IntelMausi/releases/download/1.0.8/IntelMausi-1.0.8-RELEASE.zip
  https://github.com/USBToolBox/kext/releases/download/1.2.0/USBToolBox-1.2.0-RELEASE.zip
  https://github.com/OpenIntelWireless/itlwm/releases/download/v2.3.0/itlwm_v2.3.0_stable.kext.zip
  https://github.com/OpenIntelWireless/itlwm/releases/download/v2.3.0/AirportItlwm_v2.3.0_stable_Sonoma14.4.kext.zip
  https://github.com/OpenIntelWireless/IntelBluetoothFirmware/releases/download/v2.4.0/IntelBluetooth-v2.4.0.zip
  https://github.com/acidanthera/BrcmPatchRAM/releases/download/2.7.2/BrcmPatchRAM-2.7.2-RELEASE.zip
  https://github.com/dortania/Getting-Started-With-ACPI/raw/master/extra-files/compiled/SSDT-PLUG-DRTNIA.aml
  https://github.com/dortania/Getting-Started-With-ACPI/raw/master/extra-files/compiled/SSDT-EC-USBX-DESKTOP.aml
)
for u in "${urls[@]}"; do curl -sSLf -O "$u"; done

for z in *.zip; do
  n="${z%.zip}"; mkdir -p "../x/$n"; unzip -q -o "$z" -d "../x/$n"
done
echo "Done. Next: python3 scripts/build_efi.py $W sequoia"
