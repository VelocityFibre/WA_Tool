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

func verifyTabStructure() error {
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

	// Tabs to verify
	tabs := []string{
		"Velo Test",
		"Mohadin WA_Tool Monitor",
		"Lawley WA_Tool Monitor",
	}

	for _, tabName := range tabs {
		fmt.Printf("\n🔍 Verifying tab: %s\n", tabName)

		// Read header row (row 1-16 should contain headers/formatting)
		readRange := fmt.Sprintf("%s!1:16", tabName)
		resp, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange).Context(ctx).Do()
		if err != nil {
			fmt.Printf("❌ Failed to read %s tab: %v\n", tabName, err)
			continue
		}

		fmt.Printf("   📊 Found %d header rows in %s\n", len(resp.Values), tabName)

		// Show first few rows to understand the structure
		for i, row := range resp.Values {
			if i >= 5 { // Show only first 5 rows
				break
			}
			fmt.Printf("   Row %d: %v\n", i+1, row)
		}

		// Check if data rows start at row 17
		dataRange := fmt.Sprintf("%s!17:20", tabName)
		dataResp, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, dataRange).Context(ctx).Do()
		if err != nil {
			fmt.Printf("❌ Failed to read data area in %s: %v\n", tabName, err)
			continue
		}

		if len(dataResp.Values) == 0 {
			fmt.Printf("   ✅ Data area (rows 17+) is empty - ready for new entries\n")
		} else {
			fmt.Printf("   ⚠️  Data area has %d existing entries\n", len(dataResp.Values))
		}

		// Check column count
		if len(resp.Values) > 0 {
			fmt.Printf("   📋 Column count: %d\n", len(resp.Values[0]))
		}
	}

	return nil
}

func main() {
	fmt.Println("🔍 Verifying Google Sheets tab structures...")

	err := verifyTabStructure()
	if err != nil {
		fmt.Printf("❌ Verification failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Verification completed!")
}