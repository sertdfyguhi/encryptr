from encryptr import EncryptrFile, TEMP_DIR_PATH
import dearpygui.dearpygui as dpg
from settings import AppSettings
import utils
import time
import os
import gc


PY_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE_PATH = os.path.join(PY_FILE_DIR, "settings.json")

MAX_TRIES_BEFORE_RATE_LIMIT = 3
RATE_LIMIT_TIME = 30


with dpg.theme() as header_row_theme:
    with dpg.theme_component(dpg.mvTableRow):
        dpg.add_theme_color(
            dpg.mvThemeCol_TableRowBg, (51, 51, 55), category=dpg.mvThemeCat_Core
        )


settings = AppSettings.from_file(SETTINGS_FILE_PATH)
dpg.set_global_font_scale(settings.font_scale)

enc_file = None
curr_path = []

last_mouse_move = None


def mouse_move():
    global last_mouse_move

    if settings.auto_lock_inactivity:
        last_mouse_move = time.time()


with dpg.handler_registry():
    dpg.add_mouse_move_handler(callback=mouse_move)


def main_loop():
    global enc_file, curr_path

    if enc_file and dpg.get_frame_count() % 30 == 0:
        if (settings.auto_lock_unfocus and not utils.is_app_focused()) or (
            settings.auto_lock_inactivity
            and (time.time() - last_mouse_move) > settings.auto_lock_inactivity_time
        ):
            enc_file = None
            gc.collect()

            curr_path = []
            dpg.hide_item("main_window")
            dpg.delete_item("file_tree_table", children_only=True)
            dpg.show_item("load_file_window")


def select_file(path: list[str], name: str):
    global open_file_path, open_file_name

    open_file_path = path
    open_file_name = name

    dpg.set_item_label("file_window", f"Open {name}...")
    dpg.show_item("file_window")


def select_dir(dirname: list[str], name: str):
    global curr_path

    curr_path = dirname + [name]
    update_file_tree_table()


def add_file_to_cell(name: str, value, dirname: list[str], parent: str = 0):
    if type(value) == dict:
        icon = utils.FOLDER_ICON
        callback = lambda: select_dir(dirname, name)
    else:
        icon = utils.get_file_icon(os.path.splitext(name)[1][1:].lower())
        callback = lambda: select_file(dirname, name)

    label = f"{icon} {name}"
    dpg.add_button(label=label, parent=parent, callback=callback)
    dpg.add_drag_payload(parent=dpg.last_item(), label=label)


def go_to(path: list[str]):
    global curr_path

    if path == curr_path:
        return

    curr_path = path
    update_file_tree_table()


def update_file_tree_table():
    dpg.delete_item("file_tree_table", children_only=True)

    dpg.add_table_column(parent="file_tree_table")

    for dir_name in curr_path:
        dpg.add_table_column(label=dir_name, parent="file_tree_table")

    # header row
    with dpg.table_row(parent="file_tree_table"):
        dpg.bind_item_theme(dpg.last_item(), header_row_theme)

        dpg.add_button(label="/", callback=lambda: go_to([]))

        for i, dir_name in enumerate(curr_path):
            dpg.add_button(
                label=dir_name,
                user_data=curr_path[: i + 1],
                callback=lambda s, a, d: go_to(d),
            )

    curr_dir = enc_file.root

    for i, name in enumerate(curr_dir):
        with dpg.table_row(tag=f"row{i}", parent="file_tree_table"):
            add_file_to_cell(name, curr_dir[name], [])

    for depth, dir_name in enumerate(curr_path):
        curr_dir = curr_dir[dir_name]

        for i, name in enumerate(curr_dir):
            row_tag = f"row{i}"
            if not dpg.does_item_exist(row_tag):
                dpg.add_table_row(tag=row_tag)

                for _ in range(depth + 1):
                    dpg.add_text(parent=row_tag)

            add_file_to_cell(name, curr_dir[name], curr_path[: depth + 1], row_tag)


# callbacks


def save_settings():
    settings.font_scale = dpg.get_value("font_scale_input")
    settings.copy_files_on_add = dpg.get_value("copy_files_chechbox")
    settings.auto_lock_inactivity = dpg.get_value("auto_lock_inactivity_checkbox")
    if settings.auto_lock_inactivity:
        settings.auto_lock_inactivity_time = dpg.get_value("auto_lock_inactivity_input")
    settings.auto_lock_unfocus = dpg.get_value("auto_lock_unfocus_checkbox")

    dpg.set_global_font_scale(settings.font_scale)
    enc_file.copy_files_on_add = settings.copy_files_on_add
    enc_file.change_algo_type(dpg.get_value("enc_method_combo"))

    settings.save(SETTINGS_FILE_PATH)
    # dpg.hide_item("settings_window")


def save_file():
    dpg.set_item_label("save_file_btn", "Saving...")
    dpg.set_viewport_title("Encryptr - Saving...")
    enc_file.save()
    dpg.set_item_label("save_file_btn", "Save File")
    dpg.set_viewport_title(f"Encryptr - {enc_file.file_path}")


def create_folder():
    name = dpg.get_value("folder_name_input")

    try:
        enc_file.new_dir(curr_path, name)
        dpg.hide_item("new_folder_window")
        update_file_tree_table()
    except Exception as e:
        dpg.set_value("new_folder_error", str(e))


def add_file_dialog(sender, app_data):
    for name, path in app_data["selections"].items():
        enc_file.add_file(curr_path, name, path)

    update_file_tree_table()


def change_pw():
    new_pw = dpg.get_value("new_pw_input")

    try:
        enc_file.set_password(new_pw)
        dpg.hide_item("change_pw_window")
    except Exception as e:
        dpg.set_value("change_pw_error", str(e))


def save_as():
    name = dpg.get_value("save_as_name_input")
    if name == "":
        dpg.set_value("save_as_error", "Name cannot be empty.")
        return

    file_path = os.path.join(dpg.get_value("save_as_dir_input"), name + ".enc")

    if os.path.isdir(file_path):
        dpg.set_value("save_as_error", "File path is a directory.")
        return

    dpg.set_item_label("save_as_file_button", "Saving...")
    enc_file.save(file_path)
    dpg.set_item_label("save_as_file_button", "Save File")

    dpg.set_viewport_title(f"Encryptr - {enc_file.file_path}")

    dpg.hide_item("save_as_window")


open_file_path = None
open_file_name = None


def open_file():
    dpg.set_item_label("open_file_btn", "Opening...")

    directory = enc_file.get_from_path(open_file_path)

    if open_file_name.endswith(("txt", "md", "rtf", "log")):
        pass
    if type(directory[open_file_name]) == int:
        temp_file_path = os.path.join(
            TEMP_DIR_PATH, str(len(open_file_path)) + open_file_name
        )

        if not os.path.isfile(temp_file_path):
            with open(temp_file_path, "wb") as f:
                f.write(enc_file.get_file_data(open_file_path, open_file_name))

        utils.open_file(temp_file_path)
    elif type(directory[open_file_name]) == str:
        utils.open_file(directory[open_file_name])

    dpg.set_item_label("open_file_btn", "Open")
    dpg.hide_item("file_window")


def rename_file():
    directory = enc_file.get_from_path(open_file_path)
    directory[dpg.get_value("rename_file_input")] = directory.pop(open_file_name)

    update_file_tree_table()
    dpg.hide_item("rename_file_window")
    dpg.set_value("rename_file_input", "")
    dpg.hide_item("rename_file_window")
    dpg.hide_item("file_window")


def delete_file():
    enc_file.delete_file(open_file_path, open_file_name)
    update_file_tree_table()
    dpg.hide_item("delete_file_window")
    dpg.hide_item("file_window")


def extract_file(sender, app_data):
    extract_file_path = os.path.join(app_data["file_path_name"], open_file_name)

    with open(extract_file_path, "wb") as f:
        f.write(enc_file.get_file_data(open_file_path, open_file_name))

    dpg.hide_item("file_window")


def delete_folder():
    global curr_path

    enc_file.delete_dir(curr_path)
    curr_path = curr_path[:-1]

    update_file_tree_table()
    dpg.hide_item("delete_dir_window")


def delete_folder_btn():
    dpg.set_value(
        "delete_dir_warning",
        f'Are you sure you want to delete "{curr_path[-1] if len(curr_path) > 0 else "/"}"?',
    )
    dpg.show_item("delete_dir_window")


def rename_folder():
    global curr_path

    new_name = dpg.get_value("rename_folder_input")

    directory = enc_file.get_from_path(curr_path[:-1])
    directory[new_name] = directory.pop(curr_path[-1])
    curr_path[-1] = new_name

    update_file_tree_table()
    dpg.hide_item("rename_folder_window")


def rename_folder_btn():
    if len(curr_path) == 0:
        return

    dpg.set_item_label("rename_folder_window", f"Rename {curr_path[-1]}...")
    dpg.show_item("rename_folder_window")


def load_file_dialog(sender, app_data):
    dpg.set_value("file_path_input", app_data["file_path_name"])


incorrect_tries = 0
rate_limit_start = None


def load_file():
    global enc_file, incorrect_tries, rate_limit_start

    if (
        incorrect_tries >= MAX_TRIES_BEFORE_RATE_LIMIT
        and (time.time() - rate_limit_start) < RATE_LIMIT_TIME
    ):
        return

    try:
        enc_file = EncryptrFile(
            dpg.get_value("file_path_input"),
            dpg.get_value("password_input"),
            settings.copy_files_on_add,
        )
        print(f"opened {enc_file.file_path}, algo type: {enc_file.algo_type}")

        update_file_tree_table()
        dpg.hide_item("load_file_window")
        dpg.show_item("main_window")

        incorrect_tries = 0
        dpg.set_value("password_input", "")
        dpg.set_value("load_file_error", "")
        dpg.set_value("enc_method_combo", enc_file.algo_type)
        dpg.set_viewport_title(f"Encryptr - {enc_file.file_path}")
    except ValueError:
        incorrect_tries += 1

        if incorrect_tries > MAX_TRIES_BEFORE_RATE_LIMIT:
            rate_limit_start = time.time()
            dpg.set_value(
                "load_file_error",
                f"Max incorrect tries reached ({MAX_TRIES_BEFORE_RATE_LIMIT}), please wait {RATE_LIMIT_TIME}s.",
            )
        else:
            dpg.set_value("load_file_error", "Incorrect password.")
    except Exception as e:
        print(e)
        dpg.set_value("load_file_error", str(e))
