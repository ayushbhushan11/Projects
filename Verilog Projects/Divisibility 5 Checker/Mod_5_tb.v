`timescale 1ns / 1ps

// ========================================================
// Mealy Modulo 5 FSM Testbench
// Author: Ayush Bhushan (24EE10043)
// ========================================================

module tb_Mod_5_Mealy();

    reg clk;
    reg reset;
    reg bit_in;
    wire out;

    // Instantiate the Mealy FSM
    Mod_5_FSM uut (
        .clk(clk),
        .reset(reset),
        .bit_in(bit_in),
        .out(out)
    );

    // Clock generation
    always #5 clk = ~clk;

    initial begin
        clk = 0;
        reset = 1;
        bit_in = 0;
        
        $dumpfile("mod5_mealy.vcd");
        $dumpvars(0, tb_Mod_5_Mealy);

        #20;
        
        // ---------------------------------------------------------
        // Test Case 1: Number 25 (Binary: 11001)
        // ---------------------------------------------------------
        $display("\n--- Starting Test Case 1: Input = 25 (11001) ---");
        
        @(posedge clk);
        reset <= 0;
        bit_in <= 1; // MSB
        
        @(posedge clk) bit_in <= 1;
        @(posedge clk) bit_in <= 0;
        @(posedge clk) bit_in <= 0;
        @(posedge clk) bit_in <= 1; // LSB
        
        // In a Mealy machine, the output is valid DURING the clock cycle 
        // the final bit is applied, right before the next clock edge!
        #1; // Wait 1 time unit for combinational output logic to settle
        $display("Final Output for 25: %b (Expected: 1)", out);
        
        @(posedge clk); // Shift the final bit into the flip-flops

        // ---------------------------------------------------------
        // Reset Between Tests
        // ---------------------------------------------------------
        reset <= 1; 
        bit_in <= 0; 
        #10; 
        
        // ---------------------------------------------------------
        // Test Case 2: Number 14 (Binary: 1110)
        // ---------------------------------------------------------
        $display("\n--- Starting Test Case 2: Input = 14 (1110) ---");
        
        @(posedge clk);
        reset <= 0;
        bit_in <= 1; // MSB
        
        @(posedge clk) bit_in <= 1;
        @(posedge clk) bit_in <= 1;
        @(posedge clk) bit_in <= 0; // LSB
        
        #1; // Wait 1 time unit for combinational output logic to settle
        $display("Final Output for 14: %b (Expected: 0)\n", out);

        #20;
        $finish;
    end
    
    // Print only on the positive edge using $strobe
    always @(posedge clk) begin
        $strobe("Time=%0t | clk=%b | reset=%b | bit_in=%b || FSM State=%b | Mealy out=%b", 
                $time, clk, reset, bit_in, uut.current_state, out);
    end

endmodule