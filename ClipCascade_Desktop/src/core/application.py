import logging
import sys


from core.constants import *

from core.config import Config
from utils.request_manager import RequestManager
from utils.cipher_manager import CipherManager
from stomp_ws.stomp_manager import STOMPManager

if PLATFORM == WINDOWS:
    import ctypes
elif PLATFORM == MACOS or PLATFORM.startswith(LINUX):
    import fcntl


if PLATFORM.startswith(LINUX) and not XMODE:
    import pyfiglet
    from cli.login import LoginForm
    from cli.info import CustomDialog
    from cli.tray import TaskbarPanel
    from cli.message_box import MessageBox
    from cli.echo import Echo
else:
    from gui.login import LoginForm
    from gui.info import CustomDialog
    from gui.tray import TaskbarPanel
    from gui.message_box import MessageBox


class Application:
    def __init__(
        self,
        log_file_path=LOG_FILE_NAME,
        data_file_path=DATA_FILE_NAME,
        mutex_identifier=MUTEX_NAME,
    ):
        try:
            self.log_file_path = os.path.join(
                get_program_files_directory(), log_file_path
            )
            self.data_file_path = os.path.join(
                get_program_files_directory(), data_file_path
            )
            self.mutex_identifier = mutex_identifier

            if PLATFORM == MACOS or PLATFORM.startswith(LINUX):
                self.lock_file = None  # File(lock) object
                self.mutex_identifier = os.path.join(
                    get_program_files_directory(), self.mutex_identifier
                )

            self.config = Config(
                file_name=self.data_file_path
            )  # Maintain a single configuration instance for the entire application lifecycle.

            self.request_manager = RequestManager(self.config)
            self.stomp_manager = STOMPManager(self.config)
            self.cipher_manager = CipherManager(self.config)
        except Exception as e:
            CustomDialog(
                f"An error occurred during application initialization: {e}",
                msg_type="error",
            ).mainloop()

    def setup_logging(self):
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            filename=self.log_file_path,
            filemode="w",
        )

    def ensure_single_instance(self):
        if PLATFORM == WINDOWS:
            ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_identifier)
            if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                CustomDialog(
                    "Another instance of ClipCascade is already running.",
                    msg_type="warning",
                ).mainloop()
                sys.exit(0)
        elif PLATFORM == MACOS or PLATFORM.startswith(LINUX):
            if PLATFORM == MACOS:
                app_dir = get_program_files_directory()
                if not os.path.exists(app_dir):
                    try:
                        os.makedirs(app_dir)
                    except Exception as e:
                        CustomDialog(
                            f"An error occurred while creating the directory '{app_dir}'. Error: {e}",
                            msg_type="error",
                        ).mainloop()
                        sys.exit(1)

            # Create the lock file
            try:
                self.create_lock_file()
            except IOError:
                run_anyway = MessageBox().askquestion(
                    "ClipCascade",
                    "Another instance of ClipCascade is already running. Do you want to run anyway?",
                )
                if run_anyway == "yes":
                    os.remove(self.mutex_identifier)
                    self.create_lock_file()
                else:
                    self.lock_file = None
                    sys.exit(0)

    def create_lock_file(self, path=None):
        if path is None:
            path = self.mutex_identifier

        if PLATFORM == MACOS or PLATFORM.startswith(LINUX):
            self.lock_file = open(path, "w")
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def authenticate_and_connect(self):
        # Attempt to connect with existing cookie
        if self.config.data.get("cookie"):
            stomp_conn_successful, msg_stomp = self.stomp_manager.connect()
            if stomp_conn_successful:
                self.stomp_manager.is_login_phase = False
                return

        # enable login form
        used_saved_credentials = False
        display_login_success_dialog = False
        if PLATFORM.startswith(LINUX) and not XMODE:
            Echo("═" * 14 + "\n║ LOGIN FORM ║\n" + "═" * 14)
        while True:
            if (
                self.config.data.get("cookie") is not None
                and self.config.data["save_password"]
                and not used_saved_credentials
            ):
                # Attempt to connect with raw password when using saved credentials
                used_saved_credentials = True
            else:
                display_login_success_dialog = True
                login_form = LoginForm(
                    self.config,
                    on_quit_callback=(
                        None
                        if (PLATFORM.startswith(LINUX) and not XMODE)
                        else lambda: sys.exit(0)
                    ),
                )
                login_form.mainloop()  # wait until login form is closed

            login_successful, msg_login, self.config.data["cookie"] = (
                self.request_manager.login()
            )
            if login_successful:
                self.config.data["maxsize"] = self.request_manager.maxsize()
                stomp_conn_successful, msg_stomp = self.stomp_manager.connect()
                if stomp_conn_successful:
                    self.stomp_manager.is_login_phase = False
                    if self.config.data["cipher_enabled"]:
                        self.config.data["hashed_password"] = (
                            self.cipher_manager.hash_password()
                        )
                    if not self.config.data["save_password"]:
                        self.config.data["password"] = ""
                    if display_login_success_dialog:
                        CustomDialog(
                            "Success! ClipCascade will now run in the task bar/menu bar.",
                            msg_type="success",
                            timeout=5000,
                        ).mainloop()
                    break
                else:
                    CustomDialog(
                        "Login successful but websocket connection failed. \nPlease check websocket-url\n"
                        + msg_stomp,
                        msg_type="error",
                    ).mainloop()
            else:
                CustomDialog("Login Failed\n" + msg_login, msg_type="error").mainloop()

            if PLATFORM.startswith(LINUX) and not XMODE:
                Echo("-" * 53)

    def get_version_update_status(self) -> list:
        """
        Checks for a new version of the application by comparing the current version
        with the one available in a remote JSON file.

        Returns:
        list: [bool, str, str, str] - [Is new version available, latest version, current version, release URL]
        """
        try:
            response = RequestManager.get(VERSION_URL)
            response_data = response.json()
            if PLATFORM == WINDOWS:
                key = "windows"
            elif PLATFORM == MACOS:
                key = "macos"
            elif PLATFORM.startswith(LINUX):
                if XMODE:
                    key = "linux_gui"
                else:
                    key = "linux_non_gui"

            if response_data[key] != APP_VERSION:
                return [True, response_data[key], APP_VERSION, RELEASE_URL]
        except Exception as e:
            logging.error(f"Error checking for new version: {e}")
        return [False, "", APP_VERSION, RELEASE_URL]

    def logoff_and_exit(self):
        try:
            self.stomp_manager.disconnect()
            self.request_manager.logout()
            self.config.data["hashed_password"] = None
            self.config.data["cookie"] = None
            self.config.data["maxsize"] = None
            self.config.data["password"] = ""
            self.config.save()
        except Exception as e:
            raise Exception(f"Error during logging off: {e}")

    def banner(self):
        if PLATFORM.startswith(LINUX) and not XMODE:
            Echo(pyfiglet.figlet_format(APP_NAME))
            Echo("*" * 53)
            Echo("Real-Time Clipboard Syncing".center(53))
            Echo(GITHUB_URL.center(53))
            Echo("*" * 53)

    def run(self):
        try:
            self.banner()
            self.setup_logging()
            self.ensure_single_instance()
            self.config.load()
            self.authenticate_and_connect()
            self.config.save()
            update_available = self.get_version_update_status()

            sys_tray = TaskbarPanel(
                on_connect_callback=self.stomp_manager.manual_reconnect,
                on_disconnect_callback=self.stomp_manager.disconnect,
                on_logoff_callback=self.logoff_and_exit,
                new_version_available=update_available,
                github_url=GITHUB_URL,
                stomp_manager=self.stomp_manager,
            )
            self.stomp_manager.set_tray_ref(sys_tray)
            sys_tray.run()
        except Exception as e:
            msg = f"An unexpected error has occurred: {e}"
            logging.error(msg)
            CustomDialog(
                msg + "\nCheck logs in project directory", msg_type="error"
            ).mainloop()
        finally:
            self.stomp_manager.disconnect()
            if PLATFORM == MACOS or PLATFORM.startswith(LINUX):
                if self.lock_file is not None:
                    fcntl.flock(self.lock_file, fcntl.LOCK_UN)
                    self.lock_file.close()
                    os.remove(self.mutex_identifier)
