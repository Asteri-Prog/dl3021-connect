import pyvisa
from LabInstruments.DL3000 import DL3000

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
    rm = pyvisa.ResourceManager('@py')
    
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
        
        inst.set_mode("CURRENT")
        inst.set_cc_current(0.050)
        print("Установлен режим постоянного тока (CC) с током 50 мА")

        inst.enable()
        print("Открыто")
        
        voltage = inst.voltage()
        print(f"Измеренное напряжение: {voltage} V")

        inst.disable()
        print("Закрыто")
        
    except pyvisa.errors.VisaIOError as e:
        print(f"Ошибка работы с прибором: {str(e)}")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main()