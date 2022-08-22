# Expanded HACK assembler

This project is part of a university course based on [nand2tetris](https://www.nand2tetris.org/) curriculum. \
Software in this repository is intended for developers that write HACK assembly language code. It expands HACK assembly language, which uses only simple C and A instructions, in a way that a developer can now write several different macro commands that are more intuitive and resemble some high-level language code.

# Macro commands

## Arguments

All macro commands use arguments which can be categorized by two types.
1. **DESTINATION(DST)**\
   Destination arguments are used so that macro command can know where to store the return value of their computation. \
   Destination argument can be a:
   * **Memory location** - @1, @mem_loc, @any, ...
   * **CPU Registry** - M, A, D

2. **SOURCE(SRC)**\
   Source arguments are used so that macro command knows where to find values that will be used in computations. \
   Source argument can be a:
   * **Memory location** - @1, @mem_loc, @any, ...
   * **CPU Registry** - M, A, D
   * **Constant** - Any integer value

## Commands

1. **$LD(*DST*,*SRC*)** \
   Loads value found on *SRC* location and stores in on *DST* location.
3. **$ADD(*DST*,*SRC1*,*SRC2*)** \
   Performs addition of values found on locations *SRC1* and *SRC2* and then stores return value on *DST* location.
3. **$SUB(*DST*,*SRC1*,*SRC2*)** \
   Performs subtraction of values found on locations *SRC1* and *SRC2* and then stores return value on *DST* location.
4. **$SWAP(*DST1*,*DST2*)** \
   Swaps the contents of *DST1* and *DST2* locations.
5. **$AND(*DST*,*SRC1*,*SRC2*)** \
   Performs logical AND on values found on locations *SRC1* and *SRC2* and then stores return value on *DST* location.
6. **$OR(*DST*,*SRC1*,*SRC2*)** \
   Performs logical OR values found on locations *SRC1* and *SRC2* and then stores return value on *DST* location.   
7. **$XOR(*DST*,*SRC1*,*SRC2*)** \
   Performs logical XOR values found on locations *SRC1* and *SRC2* and then stores return value on *DST* location.
8. **$NOT(*DST*,*SRC*)** \
   Performs logical NOT on value found on location *SRC* and then stores return value on *DST* location.
9. **$IF(*SRC*)** \
   Used for conditional branching. Needs to be followed by "{" which opens a code block that needs to be closed with "}" at some point in the code. Code block that follows **$IF(*SRC*)** is executed if the value found on *SRC* location is equal to 0.
10. **$LOOP(*SRC*)** \
   Used for looping. Needs to be followed by "{" which opens a code block that needs to be closed with "}" at some point in the code. Code block that follows **$LOOP(*SRC*)** is repeatedly executed as long as value found on *SRC* location is equal to 0. Checking of value found on *SRC* location is performed iteratively before each execution of code block. \
   \
*NOTE: Nested code blocks are supported.*

# Usage

After writing *Expanded HACK assembly code* you need to translate it using the code from this repository. In order to do so, execute the following command in your terminal: 
```
python parser.py file_path
```
file_path is a command line argument in which you need to specify relative path to .asm file that you want to parse. \
As example, if you were to do so with INS_SORT.asm file from example folder of this repository, you would execute this:
```
python parser.py Example\INS_SORT.asm
```
After code is executed, a .hack file will be created in the same folder as .asm file that you parsed. 

## CPU Emulator

Easy way to execute .hack files is using the software called CPU Emulator that comes as a part of [nand2tetris software package](https://www.nand2tetris.org/software).

## Examples

In this repository, there are two .asm example files in Examples folder. INS_SORT.asm and INS_SORT_MACRO.asm both have same functionality. They perform an *Insertion sort* algorithm on array of integer values located on memory locations from @100 to @109. The difference is in the way they are written. It is a way to show improved readability of code written with macro commands from *Expanded HACK assembly code*.  
