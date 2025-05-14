import pyvisa
from pyvisa.resources import MessageBasedResource

class VisaLogger(MessageBasedResource):
    def write(self, command):
        print(f"[SENT] {command.strip()}")
        super().write(command)

    def query(self, command):
        print(f"[SENT] {command.strip()}")
        response = super().query(command)
        print(f"[RECV] {response.strip()}")
        return response

rm = pyvisa.ResourceManager()
resource = rm.open_resource('USB0::6833::3601::DL3A204100212::0::INSTR')
instrument = VisaLogger(resource._resource)

instrument.write(":APPL:BATT")
print(instrument.query("*IDN?"))