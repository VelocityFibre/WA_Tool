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

func verifyFix() error {
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

	// Read all data from Velo Test tab
	fmt.Printf("🔍 Reading all data from Velo Test tab...\n")
	readRange := "Velo Test!A:X"
	resp, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to read Velo Test tab: %v", err)
	}

	if len(resp.Values) == 0 {
		fmt.Printf("❌ No data found in Velo Test tab\n")
	} else {
		fmt.Printf("📊 Velo Test tab has %d total rows\n", len(resp.Values))

		// Show all rows that contain "DR"
		fmt.Printf("🔍 Searching for DR entries...\n")
		drCount := 0
		for i, row := range resp.Values {
			if len(row) >= 2 {
				dropNumber := fmt.Sprintf("%v", row[1]) // Column B
				if len(dropNumber) >= 2 && dropNumber[:2] == "DR" {
					drCount++
					fmt.Printf("   Row %d: %s | User: %v\n", i+1, dropNumber, safeGet(row, 17)) // Column S
				}
			}
		}

		if drCount == 0 {
			fmt.Printf("❌ No DR numbers found in Velo Test tab\n")
		} else {
			fmt.Printf("✅ Found %d DR numbers in Velo Test tab\n", drCount)
		}

		// Show the last 3 rows
		fmt.Printf("\n📄 Last 3 rows in Velo Test:\n")
		start := len(resp.Values) - 3
		if start < 0 {
			start = 0
		}

		for i := start; i < len(resp.Values); i++ {
			row := resp.Values[i]
			date := safeGet(row, 0)
			dropNumber := safeGet(row, 1)
			user := safeGet(row, 17)
			fmt.Printf("   Row %d: [%s] %s | User: %s\n", i+1, date, dropNumber, user)
		}
	}

	return nil
}

func safeGet(row []interface{}, index int) string {
	if index >= len(row) {
		return ""
	}
	if row[index] == nil {
		return ""
	}
	return fmt.Sprintf("%v", row[index])
}

func main() {
	fmt.Println("🔍 Verifying Google Sheets fix...")

	err := verifyFix()
	if err != nil {
		fmt.Printf("❌ Verification failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Verification completed!")
}