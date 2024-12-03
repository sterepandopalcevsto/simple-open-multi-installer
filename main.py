import subprocess
import os
import requests
import sys

class MultiInstaller:
    def __init__(self, config_file="installer_config.txt", download_dir="downloads", log_file="install_log.txt"):
        self.config_file = config_file
        self.download_dir = download_dir
        self.log_file = log_file
        self.apps = self.load_config()
        os.makedirs(self.download_dir, exist_ok=True)

    def load_config(self):
        apps = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                for idx, line in enumerate(file):
                    line = line.strip()
                    if line and not line.startswith("#"):  # Ignore comments and empty lines
                        name, url, command = line.split(";", 2)
                        apps[idx + 1] = {
                            "name": name.strip(),
                            "url": url.strip(),
                            "command": command.strip()
                        }
        return apps

    def log_installation(self, app_name, installer_path):
        install_info = f"{app_name};{installer_path}\n"
        with open(self.log_file, "a") as log:
            log.write(install_info)

    def read_installation_log(self):
        installations = {}
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as log:
                for line in log:
                    name, path = line.strip().split(";")
                    installations[name] = path
        return installations

    def uninstall_app(self, app_name):
        installations = self.read_installation_log()
        if app_name not in installations:
            print(f"[ERROR] {app_name} not found in installation log.")
            return

        path = installations[app_name]
        try:
            print(f"[INFO] Uninstalling {app_name} from {path}...")
            subprocess.run(f"msiexec /x {path} /quiet", shell=True, check=True)  # Adjust command for different installers
            print(f"[SUCCESS] {app_name} uninstalled successfully!")
            # Remove from log
            with open(self.log_file, "r") as log:
                lines = log.readlines()
            with open(self.log_file, "w") as log:
                for line in lines:
                    if not line.startswith(app_name):
                        log.write(line)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to uninstall {app_name}. Error: {e}")

    def download_file(self, app_number):
        app = self.apps.get(app_number)
        if not app:
            print(f"[ERROR] Application #{app_number} not found.")
            return None

        url = app["url"]
        file_name = os.path.join(self.download_dir, os.path.basename(url))
        try:
            print(f"[INFO] Downloading {app['name']} from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(file_name, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"[SUCCESS] {app['name']} downloaded successfully!")
            return file_name
        except requests.RequestException as e:
            print(f"[ERROR] Failed to download {app['name']}. Error: {e}")
            return None

    def install_app(self, app_number):
        app = self.apps.get(app_number)
        if not app:
            print(f"[ERROR] Application #{app_number} not found.")
            return

        installer_path = self.download_file(app_number)
        if not installer_path:
            return

        command = app["command"].replace("{installer}", installer_path)
        try:
            print(f"[INFO] Installing {app['name']}...")
            subprocess.run(command, shell=True, check=True)
            print(f"[SUCCESS] {app['name']} installed successfully!")
            self.log_installation(app["name"], installer_path)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install {app['name']}. Error: {e}")

    def install_all(self):
        for app_number in self.apps.keys():
            self.install_app(app_number)

if __name__ == "__main__":
    installer = MultiInstaller()

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("[INFO] Auto-install mode activated.")
        installer.install_all()
    else:
        while True:
            print("\nAvailable Applications:")
            for number, app in installer.apps.items():
                print(f"{number}. {app['name']}")
            print("\nMenu:")
            print("1. Install by number")
            print("2. Install all applications")
            print("3. Uninstall an application")
            print("4. Exit")

            choice = input("\nEnter your choice: ").strip()
            if choice == "1":
                app_number = input("Enter the number of the application to install: ").strip()
                if app_number.isdigit() and int(app_number) in installer.apps:
                    installer.install_app(int(app_number))
                else:
                    print("[ERROR] Invalid application number.")
            elif choice == "2":
                installer.install_all()
            elif choice == "3":
                installations = installer.read_installation_log()
                if not installations:
                    print("[INFO] No applications to uninstall.")
                else:
                    print("\nInstalled Applications:")
                    for name in installations:
                        print(f" - {name}")
                    app_name = input("Enter the name of the application to uninstall: ").strip()
                    installer.uninstall_app(app_name)
            elif choice == "4":
                print("Exiting the installer. Goodbye!")
                break
            else:
                print("[ERROR] Invalid choice. Please try again.")
