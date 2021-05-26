# cpu.py - designing a single-cycle CPU in PyRTL

import pyrtl

# Initialize memblocks 
i_mem = pyrtl.MemBlock(32, addrwidth=32, name='i_mem', max_read_ports=2,
        max_write_ports=4, asynchronous=False, block=None)  # will hold each instruction as hex
d_mem = pyrtl.MemBlock(32, addrwidth=32, name='d_mem', max_read_ports=2,
        max_write_ports=4, asynchronous=True, block=None)  # holds data memory
rf    = pyrtl.MemBlock(32, addrwidth=32, name='rf', max_write_ports=2,
        max_write_ports=4, asynchronous=True, block=None)  # holds register memory

def decode(instruction):
    """
        decodes instructions
    """
    op = pyrtl.WireVector(6, 'op')
    rs = pyrtl.WireVector(5, 'rs')
    rt = pyrtl.WireVector(5, 'rt')
    rd = pyrtl.WireVector(5, 'rd')
    sh = pyrtl.WireVector(5, 'sh')
    func = pyrtl.WireVector(6, 'func')
    imm = pyrtl.WireVector(16, 'imm')  # for I-type 
    addr = pyrtl.WireVector(26, 'addr')  # for J-type instruct

    func <<= data[:6]
    sh <<= data[6:11]
    rd <<= data[11:16]
    rt <<= data[16:21]
    rs <<= data[21:26]
    op <<= data[26:]
    addr <<= data[:26]
    imm <<= data[:16]

    return op,rs,rt,rd,sh,func,imm,addr


def alu():
    """
        performs operations
    """

def controller(op, func):
    """
        returns 1-3-bit wirevectors of control signals
        used for telling hardware components what to do
    """
 
    reg_dst = pyrtl.WireVector(1, 'reg_dst')
    branch = pyrtl.WireVector(1, 'branch')
    reg_write = pyrtl.WireVector(1, 'reg_write')
    alu_src = pyrtl.WireVector(2, 'alu_src')
    mem_write = pyrtl.WireVector(1, 'mem_write')
    mem_to_reg = pyrtl.WireVector(1, 'mem_to_reg')
    alu_op = pyrtl.WireVector(3, 'alu_op')

    # get control signals as 10-bit wirevector of control sigs -> hex
    control_signals = pyrtl.WireVector(10, 'control_signals')
    with pyrtl.conditional_assignment:
        with op == 0:
            with func == 0x20:
                control_signals |= 0x280
            # ...
        # ...

    # extract control signals
    alu_op <<= control_signals[0:3]
    mem_to_reg <<= control_signals[3]
    mem_write <<= control_signals[4]
    alu_src <<= control_signals[5:7]
    reg_write <<= control_signals[7]
    branch <<= control_signals[8]
    reg_dst <<= control_signals[9]

    return reg_dst,branch,reg_write,alu_src,mem_write,mem_toreg,alu_op

def reg_read():
    """
        read values from register
    """

def pc_update(pc, branch, jump_addr):
    """
        Increments pc address, since i_mem/d_mem = word addressable
        pc_addr: a register holding the address of current instruction
        branch: control signal, whether pc to jump to branch addr or not
        jump_addr: 16-bit relative address of instruction to jump to if branch needed 
        
        if branch instruction: pc goes to that instruct
        else: pc increments by 1
    """
    pc_next = pyrtl.WireVector(32)  # this will be the next pc value
    pc_incr = pyrtl.WireVector(32)  # wire after pc is incremented
    pc_branch = pyrtl.WireVector(32)  # wire after branch jump
    pc_incr <<= pc + 1  # always start by incrementing pc to next address
    pc_branch <<= jump_addr.sign_extended(32)  # included pyrtl function

    # use a mux w/ control-sig branch as input to decide if jump needed
    with pyrtl.conditional_assignment:
        with branch == 0:
            pc_next |= pc_incr
        with branch == 1:
            pc_next |= pc_branch

    return pc_next

def write_back():
    # writes to memory, for store word
    raise NotImplementedError

# These functions implement smaller portions of the CPU design. A 
# top-level function is required to bring these smaller portions
# together and finish your CPU design. Here you will instantiate 
# the functions, i.e., build hardware, and orchestrate the various 
# parts of the CPU together. 

def top():

    # initialize register input/outputs

    # initialize program counter (pc): holds word address of current instruction
    pc = pyrtl.Register(32)

    # get instructions by pc
    instruction = pyrtl.WireVector(32, 'instruction')
    instruction <<= i_mem[pc]

    # decode instructions
    op,rs,rt,rd,sh,func,imm,addr = decode(instruction)
    
    # get control signals
    reg_dst,branch,reg_write,alu_src,mem_write,mem_toreg,alu_op = controller(op,func)

    # initialize register ports reg_read() i think

    # pass instructions through alu

    # write_back()

    # increment pc
    pc.next <<= pc_update(pc, branch, immed)
    

if __name__ == '__main__':

    """

    Here is how you can test your code.
    This is very similar to how the autograder will test your code too.

    1. Write a MIPS program. It can do anything as long as it tests the
       instructions you want to test.

    2. Assemble your MIPS program to convert it to machine code. Save
       this machine code to the "i_mem_init.txt" file.
       You do NOT want to use QtSPIM for this because QtSPIM sometimes
       assembles with errors. One assembler you can use is the following:

       https://alanhogan.com/asu/assembler.php

    3. Initialize your i_mem (instruction memory).

    4. Run your simulation for N cycles. Your program may run for an unknown
       number of cycles, so you may want to pick a large number for N so you
       can be sure that the program so that all instructions are executed.

    5. Test the values in the register file and memory to make sure they are
       what you expect them to be.

    6. (Optional) Debug. If your code didn't produce the values you thought
       they should, then you may want to call sim.render_trace() on a small
       number of cycles to see what's wrong. You can also inspect the memory
       and register file after every cycle if you wish.

    Some debugging tips:

        - Make sure your assembly program does what you think it does! You
          might want to run it in a simulator somewhere else (SPIM, etc)
          before debugging your PyRTL code.

        - Test incrementally. If your code doesn't work on the first try,
          test each instruction one at a time.

        - Make use of the render_trace() functionality. You can use this to
          print all named wires and registers, which is extremely helpful
          for knowing when values are wrong.

        - Test only a few cycles at a time. This way, you don't have a huge
          500 cycle trace to go through!

    """

    # Start a simulation trace
    sim_trace = pyrtl.SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):
        sim.step({})

    # Use render_trace() to debug if your code doesn't work.
    # sim_trace.render_trace()

    # You can also print out the register file or memory like so if you want to debug:
    # print(sim.inspect_mem(d_mem))
    # print(sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
    assert(sim.inspect_mem(d_mem)[0] == 10)
    assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    print('Passed!')
