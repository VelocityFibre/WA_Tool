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

func clearRow17() error {
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

	// Tabs to clear row 17
	tabs := []string{
		"Velo Test",
		"Mohadin WA_Tool Monitor",
		"Lawley WA_Tool Monitor",
	}

	for _, tabName := range tabs {
		fmt.Printf("🧹 Clearing row 17 in tab: %s\n", tabName)

		// Clear row 17 specifically
		var clearRange string
		switch tabName {
		case "Velo Test":
			clearRange = fmt.Sprintf("%s!A17:X17", tabName) // 24 columns
		case "Mohadin WA_Tool Monitor", "Lawley WA_Tool Monitor":
			clearRange = fmt.Sprintf("%s!A17:Z17", tabName) // 26 columns
		}

		clearReq := &sheets.BatchClearValuesRequest{
			Ranges: []string{clearRange},
		}

		_, err = srv.Spreadsheets.Values.BatchClear(GOOGLE_SHEETS_ID, clearReq).Context(ctx).Do()
		if err != nil {
			fmt.Printf("❌ Failed to clear row 17 in %s tab: %v\n", tabName, err)
		} else {
			fmt.Printf("✅ Cleared row 17 in %s tab\n", tabName)
		}
	}

	return nil
}

func main() {
	fmt.Println("🧹 Clearing row 17 in all tabs...")

	err := clearRow17()
	if err != nil {
		fmt.Printf("❌ Clear operation failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Row 17 cleared in all tabs!")
}