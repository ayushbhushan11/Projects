module Mod_5_FSM (
    input      clk,
    input      reset,
    input      bit_in,
    output reg out);


    reg [2:0] current_state, next_state;

    parameter REM_0 = 3'b000; 
    parameter REM_1 = 3'b001; 
    parameter REM_2 = 3'b010; 
    parameter REM_3 = 3'b011; 
    parameter REM_4 = 3'b100; 

    always @(posedge clk or posedge reset) begin
        if (reset)
            current_state <= REM_0;
        else
            current_state <= next_state;
    end

    always @(*) begin
        case (current_state)
            REM_0: next_state = bit_in ? REM_1 : REM_0; 
            REM_1: next_state = bit_in ? REM_3 : REM_2; 
            REM_2: next_state = bit_in ? REM_0 : REM_4; 
            REM_3: next_state = bit_in ? REM_2 : REM_1; 
            REM_4: next_state = bit_in ? REM_4 : REM_3; 
            default: next_state = REM_0;
        endcase
    end

    always @(*) begin
        if ((current_state == REM_0 && bit_in == 1'b0) || 
            (current_state == REM_2 && bit_in == 1'b1))
            out = 1'b1; 
        else
            out = 1'b0;
    end

endmodule