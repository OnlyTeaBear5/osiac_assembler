from enum import Enum
from typing import Dict, List, Tuple

class OpcodeValue(Enum):
    pass


class SingleOperandOpcodeValue(OpcodeValue):
    CLR = 0X01
    INC = 0X02
    DEC = 0X03
    NEG = 0X04
    COMP = 0X05
    JMP = 0X06
    JSR = 0X07
    TST = 0X08


class DoubleOperandOpcodeValue(OpcodeValue):
    ADD = 0X1
    SUB = 0X2
    MOVE  = 0X3
    EXG = 0X4
    OR = 0x5
    AND = 0X6


class BranchOpcodeValue(OpcodeValue):
    BEQ = 0x0092
    BNE = 0x0082
    BMI = 0x0091
    BPL = 0x0081
    BLS = 0x009A
    BHI = 0x00BA


class SpecialInstructionsValue(OpcodeValue):
    RTS = 0x0080
    DBRA = 0x09
    SC = 0x003
    cc = 0x002
    HALT = 0x0000


class AddressingMode(Enum):
    REGISTER = 0
    REGISTER_INDIRECT = 1
    AUTO_INCREMENT = 2
    AUTO_DECREMENT = 3
    INDEX = 4
    ABSOLUTE = 5
    IMMEDIATE = 6


    def requires_extra_word(self):
        return self == AddressingMode.INDEX or self == AddressingMode.ABSOLUTE or self == AddressingMode.IMMEDIATE


class Register(Enum):
    AC = 0
    X = 1
    SP = 2
    PC = 3

    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    
    NONE = 0


class Opcode:
     
    def __init__(self, opcode: OpcodeValue) -> None:
        self.opcode: OpcodeValue = opcode
    
    def _generate_hex(self) -> bytearray:
        pass
    
    def add_to_hex(
        self,
        bytes: bytearray
        ):
        bytes.extend(self._generate_hex())
        
    def get_num_bytes(self):
        return len(self._generate_hex())


class SingleOperandOpcode(Opcode):

    def __init__(
        self,
        opcode: SingleOperandOpcodeValue,
        destination_addressing_mode: AddressingMode,
        register: Register or None = None,
        destination_data: int = None
        ):
        self.opcode: SingleOperandOpcodeValue = opcode
        self.destination_addressing_mode: AddressingMode = destination_addressing_mode
        self.register: Register = register
        self.destination_data: int = destination_data

    def _generate_hex(self) -> bytearray:
        output = bytearray(2)
        output[0] = self.opcode.value
        output[1] = (
            (self.destination_addressing_mode.value << 4 )
            | (self.register.value if self.register != Register.NONE else 0x00)
            )
        if self.destination_addressing_mode.requires_extra_word():
            output.append((self.destination_data & 0xFF00) >> 8)
            output.append(self.destination_data & 0xFF)
        return output


class DoubleOperandOpcode(Opcode):

    def __init__(
        self,
        opcode: DoubleOperandOpcodeValue,
        source_addressing_mode: AddressingMode,
        destination_addressing_mode: AddressingMode,
        source_register: Register or None = None,
        destination_register: Register or None = None,
        source_data: int or None = None,
        destination_data: int or None = None
        ):

        self.opcode: DoubleOperandOpcodeValue = opcode

        self.source_addressing_mode: AddressingMode = source_addressing_mode
        self.destination_addressing_mode: AddressingMode = destination_addressing_mode

        self.source_register: Register = source_register
        self.destination_register: Register = destination_register

        self.source_data: int = source_data
        self.destination_data: int = destination_data

    def _generate_hex(self) -> bytearray:
        output = bytearray(2)
        output[0] = (self.opcode.value << 4) | self.source_addressing_mode.value
        output[1] = (self.destination_addressing_mode.value << 4) | (self.source_register.value << 2) | self.destination_register.value


        if self.source_addressing_mode.requires_extra_word():
            output.append((self.source_data & 0xFF00) >> 8)
            output.append(self.source_data & 0xFF)

        if self.destination_addressing_mode.requires_extra_word():
                output.append((self.destination_data & 0xFF00) >> 8)
                output.append(self.destination_data & 0xFF)
        return output

    def add_to_hex(
        self,
        bytes: bytearray
        ):
        bytes.extend(self._generate_hex())


class BranchOpcode(Opcode):
    
    def __init__(self, opcode: BranchOpcodeValue, offset: int, label):
        
        self.opcode = opcode
        self.offset = offset
        self.label = label
        
    def _generate_hex(self) -> bytearray:
        return bytearray([00, self.opcode.value, (self.offset & 0xFF00) >> 8, self.offset & 0x00FF])
    
    def get_num_bytes(self):
        return 4
    
class Halt(Opcode):
    
    def __init__(self):
        opcode = SpecialInstructionsValue.HALT
    
    def _generate_hex(self) -> bytearray:
        return bytearray([0])
class Label():
    
    def __init__(self, name, address):
        self.name = name
        self.address= address
    
    @staticmethod
    def is_in_list(word, lst) -> None or int:
        for i in lst:
            if isinstance(i, Label) and i.name == word:
                return i.address
        return None
                
 
class Origin(Label):
    
    def __init__(self, address):
        super(Origin, self).__init__("origin", address)
    