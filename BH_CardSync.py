import socket
import hashlib
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
from datetime import datetime

SERVER_ADDRESS = '255.255.255.255'  # типа адрес
PORT = 1337
FOLDER = os.path.abspath('C:\\KKS\\UserData\\chara\\female\\burning_hellas_2')

sock = None

def connect_to_server():
    global sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_ADDRESS, PORT))
        status_label.config(text="Подключено к серверу!")
        update_file_lists()
    except Exception as e:
        messagebox.showerror("Error", f"Невозможно подключиться к серверу: {e}")


def disconnect_from_server():
    global sock
    if sock:
        sock.close()
        sock = None
        status_label.config(text="Отключено.")
        clear_file_lists()

def clear_file_lists():
    for i in server_file_treeview.get_children():   # уох
        server_file_treeview.delete(i)
    for i in local_file_treeview.get_children():    #уох х2
        local_file_treeview.delete(i)

def update_file_lists():
    clear_file_lists()
    if not sock:
        return

    try:
        sock.sendall(json.dumps({'command': 'list_files'}).encode())
        response = sock.recv(8192).decode()

        try:
            server_files = json.loads(response)
            if 'error' in server_files:
                raise Exception(server_files['error'])

            for filename, data in server_files.items():
                mtime = datetime.fromtimestamp(data['mtime'])
                mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S')
                size_mb = round(data['size'] / (1024 * 1024), 2)  # Размер в МБ, nerd shit
                server_file_treeview.insert("", tk.END, values=(filename, size_mb, mtime_str))

        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Ошибка загрузки с сервера: {e}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Ошибка обработки данных: {e}")
            return

        for filename in os.listdir(FOLDER):
            filepath = os.path.join(FOLDER, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                size_mb = round(size / (1024 * 1024), 2)
                local_file_treeview.insert("", tk.END, values=(filename, size_mb, mtime_str))

    except Exception as e:
        messagebox.showerror("Error", f"Не получилось обновить списки файлов: {e}")


                        # я ничерта не помню, что я тут написал.
def download_selected():
    if not sock:
        return
    selected_items = server_file_treeview.selection()
    for item in selected_items:
        filename = server_file_treeview.item(item)['values'][0]
        try:
            sock.sendall(json.dumps({'command': 'get_file', 'filename': filename}).encode())
            filesize_bytes = sock.recv(1024).decode().strip()
            filesize = int(filesize_bytes)
            filepath = os.path.join(FOLDER, filename)
            with open(filepath, 'wb') as f:
                received = 0
                while received < filesize:
                    data = sock.recv(4096)
                    if not data:
                        raise Exception("Загрузка файла прервана по хер его знает каким причинам.")
                    f.write(data)
                    received += len(data)

        except Exception as e:
            messagebox.showerror("Error", f"Could not download '{filename}': {e}")
            continue  # продолжаем загрузку других файлов

        messagebox.showinfo("Заебис)", f"'{filename}' успешно загружен.")


    update_file_lists()  # обновляем списки после загрузки


def upload_selected():
    if not sock:
        return

    selected_items = local_file_treeview.selection() #  Выбор из Treeview
    if not selected_items:
        return

    for item in selected_items:
        filename = local_file_treeview.item(item)['values'][0]
        filepath = os.path.join(FOLDER, filename) # Формируем полный путь
        filesize = os.path.getsize(filepath)

        try:
            sock.sendall(json.dumps({'command': 'upload_file', 'filename': filename, 'size': filesize}).encode())
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    sock.sendall(data)

            messagebox.showinfo("Заебис)", f"'{filename}' успешно выгружен на сервер.")


        except Exception as e:
            messagebox.showerror("Error", f"Не получилось выгрузить на сервер '{filename}': {e}")
            continue

    update_file_lists()

# --- GUI ---

window = tk.Tk()
window.title("Вайфу-синхроз-инатор")
window.resizable(True, True) # Разрешаем масштабирование...


button_frame = ttk.Frame(window)
button_frame.pack(pady=10)


connect_button = ttk.Button(button_frame, text="Подключиться к серверу", command=connect_to_server)
connect_button.pack(side=tk.LEFT, padx=5)

disconnect_button = ttk.Button(button_frame, text="Отключиться от сервера", command=disconnect_from_server)
disconnect_button.pack(side=tk.LEFT, padx=5)



status_label = ttk.Label(window, text="Не подключено")
status_label.pack()


list_frame = ttk.Frame(window)
list_frame.pack(pady=5, fill=tk.BOTH, expand=True) # fill=tk.BOTH, expand=True для заполнения пространства, а то мало ли

list_frame.columnconfigure(0, weight=1)
list_frame.columnconfigure(1, weight=1)
list_frame.rowconfigure(1, weight=1) # weight=1 для listbox


server_file_label = ttk.Label(list_frame, text="Файлы на сервере:")
server_file_label.grid(row=0, column=0, sticky=tk.W, padx=(100,0))

server_file_treeview = ttk.Treeview(list_frame, columns=("Name", "Size (MB)", "Modified"), show="headings")
server_file_treeview.heading("Name", text="Name")
server_file_treeview.heading("Size (MB)", text="Size (MB)")
server_file_treeview.heading("Modified", text="Modified")
server_file_treeview.grid(row=1, column=0, sticky="nsew")


download_button = ttk.Button(list_frame, text="Скачать выделенное", command=download_selected)
download_button.grid(row=2, column=0, pady=(5,0))



local_file_label = ttk.Label(list_frame, text="Файлы на диске:")
local_file_label.grid(row=0, column=1, sticky=tk.W, padx=(150,0))


local_file_treeview = ttk.Treeview(list_frame, columns=("Name", "Size (MB)", "Modified"), show="headings")
local_file_treeview.heading("Name", text="Name")
local_file_treeview.heading("Size (MB)", text="Size (MB)")
local_file_treeview.heading("Modified", text="Modified")
local_file_treeview.grid(row=1, column=1, sticky="nsew", padx=(20,0))


upload_button = ttk.Button(list_frame, text="Выгрузить выделенное на сервер", command=upload_selected)
upload_button.grid(row=2, column=1, pady=(5, 0), padx=(20,0))



window.mainloop()







# sosal?