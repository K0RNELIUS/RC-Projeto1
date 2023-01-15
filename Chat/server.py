import socket


def nickClientHandler(address, nickname_novo, dicAddresses, dicClientes, dicCanais):  # NICK
    nickname_velho = dicAddresses[address][0]
    if nickname_novo == nickname_velho:
        return "Nick especificado ja e o seu"
    elif nickname_novo in dicClientes.keys():
        return "Nickname indisponivel"
    else:
        dicAddresses[address][0] = nickname_novo
        for canal in dicCanais.keys():
            if nickname_velho in dicCanais[canal]:
                ind = dicCanais[canal].index(nickname_velho)
                dicCanais[canal][ind] = nickname_novo
        info_nickname = dicClientes[nickname_velho]
        del dicClientes[nickname_velho]
        dicClientes[nickname_novo] = info_nickname
        return "Operacao concluida"


def nameClientHandler(address, name_novo, dicAddresses, dicClientes):  # NAME
    nickname = dicAddresses[address][0]
    dicClientes[nickname][0] = name_novo
    return "Operacao concluida"


def newClientHandler(address, dicAddresses, dicClientes):  # USER
    usuario = dicAddresses[address][0]
    if usuario in dicClientes.keys():
        return f'Nickname: {usuario}\nName: {dicClientes[usuario][0]}\nHost: {dicClientes[usuario][1]}\nPorta: {dicClientes[usuario][2]}'


def quitHandler(address, dicAddresses, dicClientes, dicCanais):
    usuario = dicAddresses[address][0]
    if usuario in dicClientes.keys():
        del dicAddresses[address]
        del dicClientes[usuario]
        for canal in dicCanais.keys():
            if usuario in dicCanais[canal]:
                dicCanais[canal].remove(usuario)
                break
        for user in dicCanais[canal]:
            msg = f'O user {usuario} saiu do canal {canal}'
            conn = conn_user(user, dicAddresses)
            conn.send(msg.encode())


def subscribeChannelHandler(address, canal, dicAddresses, dicCanais):  # JOIN
    usuario = dicAddresses[address][0]
    if canal not in dicCanais.keys():
        return 'O canal nao existe'
    for channel in dicCanais.keys():
        if usuario in dicCanais[channel]:
            unsubscribeChannelHandler(address, channel, dicAddresses, dicCanais)
    dicCanais[canal].append(usuario)
    return f'{usuario} foi adicionado ao {canal}'


def unsubscribeChannelHandler(address, canal, dicAddresses, dicCanais):  # PART
    usuario = dicAddresses[address][0]
    if canal not in dicCanais.keys():
        return 'O canal nao existe'
    elif usuario not in dicCanais[canal]:
        return 'O cliente nao esta no canal'
    dicCanais[canal].remove(usuario)
    return f'{usuario} foi removido do {canal}'


def listChannelHandler(dicCanais):  # LIST
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
    for address in dicAddresses.keys():
        if dicAddresses[address][0] == user:
            return dicAddresses[address][1]


def privMsgChannelHandler(address, entrada, msg, dicAddresses, dicClientes, dicCanais):  # PRIVMSG
    user_origem = dicAddresses[address][0]
    if entrada in dicCanais.keys():
        msg = f'Mensagem recebida pelo {user_origem} para o canal {entrada} -> ' + msg
        users_canal = dicCanais[entrada]
        for user in users_canal:
            if user != user_origem:
                conn = conn_user(user, dicAddresses)
                conn.send(msg.encode())
        return True
    elif entrada in dicClientes.keys():
        msg = f'Mensagem recebida pelo {user_origem} -> ' + msg
        conn = conn_user(entrada, dicAddresses)
        conn.send(msg.encode())
    else:
        conn_origem = conn_user(user_origem, dicAddresses)
        conn_origem.send("O user ou canal digitado n existe".encode())
    return False


def whoChannelHandler(canal, dicCanais):  # WHO
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
    # pega nome do host
    host = socket.gethostname()
    port = 1023

    '''
    ------------------------------------
    Estrutura dos dicionarios definidos
    ------------------------------------
    Estrutura address
    dic addresses -> chave address, valor: [nick, conn]
    Estrutura cliente
    dic clientes -> chave: nick, valor: [realname, host, port]
    Estrutura canais
    dic canais -> chave: nomecanal, valor: [nicks]
    ------------------------------------
    '''

    # Inicializacao dos dics colocando alguns canais para teste
    addressclientes = {}
    clientes = {}
    canais = {"CANAL1": [], "CANAL2": [], "CANAL3": []}

    server_socket = socket.socket()  # instancia servidor
    server_socket.bind((host, port))   # une host e port juntos

    server_socket.listen(3)
    conn, address = server_socket.accept()  # aceita nova conexao

    # Inicializa com valores arbitrarios
    if cond:
        nome_temp = 0
        cond = False
    addressclientes[address] = [str(nome_temp), conn]
    clientes[str(nome_temp)] = ["realnameinicial", socket.gethostname(), 1023]
    nome_temp += 1

    print("Connection from: " + str(address))
    while True:
        data = conn.recv(1024).decode()  # Recebendo comando
        '''if not data:
            # if data is not received break
            break'''
        comando_enviar_unico = True
        canal_teste = False
        if data.split()[0] == "NICK":
            data = nickClientHandler(address, data.split()[1], addressclientes, clientes, canais)
        elif data.split()[0] == "NAME":  # Comando pra alterar nome real, n presente no guia
            data = nameClientHandler(address, " ".join(data.split()[1:]), addressclientes, clientes)
        elif data.split()[0] == "USER":
            data = newClientHandler(address, addressclientes, clientes)
        elif data.split()[0] == "QUIT":
            quitHandler(address, addressclientes, clientes, canais)
            comando_enviar_unico = False
        elif data.split()[0] == "JOIN":
            data = subscribeChannelHandler(address, " ".join(data.split()[1:]), addressclientes, canais)
        elif data.split()[0] == "PART":
            data = unsubscribeChannelHandler(address, " ".join(data.split()[1:]), addressclientes, canais)
        elif data.split()[0] == "LIST":
            data = listChannelHandler(canais)
        elif data.split()[0] == "PRIVMSG":
            comando_enviar_unico = False
            canal_teste = privMsgChannelHandler(address,
                                  data.split()[1],
                                  " ".join(data.split()[2:]),
                                  addressclientes, clientes, canais)
            if canal_teste:
                data = "Mensagem enviada para o canal"
        elif data.split()[0] == "WHO":
            data = whoChannelHandler(data.split()[1], canais)
        else:
            data = "Comando invalido"

        if comando_enviar_unico or canal_teste:
            conn.send(data.encode())  # envia data ao usuario

        '''# Testes das funcs dos comandos
        print(addressclientes)
        print(clientes)
        print(canais)'''


if __name__ == '__main__':
    server_program(True)
