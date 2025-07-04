import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta

def plot_battery_data(filename, battery_name=None, battery_capacity=None):
    try:
        # Попытка извлечь имя и ёмкость из имени файла, если не передано явно
        if battery_name is None or battery_capacity is None:
            base = os.path.basename(filename)
            parts = base.split('_')
            cap_idx = next((i for i, p in enumerate(parts) if 'mAh' in p), None)
            if cap_idx is not None:
                battery_capacity = parts[cap_idx].replace('mAh', '')
                battery_name = ' '.join(parts[:cap_idx])
            else:
                battery_name = battery_name or "?"
                battery_capacity = battery_capacity or "?"

        data = pd.read_csv(filename)
        required_columns = ['timestamp', 'voltage', 'current', 'power', 'capacity', 'watthours', 'resistance']
        if not all(col in data.columns for col in required_columns):
            raise ValueError("Файл не содержит всех необходимых колонок данных")

        # Определяем, содержит ли timestamp дату
        has_date = data['timestamp'].str.contains(r'\d{2}-\d{2}-\d{4}')

        if has_date.any():
            data['datetime'] = pd.to_datetime(data['timestamp'], format='%d-%m-%Y %H:%M:%S')
            
        else:
            base_date = datetime.today().date()
            times = pd.to_datetime(data['timestamp'], format='%H:%M:%S').dt.time
            datetimes = []
            current_date = base_date
            previous_time = times.iloc[0]
            for t in times:
                if t < previous_time:
                    current_date += timedelta(days=1)
                datetimes.append(datetime.combine(current_date, t))
                previous_time = t
            data['datetime'] = pd.to_datetime(datetimes)

        data = data.sort_values('datetime')

        # Метки времени
        time_labels = data['datetime'].dt.strftime('%H:%M:%S')
        if data['datetime'].dt.date.nunique() > 1:
            if has_date.any():
                time_labels = [dt.strftime('%d.%m.%y') + '<br>' + dt.strftime('%H:%M:%S') for dt in data['datetime']]
            else:
                last_date = data['datetime'].iloc[-1].date()
                time_labels = [
                    f"(вчера)<br>{dt.strftime('%H:%M:%S')}" if dt.date() < last_date else dt.strftime('%H:%M:%S')
                    for dt in data['datetime']
                ]

        avg_current = data['current'].mean()
        avg_resistance = data['resistance'].mean()

        fig = make_subplots(
            rows=5, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.07,
            subplot_titles=(
                'Изменение напряжения во времени',
                'Изменение мощности во времени',
                'Ёмкость',
                'Энергия',
                'Сопротивление'
            )
        )

        fig.add_trace(go.Scatter(x=time_labels, y=data['voltage'], name='Напряжение', line=dict(color='red')), row=1, col=1)
        fig.add_trace(go.Scatter(x=time_labels, y=data['power'], name='Мощность', line=dict(color='green')), row=2, col=1)
        fig.add_trace(go.Scatter(x=time_labels, y=data['capacity'], name='Ёмкость', line=dict(color='purple')), row=3, col=1)
        fig.add_trace(go.Scatter(x=time_labels, y=data['watthours'], name='Энергия', line=dict(color='blue')), row=4, col=1)
        fig.add_trace(go.Scatter(x=time_labels, y=data['resistance'], name='Сопротивление', line=dict(color='orange')), row=5, col=1)

        fig.update_yaxes(title_text="Напряжение, В", row=1, col=1)
        fig.update_yaxes(title_text="Мощность, Вт", row=2, col=1)
        fig.update_yaxes(title_text="Ёмкость, мА·ч", row=3, col=1)
        fig.update_yaxes(title_text="Энергия, Вт·ч", row=4, col=1)
        fig.update_yaxes(title_text="Сопротивление, Ом", row=5, col=1)

        for i in range(1, 6):
            fig.update_xaxes(
                title_text="",
                ticks="outside",
                showline=True,
                showticklabels=True,
                nticks=15,
                row=i, col=1
            )

        date_range = data['datetime'].iloc[0].strftime('%d.%m.%Y')
        if data['datetime'].iloc[0].date() != data['datetime'].iloc[-1].date():
            date_range += f" - {data['datetime'].iloc[-1].strftime('%d.%m.%Y')}"

        # Итоговые значения
        final_capacity = data['capacity'].iloc[-1]
        final_watthours = data['watthours'].iloc[-1]
        total_time = data['datetime'].iloc[-1] - data['datetime'].iloc[0]
        total_hours = total_time.total_seconds() / 3600

        # Формируем строку с итогами
        summary = f"Заявленная ёмкость {battery_capacity} мА·ч<br>Итоговая ёмкость: {final_capacity:.3f} мА·ч<br>Итоговая энергия: {final_watthours:.3f} Вт·ч<br>Время работы: {str(total_time).split('.')[0]} (≈ {total_hours:.2f} ч)"

        fig.update_layout(
            title_text=f'<b>Результаты тестирования батареи: {battery_name} ({battery_capacity} мА·ч) ({date_range})</b><br>Средний ток: {avg_current:.3f} А<br>Среднее сопротивление: {avg_resistance:.3f} Ом<br>{summary}',
            height=2200,
            showlegend=False,
            hovermode="x unified",
            margin=dict(t=340, b=80, l=50, r=30),
        )

        print(summary)

        plot_filename = os.path.splitext(filename)[0] + '_interactive.html'
        fig.write_html(plot_filename)
        print(f"Интерактивные графики сохранены в файл: {plot_filename}")
        fig.show()

    except FileNotFoundError:
        print(f"Ошибка: файл {filename} не найден")
    except Exception as e:
        print(f"Ошибка при построении графиков: {str(e)}")


if __name__ == "__main__":
    print("Программа построения графиков данных тестирования батареи")
    print("Пример ввода пути к файлу:")
    print(r"C:\Users\UserName\Desktop\battery_test_20230815_143200.csv")
    print()
    
    while True:
        filepath = input("Введите полный путь к CSV файлу с данными (или 'q' для выхода): ").strip()
        
        if filepath.lower() == 'q':
            break
        
        if not os.path.isfile(filepath):
            print("Ошибка: файл не найден. Попробуйте снова.")
            continue
        
        if not filepath.lower().endswith('.csv'):
            print("Ошибка: файл должен иметь расширение .csv")
            continue
        
        plot_battery_data(filepath)
        break