# Complete Debugging Audit Guide: Pinecone Semantic Memory Pipeline

## Overview

This guide explains the extensive debug logging added to your semantic memory pipeline and how to interpret the output to identify exactly where execution stops in your Render deployment.

---

## File Changes

Two debug files have been created (ready to use):

1. **`nodes/save_semantic_memory_DEBUG.py`** - Enhanced version of `save_semantic_memory.py`
2. **`memory/vector_memory_DEBUG.py`** - Enhanced version of `vector_memory.py`

To activate debugging, replace the imports in your workflow or main.py to use these debug versions.

---

## What Each Debug Log Diagnoses

### Layer 1: LangGraph Orchestration (save_semantic_memory_DEBUG.py)

#### Log: `[DEBUG-SEMANTIC] ENTERING save_semantic_memory()`
- **Diagnoses:** Whether LangGraph is even reaching the semantic memory node
- **What it checks:** Node execution begins
- **If missing in logs:** The workflow isn't reaching this node at all

#### Log: `[DEBUG-SEMANTIC] state['memory_saved'] = {value}`
- **Diagnoses:** Whether PostgreSQL save succeeded before semantic save
- **What it checks:** PostgreSQL checkpoint status
- **If False:** PostgreSQL saved data is missing; skip semantic save and debug PostgreSQL first
- **If True:** Continue debugging vector memory

#### Logs: `[DEBUG-SEMANTIC] phone_number: '{value}'`, `call_summary: '{value}'`
- **Diagnoses:** Whether state data was properly extracted
- **What it checks:** Data structure integrity from previous nodes
- **If empty:** State propagation issue; data lost between nodes
- **If present:** State data is available; problem is downstream

#### Log: `[DEBUG-SEMANTIC] semantic_text constructed (len={value})`
- **Diagnoses:** Whether the semantic text was properly formatted
- **What it checks:** Text concatenation and validation
- **First 200 / Last 200 chars logs:** Help spot truncation or encoding issues

#### Log: `[DEBUG-SEMANTIC] CALLING save_memory()`
- **Diagnoses:** Ready to hand off to vector memory layer
- **What it checks:** All prerequisite checks passed
- **What happens next:** Execution transfers to `vector_memory_DEBUG.py`

---

### Layer 2: Vector Memory Operations (vector_memory_DEBUG.py)

#### A. Environment & Initialization (`_get_pinecone_client()`)

##### Log: `[DEBUG-PINECONE-CLIENT] PINECONE_API_KEY exists: True/False`
- **Diagnoses:** Whether environment variables are loaded in Render
- **If False:** 
  - `.env` file not deployed to Render
  - Environment variables not set in Render dashboard
  - `load_dotenv()` not called or not working
- **Action:** Check Render dashboard → Environment variables section
- **Render-specific issue:** Render doesn't auto-load `.env` files; must set manually

##### Log: `[DEBUG-PINECONE-CLIENT] PINECONE_INDEX value: 'signo-memory'`
##### Log: `[DEBUG-PINECONE-CLIENT] PINECONE_REGION value: 'us-east-1'`
##### Log: `[DEBUG-PINECONE-CLIENT] PINECONE_CLOUD value: 'aws'`
- **Diagnoses:** Whether all Pinecone configuration is loaded
- **If missing or showing defaults:** Check environment variable setup
- **Normal values:** Should match your Pinecone organization settings

##### Log: `[DEBUG-PINECONE-CLIENT] ✓ Pinecone client created successfully`
- **Diagnoses:** Network connection to Pinecone API successful
- **If missing:** 
  - Pinecone API is unreachable from Render (network issue)
  - API key is invalid
  - Render firewall blocking Pinecone connections

#### B. Embedding Generation (`get_embedding()`)

##### Log: `[DEBUG-EMBEDDING] Loading local embedding model...`
##### Log: `[DEBUG-EMBEDDING] ✓ Model loaded successfully`
- **Diagnoses:** Whether sentence-transformers is installed and model downloads
- **If fails immediately:** 
  - `sentence-transformers` not in requirements.txt
  - Model download failed (network issue from Render)
  - Insufficient disk space on Render
  - Permission issues downloading model files
- **Critical checkpoint:** If this fails, embedding generation cannot proceed

**Render-specific issues:**
- Render has limited disk space; model must fit (~50 MB)
- Model downloads happen on first app startup; may timeout
- No persistent storage; model downloaded every cold start (slow!)
- Solution: Consider pre-downloading model or caching to persistent volume

##### Log: `[DEBUG-EMBEDDING] Input text length: {value}`
##### Log: `[DEBUG-EMBEDDING] Text first 100 chars: {value}`
- **Diagnoses:** Data received by embedding function
- **If length 0:** Empty text passed (state data issue)
- **If unusual characters:** Text encoding problem

##### Log: `[DEBUG-EMBEDDING] Calling model.encode()...`
##### Log: `[DEBUG-EMBEDDING] ✓ encode() returned (type: numpy.ndarray)`
- **Diagnoses:** Model is executing in Render environment
- **If fails:** PyTorch or NumPy issue; model can't execute in Render's environment
- **Possible cause:** Render doesn't have Python dev headers; C extensions won't compile

##### Log: `[DEBUG-EMBEDDING] Embedding length: {value} (Expected: 384)`
- **Diagnoses:** Embedding dimension matches model
- **If not 384:** 
  - Wrong model loaded
  - Model library updated and changed output dimension
- **Mismatch is critical:** Cannot save to Pinecone if dimension doesn't match index

#### C. Index Management (`_get_or_create_index()`)

##### Log: `[DEBUG-INDEX] Existing indexes: ['signo-memory', 'other-index']`
- **Diagnoses:** Connection to Pinecone and accessible indexes
- **If empty:** 
  - No indexes exist; need to create one
  - Permission issue; can't list indexes
- **If 'signo-memory' present:** Index exists; proceed to verification

##### Log: `[DEBUG-INDEX] Index 'signo-memory' already exists`
- **Diagnoses:** Index found; no creation needed
- **Next step:** Verify its configuration (dimension, status)

##### Log: `[DEBUG-INDEX] Creating new Pinecone index...`
##### Log: `[DEBUG-INDEX] ✓ Create index command submitted`
- **Diagnoses:** Index creation initiated
- **Next:** Monitor readiness checks

##### Log: `[DEBUG-INDEX] Checking readiness (attempt 1/30)...`
##### Log: `[DEBUG-INDEX] Is ready: True`
- **Diagnoses:** Index initialization status
- **If never reaches ready=True:** 
  - Index creation queued but not progressing
  - Pinecone quota issue
  - API throttling

##### Log: `DIMENSION MISMATCH! Expected: 384, Found: X`
- **Diagnoses:** Index dimension incompatible with embedding model
- **If X ≠ 384:** 
  - Index was created with wrong dimension
  - Model library was updated and changed output size
- **Action:** Delete index and recreate OR change embedding model
- **Critical:** This will block ALL upserts until fixed

#### D. Pinecone Upsert (`save_memory()`)

##### Log: `[DEBUG-SAVE] STEP 2: Generating embedding...`
##### Log: `[DEBUG-SAVE] ✓ Embedding obtained (length: {value})`
- **Diagnoses:** Embedding generation checkpoint
- **If fails:** Debug output from `get_embedding()` will show why

##### Log: `[DEBUG-SAVE] STEP 3: Getting or creating Pinecone index...`
##### Log: `[DEBUG-SAVE] ✓ Index obtained (type: ...)`
- **Diagnoses:** Index access checkpoint
- **If fails:** Debug output from `_get_or_create_index()` will show why

##### Log: `[DEBUG-SAVE] STEP 7: Upserting to Pinecone index...`
##### Log: `[DEBUG-SAVE] 🔄 CALLING index.upsert() with 1 vector...`
- **Diagnoses:** About to send vector to Pinecone
- **This is the critical moment:** If next log is missing, upsert failed

##### Log: `[DEBUG-SAVE] ✓ upsert() returned`
- **Diagnoses:** Vector successfully sent and received by Pinecone
- **If missing:** Upsert call timed out or threw exception
- **If present:** Vector is in Pinecone; semantic memory save succeeded!

---

## Render-Specific Deployment Checklist

### 1. Environment Variables
- [ ] Set in Render dashboard (not in .env file)
- [ ] Required variables:
  - `PINECONE_API_KEY`
  - `PINECONE_INDEX`
  - `PINECONE_REGION`
  - `PINECONE_CLOUD`
- [ ] Check: Look for `PINECONE_API_KEY exists: True` in logs

### 2. Python Dependencies
- [ ] `requirements.txt` includes:
  ```
  sentence-transformers>=2.2.0
  pinecone-client>=4.0.0
  torch>=2.0.0
  ```
- [ ] Check: Look for `✓ Model loaded successfully` in logs
- [ ] If fails: Missing or incompatible package in Render environment

### 3. Disk Space & Model Caching
- [ ] Render free tier: Only ~400 MB disk
- [ ] `all-MiniLM-L6-v2` model: ~50 MB
- [ ] Check: Does model load on first cold start?
- [ ] Problem: Model re-downloads every cold start (slow startup time)
- [ ] Solution: Use smaller model or implement persistent caching

### 4. Network Access
- [ ] Render outbound network available to `api.pinecone.io`
- [ ] Check: Can reach Pinecone from Render
- [ ] Test: Try manual Pinecone SDK test in Render shell
- [ ] If blocked: Contact Render support about firewall

### 5. Build & Startup
- [ ] No compilation errors during build
- [ ] Model downloads complete during startup (monitor logs)
- [ ] If timeouts: Model download taking too long; need pre-fetch strategy

---

## How to Activate Debugging

### Option 1: Temporary Testing
In your main workflow file (e.g., `graphs/fetch_memory_graph.py`):

```python
# Change from:
from nodes.save_semantic_memory import save_semantic_memory

# To:
from nodes.save_semantic_memory_DEBUG import save_semantic_memory
```

And in your memory imports (e.g., `nodes/save_semantic_memory_DEBUG.py`):

```python
# Change from:
from memory.vector_memory import save_memory

# To:
from memory.vector_memory_DEBUG import save_memory
```

### Option 2: Permanent Integration
Replace the original files with debug versions:

```bash
cp nodes/save_semantic_memory_DEBUG.py nodes/save_semantic_memory.py
cp memory/vector_memory_DEBUG.py memory/vector_memory.py
```

---

## Interpreting Full Execution Flow

### Success Path
```
✓ ENTERING save_semantic_memory()
✓ state['memory_saved'] = True
✓ phone_number extracted
✓ semantic_text constructed
✓ CALLING save_memory()
  ✓ ENTERING save_memory()
  ✓ Generating embedding...
    ✓ Model loaded successfully
    ✓ Embedding obtained (length: 384)
  ✓ Getting or creating Pinecone index...
    ✓ Index obtained
  ✓ STEP 7: Upserting to Pinecone index...
    ✓ upsert() returned
✓ save_memory() returned semantic_memory object
✓ semantic_memory saved successfully
✓ SEMANTIC MEMORY PIPELINE COMPLETED SUCCESSFULLY
```

If you see all these logs, your Pinecone semantic memory is working!

### Failure Path Example 1: Missing Environment Variables
```
ENTERING save_semantic_memory()
state['memory_saved'] = True
CALLING save_memory()
  ENTERING save_memory()
  Generating embedding...
    Loading local embedding model...
    ✓ Model loaded successfully
    ✓ Embedding obtained (length: 384)
  Getting or creating Pinecone index...
    Initializing Pinecone client...
    ❌ PINECONE_API_KEY exists: False
    ❌ EXCEPTION IN _get_pinecone_client()
    Exception: PINECONE_API_KEY is missing
```

**Action:** Set PINECONE_API_KEY in Render environment variables

### Failure Path Example 2: Dimension Mismatch
```
Getting or creating Pinecone index...
  Existing indexes: ['signo-memory']
  ✓ Index 'signo-memory' already exists
  Extracted index dimension: 1536
  Expected dimension: 384
  ❌ DIMENSION MISMATCH! Expected: 384, Found: 1536
```

**Action:** Delete index in Pinecone and recreate with dimension 384

### Failure Path Example 3: Model Download Failure
```
Loading local embedding model...
Model name: all-MiniLM-L6-v2
❌ FAILED TO LOAD MODEL
Exception type: FileNotFoundError
Exception: Model files not downloaded
```

**Action:** 
- Check if `sentence-transformers` is in requirements.txt
- Verify Render has internet access during build
- Check Render logs for timeouts during model download

---

## Key Diagnostics Summary Table

| Symptom | Log to Check | Likely Cause |
|---------|--------------|--------------|
| Semantic memory never saved | No `save_semantic_memory()` logs | Workflow not reaching semantic node |
| No Pinecone logs | `state['memory_saved'] = False` | PostgreSQL save failed first |
| Embedding fails | `❌ FAILED TO LOAD MODEL` | sentence-transformers missing/download failed |
| Pinecone connection fails | `PINECONE_API_KEY exists: False` | Environment variables not set in Render |
| Upsert never returns | Missing `✓ upsert() returned` | Network timeout or quota exceeded |
| Dimension mismatch error | `DIMENSION MISMATCH!` | Index created with wrong dimension |
| Logs cut off mid-operation | No final `✓` messages | Process crashed or timed out |

---

## Render-Specific Tips

### Cold Start Optimization
First request after deploy will be slow because:
1. Python environment starts
2. PyTorch loads
3. Model downloads (~50 MB)
4. First API request completes

### Monitor Build Logs
In Render dashboard:
1. Go to your service
2. Click "Build & Deploy" tab
3. Watch the build and deploy logs
4. Look for:
   - `pip install` output (check for errors)
   - Model download progress
   - Any Python syntax errors

### Test in Render Shell
SSH into your Render service:
```bash
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print(m)"
python -c "from pinecone import Pinecone; c = Pinecone(api_key='...'); print(c.list_indexes())"
```

### Check Render Logs
Real-time logs show print statements:
1. Go to Render dashboard → your service
2. Click "Logs" tab
3. Filter by the logs (search for `[DEBUG-` prefix)
4. Follow execution in real-time as requests come in

---

## Production Considerations

The debug logging is production-safe because:
1. **No sensitive data:** API keys not printed in full
2. **Structured logging:** All logs use `[DEBUG-*]` prefix for easy filtering
3. **Performance:** Extra logging adds negligible overhead
4. **Error handling:** Full stack traces help with troubleshooting
5. **Cleanup:** Once working, can be removed or conditionally disabled

To disable all debug logs once resolved:
```python
import os
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

if DEBUG_MODE:
    print("[DEBUG-...] message")
```

---

## Next Steps

1. **Activate debug code** using Option 1 or 2 above
2. **Deploy to Render** (push changes to your branch)
3. **Trigger a semantic memory save** via OmniDimension webhook
4. **Collect full logs** from Render dashboard
5. **Share logs** starting from `ENTERING save_semantic_memory()` to the end
6. **Use this guide** to interpret which checkpoint failed
7. **Fix the specific issue** identified by the logs
8. **Re-test** with new webhook call
9. **Remove debug code** once working (or keep it for future troubleshooting)

---

## Additional Resources

- **Pinecone SDK:** https://docs.pinecone.io/home
- **sentence-transformers:** https://www.sbert.net/
- **Render deployment:** https://render.com/docs
- **Environment variables in Render:** https://render.com/docs/environment-variables

---

## Questions to Answer From Logs

Once you deploy and generate logs, answer these:

1. **Does `PINECONE_API_KEY exists: True` appear?**
   - No → Set environment variables in Render

2. **Does `✓ Model loaded successfully` appear?**
   - No → Add `sentence-transformers` to requirements.txt

3. **Does `Embedding obtained (length: 384)` appear?**
   - No → Model has different output dimension; check model compatibility

4. **Does `✓ Index obtained` appear?**
   - No → Pinecone connection issue; check API key and network

5. **Does `DIMENSION MISMATCH` appear?**
   - Yes → Delete index in Pinecone console and recreate

6. **Does `✓ upsert() returned` appear?**
   - No → Pinecone API error; check quota and permissions

7. **Does the last checkpoint `✓ SEMANTIC MEMORY PIPELINE COMPLETED SUCCESSFULLY` appear?**
   - Yes → Semantic memory save succeeded!
   - No → Look for the last `✓` or `❌` message to find failure point

**Provide the complete log sequence and these answers for quick diagnosis.**
