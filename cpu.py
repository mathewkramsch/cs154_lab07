# cpu.py - designing a single-cycle CPU in PyRTL

import pyrtl
from pyrtl import *

def decode(instruction, instr):
    instr['func'] <<= instruction[:6]
    instr['rd'] <<= instruction[11:16]
    instr['rt'] <<= instruction[16:21]
    instr['rs'] <<= instruction[21:26]
    instr['op'] <<= instruction[26:]
    instr['imm'] <<= instruction[:16]

def controller(op, func, control_sigs):
    # get control signals as 10-bit wirevector of control sigs -> hex
    control_hex = WireVector(10, 'control_hex')
    with conditional_assignment:
        with op == 0:  # R-Type
            with func == 0x20:  # ADD
                control_hex |= 0x280
            with func == 0x24:  # AND
                control_hex |= 0x281
            with func == 0x2A:  # SLT
                control_hex |= 0x284
        with op == 0x8:  # ADDI
            control_hex |= 0x0A0
        with op == 0xF:  # LUI
            control_hex |= 0x0E2
        with op == 0xD:  # ORI
            control_hex |= 0x0C3
        with op == 0x23:  # LW
            control_hex |= 0x0A8
        with op == 0x2B:  # SW
            control_hex |= 0x030
        with op == 0x4:  # BEQ
            control_hex |= 0x105

    control_sigs['alu_op'] <<= control_hex[0:3]
    control_sigs['mem_to_reg'] <<= control_hex[3]
    control_sigs['mem_write'] <<= control_hex[4]
    control_sigs['alu_src'] <<= control_hex[5:7]
    control_sigs['reg_write'] <<= control_hex[7]
    control_sigs['branch'] <<= control_hex[8]
    control_sigs['reg_dst'] <<= control_hex[9]

def alu(input1, input2, alu_op, alu_output, alu_branch_enable):

    ADD = input1 + input2  # shared w/ addi, lw, sw
    AND = input1 & input2
    LUI = input2  # load upper immediate
    ORI = input1 | input2  # or immediate
    SLT = pyrtl.signed_lt(input1,input2)  # SLT = input1<input2? 1:0
    BEQ = input2 - input1  # subtract & compare to zero reg
    
    with conditional_assignment:
        with alu_op == 0: alu_output |= ADD
        with alu_op == 1:
            alu_output |= AND
        with alu_op == 2:
            alu_output |= LUI
        with alu_op == 3:
            alu_output |= ORI
        with alu_op == 4:
            alu_output|= SLT
        with alu_op == 5:
            with BEQ == 0:
                alu_branch_enable |= 1
            with otherwise:
                alu_branch_enable |= 0

def write_back_reg(write_reg, write_data, rf, reg_write):
    with conditional_assignment:  # check if writing to $zero reg (rf[0])
        with write_reg != 0:
            rf[write_reg] |= MemBlock.EnabledWrite(write_data, enable=reg_write)

def write_back_mem(mem_addr, write_data, d_mem, mem_write):
    d_mem[mem_addr] <<= MemBlock.EnabledWrite(write_data, enable=mem_write)

def pc_update(pc, branch_sig, alu_branch_enable, sign_extended_immed):
    pc_next = WireVector(32)  # this will be the next pc value
    with conditional_assignment:  # mux to decide if pc jump needed
        with branch_sig == 0:
            pc_next |= pc + 1
        with branch_sig == 1:  # branch: pc = pc + 1 + sign_extended_immed
            with alu_branch_enable == 0:
                pc_next |= pc + 1
            with alu_branch_enable == 1:
                pc_next |= pc + 1 + sign_extended_immed
    return pc_next

def cpu(pc, i_mem, d_mem, rf, instr, control_sigs):
    # get instruction, decode, set up control signals
    instruction = WireVector(32, 'instruction')
    instruction <<= i_mem[pc]  # get instruction
    decode(instruction, instr)  # populates instr wires
    controller(instr['op'], instr['func'], control_sigs)  # populates control_sigs

    # register outputs (value of data at rs/rt
    rs_data = WireVector(32, 'rs_data')  # value of rs register (ie. rs=$t0=2)
    rt_data = WireVector(32, 'rt_data')  # value of rt register
    rs_data <<= rf[instr['rs']]
    rt_data <<= rf[instr['rt']]

    # pass instructions through alu
    alu_out = WireVector(32, 'alu_out')
    alu_branch_enable = WireVector(32, 'alu_branch_enable')
    input2 = WireVector(32, 'alu_operand')
    with conditional_assignment:  # figure out what to input into alu
        with control_sigs['alu_src'] == 0: 
            input2 |= rt_data
        with control_sigs['alu_src'] == 1:
            input2 |= instr['imm'].sign_extended(32)
        with control_sigs['alu_src'] == 2:
            input2 |= instr['imm'].zero_extended(32)  # for ori
        with control_sigs['alu_src'] == 3:
            input2 |= shift_left_logical(instr['imm'].zero_extended(32), Const(16))  # for lui
    alu(rs_data, input2, control_sigs['alu_op'], alu_out, alu_branch_enable)

    # determine which register to write to
    write_register = WireVector(32, 'write_register')
    with conditional_assignment:
        with control_sigs['reg_dst'] == 0:
            write_register |= instr['rt']
        with control_sigs['reg_dst'] == 1:
            write_register |= instr['rd']
    
    # determine where to get data to write to
    write_data_reg = WireVector(32, 'write_data')
    with conditional_assignment:
        with control_sigs['mem_to_reg'] == 0:
            write_data_reg |= alu_out
        with control_sigs['mem_to_reg'] == 1:
            write_data_reg |= d_mem[alu_out]  # here alu_result is an address (lw)
    
    write_back_reg(write_register, write_data_reg, rf, control_sigs['reg_write'])
    write_back_mem(alu_out, rt_data, d_mem, control_sigs['mem_write'])
    
    # increment pc
    pc.next <<= pc_update(pc, control_sigs['branch'], alu_branch_enable, instr['imm'].sign_extended(32))
    
########################################################################

# Initialize memblocks 
i_mem = MemBlock(32, addrwidth=32, name='i_mem')  # will hold each instruction as hex
d_mem = MemBlock(32, addrwidth=32, name='d_mem', asynchronous=True)  # holds data memory
rf    = MemBlock(32, addrwidth=32, name='rf', asynchronous=True)  # holds register memory

# get instructions by pc
pc = Register(32)

instr = {  # instruction wires
        'op' : WireVector(6, 'op'),
        'rs' : WireVector(5, 'rs'),
        'rt' : WireVector(5, 'rt'),
        'rd' : WireVector(5, 'rd'),
        'func' : WireVector(6, 'func'),
        'imm' : WireVector(16, 'imm')  # for I-type 
}

control_sigs = {  # control signal wires
        'reg_dst' : WireVector(1, 'reg_dst'),
        'branch' : WireVector(1, 'branch'),
        'reg_write' : WireVector(1, 'reg_write'),
        'alu_src' : WireVector(2, 'alu_src'),
        'mem_write' : WireVector(1, 'mem_write'),
        'mem_to_reg' : WireVector(1, 'mem_to_reg'),
        'alu_op' : WireVector(3, 'alu_op')
}

cpu(pc, i_mem, d_mem, rf, instr, control_sigs)

########################################################################

if __name__ == '__main__':

    # Start a simulation trace
    sim_trace = SimulationTrace()

    # Initialize the i_mem with your instructions.
    i_mem_init = {}
    with open('i_mem_init.txt', 'r') as fin:
        i = 0
        for line in fin.readlines():
            i_mem_init[i] = int(line, 16)
            i += 1

    sim = Simulation(tracer=sim_trace, memory_value_map={
        i_mem : i_mem_init
    })

    # Run for an arbitrarily large number of cycles.
    for cycle in range(500):  # make this 500
        sim.step({})

    # Use render_trace() to debug if your code doesn't work.
    # sim_trace.render_trace(symbol_len=6)

    # You can also print out the register file or memory like so if you want to debug:
    print('d_mem:', sim.inspect_mem(d_mem))
    print('rf:', sim.inspect_mem(rf))

    # Perform some sanity checks to see if your program worked correctly
    #assert(sim.inspect_mem(d_mem)[0] == 10)
    #assert(sim.inspect_mem(rf)[8] == 10)    # $v0 = rf[8]
    #print('Passed!')
