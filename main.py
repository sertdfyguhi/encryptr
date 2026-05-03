import dearpygui.dearpygui as dpg

dpg.create_context()

from encryptr import ALGOS
import callbacks
import utils
import os
import gc

PY_FILE_DIR = os.path.dirname(os.path.abspath(__file__))

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


dpg.create_viewport(title="Encryptr", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)


with dpg.theme() as error_theme:
    with dpg.theme_component(dpg.mvText):
        dpg.add_theme_color(
            dpg.mvThemeCol_Text, (255, 51, 51), category=dpg.mvThemeCat_Core
        )

with dpg.theme() as table_theme:
    with dpg.theme_component(dpg.mvTable):
        dpg.add_theme_color(
            dpg.mvThemeCol_TableRowBgAlt, (0, 0, 0, 0), category=dpg.mvThemeCat_Core
        )


with dpg.font_registry():
    default_font = dpg.add_font(
        os.path.join(PY_FILE_DIR, "font", "SFMono Regular Nerd Font Complete.otf"), 14
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


with input_window("Settings", "settings_window"):
    dpg.add_text("Global Settings")

    with dpg.group(indent=20):
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

        dpg.add_checkbox(
            label="Lock on Inactivity",
            default_value=callbacks.auto_lock,
            tag="auto_lock_checkbox",
        )
        with dpg.tooltip("auto_lock_checkbox"):
            dpg.add_text(
                "If enabled, auto unloads the file when window is unfocused.",
            )

    dpg.add_spacer(height=9)

    dpg.add_text("File Settings")

    with dpg.group(indent=20):
        dpg.add_combo(
            items=tuple(ALGOS.values()),
            default_value="AES256-GCM",
            label="Encryption Method",
            tag="enc_method_combo",
            width=WINDOW_WIDTH / 5,
        )

    dpg.add_spacer(height=9)

    dpg.add_button(label="Save", callback=callbacks.save_settings)


with input_window("New folder...", "new_folder_window"):
    dpg.add_input_text(
        label="Folder Name", tag="folder_name_input", width=WINDOW_WIDTH / 5
    )
    dpg.add_button(label="Create Folder", callback=callbacks.create_folder)
    dpg.add_text(tag="new_folder_error")
    dpg.bind_item_theme("new_folder_error", error_theme)


with dpg.file_dialog(
    label="Select file to add...",
    callback=callbacks.add_file_dialog,
    tag="add_file_dialog",
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
):
    dpg.add_file_extension(".*")


with input_window("Change password...", "change_pw_window"):
    dpg.add_input_text(
        label="New Password", password=True, tag="new_pw_input", width=WINDOW_WIDTH / 5
    )
    dpg.add_button(label="Change Password", callback=callbacks.change_pw)
    dpg.add_text(tag="change_pw_error")
    dpg.bind_item_theme("change_pw_error", error_theme)


dpg.add_file_dialog(
    directory_selector=True,
    callback=lambda s, a: dpg.set_value("save_as_dir_input", a["file_path_name"]),
    tag="save_as_dir_dialog",
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
)


with input_window("Save as...", "save_as_window"):
    with dpg.group(horizontal=True):
        dpg.add_input_text(width=WINDOW_WIDTH / 5, tag="save_as_dir_input")
        dpg.add_button(
            label="Open Directory", callback=lambda: dpg.show_item("save_as_dir_dialog")
        )

    dpg.add_input_text(
        label="File Name", width=WINDOW_WIDTH / 5, tag="save_as_name_input"
    )
    dpg.add_button(
        label="Save File", tag="save_as_file_button", callback=callbacks.save_as
    )
    dpg.add_text(tag="save_as_error")
    dpg.bind_item_theme("save_as_error", error_theme)


with input_window(f"Rename file...", tag="rename_file_window"):
    dpg.add_input_text(
        label="New Name", width=WINDOW_WIDTH / 5, tag="rename_file_input"
    )
    dpg.add_button(label="Rename", callback=callbacks.rename_file)


with input_window(f"Delete file...", tag="delete_file_window"):
    dpg.add_text("Are you sure you want to delete this file?")

    with dpg.group(horizontal=True):
        dpg.add_button(label="Yes", callback=callbacks.delete_file)
        dpg.add_button(label="No", callback=lambda: dpg.hide_item("delete_file_window"))


dpg.add_file_dialog(
    label="Extract file to...",
    directory_selector=True,
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
    tag="extract_file_dialog",
    callback=callbacks.extract_file,
)


with input_window(f"Open file...", tag="file_window"):
    with dpg.group(horizontal=True):
        dpg.add_button(label="Open", callback=callbacks.open_file, tag="open_file_btn")
        dpg.add_button(
            label="Rename", callback=lambda: dpg.show_item("rename_file_window")
        )
        dpg.add_button(
            label="Delete", callback=lambda: dpg.show_item("delete_file_window")
        )
        dpg.add_button(
            label="Extract", callback=lambda: dpg.show_item("extract_file_dialog")
        )


with input_window("Delete directory...", "delete_dir_window"):
    dpg.add_text(tag="delete_dir_warning")

    with dpg.group(horizontal=True):
        dpg.add_button(label="Yes", callback=callbacks.delete_folder)
        dpg.add_button(label="No", callback=lambda: dpg.hide_item("delete_dir_window"))


with input_window(tag="rename_folder_window"):
    dpg.add_input_text(
        label="New Name", width=WINDOW_WIDTH / 5, tag="rename_folder_input"
    )
    dpg.add_button(label="Rename", callback=callbacks.rename_folder)


with dpg.window(tag="main_window", show=False):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_button(
                label="Save File", callback=callbacks.save_file, tag="save_file_btn"
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
                label="New Folder", callback=lambda: dpg.show_item("new_folder_window")
            )
            dpg.add_button(label="Rename Folder", callback=callbacks.rename_folder_btn)
            dpg.add_button(label="Delete Folder", callback=callbacks.delete_folder_btn)

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


with dpg.file_dialog(
    label="Select file to load...",
    callback=callbacks.load_file_dialog,
    tag="load_file_dialog",
    width=WINDOW_WIDTH / 2,
    height=WINDOW_HEIGHT / 2,
    show=False,
):
    dpg.add_file_extension(".enc")


with input_window(
    "Load file...", "load_file_window", show=True, modal=False, no_close=True
):
    with dpg.group(horizontal=True):
        dpg.add_input_text(width=WINDOW_WIDTH / 5, tag="file_path_input")
        dpg.add_button(
            label="Find File", callback=lambda: dpg.show_item("load_file_dialog")
        )

    dpg.add_input_text(
        label="Password", password=True, width=WINDOW_WIDTH / 5, tag="password_input"
    )
    dpg.add_button(label="Load File", callback=callbacks.load_file)
    dpg.add_text(tag="load_file_error")
    dpg.bind_item_theme("load_file_error", error_theme)


dpg.bind_font(default_font)
dpg.set_primary_window("main_window", True)
dpg.set_viewport_vsync(True)

if __name__ == "__main__":
    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        if (
            callbacks.auto_lock
            and enc_file
            and dpg.get_frame_count() % 30 == 0
            and not utils.is_app_focused()
        ):
            enc_file = None
            gc.collect()

            curr_path = []
            dpg.hide_item("main_window")
            dpg.delete_item("file_tree_table", children_only=True)
            dpg.show_item("load_file_window")

        dpg.render_dearpygui_frame()

    dpg.destroy_context()
