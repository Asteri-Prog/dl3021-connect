import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta
import argparse

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


def plot_nrf_data(filename):
    """Построение графиков из NRF логов (формат: Seconds,Current(A),Voltage(V),Temperature(C))"""
    try:
        # Читаем CSV файл
        data = pd.read_csv(filename)
        
        # Проверяем наличие необходимых колонок
        required_columns = ['Seconds', 'Current(A)', 'Voltage(V)', 'Temperature(C)']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Файл не содержит всех необходимых колонок. Ожидаются: {required_columns}")
        
        # Переименовываем колонки для удобства
        data = data.rename(columns={
            'Seconds': 'seconds',
            'Current(A)': 'current',
            'Voltage(V)': 'voltage',
            'Temperature(C)': 'temperature'
        })
        
        # Сортируем по времени
        data = data.sort_values('seconds')
        
        # Вычисляем время в формате HH:MM:SS для отображения
        total_seconds = data['seconds'].max()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        # Формируем метки времени (в секундах от начала)
        time_labels = [f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}" for s in data['seconds']]
        
        # Вычисляем средние значения
        avg_current = data['current'].mean()
        avg_voltage = data['voltage'].mean()
        avg_temperature = data['temperature'].mean()
        
        # Создаем графики
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(
                'Изменение напряжения во времени',
                'Изменение тока во времени',
                'Изменение температуры во времени'
            )
        )
        
        # График напряжения
        fig.add_trace(
            go.Scatter(
                x=time_labels, 
                y=data['voltage'], 
                name='Напряжение', 
                line=dict(color='red')
            ), 
            row=1, col=1
        )
        
        # График тока
        fig.add_trace(
            go.Scatter(
                x=time_labels, 
                y=data['current'], 
                name='Ток', 
                line=dict(color='blue')
            ), 
            row=2, col=1
        )
        
        # График температуры
        fig.add_trace(
            go.Scatter(
                x=time_labels, 
                y=data['temperature'], 
                name='Температура', 
                line=dict(color='orange')
            ), 
            row=3, col=1
        )
        
        # Настройка осей Y
        fig.update_yaxes(title_text="Напряжение, В", row=1, col=1)
        fig.update_yaxes(title_text="Ток, А", row=2, col=1)
        fig.update_yaxes(title_text="Температура, °C", row=3, col=1)
        
        # Настройка осей X
        for i in range(1, 4):
            fig.update_xaxes(
                title_text="Время",
                ticks="outside",
                showline=True,
                showticklabels=True,
                nticks=15,
                row=i, col=1
            )
        
        # Итоговые значения
        total_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        total_hours = total_seconds / 3600
        
        # Формируем строку с итогами
        summary = f"Общее время: {total_time_str} (≈ {total_hours:.2f} ч)<br>Среднее напряжение: {avg_voltage:.3f} В<br>Средний ток: {avg_current:.6f} А<br>Средняя температура: {avg_temperature:.2f} °C"
        
        # Получаем имя файла для заголовка
        base_name = os.path.basename(filename)
        file_title = os.path.splitext(base_name)[0]
        
        fig.update_layout(
            title_text=f'<b>NRF логи: {file_title}</b><br>{summary}',
            height=1500,
            showlegend=False,
            hovermode="x unified",
            margin=dict(t=200, b=80, l=50, r=30),
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
    parser = argparse.ArgumentParser(
        description='Программа построения графиков данных тестирования батареи',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python charts.py --type 1 --file data.csv
  python charts.py --type 2 --file nrf_data.csv
  python charts.py --type 2 (путь будет запрошен интерактивно)
  python charts.py  (интерактивный режим)
        """
    )
    parser.add_argument(
        '--type', 
        type=str, 
        choices=['1', '2', 'dl3021', 'nrf'],
        help='Тип графика: 1 или dl3021 - DL3021 логи, 2 или nrf - NRF логи'
    )
    parser.add_argument(
        '--file', 
        type=str,
        help='Путь к CSV файлу с данными'
    )
    
    args = parser.parse_args()
    
    # Если аргументы не переданы, используем интерактивный режим
    if args.type is None and args.file is None:
        print("Программа построения графиков данных тестирования батареи")
        print("Пример ввода пути к файлу:")
        print(r"C:\Users\UserName\Desktop\battery_test_20230815_143200.csv")
        print()
        
        # Выбор типа графика
        while True:
            chart_type = input("Выберите тип графика:\n1 - DL3021 логи (по умолчанию)\n2 - NRF логи\nВведите номер (1 или 2 или нажмите Enter для выбора по умолчанию): ").strip()
            
            if chart_type == '1' or chart_type == '':
                plot_func = plot_battery_data
                break
            elif chart_type == '2':
                plot_func = plot_nrf_data
                break
            else:
                print("Ошибка: введите 1 или 2 или нажмите Enter для выбора по умолчанию")
                continue
        
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
            
            plot_func(filepath)
            break
    else:
        # CLI режим
        # Определяем функцию построения графика
        if args.type is None:
            # Если тип не указан, используем DL3021 по умолчанию
            plot_func = plot_battery_data
        elif args.type in ['1', 'dl3021']:
            plot_func = plot_battery_data
        elif args.type in ['2', 'nrf']:
            plot_func = plot_nrf_data
        else:
            print("Ошибка: неверный тип графика. Используйте 1, 2, dl3021 или nrf")
            exit(1)
        
        # Если файл не указан, запрашиваем интерактивно
        if args.file is None:
            print("Программа построения графиков данных тестирования батареи")
            print("Пример ввода пути к файлу:")
            print(r"C:\Users\UserName\Desktop\battery_test_20230815_143200.csv")
            print()
            
            while True:
                filepath = input("Введите полный путь к CSV файлу с данными (или 'q' для выхода): ").strip()
                
                if filepath.lower() == 'q':
                    exit(0)
                
                if not os.path.isfile(filepath):
                    print("Ошибка: файл не найден. Попробуйте снова.")
                    continue
                
                if not filepath.lower().endswith('.csv'):
                    print("Ошибка: файл должен иметь расширение .csv")
                    continue
                
                break
        else:
            filepath = args.file
            
            if not os.path.isfile(filepath):
                print(f"Ошибка: файл {filepath} не найден")
                exit(1)
            
            if not filepath.lower().endswith('.csv'):
                print("Ошибка: файл должен иметь расширение .csv")
                exit(1)
        
        plot_func(filepath)