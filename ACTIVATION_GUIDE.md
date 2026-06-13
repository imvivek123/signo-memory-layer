# Quick Activation Guide: Using Debug Code

## Step 1: Choose Your Approach

### Approach A: Temporary Testing (Recommended First Try)
Keep original files intact. Create a test branch that uses debug versions.

### Approach B: Replace Originals
Fully replace with debug versions once you're ready to commit.

---

## Step 1: Activate Debug Code

### If using Approach A (Temporary):

In **`nodes/identify_driver.py`** (or wherever you call save_semantic_memory):

Change this line:
```python
from nodes.save_semantic_memory import save_semantic_memory
```

To this:
```python
from nodes.save_semantic_memory_DEBUG import save_semantic_memory as save_semantic_memory
```

This imports the debug version without renaming your node in the graph.

---

### If using Approach B (Permanent):

Replace the files:
```bash
# In your workspace directory
mv nodes/save_semantic_memory.py nodes/save_semantic_memory_BACKUP.py
mv nodes/save_semantic_memory_DEBUG.py nodes/save_semantic_memory.py

mv memory/vector_memory.py memory/vector_memory_BACKUP.py
mv memory/vector_memory_DEBUG.py memory/vector_memory.py
```

Your existing imports will automatically use the debug versions.

---

## Step 2: Deploy to Render

1. Commit the debug files to your branch:
   ```bash
   git add nodes/save_semantic_memory_DEBUG.py
   git add memory/vector_memory_DEBUG.py
   git commit -m "Add extensive debugging to Pinecone pipeline"
   git push
   ```

2. Trigger a new Render deployment (automatic on push)

3. Wait for build and deploy to complete

---

## Step 3: Trigger a Test Call

Use OmniDimension webhook to create a new incoming call that will trigger semantic memory save:
- Make a call from your driver's phone number
- The call should end and trigger POST `/memory/save`
- This will execute your debug-instrumented code

---

## Step 4: Collect Logs

1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab
4. Look for lines starting with `[DEBUG-`
5. Copy all logs from when the webhook was received to the end
6. Save to a text file for analysis

---

## Step 5: Analyze Using the Debug Guide

Reference **`DEBUG_GUIDE.md`** and use the "Interpreting Full Execution Flow" section:

1. **Find the first `✓` checkpoint** - Code is reaching here successfully
2. **Find the first `❌` or missing checkpoint** - Code fails here
3. **Look up that checkpoint in the guide** - Get explanation and fix

---

## Common Issues & Quick Fixes

### Issue 1: No `[DEBUG-` logs appear at all

**Possible cause:** Debug code not being called

**Quick check:**
- Did you activate debug code (Step 1)?
- Did Render re-deploy (check build logs)?
- Are logs from the right time period?

**Fix:**
- Confirm you changed the import or replaced the files
- Check Render deployment timestamp matches your push
- Look at full Render logs, not just "Logs" tab

---

### Issue 2: Logs stop at `[DEBUG-SEMANTIC] CALLING save_memory()`

**Possible cause:** save_memory() crashed immediately

**What happened:**
- Semantic node executed successfully
- save_memory() was called
- But it failed before printing any debug logs

**Why:** save_memory is in vector_memory.py - did you activate those debug logs too?

**Fix:**
- Ensure memory/vector_memory_DEBUG.py is also deployed
- Change the import in save_semantic_memory to use DEBUG version
- Re-deploy and re-test

---

### Issue 3: `PINECONE_API_KEY exists: False`

**Possible cause:** Environment variables not set in Render

**Quick fix:**
1. Go to Render dashboard → your service → Environment
2. Add these variables:
   ```
   PINECONE_API_KEY = (your actual key)
   PINECONE_INDEX = signo-memory
   PINECONE_REGION = us-east-1
   PINECONE_CLOUD = aws
   ```
3. Click "Save"
4. Render will auto-redeploy
5. Test again

**Note:** `.env` files are NOT deployed to Render; must use dashboard

---

### Issue 4: `❌ FAILED TO LOAD MODEL`

**Possible cause:** sentence-transformers not installed or download failed

**Quick fix:**
1. Check `requirements.txt` includes:
   ```
   sentence-transformers>=2.2.0
   torch>=2.0.0
   ```
2. If missing, add it
3. Commit and push
4. Render will rebuild and re-test

**If still fails:**
- May be download timeout on Render free tier
- Consider using a smaller model or GPU tier

---

### Issue 5: `DIMENSION MISMATCH! Expected: 384, Found: 1536`

**Possible cause:** Index was created with wrong dimension

**Quick fix:**
1. Go to Pinecone console
2. Find your index in the Indexes tab
3. Delete it
4. Pinecone will auto-recreate on next save_memory() call
5. Re-test

**Why this happens:** Previous model used OpenAI embeddings (1536 dim), new uses sentence-transformers (384 dim)

---

### Issue 6: Logs show `upsert() returned` but Pinecone memory not appearing

**Possible cause:** Embedding generated successfully, but didn't actually save

**Check:**
1. In Pinecone console, check vector count in your index
2. Is it increasing with each test?
3. If count increases but you can't search, might be metadata issue

**Debug:**
- Look at `Safe metadata prepared:` section in logs
- Check all field types are correct (strings, not objects)
- Try searching by phone_number directly

---

## Quick Reference: Log Prefixes

| Prefix | Meaning | Where to Look |
|--------|---------|---------------|
| `[DEBUG-SEMANTIC]` | LangGraph orchestration | Logs start here when webhook received |
| `[DEBUG-SAVE]` | Main save_memory() flow | Step 1-7 show progression through embedding/index/upsert |
| `[DEBUG-EMBEDDING]` | Embedding generation | Check if model loads and dimensions match |
| `[DEBUG-PINECONE-CLIENT]` | Pinecone auth & connection | Check API key and network connectivity |
| `[DEBUG-INDEX]` | Index creation & verification | Check if index exists and has correct dimension |
| `[DEBUG-SEARCH]` | Vector search (if called) | Separate from save; shows search execution |

**Pro tip:** Search for `❌` to jump directly to first failure point

---

## Verify Setup: Pre-Deployment Checklist

Before testing, verify:

- [ ] Do you have Pinecone account with API key?
- [ ] Do you have PostgreSQL on Render with connection string?
- [ ] Is FastAPI running on Render?
- [ ] Do you have OmniDimension webhook configured?
- [ ] Are debug files in your repository?
- [ ] Have you activated the debug imports?
- [ ] Did Render complete the build?
- [ ] Can you access Render logs in real-time?

---

## Deactivating Debug Code

Once you identify and fix the issue:

### Option A: Keep debug code (recommended)
Leave it in place. Can conditionally disable with environment variable:

```python
import os

DEBUG_ENABLED = os.getenv("DEBUG_MODE", "False") == "True"

if DEBUG_ENABLED:
    print("[DEBUG-...] message")
```

Then set `DEBUG_MODE = False` in Render for production.

### Option B: Revert to original
```bash
# Restore from backups
mv nodes/save_semantic_memory_BACKUP.py nodes/save_semantic_memory.py
mv memory/vector_memory_BACKUP.py memory/vector_memory.py

# Or delete debug files
rm nodes/save_semantic_memory_DEBUG.py
rm memory/vector_memory_DEBUG.py
```

Then update imports back to originals.

---

## Emergency Logs Collection

If things are moving fast and you need to capture logs:

### In Render Dashboard:
1. Click "Logs" tab (not "Build & Deploy")
2. Scroll to the top
3. Select all text (Ctrl+A)
4. Copy (Ctrl+C)
5. Paste into text file
6. Attach to issue/support ticket

### Filter to just debug output:
Look for lines containing:
```
[DEBUG-SEMANTIC]
[DEBUG-SAVE]
[DEBUG-EMBEDDING]
[DEBUG-PINECONE-CLIENT]
[DEBUG-INDEX]
```

These are the instrumented checkpoints.

---

## Sharing Logs for Help

When asking for help, provide:

1. **First checkpoint reached:**
   ```
   ✓ ENTERING save_semantic_memory()
   ✓ CALLING save_memory()
   ```

2. **First failure checkpoint:**
   ```
   ❌ FAILED TO LOAD MODEL
   Exception: ModuleNotFoundError: No module named 'sentence_transformers'
   ```

3. **Full traceback** from the `❌` section

4. **Environment confirmation:**
   ```
   PINECONE_API_KEY exists: True/False
   PINECONE_INDEX value: 'signo-memory'
   ```

This pinpoints the exact issue within seconds.

---

## Next: Running Your Tests

1. Have OmniDimension ready to trigger a webhook
2. Start monitoring Render logs in real-time
3. Trigger a call
4. Watch logs appear in Render dashboard
5. Collect full output
6. Use DEBUG_GUIDE.md to interpret

Ready to debug!
