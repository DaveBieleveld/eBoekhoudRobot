# Build Order

1. **Fetch Refresh:**
   * Fetch the data from e-boekhouden
   * Fetch the data from the database

2. **Event Identification:**
   * Implement the logic to extract the `event_id` from the e-boekhouden description field.
   * The `event_id` will be formatted as `[event_id:<event_id>]` and will always be the last line in the description.

3. **Database Event Processing:**
   * Iterate through each event retrieved from the database.
   * For each database event:
       * Check if the event has a project category and an activity category.
           * If not, log an "Missing Category" error and
             * skip this event and
             * allow the user to mark an event as "Do not sync" in the database.
       * Check if a corresponding event exists in e-boekhouden using the `event_id`.
       * **If the event exists in e-boekhouden:**
           * Check if the event is invoiced.
           * If invoiced, skip this event.
           * If not invoiced, compare the data between the database and e-boekhouden event.
           * If data differs, update the e-boekhouden event with the database data.
       * **If the event does not exist in e-boekhouden:**
           * Check for "Base Data Conflicts" (Employee, Project, Activity).
           * If a conflict exists, log a "Base Data Conflict" error and skip insertion.
           * If no conflict exists, insert the new event into e-boekhouden, including the `event_id`.

   ```mermaid
   sequenceDiagram
       participant DB as Database
       participant Sync as Sync Process
       participant EB as e-boekhouden
       participant Log as Error Logger
       
       Note over DB,Log: Database Event Processing Flow
       
       DB->>Sync: Fetch event
       
       Sync->>Sync: Check categories
       alt Missing categories
           Sync->>Log: Log "Missing Category" error
           Note over Sync: Skip event
       else Has categories
           Sync->>EB: Check event_id exists
           
           alt Event exists in e-boekhouden
               EB->>Sync: Return event data
               Sync->>Sync: Check if invoiced
               alt Is invoiced
                   Note over Sync: Skip event
               else Not invoiced
                   Sync->>Sync: Compare data
                   alt Data differs
                       Sync->>EB: Update event
                   end
               end
           else Event doesn't exist
               Sync->>Sync: Check base data conflicts
               alt Has conflicts
                   Sync->>Log: Log "Base Data Conflict" error
                   Note over Sync: Skip insertion
               else No conflicts
                   Sync->>EB: Insert new event
               end
           end
       end
   ```

4. **E-boekhouden Event Processing:**
   * Iterate through each event retrieved from e-boekhouden.
   * For each e-boekhouden event:
       * Check if the event has an `event_id` in the description.
       * **If the event has an `event_id`:**
           * Check if a corresponding event exists in the database using the `event_id`.
           * If no corresponding event exists in the database, log an "Orphaned Event" error.
       * **If the event does not have an `event_id`:**
           * Log an "Out of Sync" error.
   * In no case should an event be deleted from e-boekhouden. Discrepancies should be resolved by
     * manually updating the database event based on the log or
     * whitelisting the event in a event-whitelist.

   ```mermaid
   %%{
     init: {
       'theme': 'base',
       'themeVariables': {
         'primaryColor': '#2b4c7e',
         'primaryTextColor': '#ffffff',
         'secondaryColor': '#88498f',
         'tertiaryColor': '#3a7d44',
         'errorColor': '#963d32',
         'fontFamily': 'arial',
         'lineColor': '#333333',
         'textColor': '#333333'
       }
     }
   }%%
   sequenceDiagram
       participant EB as e-boekhouden
       participant Sync as Sync Process
       participant DB as Database
       participant Log as Error Logger
       participant WL as Event Whitelist

       Note over EB,WL: E-boekhouden Event Processing Flow

       EB->>Sync: Fetch event
       
       Sync->>Sync: Check for event_id in description
       
       alt Has event_id
           Sync->>DB: Check for corresponding event
           alt No matching event in DB
               Sync->>Log: Log "Orphaned Event" error
               Note over Sync: Event exists in EB but not in DB
           end
       else No event_id
           Sync->>WL: Check if event is whitelisted
           alt Event is whitelisted
               Note over Sync: Skip processing
           else Event not whitelisted
               Sync->>Log: Log "Out of Sync" error
               Note over Sync: Manual intervention required
           end
       end
   ```

5. **Data Refresh:**
   * After processing all events, refresh the data from e-boekhouden to ensure all changes are reflected.

6. **Error Logging:**
   * Implement a robust logging mechanism to capture all actions and errors.
   * Log the following for each error:
       * All data fields fetched from e-boekhouden.
       * Date of the error.
       * Specific error message.

7. **User Notification:**
   * Implement a mechanism to send email notifications to the user.
   * The email should contain information about any sync errors or other errors from the log file.

8. **Invoiced Event Protection:**
   * Ensure that invoiced events cannot be modified or deleted in either the database or e-boekhouden. This should be enforced at the application level.
