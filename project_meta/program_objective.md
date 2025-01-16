# Program Objective

1. **Data Synchronization:**
   - Compare event data between the database and e-boekhouden.
   - Identify events using a unique `event_id` (GUID from the database) stored in the e-boekhouden description field as "[event_id: <event_id>]".
   - **Add:** Insert new events from the database into e-boekhouden if they don't exist.
   - **Update:** Modify events in e-boekhouden if they differ from the database, unless the event is invoiced. Database is leading.
   - **Refresh:** After all operations, verify changes are reflected in e-boekhouden.

2. **Error Handling:**
   - **Sync Errors:**
       - Log "Orphaned Events": Events in e-boekhouden without a matching `event_id` in the database.
       - Log "Conflict Events":
           - Events that are invoiced and cannot be updated.
           - Events that exist in both systems but have data discrepancies.
       - Log "Base Data Conflicts": When e-boekhouden dropdown values for Employee, Project, or Activity do not match the database values. These events cannot be inserted.
   - Log all actions and errors, including:
       - All data fields fetched from e-boekhouden.
       - Date of the error.
       - Specific error message.
   - Prohibit modification or deletion of invoiced events in both the database and e-boekhouden.

3. **User Notification:**
   - Notify the user of any sync errors or other errors from the log file via email.
