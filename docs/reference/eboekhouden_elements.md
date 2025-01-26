# E-boekhouden Website Elements Reference

This document serves as a technical reference for the e-boekhouden website elements used in our automation tasks. It documents all critical URLs, selectors, and interactive elements required for the RPA implementation.

## Configuration

### Browser Settings
- Browser: Chromium (via Playwright)
- Viewport: 1920x1080
- User Agent: Chrome 121
- Default Timeout: 5000ms
- Download Timeout: 30000ms
- Slow Motion: 25ms (configurable)

### Base URLs
- Main Portal: `https://secure20.e-boekhouden.nl`
- Login Page: `https://secure.e-boekhouden.nl/bh/?ts=340591811462&c=homepage&SV=A`
- Hours Overview: `https://secure20.e-boekhouden.nl/uren/overzicht`

## Authentication Process

### Login Elements
- Username Field: `input[name='txtEmail']`
- Password Field: `input[name='txtWachtwoord']`
- Submit Button: `input.act-btn[name='submit1']`

### Login Verification
- Success Indicators:
  - Menu Frame: `frame[name='menuframe']`
  - Main Frame: `frame[name='mainframe']`
- Error Handling:
  - Screenshot capture on failure
  - HTML content preservation
  - Retry mechanism with configurable attempts

## Hours Management

### Overview Page Navigation
1. Year Selection:
   - Radio Button: `input[type="radio"][value="jaar"]`
   - Year Dropdown: `select.form-select.rect#input-year`
   - Confirm Button: `button.button.form-submit span:has-text("Verder")`

2. Data Grid:
   - Container: `app-grid`
   - Table: `app-grid table.table-v1`
   - Row Elements: `app-grid table.table-v1 tbody tr`

### Data Columns
- Date: `td:nth-child(4)`
- Employee: `td:nth-child(5)`
- Project: `td:nth-child(6)`
- Activity: `td:nth-child(7)`
- Description: `td:nth-child(8)`
- Hours: `td:nth-child(9)`
- Kilometers: `td:nth-child(10)`

### Export Functionality
- Export Button: `app-icon[title="Exporteren naar Excel"]`
- File Handling:
  - Download Path: `output/e-boekhouden_events_{year}_{timestamp}.xls`
  - JSON Conversion: `output/e-boekhouden_events_{year}_{timestamp}.json`
  - Validation against schema: `schemas/events.schema.json`

## Error Handling

### Screenshot Capture
- Directory: `temp/screenshots`
- Naming: `{operation}_{timestamp}.png`
- Triggers:
  - Login failures
  - Navigation errors
  - Element interaction failures
  - Data validation errors

### HTML Content Preservation
- Location: `temp/`
- Files:
  - `login_page.html`
  - `page_content.html`
- Captured on:
  - Authentication errors
  - Page load failures
  - Element location failures

### Retry Mechanism
- Default Operations:
  - Max Attempts: 60
  - Delay: 100ms
- Long-running Operations:
  - Max Attempts: 1000
  - Configurable delay

## Best Practices

### Page Interactions
1. Wait for Network Idle:
   ```python
   page.wait_for_load_state('networkidle')
   ```

2. Element Visibility:
   ```python
   element.wait_for_state('visible')
   ```

3. Frame Handling:
   ```python
   frame = page.frame_locator('frame[name="mainframe"]')
   ```

### Data Validation
1. Schema Validation:
   - Use JSON schema for event data
   - Validate before processing
   - Log validation errors

2. Data Type Handling:
   - Date formatting
   - Numeric conversions
   - Empty value handling

### Resource Management
1. Browser Context:
   - Single instance per session
   - Proper cleanup on exit
   - Error state preservation

2. File Management:
   - Temporary file cleanup
   - Output file organization
   - Log rotation

## Implementation Notes

1. **Browser Automation**
   - Use Playwright's sync API
   - Handle frame navigation carefully
   - Implement proper waiting strategies

2. **Data Processing**
   - Convert XLS to structured JSON
   - Validate against schema
   - Preserve original files

3. **Error Recovery**
   - Capture detailed error states
   - Implement graceful degradation
   - Maintain audit trail

4. **Performance**
   - Optimize wait times
   - Batch operations where possible
   - Clean up resources promptly

This document should be updated when changes are made to the automation implementation or when new features are added. 