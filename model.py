import simpy
import random


class WebServiceModel:
    def __init__(self, env, params):
        """
        Инициализация модели.
        :param env: simpy.Environment
        :param params: словарь с параметрами модели
        """
        self.env = env
        self.params = params

        # Изначально доступные серверы (каждый сервер - отдельный ресурс)
        self.num_servers = params["num_servers"]
        self.servers = [
            simpy.Resource(env, capacity=1) for _ in range(self.num_servers)
        ]

        # Метрики
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.latency = []  # Список задержек для вычисления средней
        self.available_servers = (
            self.num_servers
        )  # Текущее количество доступных серверов

        # Запуск генератора запросов
        self.env.process(self.generate_requests())
        self.env.process(self.server_failures())

    def random_value(self, distribution, **kwargs):
        """
        Генерация случайного значения в зависимости от распределения.
        :param distribution: название распределения (str)
        :param kwargs: параметры распределения
        """
        if distribution == "exponential":
            return random.expovariate(kwargs.get("rate", 1))
        elif distribution == "uniform":
            return random.uniform(kwargs.get("low", 0), kwargs.get("high", 1))
        elif distribution == "normal":
            return max(
                0, random.gauss(kwargs.get("mean", 0), kwargs.get("std", 1))
            )  # Задержки не могут быть отрицательными
        elif distribution == "custom":
            return random.choice(kwargs.get("values", [1]))
        else:
            raise ValueError("Unsupported distribution")

    def process_request(self, request_id):
        """Обработка одного запроса."""
        arrival_time = self.env.now  # Время поступления запроса

        try:
            # Поиск первого доступного сервера
            server = None
            for s in self.servers:
                if len(s.users) == 0:  # Если сервер свободен
                    server = s
                    break

            if server is None:
                # Если нет свободных серверов, запрос отклоняется
                self.failed_requests += 1
                return

            with server.request() as req:
                # Ожидание, пока сервер не освободится
                yield req
                # Обработка запроса
                processing_time = self.random_value(
                    self.params["server_processing_time_distribution"],
                    mean=self.params["server_processing_time"],
                    std=self.params.get("server_processing_time_std", 0.1),
                    low=0.1,
                    high=self.params["server_processing_time"] * 2,
                )
                yield self.env.timeout(processing_time)

                # Успешно обработан запрос
                self.completed_requests += 1
                # Задержка = время обработки + время ожидания
                latency = self.env.now - arrival_time
                self.latency.append(latency)

        except simpy.Interrupt:
            # Обработка прерывания из-за сбоя сервера
            self.failed_requests += 1

    def generate_requests(self):
        """Генерация запросов с учетом распределения."""
        while True:
            self.total_requests += 1
            request_id = self.total_requests

            # Интервал между запросами
            interarrival_time = self.random_value(
                self.params["request_rate_distribution"],
                rate=self.params["request_rate"],
                mean=1 / self.params["request_rate"],
                std=0.1,
                low=0.1,
                high=1 / self.params["request_rate"] * 2,
            )
            yield self.env.timeout(interarrival_time)

            # Добавление запроса в систему
            self.env.process(self.process_request(request_id))

    def server_failures(self):
        """Симуляция отказов серверов."""
        while True:
            # Время до следующего сбоя
            time_to_failure = self.random_value(
                self.params["failure_rate_distribution"],
                rate=self.params["failure_rate"],
                mean=1 / self.params["failure_rate"],
                std=0.1,
                low=0.1,
                high=1 / self.params["failure_rate"] * 2,
            )
            yield self.env.timeout(time_to_failure)

            # Выбор случайного сервера для отключения
            server = random.choice(self.servers)
            if len(server.users) == 0:  # Если сервер не используется
                server._capacity = 0  # Сервер выходит из строя
                self.available_servers -= 1
                # Время до восстановления
                recovery_time = self.random_value(
                    self.params["recovery_time_distribution"],
                    rate=self.params["recovery_rate"],
                    mean=1 / self.params["recovery_rate"],
                    std=0.1,
                    low=0.1,
                    high=1 / self.params["recovery_rate"] * 2,
                )
                yield self.env.timeout(recovery_time)
                server._capacity = 1  # Восстановление сервера
                self.available_servers += 1

    def get_metrics(self):
        """Получение метрик после завершения симуляции."""
        avg_latency = sum(self.latency) / len(self.latency) if self.latency else 0
        return {
            "total_requests": self.total_requests,
            "completed_requests": self.completed_requests,
            "failed_requests": self.failed_requests,
            "avg_latency": avg_latency,
            "available_servers": self.available_servers,
        }
