import concurrent
import os
import subprocess
import sys
import threading

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QStringListModel, QDir
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QFileDialog, QDialog, QVBoxLayout, QPlainTextEdit, \
    QFileSystemModel

from dialog import Ui_Dialog
from multi_install import *
from concurrent.futures import ThreadPoolExecutor


class MyDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)


class MultiInstall(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.install_thread = None
        self.setupUi(self)
        self.init_model()
        self.showDevicesBtn.clicked.connect(self.show_devices)
        self.installSelectBtn.clicked.connect(self.select_install)
        self.installAllBtn.clicked.connect(self.all_install)
        self.openFileBtn.clicked.connect(self.open_file_dialog)
        self.apkfreshBtn.clicked.connect(self.show_apk)
        self.dialogBtn.clicked.connect(self.show_dialog)
        self.freshscripts.clicked.connect(self.show_airtestscripst)
        self.runselectscrBtn.clicked.connect(self.run_selectscr)
        self.showallBtn.clicked.connect(self.show_all)

        self.show()

        self.apk = ''
        self.devices_info = {}

    def show_all(self):
        self.show_devices()
        self.show_apk()
        self.show_airtestscripst()

    def show_dialog(self):
        self.dialog_window = MyDialog(self)
        self.dialog_window.show()

    def show_apk(self):
        self.apk_model.clear()
        # 假设当前脚本位于项目根目录下
        # 获取当前脚本的目录（项目根目录）
        project_root = os.path.dirname(os.path.abspath(__file__))

        # 构造APK文件夹的路径
        apk_folder_path = os.path.join(project_root, 'APK')

        # 列出APK文件夹中的所有文件和文件夹
        apk_files = [f for f in os.listdir(apk_folder_path) if f.endswith('.apk')]

        # 打印所有APK文件的文件名
        for apk_file in apk_files:
            print(apk_file)
            # 利用QStringListModel来展示文件名
            self.apk_model.appendRow(QStandardItem(apk_file))

        self.output.appendPlainText("获取apk成功！共获取到 {} 个apk！".format(len(apk_files)))

    def open_file_dialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "All Files (*);;Text Files (*.txt)",
                                                  options=options)
        if fileName:
            self.filePath.setPlainText(fileName)
            self.apk = fileName

    def init_model(self):
        self.devices_model = QStandardItemModel()
        self.devices_model.setHorizontalHeaderLabels(["device_id", "device_name"])
        self.tableView.setModel(self.devices_model)
        self.airtestmodel = QStandardItemModel()
        self.airtestscipstlistView.setModel(self.airtestmodel)
        self.apk_model = QStandardItemModel()
        self.apkList.setModel(self.apk_model)


    def dragEnterEvent(self, event: QDragEnterEvent):
        # 当拖拽进入窗口时调用
        if event.mimeData().hasUrls():  # 检查是否有URLs
            event.acceptProposedAction()  # 接受拖拽动作

    def dropEvent(self, event: QDropEvent):
        # 当释放拖拽动作时调用
        if event.mimeData().hasUrls():
            print("拖拽文件")
            event.setDropAction(Qt.CopyAction)  # 设置拖拽动作为复制
            event.accept()
            # 获取文件路径
            urls = event.mimeData().urls()
            if len(urls) > 1:
                QMessageBox.warning(self, "警告", "一次只能拖拽一个文件！")
                return
            if urls[0].scheme() == 'file':
                file_path = urls[0].toLocalFile()  # 获取本地文件路径
                # print(file_path)
                self.apk = file_path
                self.filePath.setPlainText(file_path)

    def show_devices(self):
        self.devices_model.clear()
        # self.output.clear()
        self.get_devices_info()
        if self.devices_info:
            self.add_devices_to_table()

    def add_devices_to_table(self):
        for device_id, device_name in self.devices_info.items():
            print(device_id, device_name)
            # 添加到模型中
            id_model = QStandardItem(device_id)
            id_model.setTextAlignment(Qt.AlignCenter)
            name_model = QStandardItem(device_name)
            name_model.setTextAlignment(Qt.AlignCenter)
            self.devices_model.appendRow([id_model, name_model])

    def get_devices_info(self):
        # 清空设备信息
        self.devices_info = {}
        # 执行 adb devices -l 命令
        result = subprocess.Popen(
            ['adb', 'devices', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # creationflags=subprocess.CREATE_NO_WINDOW
        )
        stdout, stderr = result.communicate()
        # 检查是否有错误输出
        if stderr:
            print("Error:", stderr)
            QMessageBox.warning(self, "警告", "获取设备信息失败！")
            return None
        else:
            # 解析输出
            lines = stdout.splitlines()
            # 跳过第一行（标题行）
            for line in lines[1:]:
                if line:  # 非空行
                    parts = line.split()
                    device_id = parts[0]
                    model = None
                    for prop in parts[1:]:
                        if prop.startswith('model:'):
                            model = prop.split(':')[1]
                            break
                    if model:
                        self.devices_info[device_id] = model
            self.output.appendPlainText("获取设备信息成功！共获取到 {} 台设备！".format(len(self.devices_info)))

    def check_apk_and_devices(self, devices_info=None):
        """
        检查是否选择了APK文件和设备
        """
        if not devices_info:
            QMessageBox.warning(self, "警告", "没有可安装设备！请选择设备安装！")
            return
        if not self.apk:
            QMessageBox.warning(self, "警告", "请先选择APK文件！")
            self.open_file_dialog()
            return
        self.output.clear()
        self.output.appendPlainText("APK文件路径：{}".format(self.apk))
        return True

    def selected_devices(self):
        # 获取选择的设备id
        selected_indices = self.tableView.selectionModel().selectedRows()  # 获取选中的行索引
        if not selected_indices:
            return
        selected_devices = {}
        for index in selected_indices:
            # 获取设备ID，角色使用Qt.DisplayRole
            device_id = self.devices_model.data(self.devices_model.index(index.row(), 0), Qt.DisplayRole)
            device_name = self.devices_model.data(self.devices_model.index(index.row(), 1), Qt.DisplayRole)
            selected_devices[device_id] = device_name
        return selected_devices

    def select_install(self):
        select_devices = self.selected_devices()
        if self.check_apk_and_devices(select_devices):
            self.start_install_thread(select_devices)
            return
        if not self.devices_info:
            self.show_devices()

    def all_install(self):
        self.show_devices()
        if self.check_apk_and_devices(self.devices_info):
            self.start_install_thread(self.devices_info)

    def start_install_thread(self, devices_info):
        if devices_info:
            self.output.appendPlainText("正在获取安装设备，请稍等...")
            self.install_thread = InstallThread(devices_info, self.apk)
            self.install_thread.update_text.connect(self.update_plaintext)
            self.install_thread.start()

    def update_plaintext(self, text):
        self.output.appendPlainText(text)

    # 刷新自动化脚本
    def show_airtestscripst(self):
        self.airtestmodel.clear()
        # 假设scripts文件夹位于项目根目录下
        scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
        scripts_list = os.listdir(scripts_dir)
        for item in scripts_list:
            # 构建完整路径
            item_path = os.path.join(scripts_dir, item)
            # 检查是否为文件夹且名称以.air结尾
            if os.path.isdir(item_path) and item.endswith('.air'):
                # 添加文件夹名到模型
                folder_item = QStandardItem(item)
                self.airtestmodel.appendRow(folder_item)

        self.output.appendPlainText("获取脚本成功！共获取到 {} 个脚本！".format(len(scripts_list)))

    # 选择自动化脚本
    def selected_airtestscripts(self):

        # 获取选择的设备id
        selected_indices = self.airtestscipstlistView.selectionModel().selectedRows()  # 获取选中的行索引
        if not selected_indices:
            return
        selected_airtestscriptname = []
        for index in selected_indices:
            airtestscriptname = self.airtestmodel.data(self.airtestmodel.index(index.row(), 0), Qt.DisplayRole)
            selected_airtestscriptname.append(airtestscriptname)
        return selected_airtestscriptname

    # def test(self):
    #     script_path = 'D:\\qa_tools\\multi_install-main\\scripts\\untitled.air'
    #     device = 'Android:///'
    #     self.run_airtest_script(script_path, device)
    #     templist = self.selected_airtestscripts()
    #     scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
    #     for item in templist:
    #
    #         item_path = os.path.join(scripts_dir, item)

    def run_airtest_script(self, script_path, device):
        """
        运行Airtest脚本

        :param script_path: Airtest脚本的路径
        :param device: 目标设备的标识符
        """
        try:
            # 构建命令行指令
            command = [
                'airtest', 'run',
                script_path,
                '--device', device
            ]

            # 执行命令行指令
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # 输出命令行的标准输出和标准错误（如果有的话）
            print("Standard Output:")
            print(result.stdout)

            if result.stderr:
                print("Standard Error:")
                print(result.stderr)

            print("Airtest script executed successfully.")

        except subprocess.CalledProcessError as e:
            # 如果命令行指令返回非零退出码，将引发此异常
            print(f"An error occurred while executing the Airtest script: {e}")
            print(f"Standard Error: {e.stderr}")

    # 执行选中脚本
    def run_selectscr(self):
        templist = self.selected_airtestscripts()
        scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
        select_devices = self.selected_devices()

        device_path_list = []

        if select_devices:
            for device in select_devices.keys():
                device_path = f'Android://127.0.0.1:5037/{device}'
                device_path_list.append(device_path)
        else:
            device_path = 'Android:///'
            device_path_list.append(device_path)
        if templist:
            for item in templist:
                for device in device_path_list:
                    item_path = os.path.join(scripts_dir, item)
                    self.run_airtest_script(item_path, device)
        else:
            QMessageBox.warning(self, "警告", "没有选择脚本！")


class InstallThread(QThread):
    update_text = pyqtSignal(str)

    def __init__(self, devices_info, apk, parent=None):
        super(InstallThread, self).__init__(parent)
        self.device_info = devices_info
        self.apk = apk

    def run(self):
        with ThreadPoolExecutor(max_workers=len(self.device_info)) as executor:
            # 创建一个未来到设备名字的映射
            future_to_device_name = {executor.submit(self.install_apk, device_id, device_name, self.apk): device_name
                                     for
                                     device_id, device_name in self.device_info.items()}

            for future in concurrent.futures.as_completed(future_to_device_name):
                device_name = future_to_device_name[future]
                try:
                    result = future.result()
                    if result['success']:
                        output = f"{device_name} 安装完成:\n{result['stdout']}"
                    else:
                        output = f"{device_name} 安装失败:\n{result['stderr']}"
                except Exception as exc:
                    output = f"An error occurred on {device_name}: {exc}"
                self.update_text.emit("\n" + output)
        self.update_text.emit("所有设备安装完成。\n")

    def install_apk(self, device_id, device_name, apk_path):
        try:
            print(f"Thread {threading.current_thread().name} started installing on {device_name}")
            self.update_text.emit(f"{device_name} 开始安装")
            # 使用Popen代替run，并设置creationflags=CREATE_NO_WINDOW
            process = subprocess.Popen(
                ['adb', '-s', device_id, 'install', apk_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # 等待进程完成
            stdout, stderr = process.communicate()
            return {'success': process.returncode == 0, 'stdout': stdout, 'stderr': stderr}
        except Exception as e:
            return {'success': False, 'stderr': str(e)}


if __name__ == '__main__':
    app = QApplication(sys.argv)
    multi_install = MultiInstall()
    sys.exit(app.exec_())
