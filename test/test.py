# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Edge, with_timeout
from cocotb.utils import get_sim_time

from tqv import TinyQV

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 14 ns (~71.5 MHz)
    clock = Clock(dut.clk, 14, units="ns")
    cocotb.start_soon(clock.start())

    led = dut.uo_out[1]

    # Interact with your design's registers through this TinyQV class.
    # This will allow the same test to be run when your design is integrated
    # with TinyQV - the implementation of this class will be replaces with a
    # different version that uses Risc-V instructions instead of the SPI 
    # interface to read and write the registers.
    tqv = TinyQV(dut)

    # Reset, always start the test by resetting TinyQV
    await tqv.reset()

    dut._log.info("Test project behavior")

    #while await tqv.read_reg(0) == 0:
    #    await ClockCycles(dut.clk, 1)

    # Test register write and read back
    await tqv.write_reg(2, 255)
    assert await tqv.read_reg(2) == 255

    await tqv.write_reg(3, 15)
    assert await tqv.read_reg(3) == 15

    await tqv.write_reg(4, 128)
    assert await tqv.read_reg(4) == 128

    await tqv.write_reg(1, 0x81)

    bitseq = await get_GRB(dut, led)
    dut._log.info(f"Read back {len(bitseq)} bits: {bitseq}")

    await check_led_reset(dut, led)


# read 24 color bits (G / R / B)
async def get_GRB(dut, led):
    bitseq = []

    for i in range(24):
        while led.value == 0:
            await Edge(dut.uo_out)
        t1 = get_sim_time('ns')

        while led.value == 1:
            await Edge(dut.uo_out)
        t2 = get_sim_time('ns')

        pulse_ns = t2-t1
        # check pulse duration
        assert pulse_ns > 300
        assert pulse_ns < 900

        # decode bit
        bitseq.append( 1 if (pulse_ns > 625) else 0 )

    return bitseq

async def check_led_reset(dut, led):
        did_timeout = False
        assert led.value == 0
        try:
            await with_timeout(Edge(dut.uo_out), 50, 'us')
        except cocotb.result.SimTimeoutError:
            did_timeout = True
        
        assert did_timeout
        assert led.value == 0

async def wait_led_reset(dut, led):
        low_time = 0
        while low_time < 50:
            try:
                await with_timeout(Edge(dut.uo_out), 1, 'us')
                if led.value == 1:
                    low_time = 0
            except cocotb.result.SimTimeoutError:
                if led.value == 0:
                    low_time += 1
