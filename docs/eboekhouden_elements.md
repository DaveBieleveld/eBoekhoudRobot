# E-boekhouden Website Elements Reference

This document serves as a technical reference for the e-boekhouden website elements used in our Robocorp tasks. It documents all critical URLs, selectors, and interactive elements required for automation.

## Base URLs

- Main Portal: `https://secure20.e-boekhouden.nl/bh/`
- Hours Overview: `https://secure20.e-boekhouden.nl/uren/overzicht`
- Add Hours Direct: `https://secure20.e-boekhouden.nl/uren/overzicht/0`

## Code Flow and Architecture

### Client Initialization
1. `EBoekhoudenClient` is initialized with:
   - Playwright browser launch (Chromium, non-headless, slow_mo=50)
   - Enhanced browser context settings:
     - Custom user agent for Chrome 121
     - Viewport 1920x1080
     - HTTPS errors ignored
     - JavaScript enabled
     - CSP bypassed
     - Service workers blocked
     - Downloads enabled
     - Strict selectors mode
   - Screenshot directory setup in `temp/screenshots`
   - Cookie clearing on initialization
   - Default timeout of 5000ms for regular operations

### Core Methods Flow

#### Login Process (`login`)
1. Navigate to login URL
2. Find login frame by URL pattern
3. Fill credentials and submit
4. Verify successful login via frame presence

#### Hours Overview (`fetch_hours`)
1. Navigate to hours overview page
2. Select year view and specific year
3. Wait for table to load
4. Extract data from table rows
5. Return structured data with year and registrations

#### Add Hours (`add_hours`, `add_hours_direct`)
1. Two implementation paths:
   - Via overview page navigation (`add_hours`)
   - Direct URL navigation (`add_hours_direct`)
2. Fill form fields sequentially
3. Handle autocomplete fields with specific timing
4. Save and verify completion

#### Download and Parse XLS (`download_hours_xls`)
1. Navigate to overview page
2. Configure year view
3. Set up download handler with extended timeout (30000ms)
4. Trigger export button
5. Save file with timestamp
6. Parse XLS file into structured events:
   - Read Excel using pandas
   - Find data start after "Datum" header
   - Process rows into event dictionaries
   - Handle missing values and data types
   - Save both XLS and JSON formats

### Error Handling
- Each major operation wrapped in try-except
- Screenshots captured at failure points with descriptive names
- HTML content saved for debugging with frame-specific content capture
- Detailed logging at each step with operation status
- Multiple retry attempts for frame detection
- Network state verification after operations
- Graceful cleanup in error cases with resource management
- Timeout differentiation:
  - Default operations: 5000ms
  - Page loads: 10000ms
  - Critical elements: Custom timeouts per operation

### Browser Management
- Single browser instance per client
- Context maintained throughout session
- Cleanup handled in `close` method
- Automatic screenshot and HTML saves

## Login Process

### Login Frame
- Frame URL Pattern: Contains `inloggen.asp`
- Username Field: `input[name='txtEmail']`
- Password Field: `input[name='txtWachtwoord']`
- Login Button: `input.act-btn[name='submit1']`

### Post-Login Verification
- Menu Frame: `frame[name='menuframe']`
- Main Frame: `frame[name='mainframe']`

## Hours Overview Page

### Year Selection
- Year Radio Button: `input[type="radio"][value="jaar"]`
- Year Dropdown: `select.form-select.rect#input-year`
  - Waits for `:not([disabled])` state
  - Dynamic option values in format "index: year"
- Confirm Button: `button.button.form-submit span:has-text("Verder")`

### Hours Grid
- Main Grid Container: `app-grid`
- Hours Table: `app-grid table.table-v1`
- Table Body Rows: `app-grid table.table-v1 tbody tr`
- Wait States:
  - Initial load: `networkidle` with 10000ms timeout
  - Table visibility: Waits for at least one row
  - Year selection: 2000ms animation delay
  - Data refresh: `networkidle` after selection

### Column Selectors
- Date: `td:nth-child(4)`
- Employee: `td:nth-child(5)`
- Project: `td:nth-child(6)`
- Activity: `td:nth-child(7)`
- Description: `td:nth-child(8)`
- Hours: `td:nth-child(9)`
- Kilometers: `td:nth-child(10)`

### Export Functionality
- Export Button Selectors (in order of preference):
  1. `div.ng-star-inserted app-icon[title="Exporteren naar Excel"]`
  2. `app-icon[title="Exporteren naar Excel"]`
  3. `app-icon[name="file-type-xls"]`
- Download Path: `output/e-boekhouden_events_{year}_{timestamp}.xls`
- JSON Output: `output/e-boekhouden_events_{year}_{timestamp}.json`

## Add Hours Page

### Navigation
- Add Button: `app-target-link a:has(app-icon[name="plus"]) >> text=Toevoegen`

### Form Fields
- Date Input: `input#datum`
- Employee Autocomplete: `input#medewerkerId-AutocompletePickerInput`
- Project Autocomplete: `input#projectId-AutocompletePickerInput`
- Activity Autocomplete: `input#activiteitId-AutocompletePickerInput`
- Hours Input: `input#aantalUren`
- Comments Textarea: `textarea#opmerkingen`
- Save Button: `button.button.form-submit:has-text("Opslaan")`

## Important Notes

1. **Page Loading**
   - Most operations require waiting for `networkidle` state
   - Form elements typically require `state='visible'` check
   - Default timeout is set to 5000ms for most operations
   - Download operations use extended timeout of 30000ms

2. **Autocomplete Fields**
   - Require click before input
   - Need clearing before new input
   - Require Enter press to confirm selection
   - Have 500ms wait after selection

3. **File Downloads**
   - Require specific browser context settings
   - Downloads are handled through `expect_download()` event
   - Files are saved with timestamped names in the `output` directory
   - Both XLS and JSON formats are preserved
   - XLS parsing handles missing values and data type conversions

4. **Error States**
   - All pages save HTML content on error for debugging
   - Screenshots are captured on errors
   - Error states are preserved in the `temp/screenshots` directory

## Successful Task Verification

The following tasks have been verified to work with these elements:

1. Login (`login_to_eboekhouden`)
2. Fetch Hours (`fetch_hours_for_year`)
3. Add Hours (`test_add_hours`, `test_add_hours_direct`)
4. Download Hours XLS (`download_hours_xls`)
5. Parse Hours XLS (`_parse_hours_xls`)

This document should be updated only when new tasks are successfully implemented and verified. 