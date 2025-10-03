# 📸 Step 1: Simple QA Photo Upload

**Very simple photo upload from WhatsApp groups with required QA information.**

## What It Does

1. **Monitors** your WhatsApp groups for image messages
2. **Requires** specific format: `DR[number] Step [1-14] [description]`
3. **Downloads** and **saves** valid photos with organized filenames
4. **Logs** all uploads with user, timestamp, and QA details

## Required Message Format

```
✅ VALID:   "DR1748808 Step 9 ONT barcode photo"
✅ VALID:   "DR123456 step 1: Property frontage" 
✅ VALID:   "Step 14 customer signature DR999999"

❌ INVALID: "Just a photo" (missing DR number and step)
❌ INVALID: "DR123456 nice photo" (missing step number)
```

## File Organization

Photos are saved as:
```
photos/lawley/DR1748808_Step09_Img1_143022.jpg
photos/velo/DR123456_Step01_Img1_144530.jpg
```

## Usage

**Test everything:**
```bash
python3 test_simple.py
```

**Process photos:**
```bash
python3 simple_upload.py
```

**Show examples:**
```bash
python3 simple_upload.py --examples
```

## Current Status

✅ Database connection working (96 images found in Lawley group)  
✅ Message parsing working perfectly  
✅ File organization ready  
⚠️  Current photos have no captions - need proper QA format

## What's Logged

Each upload creates a JSON log entry with:
- Timestamp
- Drop number & QA step
- User who sent it
- Original message content
- File location

## Next Steps

1. **Test with properly formatted messages** in WhatsApp
2. **Add AI approval** (Phase 2)
3. **Integrate with QA Photos Review** (Phase 3)
4. **Add Cloudflare storage** (Phase 4)

---
**Current Test Results:** System ready, just needs properly formatted photo messages!