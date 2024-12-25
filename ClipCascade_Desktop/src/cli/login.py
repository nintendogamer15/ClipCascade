import getpass
import re

from core.config import Config
from cli.info import CustomDialog
from core.constants import *


class LoginForm:
    def __init__(
        self,
        config: Config,
        on_login_callback=None,
        on_quit_callback=None,
    ):
        super().__init__()
        self.config = config
        self.on_login_callback = on_login_callback
        self.on_quit_callback = on_quit_callback

    @staticmethod
    def remove_trailing_slash(entry):
        return re.sub(r"/+$", "", entry)

    @staticmethod
    def is_positive_integer(value):
        if value.isdigit() and int(value) > 0:
            return True
        else:
            return False

    @staticmethod
    def bool_to_str(value):
        return "y" if value else "n"

    @staticmethod
    def str_to_bool(value):
        return value.lower().strip() == "y"

    @staticmethod
    def is_positive_integer(value):
        if value.isdigit() and int(value) > 0:
            return True
        else:
            return False

    def mainloop(self):
        # save data to config
        self.config.data["username"] = (
            input(f"username [{self.config.data['username']}]: ")
            or self.config.data["username"]
        )

        self.config.data["password"] = getpass.getpass("password: ")

        server_url = (
            input(f"server url [{self.config.data['server_url']}]: ")
            or self.config.data["server_url"]
        )
        self.config.data["server_url"] = LoginForm.remove_trailing_slash(
            server_url.strip()
        )

        websocket_url = (
            input(f"websocket url [{self.config.data['websocket_url']}]: ")
            or self.config.data["websocket_url"]
        )
        self.config.data["websocket_url"] = LoginForm.remove_trailing_slash(
            websocket_url.strip()
        )

        self.config.data["cipher_enabled"] = LoginForm.str_to_bool(
            input(
                f"enabled encryption(recommended) [{LoginForm.bool_to_str(self.config.data['cipher_enabled'])}]: "
            )
            or LoginForm.bool_to_str(self.config.data["cipher_enabled"])
        )

        self.config.data["notification"] = LoginForm.str_to_bool(
            input(
                f"enabled notification [{LoginForm.bool_to_str(self.config.data['notification'])}]: "
            )
            or LoginForm.bool_to_str(self.config.data["notification"])
        )

        # extra fields
        show_extra_fields = input(f"show extra fields [n]: ") or "n"
        if not LoginForm.str_to_bool(show_extra_fields):
            CustomDialog("Logging in...").mainloop()
            return

        subscription_destination = (
            input(
                f"subscription destination [{self.config.data['subscription_destination']}]: "
            )
            or self.config.data["subscription_destination"]
        )
        self.config.data["subscription_destination"] = LoginForm.remove_trailing_slash(
            subscription_destination.strip()
        )

        send_destination = (
            input(f"send destination [{self.config.data['send_destination']}]: ")
            or self.config.data["send_destination"]
        )
        self.config.data["send_destination"] = LoginForm.remove_trailing_slash(
            send_destination.strip()
        )

        login_url = (
            input(f"login url [{self.config.data['login_url']}]: ")
            or self.config.data["login_url"]
        )
        self.config.data["login_url"] = LoginForm.remove_trailing_slash(
            login_url.strip()
        )

        logout_url = (
            input(f"logout url [{self.config.data['logout_url']}]: ")
            or self.config.data["logout_url"]
        )
        self.config.data["logout_url"] = LoginForm.remove_trailing_slash(
            logout_url.strip()
        )

        maxsize_url = (
            input(f"maxsize url [{self.config.data['maxsize_url']}]: ")
            or self.config.data["maxsize_url"]
        )
        self.config.data["maxsize_url"] = LoginForm.remove_trailing_slash(
            maxsize_url.strip()
        )

        # Validate hash_rounds
        while True:
            hash_rounds = input(
                f"hash rounds [{self.config.data['hash_rounds']}]: "
            ) or str(
                ""
                if self.config.data["hash_rounds"] is None
                else str(self.config.data["hash_rounds"])
            )
            hash_rounds = hash_rounds.strip()

            if not LoginForm.is_positive_integer(hash_rounds):
                CustomDialog(
                    "Invalid Input\nHash Rounds must be a positive integer.",
                    msg_type="error",
                )
                continue

            self.config.data["hash_rounds"] = int(hash_rounds)
            break

        self.config.data["salt"] = (
            input(f"salt [{self.config.data['salt']}]: ") or self.config.data["salt"]
        )

        self.config.data["save_password"] = LoginForm.str_to_bool(
            input(
                f"store password locally(not recommended) [{LoginForm.bool_to_str(self.config.data['save_password'])}]: "
            )
            or LoginForm.bool_to_str(self.config.data["save_password"])
        )

        # Validate max_clipboard_size_local_limit_bytes
        while True:
            saved_mcsll = str(
                ""
                if self.config.data["max_clipboard_size_local_limit_bytes"] is None
                else str(self.config.data["max_clipboard_size_local_limit_bytes"])
            )

            max_clipboard_size_local_limit_bytes = (
                input(
                    f"maximum clipboard size local limit (in bytes) [{saved_mcsll}]: "
                )
                or saved_mcsll
            )
            max_clipboard_size_local_limit_bytes = (
                max_clipboard_size_local_limit_bytes.strip()
            )
            if max_clipboard_size_local_limit_bytes == "":
                self.config.data["max_clipboard_size_local_limit_bytes"] = None
                break

            if not LoginForm.is_positive_integer(max_clipboard_size_local_limit_bytes):
                CustomDialog(
                    "Invalid Input\nMax Clipboard Size Local Limit must be a positive integer.",
                    msg_type="error",
                )
                continue

            self.config.data["max_clipboard_size_local_limit_bytes"] = int(
                max_clipboard_size_local_limit_bytes
            )
            break

        self.config.data["enable_image_sharing"] = LoginForm.str_to_bool(
            input(
                f"enable image sharing [{LoginForm.bool_to_str(self.config.data['enable_image_sharing'])}]: "
            )
            or LoginForm.bool_to_str(self.config.data["enable_image_sharing"])
        )

        self.config.data["enable_file_sharing"] = LoginForm.str_to_bool(
            input(
                f"enable file sharing [{LoginForm.bool_to_str(self.config.data['enable_file_sharing'])}]: "
            )
            or LoginForm.bool_to_str(self.config.data["enable_file_sharing"])
        )

        CustomDialog("Logging in...").mainloop()

    def on_quit(self):
        pass

    def close(self):
        pass
