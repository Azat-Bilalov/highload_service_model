import time
import streamlit as st
import simpy
import pandas as pd

# Импорт модели
from model import WebServiceModel


# Функция для запуска симуляции и передачи данных в реальном времени
def run_simulation(params, simulation_time, update_interval, time_scale):
    """Запускает симуляцию с использованием ускорения времени."""
    env = simpy.Environment()
    model = WebServiceModel(env, params)

    results = []
    last_update = 0

    # Запуск симуляции
    for t in range(simulation_time + 1):
        env.run(until=t + 1)

        # Сохраняем метрики каждые update_interval секунд
        if t - last_update >= update_interval:
            metrics = model.get_metrics()
            metrics["time"] = t
            results.append(metrics)
            last_update = t

            # Эмуляция реального времени с ускорением
            time.sleep(1 / time_scale)  # Ускоряем симуляцию

            # Передаем текущие метрики для отображения
            yield metrics

    # Финальные метрики
    final_metrics = model.get_metrics()
    final_metrics["time"] = simulation_time
    results.append(final_metrics)

    return pd.DataFrame(results)


# Интерфейс Streamlit
st.title("Моделирование высоконагруженного веб-сервиса")

# Параметры модели
st.sidebar.header("Параметры модели")
num_servers = st.sidebar.slider("Количество серверов", 1, 50, 10)
server_processing_time = st.sidebar.slider(
    "Среднее время обработки запроса (сек)", 0.1, 5.0, 1.0, 0.1
)
queue_timeout = st.sidebar.slider("Таймаут ожидания в очереди (сек)", 1, 30, 5)
request_rate = st.sidebar.slider("Интенсивность запросов (запросов/сек)", 1, 100, 10)
failure_rate = st.sidebar.slider(
    "Вероятность отказа сервера (от 0 до 1)", 0.0, 1.0, 0.01, 0.01
)
recovery_rate = st.sidebar.slider("Время восстановления сервера (сек)", 1, 60, 10)

simulation_time = st.sidebar.slider("Время моделирования (сек)", 10, 300, 60)
update_interval = st.sidebar.slider("Интервал обновления данных (сек)", 1, 10, 5)

# Параметры времени
st.sidebar.header("Ускорение времени")
time_scale = st.sidebar.slider("Масштаб времени (1 = реальное время)", 0.1, 10.0, 1.0)

# Выбор распределений
st.sidebar.header("Распределения параметров")
request_rate_distribution = st.sidebar.selectbox(
    "Распределение интенсивности запросов",
    ["exponential", "uniform", "normal", "custom"],
)
server_processing_time_distribution = st.sidebar.selectbox(
    "Распределение времени обработки запросов",
    ["exponential", "uniform", "normal", "custom"],
)
failure_rate_distribution = st.sidebar.selectbox(
    "Распределение времени между сбоями серверов",
    ["exponential", "uniform", "normal", "custom"],
)
recovery_time_distribution = st.sidebar.selectbox(
    "Распределение времени восстановления серверов",
    ["exponential", "uniform", "normal", "custom"],
)

# Прочие параметры
custom_values = st.sidebar.text_area(
    "Пользовательские значения (для распределения 'custom', через запятую)", ""
)
if custom_values:
    custom_values = list(map(float, custom_values.split(",")))
else:
    custom_values = [1.0]

# Подготовка параметров
params = {
    "num_servers": num_servers,
    "server_processing_time": server_processing_time,
    "queue_timeout": queue_timeout,
    "request_rate": request_rate,
    "failure_rate": failure_rate,
    "recovery_rate": recovery_rate,
    "request_rate_distribution": request_rate_distribution,
    "server_processing_time_distribution": server_processing_time_distribution,
    "failure_rate_distribution": failure_rate_distribution,
    "recovery_time_distribution": recovery_time_distribution,
    "custom_values": custom_values,
}

# Кнопка для запуска симуляции
if st.button("Запустить симуляцию"):
    # Контейнеры для графиков и метрик
    progress_placeholder = st.empty()
    graph_placeholder = st.empty()

    # Запуск симуляции
    st.write("Запуск симуляции...")
    results = []
    for metrics in run_simulation(params, simulation_time, update_interval, time_scale):
        # Обновление прогресса
        progress_placeholder.write(f"Прошло времени: {metrics['time']} сек")

        # Обновление данных
        results.append(metrics)
        df = pd.DataFrame(results)

        # Обновление графика
        graph_placeholder.line_chart(df[["completed_requests", "failed_requests"]])

    st.success("Симуляция завершена!")

    # Итоговые метрики
    final_df = pd.DataFrame(results)
    st.write("Итоговые метрики:")
    st.dataframe(final_df)
    st.download_button(
        label="Скачать результаты",
        data=final_df.to_csv(index=False),
        file_name="simulation_results.csv",
        mime="text/csv",
    )
