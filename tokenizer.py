
from re import findall
from typing import Dict, List
from opcodes import *
import numpy as np

STRING_TO_OPCODE_DICT: Dict[str, OpcodeValue] = {
    "clr": SingleOperandOpcodeValue.CLR,
    "inc": SingleOperandOpcodeValue.INC,
    "dec": SingleOperandOpcodeValue.DEC,
    "neg": SingleOperandOpcodeValue.NEG,
    "comp": SingleOperandOpcodeValue.COMP,
    "jmp": SingleOperandOpcodeValue.JMP,
    "jsr": SingleOperandOpcodeValue.JSR,
    "tst": SingleOperandOpcodeValue.TST,
    
    "add": DoubleOperandOpcodeValue.ADD,
    "sub": DoubleOperandOpcodeValue.SUB,
    "move": DoubleOperandOpcodeValue.MOVE,
    "exg": DoubleOperandOpcodeValue.EXG,
    "or": DoubleOperandOpcodeValue.OR,
    "and": DoubleOperandOpcodeValue.AND,
    
    "rts": SpecialInstructionsValue.RTS,
    "dbra": SpecialInstructionsValue.DBRA,
    "sc": SpecialInstructionsValue.SC,
    "cc": SpecialInstructionsValue.cc,
    "halt": SpecialInstructionsValue.HALT,
    
    "beq": BranchOpcodeValue.BEQ,
    "bne": BranchOpcodeValue.BNE,
    "bmi": BranchOpcodeValue.BMI,
    "bpl": BranchOpcodeValue.BPL,
    "bls": BranchOpcodeValue.BLS,
    "bhi": BranchOpcodeValue.BHI,
        
}

STRING_TO_REGISTER_DICT: Dict[str, Register] = {
    "r0": Register.R0,
    "r1": Register.R1,
    "r2": Register.R2,
    "r3": Register.R3,
    
    "ac": Register.R0,
    "x": Register.R1,
    "sp": Register.R2,
    "pc": Register.R3,
}

def get_number(word):
    number = max(
            findall(r"0x[a-fA-F0-9]+", word.lower()),
            findall(r"0b[01]+", word.lower()),
            findall(r"[0-9]+", word.lower())
        )

    if number != '' and number != []:
        number = number[0]
        if number.startswith("0b"):
            number = int(number[2:], 2)
        elif number.startswith("0x"):
            number = int(number[2:], 16)
        else:
            number = int(number)

    return number

def get_addressing_mode(word) -> AddressingMode:
    
    # register addressing mode
    if word.lower() in STRING_TO_REGISTER_DICT.keys():
        return AddressingMode.REGISTER
    
    # is indirect register addressing mode
    if findall(r"^\(\w+\)$", word.lower()) != []:
        return AddressingMode.REGISTER_INDIRECT
    
    # is auto-increment
    if findall(r"^\(\w+\)\+$", word.lower()) != []:
        return AddressingMode.AUTO_INCREMENT
    
    # is auto-decrement
    if findall(r"^-\(\w+\)$", word.lower()) != []:
        return AddressingMode.AUTO_DECREMENT
    
    number = get_number(word)
    
    # is index 
    if (
        findall(r"0x[a-fA-F0-9]\(\w+\)", word.lower()) != []
        or
        findall(r"0b[01]+\(\w+\)", word.lower()) != []
        or
        findall(r"[0-9]+\(\w+\)", word.lower()) != []
        ):
        
        addressing_mode = AddressingMode.INDEX
        addressing_mode.data = number
        return addressing_mode
    
    # is absolute
    elif (
        findall(r"^0x[a-fA-F0-9]+$", word.lower()) != []
        or
        findall(r"^0b[01]+$", word.lower()) != []
        or
        findall(r"^[0-9]+$", word.lower()) != []
        ):
        addressing_mode = AddressingMode.ABSOLUTE
        addressing_mode.data = number
        return addressing_mode
    
    # is immediate
    elif (
        findall(r"^#0x[a-fA-F0-9]+$", word.lower()) != []
        or
        findall(r"^#0b[01]+$", word.lower()) != []
        or
        findall(r"^#[0-9]+$", word.lower()) != []
        ):
        addressing_mode = AddressingMode.IMMEDIATE
        addressing_mode.data = number
        return addressing_mode
    
    print(word)
    return None

def get_register(word, addressing_mode: AddressingMode):
    if (
        addressing_mode == AddressingMode.ABSOLUTE
        or
        addressing_mode == AddressingMode.IMMEDIATE
    ):
        return Register.NONE
    registers = STRING_TO_REGISTER_DICT.keys()
    if (
        addressing_mode == AddressingMode.REGISTER
        or
        addressing_mode == AddressingMode.REGISTER_INDIRECT
        or
        addressing_mode == AddressingMode.AUTO_INCREMENT
        or
        addressing_mode == AddressingMode.AUTO_DECREMENT
        ):
        for register in registers:
            if register in word.lower():
                return STRING_TO_REGISTER_DICT[register]
    elif addressing_mode == AddressingMode.INDEX:
        return STRING_TO_REGISTER_DICT[findall(r"\(\w+\)", word)[0][1:-1]]
    
    raise Exception(f"Unable to detect register in word {word}")

def tokenize(text: str):
    
    tokens = []
    
    # split text by lines
    lines: List[str] = text.split("\n")
    
    # split by white space
    words: List[List[str]] = []
    for line in lines:
        line = line.split()
        words.append(line)
    
    for line in words:

        line_iter = iter(line)
        for word in line_iter:
            
            if word.startswith("//"):
                break
            
            # if is origin
            elif word.lower() == "origin":
                address = get_number(next(line_iter))
                tokens.append(Origin(address))
            
            # if is label
            elif findall(":$", word) != []:
                tokens.append(Label(word[:-1], None))
                
            
            # if is opcode
            elif word.lower() in STRING_TO_OPCODE_DICT.keys():
                opcode = STRING_TO_OPCODE_DICT[word.lower()]
                
                # if is single operand opcode
                if isinstance(opcode, SingleOperandOpcodeValue):
                    # next word should be operand
                    destination = next(line_iter)
                    destination_addressing_mode = get_addressing_mode(destination)
                    destination_register = get_register(destination, destination_addressing_mode)
                    
                    tokens.append(SingleOperandOpcode(
                        opcode,
                        destination_addressing_mode,
                        destination_register,
                        destination_addressing_mode.data
                        if destination_addressing_mode.requires_extra_word()  
                        else None
                        )
                    )
                    
                    
                # if is double operand opcode
                elif isinstance(opcode, DoubleOperandOpcodeValue):
                    source = next(line_iter)
                    source_addressing_mode = get_addressing_mode(source)
                    source_register = get_register(source, source_addressing_mode)
                    
                    
                    destination = next(line_iter)
                    destination_addressing_mode = get_addressing_mode(destination)
                    destination_register = get_register(destination, destination_addressing_mode)
                    
                    tokens.append(DoubleOperandOpcode(
                        opcode,
                        source_addressing_mode,
                        destination_addressing_mode,
                        source_register,
                        destination_register,
                        source_addressing_mode.data
                        if source_addressing_mode.requires_extra_word() else None,
                        destination_addressing_mode.data
                        if destination_addressing_mode.requires_extra_word() else None)
                    )
                
                # if is branch opcode
                elif isinstance(opcode, BranchOpcodeValue):
                    label = next(line_iter)
                    tokens.append(BranchOpcode(
                        opcode,
                        None,
                        label
                    ))
                
                # if if halt
                elif isinstance(opcode, SpecialInstructionsValue) and opcode.value == 0:
                    tokens.append(Halt())
            elif (num := get_number(word)) != []:
                tokens.append(num) 
            else:
                raise Exception(f"unable to parse {word} on line {words.index(line)+1}")

    return tokens
                    
def assemble(tokes):
    # get all labels
    address = 0
    labels = []
    for token in tokens:
        if isinstance(token, Origin):
            address = token.address

        if isinstance(token, Label):
            token.address = address
            labels.append(token)
            
        elif isinstance(token, Opcode):
            address += token.get_num_bytes()
    
    # get branch addresses 
    address = 0
    for token in tokens:
        if isinstance(token, Origin):
            address = token.address
            
        if isinstance(token, Opcode):
            address += token.get_num_bytes()
            
        if isinstance(token, BranchOpcode):
            if (label_address := Label.is_in_list(token.label, labels)) is not None:
                offset = label_address - address - 2
                token.offset = offset
            else:
                raise Exception(f"Undefined Label {token.label}")
        
    # assemble into memory
    memory = np.zeros((2**16 - 1,), dtype=np.uint8)
    
    address = 0
    for token in tokens:
        if isinstance(token, Origin):
            address = token.address
            continue
        elif isinstance(token, Label):
            continue
        if isinstance(token, int):
            memory[address] = token
            address += 2
            continue

        token: Opcode
        data = token._generate_hex()
        
        for i, b in enumerate(data):
            memory[address + i] = b
        
        address += len(data)
        
    return memory
        
        
        
if __name__ == "__main__":
    with open("test.asm", "r", encoding="utf-8") as asm:
        text = asm.read()
        

    tokens = tokenize(text)
    memory = assemble(tokens)

    with open("test.txt", 'w', encoding='utf-8') as output_file:
        for address in range(0, len(memory), 2):
            word = (memory[address] << 8) | memory[address+1]
            output_file.write(f"{word:04X}\n")
            
            if np.sum(memory[address+2:]) == 0:
                output_file.write(f"{0000:04}\n")
                break

    


