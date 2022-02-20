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

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the server to IP Address
server.bind((host, port))
# Start Listening Mode
server.listen()
# List to contain the Clients getting connected and nicknames
clients = []
nicknames = []

# 1.Broadcasting Method
def broadcast(message):
    for client in clients:
        client.send(message)
        if uHistory:
            with open(fileHistory, 'a', encoding=encoding) as f:
                fms = f'{message.decode()}\n'
                f.write(fms)



# 2.Recieving Messages from client then broadcasting
def handle(client):
    while True:
        try:
            msg = message = client.recv(4096)
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
                # Index is used to remove client from list after getting diconnected
                client.remove(client)
                client.close
                nickname = nicknames[index]
                broadcast(f'{nickname} left the Chat!'.encode(encoding))
                nicknames.remove(nickname)
                break


# Main Recieve method
def recieve():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        # Ask the clients for Nicknames
        client.send('NICK'.encode(encoding))
        nickname = client.recv(4096).decode(encoding)
        # If the Client is an Admin promopt for the password.
        with open('bans.txt', 'r') as f:
            bans = f.readlines()

        if nickname + '\n' in bans:
            client.send('BAN'.encode(encoding))
            client.close()
            continue

        if nickname == 'admin':
            client.send('PASS'.encode(encoding))
            password = client.recv(4096).decode(encoding)
            # I know it is lame, but my focus is mainly for Chat system and not a Login System
            if password != uPass:
                client.send('REFUSE'.encode(encoding))
                client.close()
                continue

        nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname of the client is {nickname}')
        broadcast(f'{nickname} joined the Chat'.encode(encoding))
        client.send('Connected to the Server!'.encode(encoding))

        # Handling Multiple Clients Simultaneously
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()



def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('You Were Kicked from Chat !'.encode(encoding))
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'{name} was kicked from the server!'.encode(encoding))


# Calling the main method
print(f'Server is Listening at [{host}:{port}] encoding: [{encoding}]...')
recieve()
