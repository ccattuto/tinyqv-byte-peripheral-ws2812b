/*
 * Copyright (c) 2025 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Change the name of this module to something that reflects its functionality and includes your name for uniqueness
// For example tqvp_yourname_spi for an SPI peripheral.
// Then edit tt_wrapper.v line 38 and change tqvp_example to your chosen module name.
module tqvp_cattuto_ws2812b_driver (
    input         clk,          // Clock - the TinyQV project clock is normally set to 64MHz.
    input         rst_n,        // Reset_n - low to reset.

    input  [7:0]  ui_in,        // The input PMOD, always available.  Note that ui_in[7] is normally used for UART RX.
                                // The inputs are synchronized to the clock, note this will introduce 2 cycles of delay on the inputs.

    output [7:0]  uo_out,       // The output PMOD.  Each wire is only connected if this peripheral is selected.
                                // Note that uo_out[0] is normally used for UART TX.

    input [3:0]   address,      // Address within this peripheral's address space

    input         data_write,   // Data write request from the TinyQV core.
    input [7:0]   data_in,      // Data in to the peripheral, valid when data_write is high.
    
    output [7:0]  data_out      // Data out from the peripheral, set this in accordance with the supplied address
);

    localparam REG_CTRL=4'h0, REG_G=4'h1, REG_R=4'h2, REG_B=4'h3;

    reg valid;
    reg latch;
    reg black;
    reg [23:0] color;

    assign ledstrip_data = black ? 24'h0 : color;
    assign ledstrip_reset = ~rst_n;
    assign ledstrip_valid = valid;
    assign ledstrip_latch = latch;

    // write to peripheral
    always @(posedge clk) begin
        if (!rst_n) begin
            latch <= 0;
            valid <= 0;
            color <= 0;
            black <= 0;
        end else begin
            if (data_write) begin
                case (address)
                    REG_CTRL: begin
                        if (ledstrip_ready) begin
                            latch <= data_in[7];
                            valid <= 1;
                            black <= ~data_in[0];
                        end
                    end

                    REG_G: begin
                        color[23:16] <= data_in;
                    end
                    
                    REG_R: begin
                        color[15:8] <= data_in;
                    end

                    REG_B: begin
                        color[7:0] <= data_in;
                    end

                    default: begin
                    end
                endcase
            end else begin
                if (!ledstrip_ready) begin
                    valid <= 0;
                end
            end
        end
    end

    // All output pins must be assigned. If not used, assign to 0.
    assign uo_out[0] = 0;
    assign uo_out[7:2] = 0;
    assign uo_out[1] = ledstrip;

    // read from peripheral
    assign data_out = (address == REG_CTRL) ? (8'h0 | ledstrip_ready) :
                      (address == REG_G) ? ((color >> 16) & 8'hFF) :
                      (address == REG_R) ? ((color >> 8) & 8'hFF) :
                      (address == REG_B) ? (color & 8'hFF) :
                      8'h0;

    // -------------- WS2812B LED STRIP ---------------------------

    wire [23:0] ledstrip_data;
    reg ledstrip_valid;
    wire ledstrip_reset;
    wire ledstrip_latch;
    wire ledstrip_ready;
    wire ledstrip;

    ws2812b ws2812b_inst (
        .clk(clk),
        .reset(ledstrip_reset),
        .data_in(ledstrip_data),
        .valid(ledstrip_valid),
        .latch(ledstrip_latch),
        .ready(ledstrip_ready),
        .led(ledstrip)  // output signal to the LED strip
    );

endmodule
