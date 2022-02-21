import socket
import threading
import argparse

ap = argparse.ArgumentParser()

ap.add_argument("-a", "--addr", required=False,
   help="Host", default='127.0.0.1')
ap.add_argument("-p", "--port", required=False,
   help="Port", default=5555)
ap.add_argument("-e", "--encoding", required=False,
   help="Encoding", default='utf8')
ap.add_argument("-u", "--adminuser", required=False,
   help="Admin User", default='admin')


args = vars(ap.parse_args())


encoding = args.get('encoding')
host = args.get('addr')
port = args.get('port')
uAdmin = args.get('adminuser')

print(f'Соединение с: [{host}:{port}] encoding: [{encoding}]...')
print('Команды для администратора чата: /kick /ban /users /history')

nickname = input("Введите Ваш никнейм:")
if nickname == uAdmin:
    password = input(f"Введите пароль для {uAdmin}:")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Соединение с хостом
client.connect((host, port))

stop_thread = False


def recieve():
    while True:
        global stop_thread
        if stop_thread:
            break
        try:
            message = client.recv(4096).decode(encoding)
            if message == 'USERS':
                next_message = client.recv(4096).decode(encoding)
                users = next_message.split(';')
                for u in users:
                    print(u)
            elif message == 'HISTORY':
                next_message = client.recv(4096).decode(encoding)
                print(next_message)
            elif message == 'NICK':
                    client.send(nickname.encode(encoding))
                    next_message = client.recv(4096).decode(encoding)
                    if next_message == 'PASS':
                        client.send(password.encode(encoding))
                        if client.recv(4096).decode(encoding) == 'REFUSE':
                            print("Пароль неверный!")
                            stop_thread = True
                    # Clients those are banned can't reconnect
                    elif next_message == 'BAN':
                        print('В соединении отказано, Вы внесены в Черный список')
                        client.close()
                        stop_thread = True
            else:
                print(message)
        except:
            print('Произошла ошибка при подключении')
            client.close()
            break


def write():
    while True:
        if stop_thread:
            break
        # Получение сообщений
        message = f'{nickname}: {input("")}'
        if message[len(nickname) + 2:].startswith('/'):
            if nickname == uAdmin:
                if message[len(nickname) + 2:].startswith('/history'):
                    client.send(f'HISTORY'.encode(encoding))
                elif message[len(nickname) + 2:].startswith('/kick'):
                    # 
                    client.send(f'KICK {message[len(nickname) + 2 + 6:]}'.encode(encoding))
                elif message[len(nickname) + 2:].startswith('/ban'):
                    # 
                    client.send(f'BAN {message[len(nickname) + 2 + 5:]}'.encode(encoding))
                if message[len(nickname) + 2:].startswith('/users'):
                    client.send(f'USERS'.encode(encoding))
            else:
                print("В доступе отказано")
        else:
            client.send(message.encode(encoding))


recieve_thread = threading.Thread(target=recieve)
recieve_thread.start()
write_thread = threading.Thread(target=write)
write_thread.start()
