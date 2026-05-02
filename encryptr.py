from Crypto.Cipher import AES, ChaCha20_Poly1305
from argon2.low_level import hash_secret_raw
from argon2 import Type
import tempfile
import atexit
import shutil
import json
import time
import os

FILE_SIG = b"ENCR\x01\x02"
FORMAT_VERSION = 1
ALGOS = {1: "AES256-GCM", 2: "ChaCha20-Poly1305"}
ALGOS_NAME_KEY = {"AES256-GCM": 1, "ChaCha20-Poly1305": 2}

TEMP_DIR_PATH = tempfile.mkdtemp()


class EncryptrFile:
    def __init__(
        self,
        file_path: str,
        password: str,
        copy_files_on_add: bool = False,
    ):
        self._file_path = file_path
        self.copy_files_on_add = copy_files_on_add
        self._has_edited_files = False
        self._new_files = []

        if os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                if f.read(len(FILE_SIG)) != FILE_SIG:
                    raise ValueError("File isn't an Encryptr file.")

                file_format_ver = int.from_bytes(f.read(8), "big")
                self._algo_type = int.from_bytes(f.read(8), "big")
                if self._algo_type not in ALGOS:
                    raise ValueError("Algorithm type unsupported.")
                self._saved_algo_type = self._algo_type

                salt = f.read(16)
                self.set_password(password, salt)
                self._saved_key = self._key

                f.seek(0, os.SEEK_END)
                raw_root_json = self._decrypt_chunk_from_file(f, reverse=True)
                self._root = json.loads(raw_root_json.decode("ascii"))
                if type(self._root) != dict:
                    raise ValueError("Incorrect metadata format.")
        else:
            self.set_password(password)
            self._root = {}
            self._algo_type = 1  # AES
            self._saved_key = None

    @property
    def root(self):
        return self._root

    @property
    def file_path(self):
        return self._file_path

    @property
    def algo_type(self):
        return ALGOS[self._algo_type]

    def set_password(self, password: str, salt: bytes = os.urandom(16)):
        if password == "":
            raise ValueError("Password cannot be empty.")

        self._salt = salt
        self._key = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=self._salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID,
        )

    def change_algo_type(self, algo: str):
        if algo not in ALGOS_NAME_KEY:
            raise ValueError(f'"{algo}" is not an algorithm type.')

        self._algo_type = ALGOS_NAME_KEY[algo]

    def _make_algo_class(
        self, key: bytes, algo_type: int, nonce: bytes = os.urandom(12)
    ):
        match algo_type:
            case 1:
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

            case 2:
                cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)

            case _:
                raise ValueError("Unknown algorithm type.")

        return cipher

    # nonce 12, tag 16, length 8, ciphertext
    def _encrypt_chunk_and_write(self, file, data: bytes, reverse: bool = False):
        cipher = self._make_algo_class(self._key, self._algo_type)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        metadata = cipher.nonce + tag + len(ciphertext).to_bytes(8, "big")

        if not reverse:
            file.write(metadata)
            file.write(ciphertext)
        else:
            file.write(ciphertext)
            file.write(metadata)

    def _decrypt_chunk_from_file(self, file, reverse: bool = False):
        if reverse:
            file.seek(-(12 + 16 + 8), os.SEEK_CUR)

        nonce = file.read(12)
        tag = file.read(16)
        length = int.from_bytes(file.read(8), "big")

        if reverse:
            file.seek(-(12 + 16 + 8 + length), os.SEEK_CUR)

        cipher = self._make_algo_class(self._saved_key, self._saved_algo_type, nonce)
        return cipher.decrypt_and_verify(file.read(length), tag)

    def _copy_chunk_into_file(self, read_file, write_file):
        nonce_and_tag = read_file.read(12 + 16)
        length_byte = read_file.read(8)
        length = int.from_bytes(length_byte, "big")

        write_file.write(nonce_and_tag)
        write_file.write(length_byte)
        write_file.write(read_file.read(length))

    def _write_files_and_update_offset(self, directory: dict, read_file, write_file):
        for name, value in directory.items():
            print(f"writing {name}...")

            if type(value) == int:  # hasn't changed
                read_file.seek(value)
                directory[name] = write_file.tell()

                if self._saved_key == self._key:  # password hasn't c´hanged
                    self._copy_chunk_into_file(read_file, write_file)
                else:
                    data = self._decrypt_chunk_from_file(read_file)
                    self._encrypt_chunk_and_write(write_file, data)
            elif type(value) == str:  # new file or changed
                with open(value, "rb") as f:
                    directory[name] = write_file.tell()
                    self._encrypt_chunk_and_write(write_file, f.read())
            elif type(value) == dict:
                self._write_files_and_update_offset(value, read_file, write_file)

    def _write_metadata(self, file):
        root_json = json.dumps(self._root, separators=(",", ":"))
        self._encrypt_chunk_and_write(file, root_json.encode("ascii"), reverse=True)

    def save(self, file_path: str = None):
        if file_path is None:
            file_path = self._file_path

        save_start = time.perf_counter()

        # if files have been edited or password has been changed, rewrite file data
        if (
            self._saved_key is None
            or self._has_edited_files
            or self._key != self._saved_key
        ):
            if self._saved_key is None:
                temp_file_path = self._file_path
                read_file = None
            else:
                temp_file_path = os.path.join(
                    TEMP_DIR_PATH, os.path.basename(file_path)
                )
                read_file = (
                    open(self._file_path, "rb")
                    if os.path.isfile(self._file_path)
                    else None
                )

            with open(temp_file_path, "wb") as write_file:
                write_file.write(FILE_SIG)
                write_file.write(FORMAT_VERSION.to_bytes(8, "big"))
                write_file.write(self._algo_type.to_bytes(8, "big"))
                write_file.write(self._salt)
                self._write_files_and_update_offset(self._root, read_file, write_file)
                self._write_metadata(write_file)

            if self._saved_key is not None:
                shutil.move(temp_file_path, file_path)
                read_file.close()
        else:
            if file_path != self._file_path:
                shutil.copy(self._file_path, file_path)

            with open(file_path, "ab") as write_file:
                for path, name in self._new_files:
                    print(f"writing {name}...")

                    directory = self.get_from_path(path)
                    if name not in directory:  # failsafe
                        continue

                    with open(directory[name], "rb") as f:
                        directory[name] = write_file.tell()
                        self._encrypt_chunk_and_write(write_file, f.read())

                self._write_metadata(write_file)

        print(f"saved in {time.perf_counter() - save_start:.03f}s")

        self._saved_key = self._key
        self._saved_algo_type = self._algo_type
        self._has_edited_files = False
        self._new_files = []
        if file_path:
            self._file_path = file_path

    def get_from_path(self, path: list[str]):
        current_dir = self._root

        for subdir in path:
            current_dir = current_dir[subdir]

        return current_dir

    def get_file_data(self, path: list[str], name: str):
        directory = self.get_from_path(path)
        if type(directory) != dict:
            raise ValueError("Path cannot point to a file, must be a directory.")

        if name not in directory:
            raise ValueError("File not found.")

        if type(directory[name]) == int:
            with open(self._file_path, "rb") as f:
                f.seek(directory[name])
                return self._decrypt_chunk_from_file(f)
        elif type(directory[name]) == str:
            with open(directory[name], "rb") as f:
                return f.read()
        else:
            raise ValueError("Path does not point to a file.")

    def new_dir(self, path: list[str], name: str):
        if name == "":
            raise ValueError("Name cannot be empty.")

        directory = self.get_from_path(path)
        if type(directory) != dict:
            raise ValueError("Path cannot point to a file, must be a directory.")

        if name not in directory:
            directory[name] = {}

    def add_file(self, path: list[str], name: str, file_path: str):
        if name == "":
            raise ValueError("Name cannot be empty.")

        directory = self.get_from_path(path)
        if type(directory) != dict:
            raise ValueError("Path cannot point to a file, must be a directory.")

        if name in directory:  # overwriting file
            self._has_edited_files = True
        else:
            self._new_files.append((path, name))

        if self.copy_files_on_add:
            copy_dest = os.path.join(TEMP_DIR_PATH, str(len(path)) + name)
            shutil.copyfile(file_path, copy_dest)
            directory[name] = copy_dest
        else:
            directory[name] = file_path

    def delete_file(self, path: list[str], name: str):
        if name == "":
            raise ValueError("Name cannot be empty.")

        directory = self.get_from_path(path)
        if type(directory) != dict:
            raise ValueError("Path cannot point to a file, must be a directory.")

        if name in directory:
            if type(directory[name]) == str:
                try:
                    os.remove(directory[name])
                except FileNotFoundError:
                    pass

            del directory[name]

            # if it is deleting a new file then files haven't been edited
            if (path, name) in self._new_files:
                self._new_files.remove((path, name))
            else:
                self._has_edited_files = True

    def delete_dir(self, path: list[str]):
        if len(path) == 0:
            if self._root:
                self._root.clear()
                self._has_edited_files = True
        else:
            directory = self.get_from_path(path[:-1])

            if path[-1] in directory:
                if not directory[path[-1]]:  # if not empty
                    self._has_edited_files = True

                del directory[path[-1]]


def cleanup_temp():
    shutil.rmtree(TEMP_DIR_PATH)


atexit.register(cleanup_temp)
