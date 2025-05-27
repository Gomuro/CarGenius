# desctop/utils/device_utils.py
import subprocess
import hashlib
import requests


# Get value from WMIC via subprocess (works on Windows)
def get_wmic_value(wmic_class: str, prop: str):
    try:
        output = subprocess.check_output(
            ["wmic", wmic_class, "get", prop],
            text=True
        )
        lines = output.strip().split("\n")
        values = [line.strip() for line in lines if line.strip()]
        return values[1] if len(values) > 1 else None
    except Exception as e:
        print(f"Error getting {prop} from {wmic_class}: {e}")
        return None


# Generate unique device ID based on hardware serials
def get_device_id():
    cpu = get_wmic_value("cpu", "ProcessorID") # CPU serial
    baseboard = get_wmic_value("baseboard", "SerialNumber") # Motherboard serial
    disk = get_wmic_value("diskdrive", "SerialNumber") # serial number of the first disk
    mac = get_wmic_value("nic where (MACAddress is not NULL and PhysicalAdapter=True)", "MACAddress")  # MAC address of the first network interface

    print("CPU:", cpu)
    print("Baseboard:", baseboard)
    print("Disk:", disk)
    print("MAC:", mac)

    combined = "|".join(filter(None, [cpu, baseboard, disk, mac]))  # Combine all values
    if combined:
        device_id = hashlib.sha256(combined.encode()).hexdigest() if combined else None  # Hash the combined string to get a unique ID
        print("Combined:", combined)
        print("Device ID (hashed):", device_id)
        return device_id
    else:
        print("No components found for device ID")
        return None


# if __name__ == "__main__":
#     device_id = get_device_id()
#     print("Final device ID:", device_id)
#
#
# # Example usage:
# # device_id = get_device_id()
# # print(f"Device ID: {device_id}")
# #
# # # Activate the license
# # response = requests.post("http://localhost:8000/api/v1/license/activate", json={
# #     "device_id": device_id,
# #     "license_key": "your_license_key_here"  # Replace with your actual license key
# # })
# #
# # print(response.status_code, response.json)