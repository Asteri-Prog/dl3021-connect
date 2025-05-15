#!/usr/bin/env python3

__all__ = ["DL3000"]

import time


class DL3000(object):
    """
    Rigol DL3000 command wrapper.
    """
    def __init__(self, inst):
        """
        Initialize the DL3000 wrapper with a specific PyVISA resource.
        This class does NOT open the resource, you have to open it for yourself!
        """
        self.inst = inst

    def voltage(self):
        # My DL3021 returns a string like '0.000067\n0'
        return float(self.inst.query(":MEAS:VOLT?").partition("\n")[0])

    def current(self):
        # My DL3021 returns a string like '0.000067\n0'
        return float(self.inst.query(":MEAS:CURR?").partition("\n")[0])

    def power(self):
        # My DL3021 returns a string like '0.000067\n0'
        return float(self.inst.query(":MEAS:POW?").partition("\n")[0])

    def resistance(self):
        return float(self.inst.query(":MEAS:RES?").partition("\n")[0])

    def capability(self):
        return float(self.inst.query(":MEAS:CAP?").partition("\n")[0])

    def watthours(self):
        return float(self.inst.query(":MEAS:WATT?").partition("\n")[0])

    def discharging_time(self):
        return self.inst.query(":MEAS:DISCHARGINGTIME?").partition("\n")[0]

    def set_cc_slew_rate(self, slew):
        # My DL3021 returns a string like '0.000067\n0'
        self.inst.write(f":SOURCE:CURRENT:SLEW {slew}")
    
    def is_enabled(self):
        """
        Enable the electronic load
        Equivalent to pressing "ON/OFF" when the load is ON
        """
        return self.inst.query(":SOURCE:INPUT:STAT?").strip() == "1"

    def enable(self):
        """
        Enable the electronic load
        Equivalent to pressing "ON/OFF" when the load is ON
        """
        self.inst.write(":SOURCE:INPUT:STAT ON")

    def disable(self):
        """
        Disable the electronic load
        Equivalent to pressing "ON/OFF" when the load is ON
        """
        self.inst.write(":SOURCE:INPUT:STAT OFF")

    def set_mode(self, mode="CC"):
        """
        Set the load mode to "CURRENT", "VOLTAGE", "RESISTANCE", "POWER"
        """
        self.inst.write(":SOURCE:FUNCTION {}".format(mode))

    def set_app_mode(self, mode="BATTERY"):
        """
        Set the load input mode to "FIXED", "LIST", "WAVE", "BATTERY"
        """
        self.inst.write(":SOURCE:FUNCTION:MODE {}".format(mode))
    
    import time

    def set_battery_vstop(self, voltage):
        """
        Sets the stop voltage (V_Stop) in BATTERY mode using virtual panel emulation
        
        Args:
            voltage (float): Stop voltage value (e.g., 3.7)
        """
        # Configure delays for different operations
        base_delay=0
        short_delay = base_delay * 0.5  # 0.1s for quick operations
        medium_delay = base_delay       # 0.2s default
        long_delay = base_delay * 2.5   # 0.5s for mode changes
        
        # Enable debug mode for virtual panel
        self.inst.write(":DEBUG:KEY ON")
        time.sleep(short_delay)
        
        # Switch to BATTERY mode if not already active
        self.set_app_mode("BATTERY")
        time.sleep(long_delay)
        
        # Press Third menu key (16) twice to access V_Stop
        self.inst.write(":SYSTEM:KEY 16")
        time.sleep(medium_delay)
        self.inst.write(":SYSTEM:KEY 16")
        time.sleep(long_delay)
        
        # Enter voltage value digit by digit
        voltage_str = f"{voltage:.3f}"  # Format to 3 decimal places
        for char in voltage_str:
            if char == '.':
                self.inst.write(":SYSTEM:KEY 30")  # Decimal point
            elif char.isdigit():
                key_code = 20 + int(char)  # Numeric keys 0-9 (codes 20-29)
                self.inst.write(f":SYSTEM:KEY {key_code}")
            time.sleep(medium_delay)
        
        # Confirm selection (OK key - 41)
        self.inst.write(":SYSTEM:KEY 41")
        time.sleep(medium_delay)
        
        # Disable debug mode
        self.inst.write(":DEBug:KEY OFF")

    def set_cc_vlim(self, vlim=5):
        """
        Sets the voltage limit in CC mode
        """
        self.inst.write(":SOURCE:CURR:VLIM  {}".format(vlim))

    def query_mode(self):
        """
        Get the mode:
        "CC", "CV", "CR", "CP"
        """
        return self.inst.query(":SOURCE:FUNCTION?").strip()

    def set_cc_current(self, current):
        """
        Set CC current limit
        """
        return self.inst.write(":SOURCE:CURRENT:LEV:IMM {}".format(current))

    def set_cp_power(self, power):
        """
        Set CP power limit
        """
        return self.inst.write(":SOURCE:POWER:LEV:IMM {}".format(power))

    def set_cp_ilim(self, ilim):
        """
        Set CP current limit
        """
        return self.inst.query(":SOURCE:POWER:ILIM {}".format(ilim))

    def cc(self, current, activate=True):
        """
        One-line constant-current configuration.
        if activate == True, also turns on the power supply
        """
        self.set_mode("CC")
        self.set_cc_current(current)
        self.enable()
        
    def cp(self, power, activate=True):
        """
        One-line constant-current configuration.
        if activate == True, also turns on the power supply
        """
        self.set_mode("CP")
        self.set_cp_power(power)
        self.enable()

    def reset(self):
        return self.inst.write("*RST")
