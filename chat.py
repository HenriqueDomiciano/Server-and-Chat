'''
Script para estudo do modulo sockets do python Chat com varios usarios 
inspirado no script de sentdex 
Data : 29/09/2022
Usando OOP
Tamanho maximo da mensagem em bytes 10**15
#TODO modificar para evitar a necessidade de um servidor e fazer comunicação p2p
#TODO implementar, em outro codigo, a transferencia de arquivos. 
#TODO tentar organizar transferencia de arquivos p2p em redes locais
'''
import time
from threading import Thread
import socket
import select
import errno


#classe de implementação do servidor 
class Server(Thread):
    def __init__(self,ip,porta):
        Thread.__init__(self)
        self.socket_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.list_sockets = [self.socket_server]
        self.ip = ip
        self.porta = porta
        self.clients = {}
        self.create_server()
        self.header_size = 15
        self.__version__= 1.0
        self.__author__ = "Henrique Domiciano Osinski"

    def build_msg(self,msg)->bytes:
        send_message_with_header = bytes(f"{len(msg):<15}",'utf-8')+ msg
        return send_message_with_header


    def create_server(self):
        
        self.socket_server.bind((self.ip,self.porta))
        self.socket_server.listen(10)

    def message_received(self,client_socket):
        try:
            msg_header = client_socket.recv(self.header_size)
            if not len(msg_header) :
                return False
            message_tam = int(msg_header.decode('utf-8').strip())

            return {"header": str(message_tam).encode('utf-8') , 'data': client_socket.recv(message_tam)}
            
        except:
            return False
    
    def run(self):
        while True:
            read_sockets,_,problem_sockets = select.select(self.list_sockets,[],self.list_sockets)

            for notified_socket in  read_sockets:
                if notified_socket == self.socket_server:
                    client_socket,client_addr = self.socket_server.accept()

                    user = self.message_received(client_socket)

                    if user == False:
                        continue

                    self.list_sockets.append(client_socket)

                    self.clients[client_socket] = user

                    print(f'Connection openned in {user}')
                else:
                    msg = self.message_received(notified_socket)
                    if msg == False:
                        print(f'Connection Closed {self.clients[notified_socket]}')
                        self.list_sockets.remove(notified_socket)
                        del self.clients[notified_socket]
                        continue

                    user = self.clients[notified_socket]
                    print(f"RECEIVED MESSAGE FROM {user['data'].decode('utf-8')}: {msg['data'].decode('utf-8')}")

                    for client_socket in self.clients:
                        if client_socket != notified_socket:
                            client_socket.send(self.build_msg(user['data'])+ self.build_msg(msg['data']))
            
            for notified_socket in problem_sockets:
                self.list_sockets.remove(notified_socket)
                del self.clients[notified_socket]


#Classe de implementação do cliente
# Recebe :
# ip:str -> IPV4 do destino 
# porta: int -> porta do servidor de detino
# username : str -> nome de usuario no chat
 
class Client():
    def __init__(self,ip,porta,username) -> None:
        self.header_size = 15
        self.soc_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.username = username
        self.ip = ip
        self.porta = porta
        self.soc_client.connect((self.ip,self.porta))
        self.soc_client.setblocking(False)
        self.send_user()
        self.receiving = False
    def build_msg(self,msg)->bytes:
        '''
        COnstroi o header de tamanho da mensagem com ate 15 digitos
        '''
        send_message_with_header = bytes(f"{len(msg):<15}",'utf-8')+ msg
        return send_message_with_header

    def send_user(self):
        '''
        Envia nome de uuario ao servidor
        '''
        user_bytes = self.username.encode('utf-8')
        message = self.build_msg(user_bytes)
        self.soc_client.send(message)
    def send_Message(self):
        msg = input(f'{self.username} > ') 
        if msg:
            msg_bytes =  str(msg).encode('utf-8')# transforma de str para bytes 
            msg = self.build_msg(msg_bytes)#constroi mensagem com header de tamanho
            self.soc_client.send(msg) #envia a mensagem ao servidor 
    def read_message(self):
        while True:
            time.sleep(0.5) # To not keep the programm running al the time (improve performance)
            try:
                while True:
                    self.receiving = True
                    username_header = self.soc_client.recv(15) # recebe o tamanho do nome de Usuario
                    if not len(username_header): # Se nao recebe nada não ha mais conexão 
                        print("Connection closed")
                        exit()

                    username_len = int(username_header.decode('utf-8').strip())#joga pra int tamanho do nome 
                    username_rcv = self.soc_client.recv(username_len).decode('utf-8')#pega o nome de usuario que enviou a mensagem 
            
                    msg_header = self.soc_client.recv(15) #recebe a mensagem do tamanho da mensagem
                    msg_header_len = int(msg_header.decode('utf-8').strip())# pega o tamanho da mensagem parsing pra int 
                    
                    msg_rcv =  self.soc_client.recv(msg_header_len) # lê a mensaagem 
                    msg_rcv = msg_rcv.decode('utf-8') #transforma a mensagem em string
                    print()
                    print(f'{username_rcv} > {msg_rcv}\n{self.username} > ',end='') #joga a tela do usuario a mensagem
            
            except IOError as e:
                if e.errno != errno.EAGAIN or e.errno!=errno.EWOULDBLOCK:
                    print('ERROR READING')
                    exit()
                self.receiving  = False
            
            except Exception as e :
                raise e 

    def run(self):
        '''
        Implementa a logica do cliente
        '''
        print('PRESS ENTER TO SEE NEW MESSAGES')
        read = Thread(target=self.read_message,daemon=True)
        read.start()

        while True:
            self.send_Message()


if __name__=='__main__':
    s = [Server('127.0.0.1',34500)]

    for i in s:
        i.start()
    for i in s:
        i.join()