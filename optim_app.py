import streamlit as st
import simpy
import random
import pandas as pd

from model import WebServiceModel


def run_simulation(env_params, simulation_params):
    """
    Запуск одной симуляции с заданными параметрами.
    :param env_params: параметры окружения (например, время моделирования).
    :param simulation_params: параметры симуляции (например, количество серверов).
    :return: результаты метрик после моделирования.
    """
    env = simpy.Environment()
    model = WebServiceModel(env, simulation_params)
    env.run(until=env_params["simulation_time"])
    return model.get_metrics()


def optimize_simulation(env_params, param_ranges, num_experiments):
    """
    Оптимизационный эксперимент.
    :param env_params: фиксированные параметры окружения.
    :param param_ranges: диапазоны параметров для оптимизации.
    :param num_experiments: количество экспериментов.
    :return: лучшие параметры и их метрики.
    """
    best_params = None
    best_metrics = None
    all_results = []

    for _ in range(num_experiments):
        # Генерация случайных параметров в пределах диапазона
        simulation_params = {
            "num_servers": random.randint(
                param_ranges["num_servers"][0], param_ranges["num_servers"][1]
            ),
            "request_rate": random.uniform(
                param_ranges["request_rate"][0], param_ranges["request_rate"][1]
            ),
            "failure_rate": random.uniform(
                param_ranges["failure_rate"][0], param_ranges["failure_rate"][1]
            ),
            "server_processing_time": random.uniform(
                param_ranges["server_processing_time"][0],
                param_ranges["server_processing_time"][1],
            ),
            "recovery_rate": random.uniform(
                param_ranges["recovery_rate"][0], param_ranges["recovery_rate"][1]
            ),
            "request_rate_distribution": "exponential",
            "server_processing_time_distribution": "normal",
            "failure_rate_distribution": "exponential",
            "recovery_time_distribution": "exponential",
        }

        # Запуск симуляции
        metrics = run_simulation(env_params, simulation_params)

        # Сохранение результатов
        all_results.append({"params": simulation_params, "metrics": metrics})

        # Поиск лучшей конфигурации (например, минимизация средней задержки)
        if best_metrics is None or metrics["avg_latency"] < best_metrics["avg_latency"]:
            best_metrics = metrics
            best_params = simulation_params

    return best_params, best_metrics, all_results


def app():
    st.title("Оптимизация высоконагруженного веб-сервиса")

    # Параметры окружения
    simulation_time = st.number_input("Время симуляции (сек)", value=100, step=10)
    num_experiments = st.number_input(
        "Количество экспериментов для оптимизации", value=50, step=5
    )

    # Диапазоны параметров для оптимизации
    st.subheader("Диапазоны параметров")
    num_servers_range = st.slider("Количество серверов", 1, 100, (1, 10))
    request_rate_range = st.slider("Интенсивность запросов", 0.1, 10.0, (0.5, 5.0))
    failure_rate_range = st.slider("Интенсивность отказов", 0.01, 1.0, (0.05, 0.2))
    server_processing_time_range = st.slider(
        "Время обработки на сервере (среднее)", 0.1, 5.0, (0.5, 2.0)
    )
    recovery_rate_range = st.slider(
        "Интенсивность восстановления серверов", 0.01, 1.0, (0.1, 0.5)
    )

    # Оптимизационный эксперимент
    if st.button("Выполнить оптимизацию"):
        st.write("Оптимизация в процессе...")
        env_params = {"simulation_time": simulation_time}
        param_ranges = {
            "num_servers": num_servers_range,
            "request_rate": request_rate_range,
            "failure_rate": failure_rate_range,
            "server_processing_time": server_processing_time_range,
            "recovery_rate": recovery_rate_range,
        }

        best_params, best_metrics, all_results = optimize_simulation(
            env_params, param_ranges, num_experiments
        )

        # Отображение результатов
        st.subheader("Оптимальные параметры")
        st.json(best_params)
        st.subheader("Результаты метрик для оптимальных параметров")
        st.json(best_metrics)

        # Сохранение всех результатов в таблице
        results_df = pd.DataFrame(
            [
                {
                    "num_servers": res["params"]["num_servers"],
                    "request_rate": res["params"]["request_rate"],
                    "failure_rate": res["params"]["failure_rate"],
                    "server_processing_time": res["params"]["server_processing_time"],
                    "recovery_rate": res["params"]["recovery_rate"],
                    "avg_latency": res["metrics"]["avg_latency"],
                    "failed_requests": res["metrics"]["failed_requests"],
                    "completed_requests": res["metrics"]["completed_requests"],
                }
                for res in all_results
            ]
        )

        st.subheader("Результаты всех экспериментов")
        st.dataframe(results_df)

        # Визуализация
        st.subheader("Графики метрик")

        # График средней задержки
        st.write("Средняя задержка (avg_latency)")
        st.scatter_chart(results_df["avg_latency"])

        # График неудачных запросов
        st.write("Неудачные запросы (failed_requests)")
        st.scatter_chart(results_df["failed_requests"])


# Запуск приложения Streamlit
if __name__ == "__main__":
    app()
