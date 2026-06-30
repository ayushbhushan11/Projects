`timescale 1ns / 1ps

module tb_uart_top;

    // ----------------------------------------------------
    // 1. Signals Declaration
    // ----------------------------------------------------
    // System
    reg clk;
    reg reset;

    // TX User Interface
    reg tx_start;
    reg [7:0] tx_data_in;
    wire tx_busy;
    wire tx_serial_out;

    // RX User Interface
    wire [7:0] rx_data_out;
    wire rx_done;
    wire parity_err;
    wire rx_serial_in; // Driven by mux (Loopback or TB)

    // Testbench Control Signals
    reg loopback_en;
    reg rx_tb_drive;

    // ----------------------------------------------------
    // 2. Constants & Configuration
    // ----------------------------------------------------
    // 50 MHz Clock = 20ns period
    localparam CLOCK_PERIOD = 20; 
    
    // Baud Rate 115200 -> Bit Period ≈ 8681 ns
    localparam BIT_PERIOD = 8681; 

    // ----------------------------------------------------
    // 3. Mux for RX Input
    // ----------------------------------------------------
    // If loopback is enabled, route TX out to RX in.
    // Otherwise, let the testbench drive the RX line manually.
    assign rx_serial_in = loopback_en ? tx_serial_out : rx_tb_drive;

    // ----------------------------------------------------
    // 4. Device Under Test (DUT) Instantiation
    // ----------------------------------------------------
    uart_top uut (
        .clk(clk),
        .reset(reset),
        .rx_serial_in(rx_serial_in),
        .tx_serial_out(tx_serial_out),
        .tx_start(tx_start),
        .tx_data_in(tx_data_in),
        .tx_busy(tx_busy),
        .rx_data_out(rx_data_out),
        .rx_done(rx_done),
        .parity_err(parity_err)
    );

    // ----------------------------------------------------
    // 5. Clock Generation
    // ----------------------------------------------------
    initial begin
        clk = 0;
        forever #(CLOCK_PERIOD / 2) clk = ~clk;
    end

    // ----------------------------------------------------
    // 6. Testbench Tasks
    // ----------------------------------------------------
    
    // Task: Trigger the TX module to send a byte
    task send_tx_byte(input [7:0] data);
        begin
            @(posedge clk);
            tx_data_in = data;
            tx_start = 1'b1;
            @(posedge clk);
            tx_start = 1'b0;
            
            // Wait for transmission to finish
            wait(tx_busy == 1'b1);
            wait(tx_busy == 1'b0);
            $display("[Time: %0t] TX finished sending: 0x%h", $time, data);
        end
    endtask

    // Task: Manually bit-bang the RX pin (simulating external device)
    task drive_rx_byte(input [7:0] data, input force_bad_parity);
        integer i;
        reg parity_bit;
        begin
            // Calculate correct parity (XOR of data)
            parity_bit = ^data;
            if (force_bad_parity) begin
                parity_bit = ~parity_bit; // Flip to create error
            end

            // Start Bit (Low)
            rx_tb_drive = 1'b0;
            #(BIT_PERIOD);

            // Data Bits (LSB First)
            for (i = 0; i < 8; i = i + 1) begin
                rx_tb_drive = data[i];
                #(BIT_PERIOD);
            end

            // Parity Bit
            rx_tb_drive = parity_bit;
            #(BIT_PERIOD);

            // Stop Bit (High)
            rx_tb_drive = 1'b1;
            #(BIT_PERIOD);
        end
    endtask

    // ----------------------------------------------------
    // 7. Main Test Sequence
    // ----------------------------------------------------
    initial begin
        // Initialize signals
        reset = 1;
        tx_start = 0;
        tx_data_in = 8'd0;
        loopback_en = 1; // Start with internal loopback
        rx_tb_drive = 1; // Idle high

        // Apply Reset
        #(CLOCK_PERIOD * 10);
        reset = 0;
        #(CLOCK_PERIOD * 10);
        $display("--- SYSTEM RESET COMPLETE ---");

        // ==========================================================
        // TEST CASE 1: Single Byte Loopback (TX -> RX)
        // ==========================================================
        $display("\n[TEST CASE 1] Single Byte Loopback (0x55)");
        fork
            send_tx_byte(8'h55);
            begin
                wait(rx_done);
                if (rx_data_out == 8'h55 && !parity_err)
                    $display("    --> PASS: Received 0x55, No Parity Error");
                else
                    $display("    --> FAIL: Received 0x%h, Parity Err: %b", rx_data_out, parity_err);
            end
        join

        // ==========================================================
        // TEST CASE 2: Back-to-Back Loopback (TX -> RX)
        // ==========================================================
        $display("\n[TEST CASE 2] Back-to-Back Data Burst (0xAA, 0xFF, 0x00)");
        send_tx_byte(8'hAA);
        #(BIT_PERIOD * 2); // Small delay between bytes
        send_tx_byte(8'hFF);
        #(BIT_PERIOD * 2);
        send_tx_byte(8'h00);
        
        // Give RX time to catch up just in case
        #(BIT_PERIOD * 15); 
        $display("    --> Burst transmission complete.");

        // ==========================================================
        // TEST CASE 3: External RX with CORRECT Parity
        // ==========================================================
        $display("\n[TEST CASE 3] External RX Drive - Correct Parity (0x33)");
        loopback_en = 0; // Disconnect TX from RX, TB will drive RX
        
        fork
            drive_rx_byte(8'h33, 1'b0); // Send 0x33, force_bad_parity = 0
            begin
                wait(rx_done);
                if (rx_data_out == 8'h33 && !parity_err)
                    $display("    --> PASS: Received 0x33, Parity check passed!");
                else
                    $display("    --> FAIL: Received 0x%h, Parity Err: %b", rx_data_out, parity_err);
            end
        join

        #(BIT_PERIOD * 2);

        // ==========================================================
        // TEST CASE 4: External RX with INCORRECT Parity (Error Inj)
        // ==========================================================
        $display("\n[TEST CASE 4] External RX Drive - Incorrect Parity Injection (0xCC)");
        
        fork
            drive_rx_byte(8'hCC, 1'b1); // Send 0xCC, force_bad_parity = 1
            begin
                wait(rx_done);
                if (rx_data_out == 8'hCC && parity_err)
                    $display("    --> PASS: Received 0xCC, Parity Error successfully flagged!");
                else
                    $display("    --> FAIL: Received 0x%h, Parity Err: %b", rx_data_out, parity_err);
            end
        join

        // ==========================================================
        // TEST CASE 5: Glitch / Noise Test on Start Bit
        // ==========================================================
        $display("\n[TEST CASE 5] RX Start Bit Glitch Immunity Test");
        // Drop RX low for a fraction of a bit period, then pull it high
        rx_tb_drive = 1'b0;
        #(BIT_PERIOD / 4); // Only low for 25% of a bit
        rx_tb_drive = 1'b1;
        
        // Wait to see if RX mistakenly triggers done
        #(BIT_PERIOD * 12);
        if (!rx_done)
            $display("    --> PASS: RX correctly ignored the start bit glitch.");
        else
            $display("    --> FAIL: RX falsely triggered on a glitch.");

        // End Simulation
        $display("\n--- SIMULATION COMPLETE ---");
        $finish;
    end

endmodule