import socket


def nickClientHandler(address, nickname_novo, dicAddresses, dicClientes, dicCanais):  # NICK
    nickname_velho = dicAddresses[address][0]
    if nickname_novo in dicClientes.keys():
        return "Nickname indisponivel"
    else:
        dicAddresses[address][0] = nickname_novo
        for canal in dicCanais.keys():
            if nickname_novo in dicCanais[canal]:
                dicCanais[canal].replace(nickname_velho, nickname_novo)
        info_nickname = dicClientes[nickname_velho]
        del dicClientes[nickname_velho]
        dicClientes[nickname_novo] = info_nickname
        return "Operacao concluida"

def nameClientHandler(address, name_novo, dicAddresses, dicClientes):  # NAME
    nickname = dicAddresses[address][0]
    dicClientes[nickname][0] = name_novo
    return "Operacao concluida"

def newClientHandler(address, dicAddresses, dicClientes): #USER
    usuario = dicAddresses[address][0]
    if usuario in dicClientes.keys():
        return f'Nickname: {usuario}\nName: {dicClientes[usuario][0]}\nHost: {dicClientes[usuario][1]}\nPorta: {dicClientes[usuario][2]}'

def subscribeChannelHandler(address, canal, dicAddresses, dicCanais): #JOIN
    usuario = dicAddresses[address][0]
    if canal not in dicCanais.keys():
        return 'O canal nao existe'
    for channel in dicCanais.keys():
        if usuario in dicCanais[channel]:
            unsubscribeChannelHandler(address, channel, dicAddresses, dicCanais)
    dicCanais[canal].append(usuario)
    return f'{usuario} foi adicionado ao {canal}'

def unsubscribeChannelHandler(address, canal, dicAddresses, dicCanais): #PART
    usuario = dicAddresses[address][0]
    if canal not in dicCanais.keys():
        return 'O canal nao existe'
    elif usuario not in dicCanais[canal]:
        return 'O cliente nao esta no canal'
    dicCanais[canal].remove(usuario)
    return f'{usuario} foi removido do {canal}'

def listChannelHandler(dicCanais): #LIST
    retorno = ""
    for canal in dicCanais.keys():
        retorno += f'{canal}:\n'
        cont_client = 1
        if dicCanais[canal] != []:
            for clientes in dicCanais[canal]:
                retorno += f'{cont_client} - {clientes}\n'
                cont_client += 1
        else:
            retorno += 'Canal sem clientes vinculados.\n'
    return retorno

def conn_user(user, dicAddresses):
    for address in dicAddresses:
        if dicAddresses[address][0] == user:
            return dicAddresses[address][1]

def privMsgChannelHandler(address, entrada, msg, dicAddresses, dicClientes, dicCanais): #PRIVMSG
    user_origem = dicAddresses[address][0]
    if entrada in dicCanais.keys():
        msg = f'Mensagem recebida pelo {user_origem} para o canal {entrada} -> ' + msg
        users_canal = dicCanais[entrada]
        for user in users_canal:
            if user != user_origem:
                conn = conn_user(user, dicAddresses)
                conn.send(msg.encode())
    elif entrada in dicClientes.keys():
        msg = f'Mensagem recebida pelo {user_origem} -> ' + msg
        conn = conn_user(entrada, dicAddresses)
        conn.send(msg.encode())
    else:
        conn_origem = conn_user(user_origem, dicAddresses)
        conn_origem.send("O user ou canal digitado n existe".encode())

def whoChannelHandler(canal, dicCanais):
    retorno = ""
    if canal in dicCanais.keys():
        retorno += f'Usuarios do {canal}:\n'
        cont_client = 1
        temalguem = False
        for cliente in dicCanais[canal]:
            temalguem = True
            retorno += f'{cont_client} - {cliente}\n'
            cont_client += 1
        if not temalguem:
            retorno += "Nao ha users nesse canal"
        return retorno
    return "Canal n existente"


def server_program(cond):
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    '''
    Estrutura address
    dic addresses -> chave address, valor: [nick, conn]
    Estrutura cliente
    dic clientes -> chave: nick, valor: [realname, host, port]
    Estrutura canais
    dic canais -> chave: nomecanal, valor: [nicks]
    '''
    addressclientes = {}
    clientes = {}
    canais = {"CANAL1": [], "CANAL2": [], "CANAL3": []}

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print(conn)

    # Inicializa com valores arbitrarios
    if cond:
        nome_temp = 0
        cond = False
    addressclientes[address] = [str(nome_temp), conn]
    clientes[str(nome_temp)] = ["realnameinicial", socket.gethostname(), 5000]
    nome_temp += 1

    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode() # Recebendo comando
        '''if not data:
            # if data is not received break
            break'''
        comando_enviar_unico = True
        if data.split()[0] == "NICK":
            data = nickClientHandler(address, data.split()[1], addressclientes, clientes, canais)
        elif data.split()[0] == "NAME": # Comando pra alterar nome real, n presente no guia
            data = nameClientHandler(address, " ".join(data.split()[1:]), addressclientes, clientes)
        elif data.split()[0] == "USER":
            data = newClientHandler(address, addressclientes, clientes)
        elif data.split()[0] == "QUIT":
            comando_enviar_unico = False
            print("quit")
        elif data.split()[0] == "JOIN":
            data = subscribeChannelHandler(address, " ".join(data.split()[1:]), addressclientes, canais)
        elif data.split()[0] == "PART":
            data = unsubscribeChannelHandler(address, " ".join(data.split()[1:]), addressclientes, canais)
        elif data.split()[0] == "LIST":
            data = listChannelHandler(canais)
        elif data.split()[0] == "PRIVMSG":
            comando_enviar_unico = False
            privMsgChannelHandler(address, data.split()[1], " ".join(data.split()[2:]), addressclientes, canais, clientes)
        elif data.split()[0] == "WHO":
            data = whoChannelHandler(data.split()[1], canais)
        else:
            data = "Comando invalido"

        if comando_enviar_unico:
            conn.send(data.encode())  # send data to the client

    conn.close()  # close the connection


if __name__ == '__main__':
    server_program(True)