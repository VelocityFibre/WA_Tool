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

func testSpecificTab() error {
	// Check if credentials file exists
	if _, err := os.Stat(GOOGLE_CREDENTIALS_PATH); os.IsNotExist(err) {
		return fmt.Errorf("Google Sheets credentials not found at %s", GOOGLE_CREDENTIALS_PATH)
	}

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

	// First, get the spreadsheet to see all available tabs
	spreadsheet, err := srv.Spreadsheets.Get(GOOGLE_SHEETS_ID).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to access spreadsheet: %v", err)
	}

	fmt.Printf("📋 Spreadsheet: %s\n", spreadsheet.Properties.Title)
	fmt.Printf("📋 Available tabs:\n")
	for _, sheet := range spreadsheet.Sheets {
		fmt.Printf("   - %s (ID: %d)\n", sheet.Properties.Title, sheet.Properties.SheetId)
	}

	// Now try to read from the Velo Test tab specifically
	tabName := "Velo Test"
	readRange := fmt.Sprintf("%s!A1:Z10", tabName)

	fmt.Printf("\n🔍 Reading from tab: %s\n", tabName)
	resp, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to read from tab %s: %v", tabName, err)
	}

	if len(resp.Values) == 0 {
		fmt.Printf("❌ No data found in %s tab\n", tabName)
	} else {
		fmt.Printf("✅ Found %d rows in %s tab\n", len(resp.Values), tabName)
		for i, row := range resp.Values {
			if i >= 5 { // Show first 5 rows only
				break
			}
			fmt.Printf("   Row %d: %v\n", i+1, row)
		}
	}

	// Now try to write a test row
	fmt.Printf("\n📝 Writing test row to %s tab...\n", tabName)

	today := time.Now().Format("2006/01/02")
	dropNumber := "DR0000001_TEST"
	userName := "36563643842564"

	// Row data for Google Sheets (columns A-Y)
	rowData := []interface{}{
		today,        // A: Date
		dropNumber,   // B: Drop Number
		false, false, false, false, false, false, false, // C-I: Steps 1-7 (checkboxes)
		false, false, false, false, false, false, false, // J-P: Steps 8-14 (checkboxes)
		0,            // Q: Completed Photos
		14,           // R: Outstanding Photos
		userName,     // S: Contractor Name
		"Processing", // T: Status
		"",           // U: QA Notes
		"",           // V: Comments
		false,        // W: Resubmitted
		"",           // X: Additional Notes
		false,        // Y: Incomplete (QA flag)
	}

	// Append to sheet
	vr := &sheets.ValueRange{
		Values: [][]interface{}{rowData},
	}

	sheetRange := fmt.Sprintf("%s!A:Y", tabName)
	fmt.Printf("📝 Writing to range: %s\n", sheetRange)

	start := time.Now()
	_, err = srv.Spreadsheets.Values.Append(GOOGLE_SHEETS_ID, sheetRange, vr).
		ValueInputOption("USER_ENTERED").
		InsertDataOption("INSERT_ROWS").
		Context(ctx).
		Do()

	duration := time.Since(start)
	fmt.Printf("⏱️  API call took: %v\n", duration)

	if err != nil {
		return fmt.Errorf("failed to write to Google Sheets (tab: %s): %v", tabName, err)
	}

	fmt.Printf("✅ Successfully wrote test data to '%s' tab\n", tabName)

	// Verify the write by reading again
	fmt.Printf("\n🔍 Verifying write by reading again...\n")
	resp2, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to read after write: %v", err)
	}

	if len(resp2.Values) > len(resp.Values) {
		fmt.Printf("✅ Row count increased from %d to %d - write successful!\n", len(resp.Values), len(resp2.Values))
		// Show the last row
		lastRow := resp2.Values[len(resp2.Values)-1]
		fmt.Printf("📄 Last row: %v\n", lastRow)
	} else {
		fmt.Printf("❌ Row count didn't change - write may have failed silently\n")
	}

	return nil
}

func main() {
	fmt.Println("🔧 Debugging Google Sheets Velo Test tab...")

	err := testSpecificTab()
	if err != nil {
		fmt.Printf("❌ Debug test failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Debug test completed!")
}