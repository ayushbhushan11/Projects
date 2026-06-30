module BaudGen (
    input clk ,
    input reset ,
    output reg baud_tick
);

    parameter Divider = 27;
    reg [4:0] counter;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter <= 0;
            baud_tick<=0;
        end
        else if (counter==Divider-1) begin
            counter <=0;
            baud_tick<=1;
        end
        else begin
            counter<=counter+1;
            baud_tick<=0;
        end

    end
endmodule