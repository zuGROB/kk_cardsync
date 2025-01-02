import socket
import hashlib
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
from datetime import datetime

SERVER_ADDRESS = 'localhost'  # Или IP
PORT = 1337
CARD_FOLDER = os.path.abspath('C:\\KKS\\UserData\\chara\\female\\burning_hellas_2')  # Папка для карточек
MOD_FOLDER = os.path.abspath('C:\\KKS\\mods')  # Папка для модов

sock = None

def connect_to_server():
    global sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_ADDRESS, PORT))
        status_label.config(text="Connected to server")
        update_file_lists()
    except Exception as e:
        messagebox.showerror("Error", f"Не получилось подключиться к серверу: {e}")

def disconnect_from_server():
    global sock
    if sock:
        sock.close()
        sock = None
        status_label.config(text="Отключено")
        clear_file_lists()

def clear_file_lists():
    for tree in [server_card_treeview, local_card_treeview, server_mod_treeview, local_mod_treeview]:
        for i in tree.get_children():
            tree.delete(i)

def update_file_lists(folder_type="all"):
    clear_file_lists()
    if not sock:
        return

    if folder_type in ("all", "cards"):
        try:
            sock.sendall(json.dumps({'command': 'list_files', 'folder': 'cards'}).encode())
            response = sock.recv(8192).decode()

            try:
                server_files = json.loads(response)
                if 'error' in server_files:
                    raise Exception(server_files['error'])

                for filename, data in server_files.items():
                    mtime = datetime.fromtimestamp(data['mtime'])
                    mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S')
                    size_mb = round(data['size'] / (1024 * 1024), 2)
                    server_card_treeview.insert("", tk.END, values=(filename, size_mb, mtime_str))

            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Ошибка загрузки карточки: {e}")
                return
            except Exception as e:
                messagebox.showerror("Error", f"Ошибка обработки данных: {e}")
                return


            for filename in os.listdir(CARD_FOLDER):
                filepath = os.path.join(CARD_FOLDER, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    size_mb = round(size / (1024 * 1024), 2)
                    local_card_treeview.insert("", tk.END, values=(filename, size_mb, mtime_str))

        except Exception as e:
            messagebox.showerror("Error", f"Не вышло обновить списки карт: {e}")



    if folder_type in ("all", "mods"):
        try:
            sock.sendall(json.dumps({'command': 'list_files', 'folder': 'mods'}).encode())
            response = sock.recv(8192).decode()

            try:
                server_files = json.loads(response)
                if 'error' in server_files:
                    raise Exception(server_files['error'])

                for filename, data in server_files.items():
                    mtime = datetime.fromtimestamp(data['mtime'])
                    mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S')
                    size_mb = round(data['size'] / (1024 * 1024), 2)
                    server_mod_treeview.insert("", tk.END, values=(filename, size_mb, mtime_str))

            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Ошибка загрузки мода: {e}")
                return
            except Exception as e:
                messagebox.showerror("Error", f"Ошибка обработки данных: {e}")
                return


            for filename in os.listdir(MOD_FOLDER):
                filepath = os.path.join(MOD_FOLDER, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    size_mb = round(size / (1024 * 1024), 2)
                    local_mod_treeview.insert("", tk.END, values=(filename, size_mb, mtime_str))

        except Exception as e:
            messagebox.showerror("Error", f"Ошибка обработки данных с сервера: {e}")


#                       ctrl-c ctrl-v goes brrrrrrrr
def download_selected(folder_type):
    if not sock:
        return

    treeview = server_card_treeview if folder_type == "cards" else server_mod_treeview
    local_folder = CARD_FOLDER if folder_type == "cards" else MOD_FOLDER
    selected_items = treeview.selection()

    for item in selected_items:
        filename = treeview.item(item)['values'][0]

        try:
            sock.sendall(json.dumps({'command': 'get_file', 'filename': filename, 'folder': folder_type}).encode())
            filesize_bytes = sock.recv(1024).decode().strip()
            filesize = int(filesize_bytes)

            filepath = os.path.join(local_folder, filename)

            with open(filepath, 'wb') as f:
                received = 0
                while received < filesize:
                    data = sock.recv(4096)
                    if not data:
                        raise Exception("Загрузка оборвалась")
                    f.write(data)
                    received += len(data)
            messagebox.showinfo("Success", f"'{filename}' успешно загружен.")


        except Exception as e:
            messagebox.showerror("Error", f"Не вышло загрузить '{filename}': {e}")

    update_file_lists(folder_type)



def upload_selected(folder_type):
    if not sock:
        return

    folder = CARD_FOLDER if folder_type == "cards" else MOD_FOLDER
    filepaths = filedialog.askopenfilenames(initialdir=folder)
    if not filepaths:
        return

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        try:
            sock.sendall(json.dumps({'command': 'upload_file', 'filename': filename, 'size': filesize, 'folder': folder_type}).encode())

            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    sock.sendall(data)

            messagebox.showinfo("Success", f"'{filename}' успешно выгружен на сервер.")


        except Exception as e:
            messagebox.showerror("Error", f"Не вышло выгрузить '{filename}' на сервер: {e}")

    update_file_lists(folder_type)


# --- GUI ---               И ЭТО ПИЗЕЦ

window = tk.Tk()
window.title("Вайфу-синхро-инатор")
window.resizable(True, True)

button_frame = ttk.Frame(window)
button_frame.pack(pady=10)

connect_button = ttk.Button(button_frame, text="Подключиться", command=connect_to_server)
connect_button.pack(side=tk.LEFT, padx=5)

disconnect_button = ttk.Button(button_frame, text="Отключиться", command=disconnect_from_server)
disconnect_button.pack(side=tk.LEFT, padx=5)

status_label = ttk.Label(window, text="Отсоединено")
status_label.pack()

main_frame = ttk.Frame(window)
main_frame.pack(pady=5, fill=tk.BOTH, expand=True)

# Карточки
card_frame = ttk.LabelFrame(main_frame, text="Карточки")
card_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5) # Изменено side=tk.TOP

server_card_label = ttk.Label(card_frame, text="На стороне сервера:")
server_card_label.grid(row=0, column=0, sticky=tk.W)

server_card_treeview = ttk.Treeview(card_frame, columns=("Name", "Size (MB)", "Modified"), show="headings")
server_card_treeview.heading("Name", text="Name")
server_card_treeview.heading("Size (MB)", text="Size (MB)")
server_card_treeview.heading("Modified", text="Modified")
server_card_treeview.grid(row=1, column=0, sticky="nsew")

download_card_button = ttk.Button(card_frame, text="Загрузить с сервера", command=lambda: download_selected("cards"))
download_card_button.grid(row=2, column=0, pady=(5, 0))

local_card_label = ttk.Label(card_frame, text="На диске:")
local_card_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

local_card_treeview = ttk.Treeview(card_frame, columns=("Name", "Size (MB)", "Modified"), show="headings")
local_card_treeview.heading("Name", text="Name")
local_card_treeview.heading("Size (MB)", text="Size (MB)")
local_card_treeview.heading("Modified", text="Modified")
local_card_treeview.grid(row=1, column=1, sticky="nsew", padx=(20, 0))

upload_card_button = ttk.Button(card_frame, text="Выгрузить на сервер", command=lambda: upload_selected("cards"))
upload_card_button.grid(row=2, column=1, pady=(5, 0), padx=(20, 0))

# Моды
mod_frame = ttk.LabelFrame(main_frame, text="Моды")
mod_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5) # Изменено side=tk.TOP

server_mod_label = ttk.Label(mod_frame, text="На стороне сервера:")
server_mod_label.grid(row=0, column=0, sticky=tk.W)

server_mod_treeview = ttk.Treeview(mod_frame, columns=("Name", "Size (MB)", "Modified"), show="headings")
server_mod_treeview.heading("Name", text="Name")
server_mod_treeview.heading("Size (MB)", text="Size (MB)")
server_mod_treeview.heading("Modified", text="Modified")
server_mod_treeview.grid(row=1, column=0, sticky="nsew")

download_mod_button = ttk.Button(mod_frame, text="Загрузить с сервера", command=lambda: download_selected("mods"))
download_mod_button.grid(row=2, column=0, pady=(5, 0))

local_mod_label = ttk.Label(mod_frame, text="На диске:")
local_mod_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

local_mod_treeview = ttk.Treeview(mod_frame, columns=("Name", "Size (MB)", "Modified"), show="headings")
local_mod_treeview.heading("Name", text="Name")
local_mod_treeview.heading("Size (MB)", text="Size (MB)")
local_mod_treeview.heading("Modified", text="Modified")
local_mod_treeview.grid(row=1, column=1, sticky="nsew", padx=(20, 0))

upload_mod_button = ttk.Button(mod_frame, text="Выгрузить на сервер", command=lambda: upload_selected("mods"))
upload_mod_button.grid(row=2, column=1, pady=(5, 0), padx=(20, 0))



main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

card_frame.columnconfigure(0, weight=1)
card_frame.columnconfigure(1, weight=1)
card_frame.rowconfigure(1, weight=1)

mod_frame.columnconfigure(0, weight=1)
mod_frame.columnconfigure(1, weight=1)
mod_frame.rowconfigure(1, weight=1)

window.mainloop()