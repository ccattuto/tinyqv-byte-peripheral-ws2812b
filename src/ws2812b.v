module ws2812b #(parameter CLOCK_MHZ=64) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [23:0] data_in,   // color data
    input  wire        valid,
    input  wire        latch,
    output reg         ready,
    output reg         led        // output signal to LED strip
);

  localparam [63:0] CLOCK_HZ = CLOCK_MHZ * 1_000_000;
  localparam [63:0] NS_PER_S = 1_000_000_000;

  localparam T0H_NS = 400;            // width of '0' high pulse (400 ns)
  localparam T1H_NS = 800;            // width of '1' high pulse (800 ns)
  localparam PERIOD_NS = 1250;        // total period of one bit (1250 ns)
  localparam RES_DELAY_NS = 325_000;  // reset duration (325 us)

  `define CYCLES_FROM_NS(_NSVAL) \
    ( ((CLOCK_HZ * (64'd0 + _NSVAL)) + (NS_PER_S/2)) / NS_PER_S )

  localparam [63:0] CYCLES_T0H_U    = `CYCLES_FROM_NS(T0H_NS);
  localparam [63:0] CYCLES_T1H_U    = `CYCLES_FROM_NS(T1H_NS);
  localparam [63:0] CYCLES_T0L_U    = `CYCLES_FROM_NS(PERIOD_NS - T0H_NS);
  localparam [63:0] CYCLES_T1L_U    = `CYCLES_FROM_NS(PERIOD_NS - T1H_NS);
  localparam [63:0] CYCLES_RESET_U  = `CYCLES_FROM_NS(RES_DELAY_NS);

  localparam [15:0] CYCLES_T0H   = CYCLES_T0H_U[15:0];
  localparam [15:0] CYCLES_T1H   = CYCLES_T1H_U[15:0];
  localparam [15:0] CYCLES_T0L   = CYCLES_T0L_U[15:0];
  localparam [15:0] CYCLES_T1L   = CYCLES_T1L_U[15:0];
  localparam [15:0] CYCLES_RESET = CYCLES_RESET_U[15:0];

  localparam [1:0] IDLE = 2'd0, START = 2'd1, SEND_BIT = 2'd2, RESET = 2'd3;
  reg [1:0]  state;

  reg [4:0]  bitpos;
  reg [23:0] data;
  reg will_latch;  // whether to issue reset after last bit
  reg [15:0] timer;
  reg phase_is_high;

  wire cur_bit = data[bitpos];

  always @(posedge clk) begin
    if (!rst_n) begin
      state <= RESET;
      bitpos <= 5'd0;
      data <= 24'd0;
      will_latch <= 0;
      timer <= 16'd0;
      phase_is_high <= 0;
      led <= 0;
      ready <= 0;
    end else begin
      case (state)
        IDLE: begin
          led  <= 0;
          ready <= 1;
          if (ready && valid) begin
            data <= data_in;
            will_latch <= latch;
            ready <= 0;
            state <= START;
          end
        end

        START: begin
          bitpos <= 5'd23;
          phase_is_high <= 1;
          led <= 1;
          timer <= data_in[23] ? CYCLES_T1H : CYCLES_T0H;
          state <= SEND_BIT;
        end

        SEND_BIT: begin
          if (phase_is_high) begin
            if (timer == 16'd1) begin
              led <= 0;
              phase_is_high <= 0;
              timer <= cur_bit ? CYCLES_T1L : CYCLES_T0L;
            end else begin
              timer <= timer - 16'd1;
            end
          end else begin
            if (timer == 16'd1) begin
              if (bitpos != 5'd0) begin
                bitpos <= bitpos - 5'd1;
                phase_is_high <= 1;
                led <= 1;
                timer <= data[bitpos - 5'd1] ? CYCLES_T1H : CYCLES_T0H;
              end else begin
                led <= 0;
                if (will_latch) begin
                  state <= RESET;
                  timer <= CYCLES_RESET;
                  will_latch <= 0;
                end else begin
                  state <= IDLE;
                end
              end
            end else begin
              timer <= timer - 16'd1;
            end
          end
        end

        RESET: begin
          led <= 0;
          if (timer == 16'd1) begin
            state <= IDLE;
          end else begin
            timer <= timer - 16'd1;
          end
        end

      endcase
    end
  end

endmodule
