# Updating Warp

Warp automatically checks for updates on startup. A notification will appear in the top right corner of the Warp window when a new update is available.

## Checking for Updates

To check for updates manually:

1. Search for "update" in the Command Palette
2. Or go to `Settings > Accounts` and click "Check for Update"

If nothing happens, it means you already have the latest stable build.

## Auto-Update Issues

Warp cannot auto-update if it does not have the correct permissions to replace the running version of Warp. If this is the case, a banner will prompt you to manually update Warp.

There are 2 main causes of this:

1. **Mounted Volume Issue**: You opened Warp directly from the mounted volume instead of dragging it into your Applications directory. 
   - **Fix**: Quit Warp, drag the application into /Applications, and restart Warp.

2. **Non-Admin User**: You are a non-Admin user. This can happen if you use a computer with multiple profiles.
   - **Fix**: If you have admin access on the computer, opening the app with the admin user should fix the auto-update issues.

## Known Issues

- **macOS Ventura**: There is a known issue with auto-update on macOS Ventura (as of Oct 2022).

## Additional Notes

- Warp uses automatic update checking to ensure you have the latest features and security updates
- The update notification appears prominently in the top right corner when available
- Manual update checking is available through the Command Palette or Settings menu