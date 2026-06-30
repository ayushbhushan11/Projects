`timescale 1ns / 1ps

module tb_PISO;

    // --- Inputs to UUT ---
    reg [0:3] A;
    reg clk;
    reg load;

    // --- Outputs from UUT ---
    wire out;

    // --- Instantiate the PISO module ---
    PISO uut (
        .A(A), 
        .clk(clk), 
        .load(load), 
        .out(out)
    );

    // --- Clock Generation ---
    always #5 clk = ~clk;

    // --- Test Stimulus ---
    initial begin
        $dumpfile("dump.vcd");       // Names the output waveform file
        $dumpvars(0, tb_PISO);

        clk = 0;
        load = 0;
        A = 4'b0000;
        #10;
        
        // TEST CASE 1: Load and shift 1011
        $display("\n--- Starting Test Case 1: Load 1011 ---");
        A = 4'b1011;  
        load = 1;     
        #10;          
        
        load = 0;     
        #40;          
        
        // TEST CASE 2: Load and shift 0110
        $display("\n--- Starting Test Case 2: Load 0110 ---");
        A = 4'b0110;  
        load = 1;     
        #10;          
        
        load = 0;     
        #40;          

        $display("\nSimulation Complete.");
        $finish;
    end
    
    // --- Signal Monitoring (UPDATED) ---
    // This will now ONLY print on the positive edge of the clock.
    // I also removed 'clk' from the print statement, since it will always be 1 here.
    always @(posedge clk) begin
        $display("Time = %0t | load = %b | A = %b | Serial Out = %b", 
                 $time, load, A, out);
    end

endmodule