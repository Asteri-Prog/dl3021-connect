import pyvisa
from LabInstruments.DL3000 import DL3000
import msvcrt
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os

class ConsoleUpdater:
    """Класс для обновления строк в консоли"""
    def __init__(self, lines=8):
        self.lines = lines
        self.last_lines = [''] * lines
    
    def update(self, *messages):
        print(f"\033[{self.lines}A", end='')
        for i, msg in enumerate(messages[:self.lines]):
            print(f"\033[K{msg}")
            self.last_lines[i] = msg
            
        for i in range(len(messages), self.lines):
            print("\033[K")

def find_dl3000_devices(resource_manager):
    """Поиск подключенных устройств Rigol DL3000"""
    devices = []
    resources = resource_manager.list_resources()
    
    for resource_str in resources:
        try:
            resource = resource_manager.open_resource(resource_str)
            idn = resource.query('*IDN?').strip()
            if 'RIGOL' in idn and 'DL30' in idn:
                devices.append({
                    'resource_str': resource_str,
                    'idn': idn,
                    'resource': resource
                })
            else:
                resource.close()
        except:
            continue
    
    return devices

def log_to_file(filename, data):
    """Записывает данные в CSV файл"""
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def plot_data(filename):
    """Строит графики из файла с данными"""
    try:
        data = pd.read_csv(filename)
        
        # Создаем фигуру с несколькими графиками
        fig, axes = plt.subplots(3, 1, figsize=(10, 12))
        
        # График напряжения и тока
        axes[0].plot(data['timestamp'], data['voltage'], 'r-', label='Voltage (V)')
        axes[0].set_ylabel('Voltage (V)')
        ax2 = axes[0].twinx()
        ax2.plot(data['timestamp'], data['current'], 'b-', label='Current (A)')
        ax2.set_ylabel('Current (A)')
        axes[0].set_title('Voltage and Current vs Time')
        axes[0].grid(True)
        
        # График мощности
        axes[1].plot(data['timestamp'], data['power'], 'g-')
        axes[1].set_ylabel('Power (W)')
        axes[1].set_title('Power vs Time')
        axes[1].grid(True)
        
        # График ёмкости и энергии
        axes[2].plot(data['timestamp'], data['capacity'], 'm-', label='Capacity (Ah)')
        axes[2].set_ylabel('Capacity (Ah)')
        ax2 = axes[2].twinx()
        ax2.plot(data['timestamp'], data['watthours'], 'c-', label='Energy (Wh)')
        ax2.set_ylabel('Energy (Wh)')
        axes[2].set_title('Capacity and Energy vs Time')
        axes[2].grid(True)
        
        # Форматирование времени на оси X
        for ax in axes:
            ax.xaxis.set_major_locator(plt.MaxNLocator(10))
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Ошибка при построении графиков: {str(e)}")

def main():
    rm = pyvisa.ResourceManager()
    
    print("Поиск подключенных устройств Rigol DL3000...")
    devices = find_dl3000_devices(rm)
    
    if not devices:
        print("Не найдено ни одного устройства Rigol DL3000")
        return
    
    print(f"Найдено устройств: {len(devices)}")
    for i, dev in enumerate(devices, 1):
        print(f"{i}. {dev['idn']} ({dev['resource_str']})")

    device = devices[0]
    print(f"\nПодключаемся к устройству: {device['idn']}")
    
    # Создаем имя файла для логов
    log_filename = f"battery_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"Данные будут записываться в файл: {log_filename}")
    
    try:
        inst = DL3000(device['resource'])
        console = ConsoleUpdater()

        inst.reset()
        print("Устройство сброшено к заводским настройкам")
        
        # Устанавливаем необходимые параметры
        inst.set_app_mode("BATTERY")
        inst.set_battery_vstop(3.3)
        inst.set_cc_current(0.050)
        
        inst.enable()
        print("Устройство включено. Нажмите любую клавишу для остановки...")
        time.sleep(1)  # Даем устройству время на стабилизацию
        
        # Выводим заголовки перед началом цикла
        console.update(
            "--- Текущие показания ---",
            "Напряжение: -",
            "Ток: -",
            "Мощность: -",
            "Сопротивление: -",
            "Ёмкость: -",
            "Энергия: -",
            "Время разряда: -"
        )
        
        # Бесконечный цикл считывания параметров
        try:
            while True:
                if msvcrt.kbhit():
                    break
                
                # Считываем все доступные параметры
                timestamp = datetime.now().strftime('%H:%M:%S')
                voltage = inst.voltage()
                current = inst.current()
                power = inst.power()
                resistance = inst.resistance()
                capacity = inst.capability()
                watthours = inst.watthours()
                discharging_time = inst.discharging_time()
                
                # Формируем данные для записи в файл
                log_data = {
                    'timestamp': timestamp,
                    'voltage': voltage,
                    'current': current,
                    'power': power,
                    'resistance': resistance,
                    'capacity': capacity,
                    'watthours': watthours,
                    'discharging_time': discharging_time
                }
                
                # Записываем данные в файл
                log_to_file(log_filename, log_data)
                
                # Обновляем данные в консоли
                console.update(
                    "--- Текущие показания ---",
                    f"Напряжение: {voltage:.6f} V",
                    f"Ток: {current:.6f} A",
                    f"Мощность: {power:.6f} W",
                    f"Сопротивление: {resistance:.6f} Ω",
                    f"Ёмкость: {capacity:.6f} Ah",
                    f"Энергия: {watthours:.6f} Wh",
                    f"Время разряда: {discharging_time}"
                )
                
                time.sleep(1)  # Интервал между измерениями
                
        except KeyboardInterrupt:
            pass
        
        # Завершение работы
        inst.disable()
        print("\nУстройство отключено")
        
        # Предлагаем построить графики
        if input("\nПостроить графики? (y/n): ").lower() == 'y':
            plot_data(log_filename)
        
    except pyvisa.errors.VisaIOError as e:
        print(f"Ошибка работы с прибором: {str(e)}")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        # Закрываем соединение
        device['resource'].close()

if __name__ == "__main__":
    main()