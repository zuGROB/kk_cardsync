import socket
import threading
import hashlib
import os
import json
import time

HOST = '0.0.0.0'  # Слушаем на всех интерфейсах
PORT = 1337  # Порт
FOLDER = 'C:\\KKS\\UserData\\chara\\female\\burning_hellas'  # Папка с карточками

def handle_client(conn, addr):
    print(f'Подключен клиент: {addr}')
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            request = json.loads(data)
            command = request.get('command')

            if command == 'list_files':
                try:
                    files = {}
                    for filename in os.listdir(FOLDER):
                        filepath = os.path.join(FOLDER, filename)
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
                filepath = os.path.join(FOLDER, filename)
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
                filesize = int(request.get('size')) # Приводим к int
                filepath = os.path.join(FOLDER, filename)
                try:
                    with open(filepath, 'wb') as f:
                        received = 0
                        while received < filesize: # Ограничиваем чтение размером файла
                            data = conn.recv(4096)
                            if not data:
                                break # Выходим, если данные не получены
                            f.write(data)
                            received += len(data)
                except Exception as e:
                    print(f"Error receiving file: {e}")


    except Exception as e:
        print(f'Ошибка: {e}')
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