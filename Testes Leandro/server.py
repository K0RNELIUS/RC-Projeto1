import socket

'''
Classe Canal
Atributos:
nomecanal
dicclientes

Classe Servidor
Atributos

dicclientes 
diccanais
dichandlers

serversocket

conexao
'''

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

class Canal:
    def __init__(self, nomecanal):
        self.nomecanal = nomecanal
        self.clientesCanal = {}

class Servidor:
    def __init__(self, host, port):
        # Instancia socket servidor
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Atributos
        self.clientesServidor = {} # chave - address e o valor e
        # Para facilitar inicializa com alguns canais
        self.canaisServidor = {"Canal1": Canal("Canal1"),
                               "Canal2": Canal("Canal2"),
                               "Canal3": Canal("Canal3")}
        # Facilita na chamada dos comandos e metodos
        self.handlers = {"NICK": self.nickClientHandler,  # NICK
                         "USER": self.newClientHandler,  # USER
                         "QUIT": self.deleteClientHandler,  # QUIT
                         "JOIN": self.subscribeChannelHandler,  # JOIN
                         "PART": self.unsubscribeChannelHandler,  # PART
                         "LIST": self.listChannelHandler,  # LIST
                         "PRIVMSG": self.privateMsg,  # PRIVMSG
                         "WHO": self.who,  # WHO
                         }

        # Processamento das infos do cliente
        self.run()

        def run():
            # Conecta cliente ao servidor
            self.serversocket.bind((host, port))

            # Aceita conexao do cliente e adiciona no dicionario de clientes
            conn, address = self.serversocket.accept() # hostname, port retornado do metodo
            print(conn)
            print(address)
            if address not in self.clientesServidor.keys():
                self.clientesServidor[address] = Client(conn.send("Preencha o seu Nick abaixo:".encode("utf-8")),
                                                        conn.send("Preencha o seu realname abaixo:".encode("utf-8")),
                                                        socket.gethostname(), 5000)

            # Recebe comandos
            data = conn.recv(1024).decode("utf-8")
            data_lista = data.split()
            # Invoca metodos dos comandos
            retorno_metodo = self.handlers[data_lista[0]](address, data_lista[1:])
            conn.send(retorno_metodo.encode("utf-8"))  # devolve retorno dos metodos para cliente

    def nickClientHandler(self, address, nickname): # NICK
        '''Dar um apelido ao user ou alterar anterior. Deve checar existencia do novo apelido.
        Portanto, e possivel afirmar que recebe apenas o novo apelido como argumento no metodo.'''

        if nickname in self.clientesServidor.keys():
            return "Nickname ja utilizado"
        else:
            self.clientesServidor[address].nickname = nickname
            return self.clientesServidor[address].nickname






def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        print("from connected user: " + str(data))
        data = input(' -> ')
        conn.send(data.encode())  # send data to the client

    conn.close()  # close the connection


if __name__ == '__main__':
    server_program()