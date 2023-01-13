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
mensagem = "?PRIVMSG canal"  # mensagem a ser enviada


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
        time.sleep(5)

    return


class ServerClient:
    numClients = 0

    def __init__(self, ipv4, sock, nickname="USR" + str(numClients), realname = "", hostname="", channel=""):
        self.ipv4 = ipv4
        self.sock = sock
        self.nickname = nickname
        self.realname = realname
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
        self.canais = {"canal": ServerChannel("canal")}

        # registra handlers para comandos
        self.handlers = {"NICK": self.nickClientHandler, # NICK
                         "USER": self.newClientHandler, # USER
                         "QUIT": self.deleteClientHandler, # QUIT
                         "JOIN": self.subscribeChannelHandler, # JOIN
                         "PART": self.unsubscribeChannelHandler, # PART
                         "LIST": self.listChannelHandler, # LIST
                         "PRIVMSG": self.privateMsg,  # PRIVMSG
                         "WHO": self.who,  # WHO
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
            self.canais["canal"].clients[clientAddr] = self.clients[clientAddr]

        client = self.clients[clientAddr]

        for command in commands:
            comm_n_args = command.split(' ')
            if comm_n_args[0][0] == '?':
                if comm_n_args[0][1:] in self.handlers.keys():
                    ans = self.handlers[comm_n_args[0][1:]](clientAddr, comm_n_args[1:])
                    '''if len(ans) > 0:
                        invalid_parameters += ans'''
                else:
                    unrecognized_commands += comm_n_args[0]
            else:
                self.sendMsgChannel(command, client.channel)

        answer = ""
        if len(unrecognized_commands) > 0:
            answer += "Unrecognized commands: %s" % unrecognized_commands
        '''if len(invalid_parameters) > 0:
            answer += "Invalid parameters: %s\n" % invalid_parameters
            print(answer)'''

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
        '''Dar um apelido ao user ou alterar anterior. Deve checar existencia do novo apelido.
        Portanto, e possivel afirmar que recebe apenas o novo apelido como argumento no metodo.'''

        if entrada_nick[0] in self.clients.keys():
            self.sendMsgClient(self, 'O nickname desejado já está sendo usado.', clientAddr)
        else:
            self.clients[clientAddr].nickname = entrada_nick
            return self.clients[clientAddr].nickname

    def newClientHandler(self, client, args): # USER
        '''Especifica o nome do user, nome do host e nome real do user.
        Supomos que especifica info de quem esta chamando e manda somente pra quem esta chamando tambem.
        N recebe argumentos alem do comando'''

        '''if len(args) < 3:
            return "Invalid parameters for USUARIO command"'''
        # else:
        client_instance = self.clients.setdefault(client)
        self.sendMsgClient(f'Nickname: {client_instance.nickname}, Host: {client_instance.hostname}, Name: {client_instance.realname}', client)
        '''client.nickname = args[0]
        client.hostname = args[1]
        client.realname = " ".join(args[2:])'''
        return ""

    def deleteClientHandler(self, clientAddr, args): # QUIT
        '''Finaliza sessao do cliente. Anuncia saida para os demais participantes do mesmo canal.
        N recebe argumentos alem do comando'''

        # remover user do server, canal (deixa de existir na plataforma) e reportar
        canalCliente = self.clients[clientAddr].channel # salva canal do user
        del self.clients[clientAddr] # remove user do server
        del self.canais[canalCliente].clients[clientAddr] # apaga user do canal
        self.sendMsgChannel(f'User {clientAddr} saiu.', canalCliente)

    def subscribeChannelHandler(self, clientAddr, canal): # JOIN
        '''Entrar em um canal, no nosso o user e limitado a somente um canal.
        Por isso, caso esteja em um deve sair do canal para se vincular ao outro.
        Como argumento deve receber o canal que deseja entrar'''

        if self.clients.setdefault(clientAddr).channel in self.canais:
            self.unsubscribeChannelHandler(clientAddr, self.clients[clientAddr].channel)
        self.clients[clientAddr].channel = canal

    def unsubscribeChannelHandler(self, clientAddr, channelAddr): # PART
        '''Sair de um canal especifico. E necessario verificar se o canal existe, se o user esta
        no canal e etc.
        Como argumento e recebido o canal que se deseja sair'''

        # erros possiveis: n existir o cliente ou canal no server
        # ou dentro do canal o user n pertencer
        if channelAddr in self.canais and clientAddr in self.canais[channelAddr].clients:
            # ao verificar que existe user no channel posso usar del
            del self.canais[channelAddr].clients[clientAddr] # desvincula user do canal
            self.clients[clientAddr].channel = None  # desvincula canal do user
            self.sendMsgChannel(f'User {clientAddr} saiu do canal {channelAddr}.', channelAddr)
        else:
            self.sendMsgClient("Canal n existe ou o cliente n pertence ao canal esspecificado", clientAddr)

    def listChannelHandler(self, client, parameters): # LIST
        '''Lista todos os canais que estao presentes no server apresentando nome e qnt users
        N recebe nenhum argumento na chamada'''

        response = "Channels:\r\n"
        for channel in self.canais.items(): # channel = (key, value)
            response += f"{channel[0]} -> ({len(channel[1].clients)} users)\r\n"
        print(response)
        return response

    #A função LIST irá gerar uma resposta listando todos os canais e o número de usuários em cada canal.
    #Para enviar esta resposta para o cliente usamos a função sendMessage
    def sendMessage(self, msg):
        for client in self.clients.keys():
            self.clients.setdefault(client).sendMsg(msg) #MODIFICADO!!! Antes era percorrido em self.clients.items() e chamava o metodo como client.sendMsg(msg). Percorria um dicionario de tuplas e client era uma tupla

    def privateMsg(self, requester, clientOrChannelAddr, message="mensagem a mandar"):
        '''Envia msg especificada para useroucanal
        se for canal, manda pra todos users vinculados ao canal, menos o cliente que mandou o comando
        se for apelido, manda pro user especificado'''

        if clientOrChannelAddr in self.canais: # destino eh canal
            self.sendMsgChannelButClient(message, clientOrChannelAddr, requester)
            print(message)
            print(clientOrChannelAddr)
        elif clientOrChannelAddr in self.clients: # destinho eh user
            self.sendMsgClient(message, clientOrChannelAddr)
            print(message)
            print(clientOrChannelAddr)
        else:
            print("entrou na excessao")
            self.sendMsgClient("Erro", requester)

    def who(self, channelAddr, requester):
        '''fornece correspondencia entre canal e usuarios pertencentes
        Como argumento deve receber o nome de canal que se deseja saber os usuarios'''

        if channelAddr in self.canais:
            clients = ""
            for client in self.canais[channelAddr].clients:
                clients += ", " + client
            clients = "Os usuários " + clients[2:] + "pertencem ao canal " + channelAddr + "." #fatiamento tira primeira virgula
            self.sendMsgClient(clients, requester)
        else:
            self.sendMsgClient("Erro", requester)

def processo2():
    # Cria servidor e escuta clients
    serv = ServerApp(portaHost)
    pass




# Para evitar dar pau com multi processos em python,
#   sempre colocar essa guarda, que evita processos filhos
#   de executarem o conteúdo da função
if __name__ == '__main__':
    main(processo1, processo2)