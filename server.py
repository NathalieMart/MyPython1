import configparser
import threading
import socket

config = configparser.ConfigParser({'Encoding': 'utf8', 'Host': '127.0.0.1', 'Port': 5555, 'AdminUser': 'admin',
                                    'AdminPassword': 'ok', 'SaveHistory': False, 'HistoryFile': 'history.txt'})
config.read("settings.ini")
section = 'DEFAULT'

encoding = config.get(section, 'Encoding')
host = config.get(section, 'Host')
port = config.getint(section, 'Port')
uAdmin = config.get(section, 'AdminUser')
uPass = config.get(section, 'AdminPassword')
uHistory = config.getboolean(section, 'SaveHistory')
fileHistory = config.get(section, 'HistoryFile')
# настройка для информационного обмена
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Привязка сервера к ip-адресу
server.bind((host, port))
# Сервер готов к приему информации
server.listen()
# Списки клиентов с никами (изначально пустые, вход для пользователей без пароля, пароль - только для админа)
clients = []
nicknames = []

# 1.Передача сообщений в архив
def broadcast(message):
    for client in clients:
        client.send(message)
        if uHistory:  # Если в настройках конфигурации SaveHistory=True, то история чата сохраняется в отдельный файл 
            with open(fileHistory, 'a', encoding=encoding) as f:
                fms = f'{message.decode()}\n'
                f.write(fms)



# 2.Прием сообщений от клиентов
def handle(client):
    while True:
        try:
            msg = message = client.recv(4096) # сообщения принимаются на сервере и классифицируются по стартовому признаку на пользовательские и служебные, обрабатываются 
            if msg.decode(encoding).startswith('USERS'):
                if nicknames[clients.index(client)] == uAdmin:  
                    client.send('USERS'.encode(encoding))
                    strnicks = ''
                    for item in nicknames:
                        strnicks = strnicks + str(item) + ';'
                    client.send(strnicks.encode(encoding))
                else:
                    client.send('Command Refused!'.encode(encoding))
            elif msg.decode(encoding).startswith('HISTORY'):
                    if nicknames[clients.index(client)] == uAdmin:
                     client.send('HISTORY'.encode(encoding))
                     with open(fileHistory, 'r') as f:
                        history = f.readlines()
                        wstr = ''.join(map(str, history))
                        client.send(wstr.encode(encoding))
                    else:
                        client.send('Command Refused!'.encode(encoding))
            elif msg.decode(encoding).startswith('KICK'):
                if nicknames[clients.index(client)] == uAdmin:
                    name_to_kick = msg.decode(encoding)[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command Refused!'.encode(encoding))
            elif msg.decode(encoding).startswith('BAN'):
                if nicknames[clients.index(client)] == uAdmin:
                    name_to_ban = msg.decode(encoding)[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt', 'a') as f:
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned by the {uAdmin}!')
                else:
                    client.send('Command Refused!'.encode(encoding))
            else:
                broadcast(message)  # As soon as message recieved, broadcast it.

        except:
            if client in clients:
                index = clients.index(client)
                # Индекс используется для удаления клиента из списков после отключения
                client.remove(client)
                client.close
                nickname = nicknames[index]
                broadcast(f'{nickname} покинул(а) чат!'.encode(encoding))
                nicknames.remove(nickname)
                break


# Основной блок
def recieve():
    while True:
        client, address = server.accept()
        print(f"Соединение с {str(address)}")
        # Запрос никнейма
        client.send('NICK'.encode(encoding))
        nickname = client.recv(4096).decode(encoding)
        # проверка клиента по "черному списку"
        with open('bans.txt', 'r') as f:
            bans = f.readlines()

        if nickname + '\n' in bans:
            client.send('BAN'.encode(encoding))
            client.close()
            continue
        # Если клиент является админом, то надо запросить пароль
        if nickname == 'admin':
            client.send('PASS'.encode(encoding))
            password = client.recv(4096).decode(encoding)
            
            if password != uPass:
                client.send('Отказано'.encode(encoding))
                client.close()
                continue
        # добавление клиента
        nicknames.append(nickname)
        clients.append(client)

        print(f'Никнейм клиента {nickname}')
        broadcast(f'{nickname} добавился в чат'.encode(encoding))
        client.send('Соединение с серввером!'.encode(encoding))

        # Обработка нескольких клиентов
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()



def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('Вы не допущены в чат!'.encode(encoding))
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'{name} исключен из чата!'.encode(encoding))


# Вызов основного метода
print(f'Сервер на линии [{host}:{port}] encoding: [{encoding}]...')
recieve()
