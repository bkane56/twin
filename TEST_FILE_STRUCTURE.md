# Digital Twin test starter file structure

Copy these files into the `bkane56/twin` repository from the repo root.

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_bedrock.py
│       └── test_memory.py
├── frontend/
│   ├── __tests__/
│   │   └── twin.test.tsx
│   ├── jest.config.js
│   ├── jest.setup.ts
│   └── package.json
└── TEST_COVERAGE.md
```

## Important package.json note

The included `frontend/package.json` removes the direct dependency on `@next/swc-darwin-x64`.

Do not directly depend on any `@next/swc-*` package. Next.js manages platform-specific SWC packages internally. Keeping `@next/swc-darwin-x64` as a direct dependency causes Apple Silicon and Linux GitHub Actions installs to fail.

After copying `frontend/package.json`, regenerate the frontend lockfile:

```bash
cd frontend
rm -rf node_modules .next out yarn.lock
yarn cache clean
yarn install --ignore-platform
yarn test:ci
yarn build
```

Then commit the updated `frontend/yarn.lock`.

## Backend local test command

```bash
cd backend
uv sync --extra test
uv run pytest --cov=. --cov-report=term-missing
```

## Frontend local test command

```bash
cd frontend
yarn install --ignore-platform
yarn test:ci
```

## CI behavior

The included `.github/workflows/ci.yml` runs backend and frontend tests on pull requests and pushes to `main` and `develop`.

This workflow does not deploy anything and does not require AWS credentials.
