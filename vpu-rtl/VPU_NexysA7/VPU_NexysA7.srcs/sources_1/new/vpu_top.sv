module vpu_top #(
  parameter int LANES = 4
)(
  input  logic clk,
  input  logic rst,

  // Simple command wires for demo (replace with UART/AXI-lite register block)
  input  logic          cmd_valid,
  output logic          cmd_ready,
  input  formats::cmd_t cmd,

  output logic busy,
  output logic done,

  // -------------------------------------------------
  // TB-only scratchpad preload interface (simulation)
  // -------------------------------------------------
  input  logic        tb_sp_load_en,
  input  logic        tb_sp_we,
  input  logic [0:0]    tb_sp_bank,
  input  logic [10:0] tb_sp_addr,
  input  logic [31:0]             tb_sp_wdata
);

  import formats::*;

  localparam int SP_WORD_W = 32;
  localparam int SP_DEPTH  = 2048;
  localparam int SP_BANKS  = 2;

  // Core-driven scratchpad signals
  logic sp_we_core;
  logic [$clog2(SP_BANKS)-1:0] sp_bank_core;
  logic [$clog2(SP_DEPTH)-1:0] sp_addr_core;
  logic [SP_WORD_W-1:0]        sp_wdata_core;

  // Muxed scratchpad signals
  logic sp_we_mux;
  logic [$clog2(SP_BANKS)-1:0] sp_bank_mux;
  logic [$clog2(SP_DEPTH)-1:0] sp_addr_mux;
  logic [SP_WORD_W-1:0]        sp_wdata_mux;

  logic [SP_WORD_W-1:0] sp_rdata;

  // -------------------------------------------------
  // Scratchpad mux (TB preload vs core)
  // -------------------------------------------------
  assign sp_we_mux    = tb_sp_load_en ? tb_sp_we    : sp_we_core;
  assign sp_bank_mux  = tb_sp_load_en ? tb_sp_bank  : sp_bank_core;
  assign sp_addr_mux  = tb_sp_load_en ? tb_sp_addr  : sp_addr_core;
  assign sp_wdata_mux = tb_sp_load_en ? tb_sp_wdata : sp_wdata_core;

  // -------------------------------------------------
  // Scratchpad
  // -------------------------------------------------
  scratchpad #(
    .WORD_W(SP_WORD_W),
    .DEPTH_WORDS(SP_DEPTH),
    .BANKS(SP_BANKS)
  ) u_sp (
    .clk   (clk),
    .we    (sp_we_mux),
    .bank  (sp_bank_mux),
    .addr  (sp_addr_mux),
    .wdata (sp_wdata_mux),
    .rdata (sp_rdata)
  );

  // -------------------------------------------------
  // VPU core
  // -------------------------------------------------
  vpu_core #(
    .LANES(LANES),
    .SP_WORD_W(SP_WORD_W),
    .SP_DEPTH_WORDS(SP_DEPTH),
    .SP_BANKS(SP_BANKS)
  ) u_core (
    .clk      (clk),
    .rst      (rst),
    .cmd_valid(cmd_valid),
    .cmd_ready(cmd_ready),
    .cmd      (cmd),
    .busy     (busy),
    .done     (done),

    // Scratchpad interface (core side)
    .sp_we    (sp_we_core),
    .sp_bank  (sp_bank_core),
    .sp_addr  (sp_addr_core),
    .sp_wdata (sp_wdata_core),
    .sp_rdata (sp_rdata)
  );

endmodule
