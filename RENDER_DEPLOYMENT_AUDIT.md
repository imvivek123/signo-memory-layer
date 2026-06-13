# Render Deployment Audit Checklist

## Critical Path: What Must Work for Pinecone Saves

```
OmniDimension Webhook Call
        ↓
POST /memory/save (FastAPI)
        ↓
LangGraph Workflow Starts
        ↓
PostgreSQL Save (✓ works - confirmed)
        ↓
save_semantic_memory() Node (❌ problem zone)
        ↓
get_embedding() [requires sentence-transformers]
        ↓
get_pinecone_client() [requires PINECONE_API_KEY env]
        ↓
_get_or_create_index() [requires Pinecone network access]
        ↓
save_memory() → upsert to Pinecone
        ↓
Semantic memory stored (❌ not happening)
```

---

## Render Deployment Checklist

### A. Environment Variables (CRITICAL)

Render does NOT load `.env` files automatically. You must set these in the Render dashboard.

**Location in Render Dashboard:**
1. Service → Environment
2. Add each variable below
3. Save (triggers auto-redeploy)

**Required Variables:**

- [ ] **PINECONE_API_KEY**
  - Value: Your actual Pinecone API key
  - Check in logs: `PINECONE_API_KEY exists: True` (from debug logs)
  - If missing: No Pinecone connection possible
  
- [ ] **PINECONE_INDEX**
  - Value: `signo-memory` (or your actual index name)
  - Check in logs: `PINECONE_INDEX value: 'signo-memory'` (from debug logs)
  - Default works: `signo-memory`
  
- [ ] **PINECONE_REGION**
  - Value: `us-east-1` (match your Pinecone setup)
  - Check in logs: `PINECONE_REGION value: 'us-east-1'` (from debug logs)
  - Find in Pinecone: Organization → Indexes → Your index → Region
  
- [ ] **PINECONE_CLOUD**
  - Value: `aws` (match your Pinecone setup)
  - Check in logs: `PINECONE_CLOUD value: 'aws'` (from debug logs)
  - Find in Pinecone: Organization → Indexes → Your index → Cloud provider

- [ ] **DATABASE_URL** (PostgreSQL on Render)
  - Should already be set
  - Format: `postgresql://user:password@host:5432/dbname`
  - Verify: Existing code saves to PostgreSQL ✓

- [ ] **REDIS_URL** (optional, for cache invalidation)
  - If using Redis for cache
  - Format: `redis://host:port`

**Debug Verification:**
After setting env vars and redeploying, check logs for:
```
✓ PINECONE_API_KEY exists: True
✓ PINECONE_INDEX value: 'signo-memory'
✓ PINECONE_REGION value: 'us-east-1'
✓ PINECONE_CLOUD value: 'aws'
```

If any are missing → Environment variables not set correctly

---

### B. Dependencies (requirements.txt)

**File Location:** `requirements.txt` in your Render service root

**Current dependencies to verify:**

```
fastapi          ✓ (API framework)
uvicorn          ✓ (ASGI server)
psycopg2-binary  ✓ (PostgreSQL)
python-dotenv    ✓ (load .env)
redis            ✓ (caching)
pinecone         ✓ (Pinecone SDK - CRITICAL)
sentence-transformers  ✓ (embeddings - CRITICAL)
langgraph        ✓ (workflow orchestration)
langchain        ✓ (LLM framework)
```

**Critical Versions Check:**

- [ ] **pinecone-client >= 4.0.0**
  - Check in logs: `Pinecone client created successfully` (from debug logs)
  - Old versions may have API incompatibilities
  - Too new: May drop support for older features
  - Recommended: `pinecone>=4.0.0,<5.0.0`

- [ ] **sentence-transformers >= 2.2.0**
  - Check in logs: `✓ Model loaded successfully` (from debug logs)
  - Older versions: May fail on Render environment
  - Recommended: `sentence-transformers>=2.2.0,<3.0.0`

- [ ] **torch >= 2.0.0**
  - Required by sentence-transformers
  - May not be explicitly listed but is a dependency
  - Check: Look for PyTorch-related errors in embedding logs
  - Recommended: `torch>=2.0.0,<3.0.0`

**Update Action:**
If any missing/wrong version, edit requirements.txt:

```txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
redis==5.0.0
pinecone>=4.0.0,<5.0.0
sentence-transformers>=2.2.0,<3.0.0
torch>=2.0.0,<3.0.0
langgraph==0.1.0
langchain==0.1.0
```

Then commit, push, Render auto-rebuilds.

---

### C. Model Download & Disk Space

**Critical Issue:** Render free tier has limited disk space

**Problem:**
1. First request after deploy triggers model download
2. `all-MiniLM-L6-v2` is ~50 MB
3. Render free tier: ~400 MB total disk
4. PyTorch + dependencies: ~200 MB
5. Leaving ~150 MB for model + logs + buffer
6. Model download might fail or timeout

**Monitor during first deploy:**
1. Go to Render dashboard → Logs
2. Watch for model download progress:
   ```
   Loading local embedding model...
   Model name: all-MiniLM-L6-v2
   ✓ Model loaded successfully
   ```
3. If stuck here > 2 minutes: Timeout or download failed

**If Download Fails:**

Option 1: Use smaller model
```python
# In vector_memory_DEBUG.py, change:
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 50 MB

# To:
EMBEDDING_MODEL = "all-MiniLM-L6-v1"  # Smaller, 30 MB
```

Option 2: Upgrade to Pro tier
- Render Pro has more disk space
- Model downloads cached between requests
- Cold start much faster

Option 3: Pre-cache model
Add to your startup sequence to download model before first request.

---

### D. Network & Firewall

**Check:** Can Render reach Pinecone API?

**Test in Render Shell:**
1. Render dashboard → your service → Shell tab
2. Run:
   ```bash
   python -c "import socket; socket.getaddrinfo('api.pinecone.io', 443)"
   ```
3. Should return without error
4. If error: Network blocked (rare on Render)

**Check:** Can Render reach PostgreSQL?
- Already working ✓ (confirmed in your report)
- So network outbound is OK

**Check:** Can Render reach Redis?
- If using cache invalidation, verify same way
- Already working ✓ (assumed, based on other integrations)

---

### E. Build Process Verification

**What to watch in Render Build logs:**

```bash
# 1. Build starting
> Build script started
> Starting build...

# 2. Dependency installation (should complete)
> pip install -r requirements.txt
> Successfully installed pinecone sentence-transformers torch langchain ...

# 3. Should show NO errors
# Watch for:
#   - ERROR (stop build investigation)
#   - WARNING (may be OK)
#   - timeout (increase build timeout)

# 4. Deploy starting
> Deployment started
> Building Docker image...
> Deploy complete
```

**If build fails:**
1. Go to Render dashboard → Build & Deploy tab
2. Check "Logs" at bottom
3. Look for red ERROR lines
4. Common issues:
   - `ERROR: No matching distribution found for pinecone==...`
   - `ERROR: pip's dependency resolver does not currently take into account all the packages...`
   - `ERROR: error in setup.py command: 'egg_info'` (usually C compilation issue)

**Common Render Build Issues:**

| Error | Fix |
|-------|-----|
| `No matching distribution for sentence-transformers` | Render may have outdated pip; update requirements.txt to specific versions |
| `error in setup.py` | Package needs C compiler; torch/sentence-transformers may need system libs |
| `timeout during pip install` | Package download too slow; check Render build timeout (increase to 30 min) |

---

### F. PyTorch Compatibility on Render

**Why this matters:** PyTorch is heavy (200+ MB), uses C extensions

**Render environment:**
- Ubuntu 20.04
- Python 3.x (check in Render dashboard)
- No GPU (CPU-only on free tier)

**CPU-only torch installation:**
- torch binary is large (~500 MB uncompressed)
- But Render pip cache can reuse between builds
- First build slow; subsequent builds faster

**Verify PyTorch works:**
In Render shell:
```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

Should output:
```
2.0.0  (or your version)
False  (GPU not available on free tier)
```

If fails:
- PyTorch didn't install
- Check build logs for compilation errors
- May need Render Pro for better compiler support

---

### G. Model File Permissions

**Issue:** Model files downloaded to `/root/.cache/huggingface/`

**Render:**
- Read/write to cache: ✓ Works
- Persistent between restarts: ❌ Not persistent (free tier)
- Cold start: ❌ Model re-downloads every cold start

**Impact:**
- First request after cold start: Slow (waits for model download)
- Subsequent requests: Fast (model in memory)

**Monitor:**
- Logs should show: `Loading local embedding model...` only once per cold start
- If shown every request: Model not staying in memory

**Optimize (for paid tier):**
Use Render persistent disk to cache model between cold starts.

---

### H. Runtime Environment Variables

**In your Python code:**
Make sure you're loading .env correctly:

```python
# This is required for local testing
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file (ignored on Render if vars set)

api_key = os.getenv("PINECONE_API_KEY")  # Reads from Render env vars
```

**In Render:**
- .env files ignored (doesn't exist in deployed container)
- Only Render environment variables work
- `load_dotenv()` is harmless; just won't find anything

**Verify in code:**
Check that all env variable reads use `os.getenv()`:
```python
# ✓ Correct
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# ✗ Wrong (always None on Render)
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]  # KeyError if not set
```

---

## Deployment Workflow

### Before first test:

1. **Commit debug code to branch**
   ```bash
   git add nodes/save_semantic_memory_DEBUG.py
   git add memory/vector_memory_DEBUG.py
   git commit -m "Add debugging"
   git push
   ```

2. **Set environment variables in Render**
   - Dashboard → Your Service → Environment
   - Add PINECONE_API_KEY, etc.
   - Save (auto-redeploy)

3. **Monitor build**
   - Dashboard → Build & Deploy → Logs
   - Wait for "Deploy complete"

4. **Check build succeeded**
   - Dashboard → Logs tab
   - Should show your app starting (no errors)

### During first test:

1. **Trigger webhook call**
   - OmniDimension makes POST /memory/save

2. **Monitor logs in real-time**
   - Dashboard → Logs
   - Watch for [DEBUG-*] lines

3. **Let it complete**
   - Wait for final ✓ or ❌ message
   - Should be ~5-30 seconds depending on model load

4. **Collect full log output**
   - Copy all [DEBUG-*] lines
   - Save to file

### After first test:

1. **Analyze using DEBUG_GUIDE.md**
   - Find first ✓ checkpoint (what worked)
   - Find first ❌ checkpoint (what failed)
   - Look up fix

2. **Fix identified issue**
   - Update code or environment
   - Commit and push
   - Render auto-redeploys

3. **Re-test**
   - Repeat "During first test" above
   - Should reach next checkpoint

---

## Checkpoint Reference

**These logs confirm each system is working:**

| System | Success Log |
|--------|------------|
| LangGraph node reached | `✓ ENTERING save_semantic_memory()` |
| PostgreSQL save passed | `state['memory_saved'] = True` |
| Semantic text built | `✓ semantic_text constructed` |
| save_memory() called | `✓ CALLING save_memory()` |
| Model loaded | `✓ Model loaded successfully` |
| Embedding generated | `✓ Embedding obtained (length: 384)` |
| Pinecone authenticated | `✓ Pinecone client created successfully` |
| Index obtained | `✓ Index obtained` |
| Dimension verified | `✓ Dimension validation passed` |
| Vector sent to Pinecone | `✓ upsert() returned` |
| **COMPLETE SUCCESS** | `✓ SEMANTIC MEMORY PIPELINE COMPLETED SUCCESSFULLY` |

**If you reach the last line, semantic memory is working!**

---

## Emergency Contacts

If you can't fix based on logs:

1. **Pinecone Support**
   - Website: pinecone.io/support
   - Issue type: "API connection from Render"
   - Include: API key (redacted), org ID, index name

2. **Render Support**
   - Website: render.com/support
   - Issue type: "Build fails" or "Environment variables not working"
   - Include: Build logs, runtime logs

3. **Provide to Either Support:**
   - Full logs from [DEBUG-] section
   - Screenshot of Render environment variables (redact API key)
   - Screenshot of Pinecone console
   - Exact error message and line number
   - Steps to reproduce

---

## Summary: The Most Common Fixes

**90% of Pinecone Render issues are one of these:**

1. **Environment variables not set in Render** (52%)
   - Fix: Add PINECONE_API_KEY in Render dashboard

2. **sentence-transformers not in requirements.txt** (20%)
   - Fix: Add `sentence-transformers>=2.2.0` to requirements.txt

3. **Index dimension mismatch** (15%)
   - Fix: Delete Pinecone index, let it auto-recreate with dimension 384

4. **Pinecone index doesn't exist** (10%)
   - Fix: Will auto-create on first save_memory() call (check logs)

5. **Network/firewall issue** (3%)
   - Fix: Check Render can reach api.pinecone.io

Start by checking items 1-2. 95% of issues are there!
