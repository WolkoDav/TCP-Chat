import copy

from tornado import gen

from common.exceptions import TcpException, MethodNotExists

__all__ = ['BaseHandler', 'ServerHandler']


class BaseHandler():

    # Список допустимых программ
    allowed_commands = []

    def __init__(self, request, *args, **kwargs):
        self._request = request

    def _get_handler(self, command):
        handler = None
        c_l = command.lower()
        if c_l in self.allowed_commands:
            handler = getattr(self, c_l, None)
        return handler


# Базовый обработчик запросов на сервер
class ServerHandler(BaseHandler):

    def __init__(self, request, socket_id, storage):
        super().__init__(request)
        self._socket_id = socket_id
        self._storage = storage
        self._data = {}
        self._status_code = 0
        self._response_command = self.get_argument("response_command", "RESP")

    # Добавить значение в Response
    def write(self, **kwargs):
        self._data.update(kwargs)

    # Получить аргумент из Request
    def get_argument(self, argument, default=None):
        return self._request.kwargs.get(argument, default)

    # Статус ответа
    def status_code(self, code):
        self._status_code = code

    # Получить данные для Response
    @property
    def data(self):
        d = copy.deepcopy(self._data)
        d["code"] = self._status_code
        return d

    # Обработка запроса
    @gen.coroutine
    def process_request(self):
        try:
            handler = self._get_handler(self._request.command)
            if handler is None:
                raise MethodNotExists(self._request.command)
            yield handler(self._request)
        except TcpException as e:
            self.write(message=e.message)
            self.status_code(e.code)
            self._response_command = "RESP"
        raise gen.Return(None if self._response_command is None else (self._response_command, self.data))