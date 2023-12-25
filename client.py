import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "26.198.66.213"
        self.port = 5555
        self.addr = (self.host, self.port)

    #подключение к серверу и возвращение идентификатора клиента, который подключился
    def connect(self, name, color):
        self.client.connect(self.addr)
        self.client.send(pickle.dumps((name, color)))
        val = self.client.recv(256)
        return int(val.decode())

    #отключение от сервера
    def disconnect(self):
        self.client.close()

    #отправка информации на сервер
    def send(self, data, pick=False):
        try:
            if pick:
                self.client.send(pickle.dumps(data.decode))
            else:
                self.client.send(data.encode())
            reply = self.client.recv(2048*4)
            try:
                reply = pickle.loads(reply)
            except Exception as e:
                print(f'ERROR reply: {e}')

            return reply
        except socket.error as e:
            print(f'Exception send: {e}')