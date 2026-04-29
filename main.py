from encryptr import EncryptrFile, PY_FILE_DIR, TEMP_DIR_PATH
import dearpygui.dearpygui as dpg
import subprocess
import platform
import atexit
import shutil
import os

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

FOLDER_ICON = "\uf07b"
DEFAULT_FILE_ICON = "\uf15b"
FILE_ICONS = {
    ("txt", "md", "rtf", "log"): "\uf0f6",
    (
        "png",
        "jpg",
        "jpeg",
        "webp",
        "svg",
        "gif",
        "raw",
        "tiff",
        "tif",
        "heic",
        "heif",
        "bmp",
    ): "\uf03e",
    ("py", "pyc"): "\ue606",
    ("cpp", "c++", "cxx", "cc", "hpp", "h++", "hxx", "hh"): "\ue61d",
    ("c", "h"): "\ue61e",
    ("js", "jsx"): "\ue781",
    ("ts", "tsx"): "\ue8ca",
    ("html", "htm"): "\ue736",
    ("css"): "\ue749",
    ("json"): "\ue60b",
    ("java", "class", "jar"): "\ue738",
    ("mp3", "wav", "flac", "m4a", "aac", "ogg"): "\ue638",
    ("mp4", "mkv", "mov", "avi", "webm"): "\uf03d",
    ("pdf"): "\uf1c1",
    ("zip", "tar", "7z", "rar", "gz"): "\uf1c6",
    ("exe", "sh", "bat"): "\ue795",
    ("app"): "\ue711",
    ("enc"): "\udb80\ude21",
}


def get_file_icon(extension: str):
    for exts, icon in FILE_ICONS.items():
        if extension in exts:
            return icon

    return DEFAULT_FILE_ICON


dpg.create_context()
dpg.create_viewport(title="Encryptr", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)


with dpg.theme() as error_theme:
    with dpg.theme_component(dpg.mvText):
        dpg.add_theme_color(
            dpg.mvThemeCol_Text, (255, 51, 51), category=dpg.mvThemeCat_Core
        )

with dpg.theme() as header_row_theme:
    with dpg.theme_component(dpg.mvTableRow):
        dpg.add_theme_color(
            dpg.mvThemeCol_TableRowBg, (51, 51, 55), category=dpg.mvThemeCat_Core
        )

with dpg.theme() as table_theme:
    with dpg.theme_component(dpg.mvTable):
        dpg.add_theme_color(
            dpg.mvThemeCol_TableRowBgAlt, (0, 0, 0, 0), category=dpg.mvThemeCat_Core
        )


with dpg.font_registry():
    font_dir_path = os.path.join(PY_FILE_DIR, "font")
    default_font = dpg.add_font(
        os.path.join(font_dir_path, "SFMono Regular Nerd Font Complete.otf"), 14
    )
    # bold_font = dpg.add_font(
    #     os.path.join(font_dir_path, "SFMono Bold Nerd Font Complete.otf"), 14
    # )


def input_window(
    label: str = None, tag: str = 0, show: bool = False, modal: bool = False, **kwargs
):
    return dpg.window(
        label=label,
        tag=tag,
        width=WINDOW_WIDTH / 2,
        height=WINDOW_HEIGHT / 2,
        pos=(WINDOW_WIDTH / 4, WINDOW_HEIGHT / 4),
        show=show,
        modal=modal,
        **kwargs,
    )


enc_file = None
curr_path = []


def save_settings_callback():
    dpg.set_global_font_scale(dpg.get_value("font_scale_input"))
    enc_file.copy_files_on_add = dpg.get_value("copy_files_chechbox")
    # dpg.hide_item("settings_window")


with input_window("Settings", "settings_window"):
    dpg.add_input_float(
        label="Font Scale",
        tag="font_scale_input",
        default_value=dpg.get_global_font_scale(),
        min_value=0.1,
        max_value=3.0,
        format="%.1f",
        width=WINDOW_WIDTH / 5,
    )
    dpg.add_checkbox(
        label="Copy Files on Add", default_value=False, tag="copy_files_chechbox"
    )
    with dpg.tooltip("copy_files_chechbox"):
        dpg.add_text(
            "If enabled, copies newly added files into a temporary folder\nto make sure the file isn't edited or deleted.",
        )

    dpg.add_button(label="Save", callback=save_settings_callback)


def save_file_callback():
    dpg.set_item_label("save_file_btn", "Saving...")
    enc_file.save()
    dpg.set_item_label("save_file_btn", "Save File")


def create_folder_callback():
    name = dpg.get_value("folder_name_input")

    try:
        enc_file.new_dir(curr_path, name)
        dpg.hide_item("new_folder_window")
        update_file_tree_table()
    except Exception as e:
        dpg.set_value("new_folder_error", str(e))


with input_window("New folder...", "new_folder_window"):
    dpg.add_input_text(
        label="Folder Name", tag="folder_name_input", width=WINDOW_WIDTH / 5
    )
    dpg.add_button(label="Create Folder", callback=create_folder_callback)
    dpg.add_text(tag="new_folder_error")
    dpg.bind_item_theme("new_folder_error", error_theme)


def add_file_dialog_callback(sender, app_data):
    for name, path in app_data["selections"].items():
        enc_file.add_file(curr_path, name, path)

    update_file_tree_table()


with dpg.file_dialog(
    label="Select file to add...",
    callback=add_file_dialog_callback,
    tag="add_file_dialog",
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
):
    dpg.add_file_extension(".*")


def change_pw_callback():
    new_pw = dpg.get_value("new_pw_input")

    try:
        enc_file.set_password(new_pw)
        dpg.hide_item("change_pw_window")
    except Exception as e:
        dpg.set_value("change_pw_error", str(e))


with input_window("Change password...", "change_pw_window"):
    dpg.add_input_text(
        label="New Password", password=True, tag="new_pw_input", width=WINDOW_WIDTH / 5
    )
    dpg.add_button(label="Change Password", callback=change_pw_callback)
    dpg.add_text(tag="change_pw_error")
    dpg.bind_item_theme("change_pw_error", error_theme)


def save_as_dir_dialog(sender, app_data):
    dpg.set_value("save_as_dir_input", app_data["file_path_name"])


dpg.add_file_dialog(
    directory_selector=True,
    callback=save_as_dir_dialog,
    tag="save_as_dir_dialog",
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
)


def save_as_callback():
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


with input_window("Save as...", "save_as_window", modal=False):
    with dpg.group(horizontal=True):
        dpg.add_input_text(width=WINDOW_WIDTH / 5, tag="save_as_dir_input")
        dpg.add_button(
            label="Open Directory", callback=lambda: dpg.show_item("save_as_dir_dialog")
        )

    dpg.add_input_text(
        width=WINDOW_WIDTH / 5, tag="save_as_name_input", label="File Name"
    )
    dpg.add_button(
        label="Save File", tag="save_as_file_button", callback=save_as_callback
    )
    dpg.add_text(tag="save_as_error")
    dpg.bind_item_theme("save_as_error", error_theme)


def open_file(dirname: list[str], name: str):
    def open_file_callback():
        temp_file_path = os.path.join(TEMP_DIR_PATH, str(len(dirname)) + name)

        dpg.set_item_label("open_file_btn", "Opening...")

        if not os.path.isfile(temp_file_path):
            with open(temp_file_path, "wb") as f:
                f.write(enc_file.get_file_data(dirname, name))

        if platform.system() == "Windows":
            os.startfile(temp_file_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", temp_file_path])
        else:
            subprocess.run(["xdg-open", temp_file_path])

        dpg.set_item_label("open_file_btn", "Open")

        dpg.delete_item(file_window)

    def rename_file_callback():
        def rename_callback():
            directory = enc_file.get_from_path(dirname)
            directory[dpg.get_value(new_name_input)] = directory.pop(name)

            update_file_tree_table()
            dpg.delete_item(rename_file_window)
            dpg.delete_item(file_window)

        with input_window(
            f"Rename {name}...",
            show=True,
            on_close=lambda: dpg.delete_item(rename_file_window),
        ) as rename_file_window:
            new_name_input = dpg.add_input_text(
                label="New Name", width=WINDOW_WIDTH / 5
            )
            dpg.add_button(label="Rename", callback=rename_callback)

    def delete_file_callback():
        enc_file.delete_file(dirname, name)
        update_file_tree_table()
        dpg.delete_item(file_window)

    with input_window(
        f"Open {name}...", show=True, on_close=lambda: dpg.delete_item(file_window)
    ) as file_window:
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Open", callback=open_file_callback, tag="open_file_btn"
            )
            dpg.add_button(label="Rename", callback=rename_file_callback)
            dpg.add_button(label="Delete", callback=delete_file_callback)


def open_dir(dirname: list[str], name: str):
    global curr_path

    curr_path = dirname + [name]
    update_file_tree_table()


def add_file_to_cell(name: str, value, dirname: list[str], parent: str = 0):
    if type(value) == dict:
        icon = FOLDER_ICON
        callback = lambda: open_dir(dirname, name)
    else:
        icon = get_file_icon(os.path.splitext(name)[1][1:].lower())
        callback = lambda: open_file(dirname, name)

    label = f"{icon} {name}"
    dpg.add_button(label=f"{icon} {name}", parent=parent, callback=callback)
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


def delete_folder_callback():
    global curr_path

    enc_file.delete_dir(curr_path)
    curr_path = curr_path[:-1]

    update_file_tree_table()
    dpg.hide_item("delete_dir_window")


with input_window("Delete directory...", "delete_dir_window"):
    dpg.add_text(tag="delete_dir_warning")

    with dpg.group(horizontal=True):
        dpg.add_button(label="Yes", callback=delete_folder_callback)
        dpg.add_button(label="No", callback=lambda: dpg.hide_item("delete_dir_window"))


def delete_folder_btn_callback():
    dpg.set_value(
        "delete_dir_warning",
        f'Are you sure you want to delete "{curr_path[-1] if len(curr_path) > 0 else "/"}"?',
    )
    dpg.show_item("delete_dir_window")


def rename_folder_callback():
    global curr_path

    new_name = dpg.get_value("rename_folder_input")

    directory = enc_file.get_from_path(curr_path[:-1])
    directory[new_name] = directory.pop(curr_path[-1])
    curr_path[-1] = new_name

    update_file_tree_table()
    dpg.hide_item("rename_folder_window")


with input_window(tag="rename_folder_window"):
    dpg.add_input_text(
        label="New Name", width=WINDOW_WIDTH / 5, tag="rename_folder_input"
    )
    dpg.add_button(label="Rename", callback=rename_folder_callback)


def rename_folder_btn_callback():
    if len(curr_path) == 0:
        return

    dpg.set_item_label("rename_folder_window", f"Rename {curr_path[-1]}...")
    dpg.show_item("rename_folder_window")


with dpg.window(tag="main_window", show=False):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_button(
                label="Save File", callback=save_file_callback, tag="save_file_btn"
            )
            dpg.add_button(
                label="Save As", callback=lambda: dpg.show_item("save_as_window")
            )
            dpg.add_button(
                label="Change Password",
                callback=lambda: dpg.show_item("change_pw_window"),
            )

        with dpg.menu(label="Edit"):
            dpg.add_button(
                label="Add File", callback=lambda: dpg.show_item("add_file_dialog")
            )
            dpg.add_button(
                label="New Folder",
                callback=lambda: dpg.show_item("new_folder_window"),
            )
            dpg.add_button(
                label="Rename Folder",
                callback=rename_folder_btn_callback,
            )
            dpg.add_button(label="Delete Folder", callback=delete_folder_btn_callback)

        dpg.add_button(
            label="Settings", callback=lambda: dpg.show_item("settings_window")
        )

    dpg.add_table(
        resizable=True,
        header_row=False,
        borders_outerV=True,
        borders_outerH=True,
        borders_innerV=True,
        row_background=True,
        height=-1,
        tag="file_tree_table",
    )
    dpg.bind_item_theme("file_tree_table", table_theme)


def load_file_dialog_callback(sender, app_data):
    dpg.set_value("file_path_input", app_data["file_path_name"])


with dpg.file_dialog(
    label="Select file to load...",
    callback=load_file_dialog_callback,
    tag="load_file_dialog",
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
):
    dpg.add_file_extension(".enc")


def load_file_callback():
    global enc_file

    try:
        enc_file = EncryptrFile(
            dpg.get_value("file_path_input"), dpg.get_value("password_input")
        )

        dpg.set_viewport_title(f"Encryptr - {enc_file.file_path}")
        dpg.hide_item("file_window")

        update_file_tree_table()
        dpg.show_item("main_window")
    except ValueError:
        dpg.set_value("load_file_error", "Incorrect password.")
    except Exception as e:
        print(e)
        dpg.set_value("load_file_error", str(e))


with input_window("Load file...", "file_window", show=True, modal=False, no_close=True):
    with dpg.group(horizontal=True):
        dpg.add_input_text(width=WINDOW_WIDTH / 5, tag="file_path_input")
        dpg.add_button(
            label="Find File", callback=lambda: dpg.show_item("load_file_dialog")
        )

    dpg.add_input_text(
        label="Password", password=True, width=WINDOW_WIDTH / 5, tag="password_input"
    )
    dpg.add_button(label="Load File", callback=load_file_callback)
    dpg.add_text(tag="load_file_error")
    dpg.bind_item_theme("load_file_error", error_theme)


dpg.bind_font(default_font)
dpg.set_primary_window("main_window", True)


def cleanup_temp():
    shutil.rmtree(TEMP_DIR_PATH)
    os.mkdir(TEMP_DIR_PATH)


atexit.register(cleanup_temp)


if __name__ == "__main__":
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
