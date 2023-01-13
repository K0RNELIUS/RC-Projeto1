import socket

class Client:
    def __init__(self, nickname, realname, host, port):
        # Instancia socket cliente
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Atributos
        self.nickname = nickname
        self.realname = realname
        self.channelConnected = None

        # Conecta cliente ao servidor
        self.clientsocket.connect((host, port))

        # Processa comandos
        message = input("?")
        while message.lower().strip() != 'bye':
            self.clientsocket.send(message.encode("utf-8"))  # envia
            data = self.clientsocket.recv(1024).decode("utf-8")  # recebe
            print('Received from server: ' + data)
            message = input("?")

        # Ao receber quit, fecha conexao com server
        self.clientsocket.close()  # close the connection


if __name__ == '__main__':
    Client("Leandro", "Leandro Beloti Kornelius", socket.gethostname(), 5000)