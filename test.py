import pymodbus
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

# Modbus server details
SERVER_IP = '192.168.178.140'  # Replace with the actual IP address of your EMS
SERVER_PORT = 502
UNIT_ID = 1
REGISTER_ADDRESS = 301  # Address for the hash of "OpenemsComponent"

def read_register_220():
    try:
        # Initialize Modbus client
        client = ModbusClient(SERVER_IP, port=SERVER_PORT)
        client.connect()

        # Read holding register at address 220 (function code 03)
        result = client.read_holding_registers(REGISTER_ADDRESS, 1, unit=UNIT_ID)

        if not result.isError():
            # Print raw register values for debugging
            print(f'Raw register value: {result.registers[0]}')

            # Decode the response as uint16
            hash_openemscomponent = result.registers[0]

            print(f'Register 220 (Hash of "OpenemsComponent"): {hash_openemscomponent:#06x}')  # Print as hexadecimal
        else:
            print(result)
            print('Error reading register')

        # Close the client
        client.close()
    except Exception as e:
        print(f'Exception occurred: {e}')

if __name__ == '__main__':
    read_register_220()
