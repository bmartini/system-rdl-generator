#!/usr/bin/env python3


import sys
from pathlib import Path
from typing import Dict, List

from systemrdl import RDLCompileError, RDLCompiler
from systemrdl.node import AddressableNode, RegfileNode

processed: List[AddressableNode] = []


def _collect_registers(node: AddressableNode, offset: int) -> Dict[int, str]:
    registers = {}

    # add the registers of the current node
    for reg in node.registers():
        if not (reg in processed):
            processed.append(reg)
            if str(reg.inst_name) != "RFU":
                addr = int(offset + node.raw_address_offset + reg.raw_address_offset)
                registers[addr] = str(reg.inst_name)

    # flatten the register space and include any registers in children nodes that are not arrays
    for child in node.children():
        if isinstance(child, RegfileNode):
            if not (child in processed):
                if not child.is_array:
                    processed.append(child)
                    registers = {**registers, **_collect_registers(child, offset)}

    return registers


def _generate_system_verilog(node: AddressableNode, alignment: int) -> str:
    contents = ""

    # create localparam of the top nodes
    registers = _collect_registers(node, 0)
    if registers:
        contents = "    localparam\n"
        for addr, name in sorted(registers.items()):
            contents = contents + f"        {name} = {int(addr / alignment)},\n"
        contents = contents[:-2] + ";\n"

    # create localparam out of register array nodes
    for child in node.children():
        if isinstance(child, RegfileNode):
            if not (child in processed):
                if child.is_array:
                    processed.append(child)
                    start = int(child.raw_address_offset)
                    repeat = int(child.array_dimensions[0])
                    stride = int(child.array_stride)

                    # create array offset localparam
                    contents = contents + f"\n    localparam [({repeat}*32)-1:0] {child.inst_name}_OFFSET = {{\n"
                    for x in range(repeat, 0, -1):
                        contents = contents + f"        32'd{int((start + ((x - 1) * stride)) / alignment)},\n"
                    contents = contents[:-2] + "\n    };\n"

                    # create array register localparam
                    registers = _collect_registers(child, -start)
                    if registers:
                        contents = contents + "\n    localparam\n"
                        for addr, name in sorted(registers.items()):
                            contents = contents + f"        {name} = {int(addr / alignment)},\n"
                        contents = contents[:-2] + ";\n"

    return contents


if __name__ == "__main__":
    """Generates SystemVerilog code from a single SystemRDL file."""

    # the first argument must be the SystemRDL file
    system_rdl = sys.argv[1]
    if Path(system_rdl).suffix != ".rdl":
        sys.exit(1)

    # parse SystemRDL config file and produce a node tree
    rdlc = RDLCompiler()
    try:
        rdlc.compile_file(system_rdl)
        root = rdlc.elaborate()
    except RDLCompileError:
        sys.exit(1)

    # name of the root node becomes the file name of the SystemVerilog header
    filename = root.top.inst_name
    alignment = root.top.get_property('alignment', default=1)

    # parse SystemRDL node tree and generate SystemVerilog code
    with open(f'{filename}.svh', 'w') as code:
        code.write(_generate_system_verilog(root.top, alignment))
