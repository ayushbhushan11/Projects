module USR(input clk, input sel0,input sel1, input a0,input a1,input a2,input a3,output q0,output q1, output q2,output q3);
    wire [4:1] mux_out, dff_out;

    
    assign {q3,q2,q1,q0}=dff_out;

    DFF dff[4:1] (mux_out[4:1],{clk,clk,clk,clk},dff_out[4:1]);

    MUX4to1 mux1 (dff_out[1],1'b0,dff_out[2],a0,sel0,sel1,mux_out[1]);
    MUX4to1 mux2 (dff_out[2],dff_out[1],dff_out[3],a1,sel0,sel1,mux_out[2]);
    MUX4to1 mux3 (dff_out[3],dff_out[2],dff_out[4],a2,sel0,sel1,mux_out[3]);
    MUX4to1 mux4 (dff_out[4],dff_out[3],1'b0,a3,sel0,sel1,mux_out[4]);
endmodule



