`timescale 1ns / 1ps

module tb_USR;

    reg clk;
    reg sel0;
    reg sel1;
    reg a0, a1, a2, a3;

    wire q0, q1, q2, q3;

    USR uut (
        .clk(clk), 
        .sel0(sel0), 
        .sel1(sel1), 
        .a0(a0), .a1(a1), .a2(a2), .a3(a3),
        .q0(q0), .q1(q1), .q2(q2), .q3(q3)
    );


    initial begin
        clk = 0;
        forever #5 clk = ~clk; 
    end


    initial begin

        $dumpfile("usr_waveforms.vcd"); 
        $dumpvars(0, tb_USR);          
        

        sel1 = 0; sel0 = 0;
        a0 = 0; a1 = 0; a2 = 0; a3 = 0;

   
        #10; 
        

        $display("Time\t S1 S0\t A0A1A2A3\t Q0Q1Q2Q3\t Operation");
        $display("-------------------------------------------------------------------");

        // TEST 1: Parallel Load (S1=1, S0=1)
        // Let's load the pattern 1011
        sel1 = 1; sel0 = 1;
        a3 = 1; a2 = 0; a1 = 1; a0 = 1; 
        #10; 
        $display("%0t\t %b  %b \t %b%b%b%b\t\t %b%b%b%b\t\t Parallel Load", $time, sel1, sel0, a0, a1, a2, a3, q0, q1, q2, q3);

        // TEST 2: No Change (S1=0, S0=0)
        // Output should remain 1011
        sel1 = 0; sel0 = 0;
        #10;
        $display("%0t\t %b  %b \t %b%b%b%b\t\t %b%b%b%b\t\t No Change", $time, sel1, sel0, a0, a1, a2, a3, q0, q1, q2, q3);

        // TEST 3: Shift Right (S1=0, S0=1)
        sel1 = 0; sel0 = 1;
        #10; 
        $display("%0t\t %b  %b \t ----\t\t %b%b%b%b\t\t Shift Right 1", $time, sel1, sel0, q0, q1, q2, q3);
        #10; 
        $display("%0t\t %b  %b \t ----\t\t %b%b%b%b\t\t Shift Right 2", $time, sel1, sel0, q0, q1, q2, q3);

        // TEST 4: Parallel Load (resetting for left shift test)
        // Let's load 1101
        sel1 = 1; sel0 = 1;
        a3 = 1; a2 = 1; a1 = 0; a0 = 1; 
        #10;
        $display("%0t\t %b  %b \t %b%b%b%b\t\t %b%b%b%b\t\t Parallel Load", $time, sel1, sel0, a0, a1, a2, a3, q0, q1, q2, q3);

        // TEST 5: Shift Left (S1=1, S0=0)
        sel1 = 1; sel0 = 0;
        #10;
        $display("%0t\t %b  %b \t ----\t\t %b%b%b%b\t\t Shift Left 1", $time, sel1, sel0, q0, q1, q2, q3);
        #10;
        $display("%0t\t %b  %b \t ----\t\t %b%b%b%b\t\t Shift Left 2", $time, sel1, sel0, q0, q1, q2, q3);

        // Finish simulation
        #20;
        $finish;
    end
endmodule