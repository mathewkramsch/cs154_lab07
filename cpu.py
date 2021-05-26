# cpu.py - designing a single-cycle CPU in PyRTL

import pyrtl

# TODO
# implement write_back()
# finish alu operations for each instruction
# fill out hex for each control sig
# finish contoller control sigs assignment
# watch lab07 video
# look at piazza


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

    func <<= instruction[:6]
    sh <<= instruction[6:11]
    rd <<= instruction[11:16]
    rt <<= instruction[16:21]
    rs <<= instruction[21:26]
    op <<= instruction[26:]
    addr <<= instruction[:26]
    imm <<= instruction[:16]

    return op,rs,rt,rd,sh,func,imm,addr


def alu(rs, rt, immed, alu_op, alu_src):
    """
        does operation
        alu_op: value 1-8 that is mapped to an operation
        alu_operand = alu_src==0? rt : immed
    """
    alu_operand = pyrtl.WireVector(32, 'alu_operand')
    with pyrtl.conditional_assignment:
        with alu_src == 0:
            alu_operand |= rt
        with alu_src == 1:
            alu_operand |= immed

    ADD = rs + alu_operand
    AND = rs & alu_operand
    ADDI = 
    LUI = 
    ORI = 
    SLT = 
    LW = rs + immed
    SW = rs + immed
    BEQ = 

    alu_output = pyrtl.WireVector(32)  # output
    
    with pyrtl.conditional_assignment:
        with alu_op == 0:
            alu_output |= ADD
        with alu_op == 1:
            alu_output |= AND
        with alu_op == 2:
            alu_output |= ADDI
        with alu_op == 3:
            alu_output |= LUI
        with alu_op == 4:
            alu_output|= ORI
        with alu_op == 5:
            alu_output |= SLT
        with alu_op == 6:
            alu_output |= LW 
        with alu_op == 7:
            alu_output |= SW
        with alu_op == 8:
            alu_output |= BEQ

    return alu_output

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
            with func == 0x20:  # ADD
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
        dont actualy think we need this one
    """
    return

def pc_update(pc, branch_sig, rel_addr):
    """
        Increments pc address, since i_mem/d_mem = word addressable
        pc_addr: a register holding the address of current instruction
        branch_sig: control signal, whether pc to jump to branch addr or not
        jump_addr: 16-bit relative address of instruction to jump to if branch needed 
        
        if branch instruction: pc goes to that instruct
        else: pc increments by 1
    """
    pc_next = pyrtl.WireVector(32)  # this will be the next pc value
    pc_incr = pyrtl.WireVector(32)  # wire after pc is incremented
    pc_branch = pyrtl.WireVector(32)  # wire after branch jump
    pc_incr <<= pc + 1  # always start by incrementing pc to next address
    pc_branch <<= rel_addr.sign_extended(32)  # included pyrtl function

    # use a mux w/ control-sig branch as input to decide if jump needed
    with pyrtl.conditional_assignment:
        with branch_sig == 0:
            pc_next |= pc_incr
        with branch_sig == 1:
            pc_next |= pc_branch

    return pc_next

def write_back(alu_result, rt, rd, rt_data, reg_write, reg_dst, mem_write, mem_to_reg):
    """
        writes alu result in place specified by control sigs
        alu_result: result of alu operation
        rt_data: for store word, the word to store in memory
        reg_write: if write to register or not
        reg_dst: specifies register destination to write to
        mem_write: if write to memory or not
        mem_to_reg: if write to register is from memory or not

        writes to either d_mem or rf
    """
    # determine which register to write to
    write_register = pyrtl.WireVector(32, 'write_register')
    with pyrtl.conditional_assignment:
        with reg_dst == 0:
            write_register |= rt
        with reg_dst == 1:
            write_register |= rd
    
    # determine where to get data to write to
    write_data = pyrtl.WireVector(32, 'write_data')
    with pyrtl.conditional_assignment:
        with mem_to_reg == 0:
            write_data |= alu_result
        with mem_to_reg == 1:
            write_data |= d_mem[alu_result]  # here alu_result is an address (lw)

    # write write_data data to write_register register
    with pyrtl.conditional_assignment:
        with reg_write == 1:
            rf[write_register] |= write_data

    # write to d_mem @ addr specified by alu_result (sw)
    with pyrtl.conditional_assignment:
        with mem_write == 1:
            d_mem[alu_result] |= rt_data


def top():
    """
        Top-level function to bring smaller portions together
    """

    # get instructions by pc
    pc = pyrtl.Register(32)
    instruction = pyrtl.WireVector(32, 'instruction')
    instruction <<= i_mem[pc]

    # decode instructions
    op,rs,rt,rd,sh,func,immed,addr = decode(instruction)
        # i dont think need addr, since no jumps implemented
    
    # get control signals
    reg_dst,branch,reg_write,alu_src,mem_write,mem_to_reg,alu_op = controller(op,func)

    # register outputs (value of data at rs/rt
    data0 = pyrtl.WireVector(32, 'data0')  # value of rs register (ie. rs=$t0=2)
    data1 = pyrtl.WireVector(32, 'data1')  # value of rt register
    data0 <<= rf[rs]
    data1 <<= rf[rt]

    # pass instructions through alu
    alu_out = pyrtl.WireVector(32, 'alu_out')
    alu_out <<= alu(data0, data1, alu_op, alu_src)

    # write_back()
    write_back(alu_out, rt, rd, data1, reg_write, reg_dst, mem_write, mem_to_reg)
    
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
