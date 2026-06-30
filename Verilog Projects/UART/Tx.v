module uart_TX (
    input clk,
    input baud,
    input reset,
    input start,
    input [7:0] tx_data,
    output reg busy,
    output reg out
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
    reg parity;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            tick_counter<=0;
            state <= Idle;
            out <= 1'b1;
            busy <= 1'b0;
        end
        else begin
            case (state) 
                Idle: begin
                    if (start) begin 
                        tick_counter<=0;
                        data<=tx_data;
                        busy <= 1'b1;
                        bit_index <=3'b000;
                        parity <= ^tx_data;
                        state <= Start;
                        out <= 1'b0;
                    end
                    else begin
                        out <= 1'b1;
                        busy <= 1'b0;
                    end
                end
                Start: begin
                    if (baud) begin
                        if (tick_counter==4'd15) begin
                            tick_counter<=0;
                            out<=data[0];
                            bit_index<=3'b000;
                            state <= Data;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                Data: begin
                    if (baud) begin
                        if (tick_counter==4'd15) begin
                            tick_counter<=0;
                            
                            if (bit_index==7) begin
                                out<=parity;
                                state <= Parity;
                            end
                            else begin
                                out<=data[bit_index+1];
                                bit_index<=bit_index+1;
                            end
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                Parity: begin
                    if (baud) begin    
                        if (tick_counter==4'd15) begin
                            tick_counter<=0;
                            out <= 1'b1;
                            state<= Stop;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                Stop: begin
                    if (baud) begin    
                        if (tick_counter==4'd15) begin
                            tick_counter<=0;
                            busy<=1'b0;
                            out<= 1'b1;
                            state<=Idle;
                        end
                        else tick_counter<=tick_counter+1;
                    end
                end
                default: begin
                    out<=1'b1;
                    state<=Idle;
                end
            endcase
        end
    end
endmodule