# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, Edge
from cocotb.utils import get_sim_time
import random

from tqv import TinyQV

@cocotb.test()
async def test_single_pixel(dut):
    dut._log.info("Start")

    # Set the clock period to 15 ns (~66.7 MHz)
    clock = Clock(dut.clk, 15, units="ns")
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

    dut._log.info("Test pushing a single pixel")

    # Test register write and read back
    dut._log.info("Write and read back G register")
    await tqv.write_reg(1, 255)
    assert await tqv.read_reg(1) == 255

    dut._log.info("Write and read back R register")
    await tqv.write_reg(2, 15)
    assert await tqv.read_reg(2) == 15

    dut._log.info("Write and read back B register")
    await tqv.write_reg(3, 128)
    assert await tqv.read_reg(3) == 128

    # wait for peripheral to be ready
    dut._log.info("Wait for peripheral to be ready")
    while await tqv.read_reg(0) == 0:
        await ClockCycles(dut.clk, 1000)

    # push pixel
    dut._log.info("Write PUSH register")
    f = cocotb.start_soon(tqv.write_reg(0, 0x01))
    assert led.value == 0
    bitseq = await get_GRB(dut, led)
    await f
    dut._log.info(f"Read back {len(bitseq)} bits: {bitseq}")
    assert bitseq == [1, 1, 1, 1, 1, 1, 1, 1,  # G: 255
                      0, 0, 0, 0, 1, 1, 1, 1,  # R: 15
                      1, 0, 0, 0, 0, 0, 0, 0]  # B: 128

    while await tqv.read_reg(0) == 0:
        await ClockCycles(dut.clk, 1000)

    # push (0,0,0) pixel
    dut._log.info("Write PUSH register")
    f = cocotb.start_soon(tqv.write_reg(0, 0x00))
    assert led.value == 0
    bitseq = await get_GRB(dut, led)
    await f
    dut._log.info(f"Read back {len(bitseq)} bits: {bitseq}")
    assert bitseq == [0] * 24

    # send a sequence of pixels with random colors + strip refresh after each pixel
    dut._log.info("Sending random color pixels + strip refresh")
    random.seed(42)

    while await tqv.read_reg(0) == 0:
        await ClockCycles(dut.clk, 1000)

    for count in range(16):
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        strip_reset = int(random.random() > 0.5)
        dut._log.info(f"Loading color {color}, reset={strip_reset}")
        await tqv.write_reg(1, color[0]) # G
        await tqv.write_reg(2, color[1]) # R
        await tqv.write_reg(3, color[2]) # B

        dut._log.info(f"Sending pixel #{count}")
        f = cocotb.start_soon(tqv.write_reg(0, 0x01 | (strip_reset << 7)))
        assert led.value == 0
        bitseq = await get_GRB(dut, led)
        await f
        dut._log.info(f"Read back {len(bitseq)} bits: {bitseq}")
        assert bitseq == list(map(int, f'{color[0]:08b}')) + list(map(int, f'{color[1]:08b}')) + list(map(int, f'{color[2]:08b}'))

        delay = await wait_peripheral_ready(tqv)
        dut._log.info(f"Peripheral ready after {delay:.2f} us")
        assert (strip_reset and delay > 250) or (not strip_reset and delay < 25)

    # send multiple pixels with final strip reset
    while await tqv.read_reg(0) == 0:
        await ClockCycles(dut.clk, 1000)

    await tqv.write_reg(1, 255)
    await tqv.write_reg(2, 15)
    await tqv.write_reg(3, 128)

    dut._log.info(f"Sending 11 pixels with final strip reset")
    f = cocotb.start_soon(tqv.write_reg(0, 0x81 | (10 << 1)))
    assert led.value == 0
    for count in range(11):
        bitseq = await get_GRB(dut, led)
        dut._log.info(f"Read back {len(bitseq)} bits: {bitseq}")
        assert bitseq == [1, 1, 1, 1, 1, 1, 1, 1,  # G: 255
                        0, 0, 0, 0, 1, 1, 1, 1,  # R: 15
                        1, 0, 0, 0, 0, 0, 0, 0]  # B: 128
    await f

    delay = await wait_peripheral_ready(tqv)
    dut._log.info(f"Peripheral ready after {delay:.2f} us")
    assert delay > 250

    while await tqv.read_reg(0) == 0:
        await ClockCycles(dut.clk, 1000)
    
    # send multiple black pixels with final strip reset
    dut._log.info(f"Sending 7 black pixels with final strip reset")
    f = cocotb.start_soon(tqv.write_reg(0, 0x80 | (6 << 1)))
    assert led.value == 0
    for count in range(7):
        bitseq = await get_GRB(dut, led)
        dut._log.info(f"Read back {len(bitseq)} bits: {bitseq}")
        assert bitseq == [0] * 24
    await f
  
    delay = await wait_peripheral_ready(tqv)
    dut._log.info(f"Peripheral ready after {delay:.2f} us")
    assert delay > 250


async def wait_peripheral_ready(tqv):
    t1 = get_sim_time('ns')
    while await tqv.read_reg(0) == 0:
        await Timer(1, units="us")
    t2 = get_sim_time('ns')
    return (t2 - t1) / 1000.0

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
