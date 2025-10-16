package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"golang.org/x/oauth2/google"
	"google.golang.org/api/option"
	"google.golang.org/api/sheets/v4"
)

const (
	GOOGLE_SHEETS_ID        = "1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk"
	GOOGLE_CREDENTIALS_PATH = "/app/credentials.json"
)

func testDifferentWriteMethods() error {
	// Read service account credentials
	creds, err := os.ReadFile(GOOGLE_CREDENTIALS_PATH)
	if err != nil {
		return fmt.Errorf("failed to read credentials file: %v", err)
	}

	// Create Google Sheets service with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	config, err := google.CredentialsFromJSON(ctx, creds, sheets.SpreadsheetsScope)
	if err != nil {
		return fmt.Errorf("failed to parse credentials: %v", err)
	}

	srv, err := sheets.NewService(ctx, option.WithCredentials(config))
	if err != nil {
		return fmt.Errorf("failed to create sheets service: %v", err)
	}

	today := time.Now().Format("2006/01/02")
	testData := []interface{}{today, "DR_TEST_WRITE", "Test", "Data", "Here"}

	// Test 1: Try writing to "Test" tab instead
	fmt.Printf("🧪 Test 1: Writing to 'Test' tab...\n")
	vr1 := &sheets.ValueRange{
		Values: [][]interface{}{testData},
	}

	_, err = srv.Spreadsheets.Values.Append(GOOGLE_SHEETS_ID, "Test!A:E", vr1).
		ValueInputOption("USER_ENTERED").
		InsertDataOption("INSERT_ROWS").
		Context(ctx).
		Do()

	if err != nil {
		fmt.Printf("❌ Test 1 failed: %v\n", err)
	} else {
		fmt.Printf("✅ Test 1: Write to 'Test' tab succeeded\n")
	}

	// Test 2: Try direct range update instead of append
	fmt.Printf("🧪 Test 2: Direct update to specific cell in Velo Test...\n")
	vr2 := &sheets.ValueRange{
		Values: [][]interface{}{{"DIRECT_TEST"}},
	}

	_, err = srv.Spreadsheets.Values.Update(GOOGLE_SHEETS_ID, "Velo Test!A100", vr2).
		ValueInputOption("USER_ENTERED").
		Context(ctx).
		Do()

	if err != nil {
		fmt.Printf("❌ Test 2 failed: %v\n", err)
	} else {
		fmt.Printf("✅ Test 2: Direct update succeeded\n")
	}

	// Test 3: Try appending to the Mohadin WA_Tool Monitor tab (should be empty)
	fmt.Printf("🧪 Test 3: Writing to 'Mohadin WA_Tool Monitor' tab...\n")
	fullRowData := []interface{}{
		today,        // A: Date
		"DR_MOHADIN_TEST", // B: Drop Number
		false, false, false, false, false, false, false, // C-I: Steps 1-7
		false, false, false, false, false, false, false, // J-P: Steps 8-14
		0,            // Q: Completed Photos
		14,           // R: Outstanding Photos
		"TestUser",   // S: Contractor Name
		"Processing", // T: Status
		"",           // U: QA Notes
		"",           // V: Comments
		false,        // W: Resubmitted
		"",           // X: Additional Notes
		false,        // Y: Incomplete (QA flag)
	}

	vr3 := &sheets.ValueRange{
		Values: [][]interface{}{fullRowData},
	}

	_, err = srv.Spreadsheets.Values.Append(GOOGLE_SHEETS_ID, "Mohadin WA_Tool Monitor!A:Y", vr3).
		ValueInputOption("USER_ENTERED").
		InsertDataOption("INSERT_ROWS").
		Context(ctx).
		Do()

	if err != nil {
		fmt.Printf("❌ Test 3 failed: %v\n", err)
	} else {
		fmt.Printf("✅ Test 3: Write to Mohadin tab succeeded\n")
	}

	// Test 4: Check what the Velo Test tab structure looks like in detail
	fmt.Printf("🧪 Test 4: Reading Velo Test tab structure...\n")
	readRange := "Velo Test!A1:Y1"
	resp, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to read Velo Test structure: %v", err)
	}

	if len(resp.Values) > 0 {
		headers := resp.Values[0]
		fmt.Printf("📋 Velo Test has %d columns\n", len(headers))
		for i, header := range headers {
			if i < 10 { // Show first 10 headers
				fmt.Printf("   Column %d: %s\n", i+1, header)
			}
		}
	}

	// Test 5: Try appending with exact same number of columns as existing data
	fmt.Printf("🧪 Test 5: Write exact format to Velo Test...\n")
	if len(resp.Values) > 0 {
		exactColumns := len(resp.Values[0])
		testRow := make([]interface{}, exactColumns)
		testRow[0] = today
		testRow[1] = "DR_EXACT_TEST"
		// Fill rest with empty values
		for i := 2; i < exactColumns; i++ {
			testRow[i] = ""
		}

		vr4 := &sheets.ValueRange{
			Values: [][]interface{}{testRow},
		}

		_, err = srv.Spreadsheets.Values.Append(GOOGLE_SHEETS_ID, "Velo Test!A:Y", vr4).
			ValueInputOption("USER_ENTERED").
			InsertDataOption("INSERT_ROWS").
			Context(ctx).
			Do()

		if err != nil {
			fmt.Printf("❌ Test 5 failed: %v\n", err)
		} else {
			fmt.Printf("✅ Test 5: Exact format write succeeded\n")
		}
	}

	return nil
}

func main() {
	fmt.Println("🔬 Testing different Google Sheets write methods...")

	err := testDifferentWriteMethods()
	if err != nil {
		fmt.Printf("❌ Test failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ All tests completed!")
}