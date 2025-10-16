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

func checkSpecificRow() error {
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

	// Read rows around 1017 to see the context
	fmt.Printf("🔍 Reading rows 1015-1020 from Velo Test tab...\n")
	readRange := "Velo Test!1015:1020"
	resp, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to read Velo Test tab: %v", err)
	}

	if len(resp.Values) == 0 {
		fmt.Printf("❌ No data found in rows 1015-1020\n")
	} else {
		fmt.Printf("📊 Found %d rows in range 1015-1020:\n", len(resp.Values))
		for i, row := range resp.Values {
			rowNum := 1015 + i
			date := safeGet(row, 0)
			dropNumber := safeGet(row, 1)
			user := safeGet(row, 17) // Column S (User)
			status := safeGet(row, 19) // Column T (Status)

			fmt.Printf("   Row %d: Date=%s, DR=%s, User=%s, Status=%s\n", rowNum, date, dropNumber, user, status)

			// If this is our target row, show more details
			if dropNumber == "DR0000010" {
				fmt.Printf("      🎯 FOUND DR0000010! Full row details:\n")
				for j, cell := range row {
					if j < 24 { // Only show first 24 columns
						colName := string(rune('A' + j))
						fmt.Printf("         Column %s: %v\n", colName, cell)
					}
				}
			}
		}
	}

	// Also check the very last few rows in case row numbers are different
	fmt.Printf("\n🔍 Reading last 5 rows from Velo Test tab...\n")
	readRange2 := "Velo Test!A:X"
	resp2, err := srv.Spreadsheets.Values.Get(GOOGLE_SHEETS_ID, readRange2).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to read Velo Test tab: %v", err)
	}

	if len(resp2.Values) > 0 {
		start := len(resp2.Values) - 5
		if start < 0 {
			start = 0
		}

		fmt.Printf("📊 Last 5 rows (total rows: %d):\n", len(resp2.Values))
		for i := start; i < len(resp2.Values); i++ {
			row := resp2.Values[i]
			rowNum := i + 1
			date := safeGet(row, 0)
			dropNumber := safeGet(row, 1)
			user := safeGet(row, 17)

			fmt.Printf("   Row %d: [%s] %s | User: %s", rowNum, date, dropNumber, user)
			if dropNumber == "DR0000010" {
				fmt.Printf(" ⭐ FOUND IT!")
			}
			fmt.Printf("\n")
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
	fmt.Println("🔍 Checking specific row for DR0000010...")

	err := checkSpecificRow()
	if err != nil {
		fmt.Printf("❌ Check failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ Check completed!")
}