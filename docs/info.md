<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## What it does

WS2812B LED strip driver for TinyQV. The input signal to the LED strip is on `uo_out[1]`.

## Register map

| Address | Name  | Access | Description                                                         |
|---------|-------|--------|---------------------------------------------------------------------|
| 0x00    | CTRL  | W      | Push pixel(s) to strip. Pushes loaded color if bit 0 = 1, pushes (0,0,0) if bit 0 = 0. The number of pushed pixels is 1 + bits [6:1] (for 1 pixel, set bits [6:1] = 0). Setting bit 7 = 1 resets the strip after pushing the pixel(s). Write is ignored if the peripheral is not ready. |
|         |       | R      | Status: bit 0 = peripheral ready                                    |
| 0x01    | G     | R/W    | Green color component                                               |
| 0x02    | R     | R/W    | Red color component                                                 |
| 0x03    | B     | R/W    | Blue color component                                                |

## How to test

Connectd a WS2812B LED strip to `uo_out[1]`. Write 255 to register R (0x02), write 0x81 to CTRL (0x00), check that a red pixel is displayed by the strip. 

## External hardware

WS2812B LED strip with DIN connected to `uo_out[1]`.
