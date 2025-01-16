# Build Order

1. **Event Identification:**
   * Implement the logic to extract the `event_id` from the e-boekhouden description field.
   * The `event_id` will be formatted as `[event_id: <event_id>]` and will always be the last line in the description.

2. **Database Event Processing:**
   * Iterate through each event retrieved from the database.
   * For each database event:
       * Check if a corresponding event exists in e-boekhouden using the `event_id`.
       * **If the event exists in e-boekhouden:**
           * Check if the event is invoiced.
           * If invoiced, log a "Conflict Event" error and skip further processing for this event.
           * If not invoiced, compare the data between the database and e-boekhouden event.
           * If data differs, update the e-boekhouden event with the database data.
       * **If the event does not exist in e-boekhouden:**
           * Check for "Base Data Conflicts" (Employee, Project, Activity).
           * If a conflict exists, log a "Base Data Conflict" error and skip insertion.
           * If no conflict exists, insert the new event into e-boekhouden, including the `event_id`.

3. **E-boekhouden Event Processing:**
   * Iterate through each event retrieved from e-boekhouden.
   * For each e-boekhouden event:
       * Check if the event has an `event_id` in the description.
       * **If the event has an `event_id`:**
           * Check if a corresponding event exists in the database using the `event_id`.
           * If no corresponding event exists in the database, log an "Orphaned Event" error.
       * **If the event does not have an `event_id`:**
           * Log an "Orphaned Event" error.

4. **Data Refresh:**
   * After processing all events, refresh the data from e-boekhouden to ensure all changes are reflected.

5. **Error Logging:**
   * Implement a robust logging mechanism to capture all actions and errors.
   * Log the following for each error:
       * All data fields fetched from e-boekhouden.
       * Date of the error.
       * Specific error message.

6. **User Notification:**
   * Implement a mechanism to send email notifications to the user.
   * The email should contain information about any sync errors or other errors from the log file.

7. **Invoiced Event Protection:**
   * Ensure that invoiced events cannot be modified or deleted in either the database or e-boekhouden. This should be enforced at the application level. 