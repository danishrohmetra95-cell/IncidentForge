# API Reference

The IncidentForge FastAPI backend provides a RESTful interface for triggering investigations, querying state, and streaming live updates.

## Incident Lifecycle Endpoints

### `POST /api/incidents`
Creates a new incident record from an alert payload.
- **Request Body**: `title`, `description`, `severity`, `service`, `scenario_id` (optional).
- **Response**: The created `Incident` object.
- **Errors**: `422 Unprocessable Entity` for malformed payloads.

### `POST /api/incidents/demo`
Creates an incident pre-loaded from one of the deterministic scenarios and automatically kicks off the investigation.
- **Request Body**: `scenario_id` (e.g., `incident-001-db-pool`).
- **Response**: `incident_id` and confirmation.
- **Errors**: `400 Bad Request` if the `scenario_id` does not exist.

### `POST /api/incidents/{incident_id}/start`
Initiates the state machine orchestrator in the background for an existing incident.
- **Errors**: `404 Not Found` if incident is missing. `400 Bad Request` if the incident is already running or completed.

### `GET /api/incidents/{incident_id}`
Retrieves the full incident state, including current orchestrator state, active symptoms, hypotheses, experiments, and remediation status.

### `GET /api/incidents/{incident_id}/timeline`
Retrieves the structured audit log of all events and transitions that have occurred during the investigation.

## Live Streaming

### `GET /api/incidents/{incident_id}/events`
Server-Sent Events (SSE) stream.
- **Purpose**: Pushes live state transitions, agent outputs, and metric updates to the frontend in real-time.
- **Behavior**: Yields a `connected` event, then streams structured JSON. Yields keepalives on timeout. If the incident does not exist, it may return 404 or gracefully yield keepalives without crashing.

## Experiment & Reasoning Endpoints

### `GET /api/incidents/{incident_id}/hypotheses`
Returns the active array of hypotheses with their current normalized belief scores.

### `GET /api/experiments/{experiment_id}`
Returns the details of a designed experiment, its verification conditions, and baseline/post-intervention telemetry snapshots.

### `POST /api/hypotheses/{hypothesis_id}/challenge`
Manually triggers the `AdversarialCritic` to critique a specific hypothesis. (Primarily for testing/demo).

### `POST /api/experiments/{experiment_id}/execute`
Manually executes a designed experiment.
- **Errors**: `404 Not Found` if experiment is unknown. `400 Bad Request` for invalid transition (e.g., already executed).

## Remediation & Memory

### `GET /api/incidents/{incident_id}/remediation`
Fetches the formulated remediation plan (diff/config).
- **Errors**: `404 Not Found` if remediation hasn't been generated yet.

### `POST /api/remediation/{remediation_id}/validate`
Applies the remediation to a fresh Digital Twin to ensure all golden signals recover.
- **Response**: The `validation_status` and post-fix metrics.
- **Errors**: `404 Not Found` for unknown remediation.

### `GET /api/incidents/{incident_id}/memory`
Retrieves institutional memory records stored for a resolved incident.

## System

### `GET /api/health`
Checks backend status.
- **Response**: Returns `ok`, reasoning mode (live vs deterministic fallback), and Featherless AI gateway configuration status.
