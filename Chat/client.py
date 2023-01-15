import socket


def client_program():
    host = socket.gethostname()
    port = 1023

    client_socket = socket.socket()  # instancia cliente
    client_socket.connect((host, port))  # conecta cliente ao servidor pela uniao host e port

    message = input(" -> ")  # entrada do cliente

    while message.lower().strip() != 'QUIT':
        client_socket.send(message.encode())  # envia para comando ser processado no server
        data = client_socket.recv(1024).decode()  # recebe processamento do server
        print('Response from server:\n' + data)  # mostra resultado do processamento
        message = input(" -> ")

    # Processar comando quit e remover ocorrencias do usuario
    client_socket.send(message.encode())
    data = client_socket.recv(1024).decode()

    print('Response from server:\n' + data)
    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()