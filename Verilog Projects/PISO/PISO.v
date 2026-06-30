module PISO (input [0:3] A, input clk, input load, output out );
    wire [3:0] dff_out,mux_out;

    DFF dff[3:0] (mux_out[3:0],clk,dff_out[3:0]);
    assign out=dff_out[3];

    MUX2to1 mux0 (1'b0,A[0],load,mux_out[0]);
    MUX2to1 mux1 (dff_out[0],A[1],load,mux_out[1]);
    MUX2to1 mux2 (dff_out[1],A[2],load,mux_out[2]);
    MUX2to1 mux3 (dff_out[2],A[3],load,mux_out[3]);
endmodule
