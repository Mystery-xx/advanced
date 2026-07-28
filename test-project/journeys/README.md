# UI E2E Tests with Playwright

This directory contains End-to-End (E2E) tests for the application using Playwright and Gherkin BDD syntax.

## Test Structure

```
journeys/
├── features/              # Gherkin feature files
│   ├── registration.feature
│   ├── error-handling.feature
│   ├── admin-flow.feature
│   └── onboarding.feature
└── steps/                 # Step definitions (TypeScript)
    └── registration.steps.ts
```

## Registration Test Scenarios

The `registration.feature` file contains 3 scenarios:

1. **Successful registration with valid data**
   - Fills registration form with valid details
   - Submits the form
   - Verifies successful registration
   - Verifies redirect to dashboard

2. **Registration fails with duplicate email**
   - Attempts to register with an existing email
   - Verifies error message is shown
   - Verifies user remains on registration page

3. **Registration fails with invalid password**
   - Attempts to register with a weak password
   - Verifies password requirements error
   - Verifies user remains on registration page

## Prerequisites

Before running the tests, ensure:

1. **Frontend is running** on `http://localhost:3000`
   ```bash
   cd test-project/frontend
   npm run dev
   ```

2. **Playwright is installed**
   ```bash
   npm install playwright
   ```

3. **Backend services** (optional, for full integration tests)
   ```bash
   cd test-project
   docker-compose up
   ```

## Running Tests

### Run All Tests

```bash
node run-ui-tests.js
```

### Test Output

The test runner will:
- Execute all scenarios sequentially
- Capture screenshots for each step
- Generate an HTML report

### Viewing Results

After test execution:

1. **HTML Report**: `playwright-report/index.html`
   - Summary of all scenarios
   - Pass/fail status for each step
   - Embedded screenshots

2. **Screenshots**: `playwright-report/screenshots/`
   - One screenshot per test step
   - Named by scenario and step number

## Test Runner Features

- **Headless execution**: Tests run in headless Chromium
- **Automatic screenshots**: Every step captures a screenshot
- **HTML report**: Visual report with pass/fail indicators
- **Retry logic**: Built-in retry for flaky steps
- **Error handling**: Continues execution even if individual steps fail

## Adding New Scenarios

1. Create a new `.feature` file in `journeys/features/`
2. Add step definitions in `journeys/steps/`
3. Add scenario execution function in `run-ui-tests.js`
4. Register the scenario in the main execution block

## CI/CD Integration

The tests can be run in CI pipelines:

```yaml
# Example GitHub Actions step
- name: Run UI Tests
  run: node run-ui-tests.js
  env:
    APP_URL: http://localhost:3000
```

## Troubleshooting

### Frontend Not Responding

```bash
# Check if frontend is running
curl http://localhost:3000

# Start frontend if not running
cd test-project/frontend && npm run dev
```

### Playwright Installation Issues

```bash
# Install Playwright browsers
npx playwright install chromium

# Install system dependencies (Linux)
npx playwright install-deps
```

### Test Failures

1. Check the HTML report for detailed error messages
2. Review screenshots to see the application state
3. Verify the frontend is in the expected state
4. Check browser console logs (temporarily set `headless: false`)

## Modifying Test Behavior

### Change App URL

Edit `run-ui-tests.js`:
```javascript
const APP_URL = 'http://localhost:3000'; // Change to your URL
```

### Run in Headed Mode

Edit `run-ui-tests.js`:
```javascript
const browser = await chromium.launch({
  headless: false, // Show browser window
  // ...
});
```

### Adjust Timeouts

Edit step execution functions:
```javascript
await page.waitForTimeout(2000); // Increase/decrease wait time
```

## Best Practices

1. **Use data-testid attributes** for stable selectors
2. **Keep scenarios independent** - clear state between tests
3. **Make assertions explicit** - verify expected outcomes
4. **Capture meaningful screenshots** - after each significant action
5. **Document edge cases** in feature files with clear scenarios