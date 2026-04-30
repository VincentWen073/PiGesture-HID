import sys
import os
print(sys.path)

import pytest
from src.serial_com import SerialManager

def test_protocol_parsing():
    sm = sm = SerialManager(disable_serial=True)
    
    assert sm.parse_command([0xAA, 0x01, 0x01]) == "START"
    assert sm.parse_command([0xAA, 0x02, 0x02]) == "STOP"
    
    assert sm.parse_command([0xAA, 0x01, 0x05]) == None
    
    assert sm.parse_command([0xBB, 0x01, 0x01]) == None