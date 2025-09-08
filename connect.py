import pyvisa
from LabInstruments.DL3000 import DL3000
import msvcrt
import time
import csv
from datetime import datetime
import os
import logging

from charts import plot_battery_data

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

def main():
    rm = pyvisa.ResourceManager()
    # Настройка логирования в файл
    run_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(os.path.join(os.getcwd(), "logs"), exist_ok=True)
    log_path = os.path.join(os.getcwd(), f"logs\\connect_run_{run_ts}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("Старт приложения connect.py")
    
    print("Поиск подключенных устройств Rigol DL3000...")
    devices = find_dl3000_devices(rm)
    
    if not devices:
        print("Не найдено ни одного устройства Rigol DL3000")
        return
    
    logging.info(f"Найдено устройств DL3000: {len(devices)}")
    for i, dev in enumerate(devices, 1):
        logging.info(f"Устройство {i}: {dev['idn']} ({dev['resource_str']})")

    device = devices[0]
    print(f"\nПодключаемся к устройству: {device['idn']}")
    
    print("Введите параметры тестируемой батареи:")
    battery_name = input("Имя батареи (например, quallion ql0200i-a): ").strip()
    battery_capacity = input("Заявленная ёмкость, mAh: ").strip()
    vstop_input = input("Vstop, В (по умолчанию 2.5): ").strip()
    cc_input = input("Ток разряда, A (по умолчанию 0.050): ").strip()

    # Значения по умолчанию
    vstop = float(vstop_input) if vstop_input else 2.5
    cc = float(cc_input) if cc_input else 0.050

    # Формируем имя файла для логов
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{battery_name.replace(' ', '_')}_{battery_capacity}mAh_test_{now_str}.csv"
    print(f"Данные будут записываться в файл: {log_filename}")
    
    try:
        inst = DL3000(device['resource'])
        console = ConsoleUpdater()

        inst.reset()
        logging.info("Устройство сброшено к заводским настройкам")
        
        # Устанавливаем необходимые параметры
        inst.set_app_mode("BATTERY")
        inst.set_battery_vstop(vstop)
        inst.set_cc_current(cc)
        logging.info(f"Режим BATTERY, Vstop={vstop} В, Icc={cc} А")
        
        inst.enable()
        logging.info("Устройство включено. Нажмите любую клавишу для остановки...")
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
                timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S') 
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
                
                if vstop >= voltage:
                    break
                
                time.sleep(1)  # Интервал между измерениями
                
        except KeyboardInterrupt:
            pass
        
        # Завершение работы
        inst.disable()
        logging.info("Нагрузка отключена")
        
        # Предлагаем построить графики
        if input("\nПостроить графики? (y/n): ").lower() == 'y':
            plot_battery_data(log_filename, battery_name, battery_capacity)
            logging.info("Построены графики")
        
    except pyvisa.errors.VisaIOError as e:
        err_text = f"Ошибка работы с прибором: {str(e)}"
        print(err_text)
        logging.exception(err_text)
        try:
            CTkMessagebox(option_focus=1, title="Error", message=err_text, icon="cancel")
        finally:
            input("Нажмите Enter для выхода...")
    except Exception as e:
        from CTkMessagebox import CTkMessagebox
        err_text = f"Произошла ошибка: {str(e)}"
        print(err_text)
        logging.exception(err_text)
        try:
            CTkMessagebox(option_focus=1, title="Error", message=err_text, icon="cancel")
        finally:
            input("Нажмите Enter для выхода...")
    finally:
        # Завершение работы
        try:
            if 'inst' in locals() and inst is not None:
                inst.disable()
                logging.info("Нагрузка отключена (finalize)")
                print("\nУстройство отключено")
        except Exception:
            logging.exception("Ошибка при отключении нагрузки")
        
        # Закрываем соединение
        try:
            if 'device' in locals() and device and 'resource' in device:
                device['resource'].close()
                logging.info("Соединение с устройством закрыто")
        except Exception:
            logging.exception("Ошибка при закрытии соединения с устройством")

if __name__ == "__main__":
    main()