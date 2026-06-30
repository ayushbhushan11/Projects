module uart_top (
    input wire clk,
    input wire reset,

    input  wire rx_serial_in,
    output wire tx_serial_out,

    input  wire tx_start,
    input  wire [7:0] tx_data_in,
    output wire tx_busy,

    output wire [7:0] rx_data_out,
    output wire rx_done,
    output wire parity_err
);

    wire baud_tick_16x_wire; 


    BaudGen Baud_generator (
        .clk(clk),
        .reset(reset),
        .baud_tick(baud_tick_16x_wire)
    );

    uart_TX TX (
        .clk(clk),
        .baud(baud_tick_16x_wire),
        .reset(reset),
        .start(tx_start),
        .tx_data(tx_data_in),
        .busy(tx_busy),
        .out(tx_serial_out)
    );

    uart_RX RX (
        .clk(clk),
        .baud(baud_tick_16x_wire),
        .reset(reset),
        .in(rx_serial_in),
        .rx_data(rx_data_out),
        .done(rx_done),
        .parity_error(parity_err)
    );
    
endmodule