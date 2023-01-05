#! /usr/bin/env python3
# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2018-2022 Gabriel Ferreira <gabrielcarvfer@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation;
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from CriaProcessos import main
import socket
import time

portaHost = 65000  # porta do servidor (fica escutando esperando conexões)
mensagem = "abobrinha"  # mensagem a ser enviada


def processo1(id):
    # requisita API do SO uma conexão AF_INET (IPV4)
    #   com protocolo de transporte SOCK_STREAM (TCP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # processo dorme por 10 segundos para evitar
    #   se conectar com servidor antes desse estar rodando
    time.sleep(10)

    # requisita estabelecimento de conexão
    sock.connect((socket.gethostname(), portaHost))

    while 1:
        # transforma mensagem em bytes e transmite
        sock.send(mensagem.encode(encoding="utf-8"))
        print("Cliente:", mensagem)
        time.sleep(5)

    return


class ServerClient:
    numClients = 0

    def __init__(self, ipv4, sock, nickname="USR" + str(numClients), hostname="", channel=""):
        self.ipv4 = ipv4
        self.sock = sock
        self.nickname = nickname
        self.hostname = hostname
        self.channel = channel

        ServerClient.numClients += 1

    def sendMsg(self, msg):
        self.sock.send(msg.encode("utf-8"))


class ServerChannel:
    def __init__(self, name):
        self.name = name
        self.clients = {}


class ServerApp:

    def __init__(self, portaHost):
        # Cria estruturas para segurar clients e canais
        self.clients = {}
        self.canais = {"": ServerChannel("")}

        # registra handlers para comandos
        self.handlers = {"NICK": self.nickClientHandler, # NICK
                         "USUARIO": self.newClientHandler, # USER
                         "SAIR": self.deleteClientHandler, # QUIT
                         "ENTRAR": self.subscribeChannelHandler, # JOIN
                         "SAIRC": self.unsubscribeChannelHandler, # PART
                         "LISTAR": self.listChannelHandler, # LIST
                         }
        # requisita API do SO uma conexão AF_INET (IPV4)
        #   com protocolo de transporte SOCK_STREAM (TCP)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # requisita ao SO a posse de uma porta associada a um IP
        self.sock.bind((socket.gethostname(), portaHost))

        # requisita ao SO que a porta indicada de um dado IP seja
        #   reservado para escuta
        self.sock.listen(5)

        self.run()

    def run(self):
        while 1:
            # aceita requisição de conexão do processo 1,
            #   e recebe um socket para o cliente e o
            #   endereço de IP dele
            (clientsock, address) = self.sock.accept()

            while 1:
                # recebe do socket do cliente (processo 1) uma mensagem de 512 bytes
                mensagem_recebida = clientsock.recv(512).decode("utf-8")

                print(mensagem_recebida)

                # processa mensagem
                answer = self.parseCommands(clientsock, address, mensagem_recebida)
                if len(answer) > 0:
                    self.sendMessage(answer)
        pass

    def parseCommands(self, clientsock, clientAddr, mensagem_recebida):
        commands = mensagem_recebida.split('\n')  # comandos separados por nova linha
        unrecognized_commands = []
        invalid_parameters = []

        if clientAddr not in self.clients.keys():
            self.clients[clientAddr] = ServerClient(clientAddr, clientsock)
            self.canais[""].clients[clientAddr] = self.clients[clientAddr]

        client = self.clients[clientAddr]

        for command in commands:
            comm_n_args = command.split(' ')
            if comm_n_args[0][0] == '?':
                if comm_n_args[0][1:] in self.handlers.keys():
                    ans = self.handlers[comm_n_args[0][1:]](clientAddr, comm_n_args[1:])
                    if len(ans) > 0:
                        invalid_parameters += ans
                else:
                    unrecognized_commands += comm_n_args[0]
            else:
                self.sendMsgChannel(command, client.channel)

        answer = ""
        if len(unrecognized_commands) > 0:
            answer += "Unrecognized commands: %s" % unrecognized_commands
        if len(invalid_parameters) > 0:
            answer += "Invalid parameters: %s\n" % invalid_parameters

        return answer

    def sendMsgChannel(self, msg, channel):
        for client in self.canais[channel].clients:
            self.clients[client].sendMsg(msg)

    def sendMsgChannelButClient(self, msg, channel, clientAddr):
        for client in self.canais[channel].clients:
            if client != clientAddr:
                self.clients[client].sendMsg(msg)

    def sendMsgClient(self, msg, client): # mandar msgs de erro diretas
        self.clients[client].sendMsg(msg)

    def nickClientHandler(self, clientAddr, entrada_nick): # NICK
        if entrada_nick in self.clients:
            self.sendMsgClient(self, 'O nickname desejado já está sendo usado.', clientAddr)
        else:
            self.clients[clientAddr].nickname = entrada_nick

    def newClientHandler(self, client, args): #USER
        if len(args) < 3:
            return "Invalid parameters for USUARIO command"
        else:
            client.nickname = args[0]
            client.hostname = args[1]
            client.realname = " ".join(args[2:])
            return ""

    def deleteClientHandler(self, clientAddr): # QUIT
        # remover user do server, canal (deixa de existir na plataforma) e reportar
        canalCliente = self.clients[clientAddr].channel # salva canal do user
        del self.clients[clientAddr] # remove user do server
        del self.canais[canalCliente].clients[clientAddr] # apaga user do canal
        self.sendMsgChannel(self, f'User {clientAddr} saiu.', canalCliente)

    def subscribeChannelHandler(self, clientAddr, canal): # JOIN
        if self.clients[clientAddr].channel in self.canais:
            self.unsubscribeChannelHandler(clientAddr, self.clients[clientAddr].channel)

        self.clients[clientAddr].channel = canal

    def unsubscribeChannelHandler(self, clientAddr, channelAddr): # PART
        # erros possiveis: n existir o cliente ou canal no server
        # ou dentro do canal o user n pertencer
        if channelAddr in self.canais and clientAddr in self.canais[channelAddr].clients:
            # ao verificar que existe user no channel posso usar del
            del self.canais[channelAddr].clients[clientAddr] # desvincula user do canal
            self.clients[clientAddr].channel = None  # desvincula canal do user
            self.sendMsgChannel(self, f'User {clientAddr} saiu do canal {channelAddr}.', channelAddr)
        else:
            self.sendMsgClient(self, "Canal n existe ou o cliente n pertence ao canal esspecificado", clientAddr)

    def listChannelHandler(self, client, parameters): # LIST
        response = "Channels:\r\n"
        # for channel_name, channel in self.canais.items():
            # Problema: response += f"{channelname} ({len(channel.clients)} users)\r\n"
        return response

    #A função LIST irá gerar uma resposta listando todos os canais e o número de usuários em cada canal.
    #Para enviar esta resposta para o cliente usamos a função sendMessage
    def sendMessage(self, msg):
        for client in self.clients.items():
            client.sendMsg(msg)

    def privateMsg(self, requester, clientOrChannelAddr, message):
        if clientOrChannelAddr in self.canais: # destino eh canal
            self.sendMsgChannelButClient(self, message, clientOrChannelAddr, requester)
        elif clientOrChannelAddr in self.clients: # destinho eh user
            self.sendMsgClient(self, message, clientOrChannelAddr)
        else:
            self.sendMsgClient(self, "Erro", requester)

    def who(self, channelAddr, requester):
        if channelAddr in self.canais:
            clients = ""
            for client in self.canais[channelAddr].clients:
                clients += ", " + client
            clients = "Os usuários " + clients[2:] + "pertencem ao canal " + channelAddr + "." #fatiamento tira primeira virgula
            self.sendMsgClient(self, clients, requester)
        else: # Erro
            self.sendMsgClient(self, "Erro", requester)

def processo2():
    # Cria servidor e escuta clients
    serv = ServerApp(portaHost)
    pass


# Para evitar dar pau com multi processos em python,
#   sempre colocar essa guarda, que evita processos filhos
#   de executarem o conteúdo da função
if __name__ == '__main__':
    main(processo1, processo2)