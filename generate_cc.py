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


def _generate_c_plus_plus(node: AddressableNode, alignment: int, filename: str) -> str:
    contents = "#pragma once\n\n"
    contents = contents + f"namespace {filename} {'{'}\n"

    # create localparam of the top nodes
    registers = _collect_registers(node, 0)
    if registers:
        for addr, name in sorted(registers.items()):
            contents = contents + f"constexpr auto {name}{'{'}{int(addr / alignment)}{'}'};\n"

    # create localparam out of register array nodes
    for child in node.children():
        if isinstance(child, RegfileNode):
            if not (child in processed):
                if child.is_array:
                    processed.append(child)
                    start = int(child.raw_address_offset)
                    repeat = int(child.array_dimensions[0])
                    stride = int(child.array_stride)

                    contents = contents + "\n"
                    contents = contents + f"namespace {child.inst_name} {'{'}\n"

                    # create array register localparam
                    registers = _collect_registers(child, -start)
                    if registers:
                        for addr, name in sorted(registers.items()):
                            contents = contents + f"constexpr auto {name}{'{'}{int(addr / alignment)}{'}'};\n"

                    contents = contents + "\n"
                    contents = contents + f"int start(int index) {'{'} return {int(start / alignment)} + (index * {int(stride / alignment)}); {'}'}\n"
                    contents = contents + "\n"
                    contents = contents + f"int repeat() {'{'} return {repeat}; {'}'}\n"
                    contents = contents + "\n"
                    contents = contents + f"int stride() {'{'} return {int(stride / alignment)}; {'}'}\n"
                    contents = contents + "\n"
                    contents = contents + f"{'} //'} namespace {child.inst_name}\n"

    contents = contents + f"{'} //'} namespace {filename}\n"

    return contents


if __name__ == "__main__":
    """Generates c++ code from a single SystemRDL file."""

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

    # name of the root node becomes the file name of the c++ header
    filename = root.top.inst_name
    alignment = root.top.get_property('alignment', default=1)

    # parse SystemRDL node tree and generate c++ code
    with open(f'{filename}.hh', 'w') as code:
        code.write(_generate_c_plus_plus(root.top, alignment, filename))
