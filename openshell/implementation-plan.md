# OpenShell + Vertex AI Implementation Plan

## 1. Implementation Plan

The goal is to run Claude (via Google Vertex AI) inside an OpenShell sandbox so that the agent's network and filesystem access is policy-enforced. This requires two things:

- **OpenShell issue #472** — adds a `vertex` provider type with automatic OAuth2 token refresh to the OpenShell gateway. Without this, Vertex AI credentials expire after 1 hour and fail silently.
- **Vertex AI configuration** — a GCP service account with appropriate permissions and the Anthropic models enabled in Model Garden.

### What issue #472 adds

A `CredentialRefresher` background task in the OpenShell gateway that:

1. Reads the service account JSON key stored in the provider record (`GOOGLE_SERVICE_ACCOUNT_JSON`)
2. Exchanges it for a short-lived OAuth2 Bearer token every ~10 minutes (well within the 1-hour expiry)
3. Writes the fresh token back to the provider record (`VERTEX_ACCESS_TOKEN`)
4. The sandbox detects the updated token via its existing 30-second bundle poll and hot-swaps it without restarting

**User-facing workflow once #472 is merged:**

```bash
openshell provider create \
  --type vertex \
  --name my-vertex \
  --credential "GOOGLE_SERVICE_ACCOUNT_JSON=$(cat sa.json)" \
  --config "VERTEX_BASE_URL=https://europe-west1-aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/europe-west1/publishers/anthropic/models/claude-sonnet-4-6:rawPredict"

openshell inference set --provider my-vertex --model claude-sonnet-4-6
openshell sandbox create -- claude
```

### Current status

- Issue #472 is open on NVIDIA/OpenShell with `state:review-ready`
- An implementation plan has been posted on the issue
- A local feature branch `feat/472-vertex-credential-refresh` exists in the kpiwko fork
- Implementation is **pending legal review** before code is written

---

## 2. Service Account Token — AI Assessment Requirement

**To investigate:** Does obtaining or using a GCP service account key for Vertex AI inference require an AI Assessment or AI Impact Assessment under company policy?

Key factors to document with legal/compliance:

- The service account key is used to call the Anthropic Claude API hosted on Google Cloud (Vertex AI), not a self-hosted model
- Data sent to the model goes through Google's infrastructure and is subject to Google's data processing terms
- The service account key itself is a credential stored in the OpenShell gateway's database (SQLite or Postgres) — it never leaves the gateway process
- Token exchange happens server-side; the sandbox never sees the raw service account key

**Action required:** Confirm with legal/IT security whether a service account key used for third-party AI inference via Vertex AI triggers an AI assessment process before use in production or developer tooling.

---

## 3. Enabling Anthropic Models in GCP Project

Before API calls work, two things must be done in the GCP project:

### 3a. Enable the Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com --project=<PROJECT_ID>
```

### 3b. Accept model terms in Model Garden

Each Claude model must be individually enabled via the GCP Console:

1. Go to [Vertex AI Model Garden](https://console.cloud.google.com/vertex-ai/model-garden)
2. Filter by **Anthropic** provider
3. Open each Claude model card (e.g. Claude Sonnet 4.6)
4. Click **Enable** and accept the terms of service

This is a one-time per-model, per-project action. Without it, API calls return a permission error even with correct IAM roles.

### 3c. IAM permissions for the service account

The service account needs only:

```
roles/aiplatform.user
```

Or at minimum the single IAM permission:

```
aiplatform.endpoints.predict
```

**Action required:** Confirm whether enabling Anthropic models in a GCP project requires approval from IT, a vendor review, or any procurement step. Anthropic models on Vertex AI are billed through the GCP project's billing account.

---

## 4. IT Global Rollout

**To investigate:** Does IT plan to roll out Vertex AI / Anthropic model access globally across all GCP projects, or is it project-by-project?

Questions to resolve with IT:

- Is there a shared GCP project that already has Anthropic models enabled that developers can use, rather than each team enabling their own?
- Is there a standard service account or Workload Identity setup that should be used instead of per-developer service account keys?
- Are there data residency requirements that affect which region (`europe-west1`, `us-central1`, `global`) should be used?
- Will IT manage the Vertex AI billing account centrally, or is each team responsible?

**Implication for OpenShell:** If IT provides a shared project with Workload Identity Federation instead of service account JSON keys, issue #472's implementation may need to support [Workload Identity](https://cloud.google.com/iam/docs/workload-identity-federation) as an alternative auth path (no JSON key required). This is out of scope for the current plan but worth noting.

---

## 5. The `global` Region Problem

### What `global` means in Claude Code

Claude Code sets `CLOUD_ML_REGION=global` which Anthropic's SDK maps to the endpoint:

```
https://aiplatform.googleapis.com/v1/...  (no region prefix)
```

This works because Anthropic's SDK has built-in knowledge of this mapping.

### Why `global` doesn't work well in OpenShell today

OpenShell's inference router makes raw HTTP calls — it does not use the Anthropic SDK. The URL is constructed directly from the `VERTEX_BASE_URL` config value. If a user sets:

```
VERTEX_BASE_URL=https://aiplatform.googleapis.com/v1/projects/.../locations/global/...
```

This may or may not route correctly depending on whether Google's global endpoint accepts Claude model calls for that project and region. In testing, `global` can return errors where an explicit region (`europe-west1`) succeeds.

### Recommendation

Always use an explicit region in `VERTEX_BASE_URL`. The confirmed working pattern is:

```
https://<REGION>-aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/<REGION>/publishers/anthropic/models/<MODEL>:rawPredict
```

For example:

```
https://europe-west1-aiplatform.googleapis.com/v1/projects/developer---gemini-api/locations/europe-west1/publishers/anthropic/models/claude-sonnet-4-6:rawPredict
```

### Validating your URL before configuring OpenShell

```bash
curl -X POST \
  "https://europe-west1-aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/europe-west1/publishers/anthropic/models/claude-sonnet-4-6:rawPredict" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "anthropic_version": "vertex-2023-10-16",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "hi"}]
  }'
```

A successful response confirms the URL, project permissions, and model enablement are all correct before wiring into OpenShell.

### Future: making `global` work

If IT confirms `global` routing is the standard, issue #472 could be extended to support region aliases — mapping `global` to the no-prefix endpoint. This is not in the current implementation scope.
