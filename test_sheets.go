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

const GOOGLE_SHEETS_ID = "1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk"
const GOOGLE_CREDENTIALS_PATH = "/app/credentials.json"

func main() {
	fmt.Println("🧪 Testing Google Sheets API access...")

	// Check if credentials file exists
	if _, err := os.Stat(GOOGLE_CREDENTIALS_PATH); os.IsNotExist(err) {
		fmt.Printf("❌ Credentials not found at %s\n", GOOGLE_CREDENTIALS_PATH)
		return
	}
	fmt.Println("✅ Credentials file found")

	// Read service account credentials
	creds, err := os.ReadFile(GOOGLE_CREDENTIALS_PATH)
	if err != nil {
		fmt.Printf("❌ Failed to read credentials: %v\n", err)
		return
	}
	fmt.Println("✅ Credentials read successfully")

	// Create Google Sheets service
	config, err := google.CredentialsFromJSON(context.Background(), creds, sheets.SpreadsheetsScope)
	if err != nil {
		fmt.Printf("❌ Failed to parse credentials: %v\n", err)
		return
	}
	fmt.Println("✅ Credentials parsed successfully")

	srv, err := sheets.NewService(context.Background(), option.WithCredentials(config))
	if err != nil {
		fmt.Printf("❌ Failed to create sheets service: %v\n", err)
		return
	}
	fmt.Println("✅ Sheets service created successfully")

	// Test data
	dropNumber := "TESTDR001"
	userName := "TestUser"
	today := time.Now().Format("2006/01/02")

	// Row data for Google Sheets (columns A-Y)
	rowData := []interface{}{
		today,        // A: Date
		dropNumber,   // B: Drop Number
		false, false, false, false, false, false, false, // C-I: Steps 1-7 (checkboxes)
		false, false, false, false, false, false, false, // J-P: Steps 8-14 (checkboxes)
		0,            // Q: Completed Photos
		14,           // R: Outstanding Photos
		userName,     // S: Contractor Name
		"Testing",    // T: Status
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

	tabName := "Velo Test"
	sheetRange := fmt.Sprintf("%s!A:Y", tabName)

	fmt.Printf("🚀 Attempting to write to sheet: %s range: %s\n", GOOGLE_SHEETS_ID, sheetRange)

	start := time.Now()
	_, err = srv.Spreadsheets.Values.Append(GOOGLE_SHEETS_ID, sheetRange, vr).
		ValueInputOption("USER_ENTERED").
		InsertDataOption("INSERT_ROWS").
		Do()

	duration := time.Since(start)
	fmt.Printf("⏱️  API call took: %v\n", duration)

	if err != nil {
		fmt.Printf("❌ Failed to write to Google Sheets: %v\n", err)
		return
	}

	fmt.Printf("✅ Successfully added %s to '%s' Google Sheets tab\n", dropNumber, tabName)
}