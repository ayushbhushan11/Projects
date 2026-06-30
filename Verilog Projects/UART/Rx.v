module uart_RX (
    input clk,
    input baud,
    input reset,
    input in,
    output reg [7:0] rx_data,
    output reg done,
    output reg parity_error
);
    localparam Idle = 3'b000;
    localparam Start = 3'b001;
    localparam Data = 3'b010;
    localparam Parity = 3'b011;
    localparam Stop = 3'b100;

    reg [2:0] state;
    reg [2:0] bit_index;
    reg [7:0] data;
    reg [3:0] tick_counter;
    reg received_parity;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            done<=1'b0;
            parity_error<=1'b0;
            state<=Idle;
        end
        else begin
            done<=1'b0;
            case (state) 
                Idle: begin
                    if (~in) begin
                        state<=Start;
                        tick_counter<=0;
                    end
                end
                Start: begin
                    if (baud) begin
                        if (tick_counter==7) begin
                            if (~in) begin
                                bit_index<=3'b000;
                                state<=Data;
                                tick_counter<=0;
                            end
                            else state<=Idle;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                Data: begin
                    if (baud) begin
                        if (tick_counter==15) begin
                            tick_counter<=0;
                            data[bit_index]<=in;
                            if (bit_index==7) begin
                                
                                state<=Parity;
                            end
                        
                            else bit_index<=bit_index+1;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                Parity: begin
                    if (baud) begin
                        if (tick_counter==15) begin
                            received_parity<=in;
                            tick_counter<=0;
                            state<=Stop;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                Stop: begin
                    if (baud) begin
                        if (tick_counter==15) begin
                            rx_data<=data;
                            done<=1'b1;
                            if (received_parity==^data) parity_error<=1'b0;
                            else parity_error<=1'b1;
                            tick_counter<=0;
                            state<=Idle;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                    
                end
                default: begin
                    state<=Idle;
                end
            endcase
        end
    end
endmodule