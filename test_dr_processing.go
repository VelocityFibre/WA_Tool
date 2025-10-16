package main

import (
	"fmt"
	"regexp"
	"strings"
	"time"
)

// Simulate the drop number processing from WhatsApp
var dropPattern = regexp.MustCompile(`DR\d+`)

// Project configuration
var PROJECT_SHEETS_TABS = map[string]string{
	"Velo Test": "Velo Test",
	"Mohadin":   "Mohadin WA_Tool Monitor",
	"Lawley":    "Lawley WA_Tool Monitor",
}

func processDropNumbers(content, chatJID, sender string, timestamp time.Time) {
	// Get project name (simplified)
	projectName := "Velo Test" // Simulating Velo Test group

	// Find all drop numbers in the message
	dropNumbers := dropPattern.FindAllString(content, -1)
	if len(dropNumbers) == 0 {
		fmt.Printf("❌ No drop numbers found in: %s\n", content)
		return
	}

	fmt.Printf("🎯 Found %d drop numbers: %v\n", len(dropNumbers), dropNumbers)

	// Process each drop number
	for _, dropNumber := range dropNumbers {
		dropNumber = strings.ToUpper(dropNumber)

		// Create contractor name from sender
		userName := sender
		if len(sender) > 20 {
			userName = sender[:20]
		}

		fmt.Printf("📝 Processing DR: %s, User: %s, Project: %s\n", dropNumber, userName, projectName)

		// Simulate database write (always succeeds in this test)
		fmt.Printf("✅ Created QA photo review for %s\n", dropNumber)

		// Test Google Sheets write
		tabName, exists := PROJECT_SHEETS_TABS[projectName]
		if !exists {
			fmt.Printf("❌ No Google Sheets tab configured for project: %s\n", projectName)
			continue
		}

		fmt.Printf("📝 Writing to Google Sheets - DR: %s, Tab: %s\n", dropNumber, tabName)

		// Simulate the API call timing or succeeding
		time.Sleep(2 * time.Second) // Simulate API call time
		fmt.Printf("✅ Added %s to '%s' Google Sheets tab\n", dropNumber, tabName)

		fmt.Printf("✅ Processed drop number: %s from %s (project: %s)\n", dropNumber, sender, projectName)
	}
}

func main() {
	fmt.Println("🧪 Testing DR number processing simulation...")

	// Test case 1: Normal DR number
	testContent1 := "DR0000001 - Completed installation"
	sender := "27823216574"
	chatJID := "120363421664266245@g.us"
	timestamp := time.Now()

	fmt.Printf("\n--- Test 1: Normal DR processing ---\n")
	fmt.Printf("Message: %s\n", testContent1)
	processDropNumbers(testContent1, chatJID, sender, timestamp)

	// Test case 2: Multiple DR numbers
	testContent2 := "DR0000002 and DR0000003 are ready for review"
	fmt.Printf("\n--- Test 2: Multiple DR processing ---\n")
	fmt.Printf("Message: %s\n", testContent2)
	processDropNumbers(testContent2, chatJID, sender, timestamp)

	// Test case 3: No DR numbers
	testContent3 := "Just a regular message without DR numbers"
	fmt.Printf("\n--- Test 3: No DR numbers ---\n")
	fmt.Printf("Message: %s\n", testContent3)
	processDropNumbers(testContent3, chatJID, sender, timestamp)

	fmt.Println("\n✅ DR processing simulation complete!")
}