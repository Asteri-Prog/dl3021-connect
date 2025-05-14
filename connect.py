import pyvisa
from LabInstruments.DL3000 import DL3000
import msvcrt

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
    
    try:
        inst = DL3000(device['resource'])

        inst.reset()
        print("Устройство сброшено к заводским настройкам")
        
        # Устанавливаем необходимые параметры
        inst.set_app_mode("BATTERY")
        inst.set_current_v_limit(3)
        inst.set_cc_current(0.050)
        
        inst.enable()
        print("Устройство включено. Нажмите любую клавишу для остановки...")
        
        # Бесконечный цикл считывания параметров
        try:
            while True:
                # Считываем все доступные параметры
                voltage = inst.voltage()
                current = inst.current()
                power = inst.power()
                resistance = inst.resistance()
                capacity = inst.capability()
                watthours = inst.watthours()
                discharging_time = inst.discharging_time()
                
                # Выводим параметры
                print("\n--- Текущие показания ---")
                print(f"Напряжение: {voltage:.6f} V")
                print(f"Ток: {current:.6f} A")
                print(f"Мощность: {power:.6f} W")
                print(f"Сопротивление: {resistance:.6f} Ω")
                print(f"Ёмкость: {capacity:.6f} Ah")
                print(f"Энергия: {watthours:.6f} Wh")
                print(f"Время разряда: {discharging_time} s")
                
                if msvcrt.kbhit():
                    break

                
        except KeyboardInterrupt:
            pass
        
    except pyvisa.errors.VisaIOError as e:
        print(f"Ошибка работы с прибором: {str(e)}")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        # Завершение работы
        inst.disable()
        print("\nУстройство отключено")
        
        # Закрываем соединение
        device['resource'].close()

if __name__ == "__main__":
    main()