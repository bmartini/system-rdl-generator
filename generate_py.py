#!/usr/bin/env python3


import sys
from pathlib import Path
from systemrdl import RDLCompiler, RDLCompileError
from systemrdl.node import AddressableNode, RegfileNode
from typing import Dict, List

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


def _generate_python(node: AddressableNode, alignment: int) -> str:
    contents = ""

    # create top level registers within package
    registers = _collect_registers(node, 0)
    if registers:
        for addr, name in sorted(registers.items()):
            contents = contents + f"{name} = {int(addr / alignment)}\n"

    # create inner class out of register array nodes
    for child in node.children():
        if isinstance(child, RegfileNode):
            if not (child in processed):
                if child.is_array:
                    processed.append(child)
                    start = int(child.raw_address_offset)
                    repeat = int(child.array_dimensions[0])
                    stride = int(child.array_stride)

                    contents = contents + "\n"
                    contents = contents + f"\nclass {child.inst_name}:\n"
                    # create array register localparam
                    registers = _collect_registers(child, -start)
                    if registers:
                        for addr, name in sorted(registers.items()):
                            contents = contents + f"    {name} = {int(addr / alignment)}\n"

                    contents = contents + "\n"
                    contents = contents + "    @staticmethod\n"
                    contents = contents + "    def start(index: int = 0) -> int:\n"
                    contents = contents + f"        return int({int(start / alignment)} + int(index * {int(stride / alignment)}))\n"
                    contents = contents + "\n"
                    contents = contents + "    @staticmethod\n"
                    contents = contents + "    def repeat() -> int:\n"
                    contents = contents + f"        return {repeat}\n"
                    contents = contents + "\n"
                    contents = contents + "    @staticmethod\n"
                    contents = contents + "    def stride() -> int:\n"
                    contents = contents + f"        return {int(stride / alignment)}\n"

    return contents


if __name__ == "__main__":
    """Generates Python code from a single SystemRDL file."""

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

    # name of the root node becomes the name of the Python package
    package = Path(root.top.inst_name)
    package.mkdir(parents=True, exist_ok=True)
    alignment = root.top.get_property('alignment', default=1)

    # parse SystemRDL node tree and generate Python code
    with open(package / '__init__.py', 'w') as code:
        code.write(_generate_python(root.top, alignment))
