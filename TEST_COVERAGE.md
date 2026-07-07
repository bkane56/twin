# Test Coverage and Validation Strategy

This project uses a focused test strategy around the seams most likely to break in a full-stack AI application: API behavior, conversation memory, Bedrock request construction, frontend chat behavior, and CI validation.

## What is covered

### Backend

The backend tests cover:

- `GET /health` runtime health response.
- `GET /` service metadata response.
- `POST /chat` request validation for missing input.
- `POST /chat` success behavior with Bedrock mocked.
- `POST /chat` error behavior when model orchestration fails.
- `GET /conversation/{session_id}` indirectly through memory behavior.
- Local conversation memory save/load behavior.
- Bedrock Nova request construction with the AWS client mocked.

The backend tests intentionally avoid calling live AWS Bedrock or S3. Those integrations are mocked at the service boundary so the test suite can run safely in local development and GitHub Actions without AWS credentials.

### Frontend

The frontend tests cover:

- Rendering the default AI Twin chat state.
- Disabled send button behavior when the input is empty.
- Sending a chat message to the configured backend API.
- Rendering the assistant response returned from the API.
- Enter-key submission behavior.
- Error-state rendering when the backend request fails.

The frontend tests mock `fetch`, including the avatar lookup and `/chat` request, so they do not require a running backend.

### CI

The CI workflow runs on pull requests and pushes to `main` and `develop`:

- Backend tests run with Python 3.12 and `uv`.
- Frontend tests run with Node 22 and Yarn.
- Frontend dependency installation uses `--ignore-platform` because Next.js includes platform-specific SWC packages, and this repository is developed on Apple Silicon while GitHub Actions runs on Linux.

## What is intentionally not covered by unit tests

These areas are intentionally not called from unit tests:

- Live AWS Bedrock model invocation.
- Live S3 bucket reads/writes.
- CloudFront behavior.
- Terraform apply/destroy.
- GitHub Actions deployment authorization.

Those are better validated through deployment checks, Terraform plans, protected GitHub environments, AWS OIDC trust policy, health checks, and manual smoke tests after deployment.

## Local commands

### Backend

```bash
cd backend
uv sync --extra test
uv run pytest --cov=. --cov-report=term-missing
```

### Frontend

```bash
cd frontend
yarn install --ignore-platform
yarn test:ci
```

## Practical coverage goal

The goal is not arbitrary high coverage. The goal is meaningful coverage around the application boundaries that matter most:

- API contract.
- Model orchestration boundary.
- Conversation memory boundary.
- User chat interaction.
- CI repeatability.

This gives the project a credible engineering-quality baseline without pretending that unit tests can fully validate live cloud infrastructure or generative AI behavior.
