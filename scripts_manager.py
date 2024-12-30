import subprocess
import threading
import queue
import time

class Device:
    def __init__(self, name):
        self.name = name
        self.lock = threading.Lock()
        self.is_busy = False

    def occupy(self, script_name):
        with self.lock:
            self.is_busy = True
            print(f"Device {self.name} is now occupied by script {script_name}.\n")
            result = self.run_airtest_script(script_name)
            if result['success']:
                print(f"{self.name} 安装完成:\n{result['stdout']}")
            else:
                print(f"{self.name} 安装失败:\n{result['stderr']}")
            print(f"Device {self.name} has completed script {script_name}.\n")
            self.is_busy = False

    def run_airtest_script(self, script_path):
        """运行 Airtest 脚本"""
        try:
            process = subprocess.Popen(
                ['airtest', 'run', script_path, '--device', self.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            return {'success': process.returncode == 0, 'stdout': stdout, 'stderr': stderr}
        except Exception as e:
            return {'success': False, 'stderr': str(e)}


class DeviceManager(threading.Thread):
    def __init__(self, devices_paths, parent=None):
        super().__init__()
        self.device_paths = devices_paths
        self.task_queue = queue.Queue()
        self.daemon = True  # Ensures the thread will exit when the main program exits

    def add_task(self, script_name):
        self.task_queue.put((script_name))

    def run(self):
        while True:
            script_name = self.task_queue.get()
            self.assign_device(script_name)
            self.task_queue.task_done()

    def assign_device(self, script_name):
        while True:
            for device_path in self.device_paths:
                if not device_path.is_busy:
                    threading.Thread(target=device_path.occupy, args=(script_name,)).start()
                    return
            time.sleep(1)  # Wait for a device to become free

if __name__ == "__main__":
    # Create devices
    devices = [Device(f"Device-{i+1}") for i in range(3)]


    # Create and start the device manager
    device_manager = DeviceManager(devices)
    device_manager.start()

    # Add tasks (script_name, duration_in_seconds)
    scripts = ['test.air'
    ]

    for script_name in scripts:
        device_manager.add_task(script_name)

    # Wait for all tasks to complete
    device_manager.task_queue.join()
    print("All scripts have been executed.")
