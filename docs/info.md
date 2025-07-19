<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## What it does

WS2812B LED strip driver for TinyQV. The input signal to the LED strip is on `uo_out[1]`.

## Register map

Register MODE (`0x00`) controls the LED strip update mode. If MODE=0, a pixel is pushed, the driver assumes that the G, R, and B registers are updated in this order and it pushes a pixel as soon as the blue (last) component of the pixel color is written. If MODE=1, registers G, R and B are written asynchronously and a pixel is pushed when a non-zero value is written to register PUSH (`0x01`). The value (1-255) is the number of times that the pixel is pushed. Writing 0 to PUSH resets the strip so that update 

| Address | Name  | Access | Description                                                         |
|---------|-------|--------|---------------------------------------------------------------------|
| 0x00    | READY | R      | Status: bit 0 = peripheral ready                                    |
| 0x01    | PUSH  | W      | Push pixel to strip: pushes loaded color if bit 0 = 1,              |
|         |       |        | pushes (0,0,0) if bit 0 = 0; bit 7 = reset/latch                    |
| 0x02    | G     | R/W    | Green color component                                               |
| 0x03    | R     | R/W    | Red color component                                                 |
| 0x04    | B     | R/W    | Blue color component                                                |

## How to test

Connectd a WS2812B LED strip to `uo_out[1]`. Write 255 to register R, write 0x81 to PUSH, check that a red pixel appears in the strip. 

## External hardware

WS2812B LED strip with DIN connected to `uo_out[1]`.
