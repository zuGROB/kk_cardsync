import socket
import threading
import hashlib
import os
import json
import time

HOST = '0.0.0.0'
PORT = 1337
CARD_FOLDER = 'C:\\KKS\\UserData\\chara\\female\\burning_hellas'  # Папка с карточками
MOD_FOLDER = 'C:\\KKS\\mods' # Папка с модами


def handle_client(conn, addr):
    print(f'Подключен клиент: {addr}')
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            request = json.loads(data)
            command = request.get('command')
            folder = request.get('folder') #  Получаем имя папки

            if command == 'list_files':
                try:
                    target_folder = CARD_FOLDER if folder == 'cards' else MOD_FOLDER if folder == 'mods' else None
                    if not target_folder:
                        raise ValueError("Invalid folder specified")
                    files = {}
                    for filename in os.listdir(target_folder):
                        filepath = os.path.join(target_folder, filename)
                        if os.path.isfile(filepath):
                            with open(filepath, 'rb') as f:
                                filehash = hashlib.md5(f.read()).hexdigest()
                            files[filename] = {'size': os.path.getsize(filepath), 'hash': filehash, 'mtime': os.path.getmtime(filepath)}
                    conn.sendall(json.dumps(files, ensure_ascii=False).encode())
                except Exception as e:
                    print(f"Error listing files: {e}")
                    conn.sendall(json.dumps({'error': str(e)}).encode())


            elif command == 'get_file':
                filename = request.get('filename')
                target_folder = CARD_FOLDER if folder == 'cards' else MOD_FOLDER if folder == 'mods' else None
                if not target_folder:
                        raise ValueError("Invalid folder specified")

                filepath = os.path.join(target_folder, filename)


                if os.path.isfile(filepath):
                    try:
                        filesize = os.path.getsize(filepath)
                        conn.sendall(str(filesize).encode() + b'\n')
                        with open(filepath, 'rb') as f:
                            conn.sendall(f.read())
                    except Exception as e:
                        print(f"Error sending file: {e}")


            elif command == 'upload_file':
                filename = request.get('filename')
                filesize = int(request.get('size'))
                target_folder = CARD_FOLDER if folder == 'cards' else MOD_FOLDER if folder == 'mods' else None

                if not target_folder:
                    raise ValueError("Invalid folder specified")


                filepath = os.path.join(target_folder, filename)

                try:
                    with open(filepath, 'wb') as f:
                        received = 0
                        while received < filesize:
                            data = conn.recv(4096)
                            if not data:
                                break
                            f.write(data)
                            received += len(data)
                except Exception as e:
                    print(f"Error receiving file: {e}")


    except Exception as e:
        print(f'Error: {e}')

    finally:
        conn.close()
        print(f'Клиент отключен: {addr}')


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f'Сервер запущен на порту {PORT}')

    while True:
        conn, addr = s.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()  # Запускаем обработку клиента в отдельном потоке