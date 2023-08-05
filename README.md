# Example SystemRDL Generator

Using the python package 'systemrdl-compiler' we create example programs that
generates register representations in SystemVerilog and other language from a
SystemRDL configuration file.

## SystemRDL Standard

The SystemRDL configuration files should follow the following [standard](https://www.accellera.org/images/downloads/standards/systemrdl/SystemRDL_2.0_Jan2018.pdf).

## Perquisites

The following packages need to be installed to get the generators working.

```bash
python3 -m pip install systemrdl-compiler
```

## Usage

To generate the desired language output simply select the script and pass the
SystemRDL file in as an argument.

```bash
./generate_cc.py cfg_registers.rdl
./generate_py.py cfg_registers.rdl
./generate_sv.py cfg_registers.rdl
./generate_vhd.py cfg_registers.rdl
```

### SystemVerilog Output

The SystemVerilog output is a header file that can be included into any
SystemVerilog file. The contents of the SystemVerilog header is a number of
'localparams'. The first 'localparam' contains all registers within the top
'addrmap' and any inner 'regfile' nodes so long as those 'regfile' nodes are
not arrays. Any 'regfile' arrays generate two 'localparams', the first
containing the start/offset address of the array segment and the second the
registers within the array section but relative to the segments start/offset
address.

### VHDL Output

The VHDL output file contains a package that can be used/included into a VHDL
module. The body of the VHDL package is a number of 'constant'. The first
'constant' contains all registers within the top 'addrmap' and any inner
'regfile' nodes so long as those 'regfile' nodes are not arrays. Any 'regfile'
arrays generate two 'constants', the first containing the start/offset address
of the array segment and the second the registers within the array section but
relative to the segments start/offset address.

### Python Output

The Python output is a package that can be imported into a Python program. The
contents of the package are all the registers within the top 'addrmap' and any
inner 'regfile' nodes so long as those 'regfile' nodes are not arrays. Any
'regfile' arrays will generate an inner class that has the arrays registers
with addresses relative to the start/offset of the arrays segment. The inner
classes also have three static methods, the 'start' method will return the
start address of an array segment whose segments position is passed into the
method as an argument. The 'repeat' method will return how many array segments
there are and the 'stride' method returns the size of the array segment.

### C++ Output

The C++ output is a header file that can be included into any C++ program. The
contents of the C++ header is a namespace containing all the registers within
the top 'addrmap' and any inner 'regfile' nodes so long as those 'regfile'
nodes are not arrays. Any 'regfile' arrays generate a nested namespace that
define the arrays registers but whose addresses are relative to the segments
start/offset address. This nested namespace also define three functions, the
'start' function will return the start address of an array segment whose
segments position is passed into the function as an argument. The 'repeat'
function will return how many array segments there are and the 'stride'
function returns the size of the array segment.

## Limitations

These generators have many limitations, some of which are listed below.

* All usable register (excluding 'RFU') must have a unique name.
* Register fields are ignored by the generators.
* Defining registers within a 'regfile' (except arrays) does not affect structure.
