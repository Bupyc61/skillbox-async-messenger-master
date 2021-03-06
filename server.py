#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):

                newlogin = decoded.replace("login:", "").replace("\r\n", "")
                if self.login_is_correct(newlogin):
                    self.login = newlogin
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.send_history()

                else:
                    self.transport.write("Логин занят,попробуй другой\n".encode())
                    self.transport.close()

            else:
                self.transport.write("Для входа введите login:ваше имя\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(message.encode())

        self.server.messages.append(message)
        self.server.messages = self.server.messages[-10:]

    def send_history(self):

        if len(self.server.messages) > 0:
            self.transport.write("Последние сообщения в чате:\n".encode())
            for message in self.server.messages:
                self.transport.write(message.encode())

    def login_is_correct(self, login):

        for user in self.server.clients:
            if user.login == login:
                return False

        return True


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")