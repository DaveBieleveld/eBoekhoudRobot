-- Ignore CURRENT_TIMEZONE_ID(). It is a valid system function, see https://learn.microsoft.com/en-us/sql/t-sql/functions/current-timezone-id-transact-sql?view=sql-server-ver16

declare @year int;
set @year = ?;

select 
      event_id       = e.event_id
    , user_email     = e.user_email
    , user_name      = e.user_name
    , subject        = e.subject
    , start_date     = CONVERT(varchar, e.start_date AT TIME ZONE 'UTC' AT TIME ZONE CURRENT_TIMEZONE_ID(), 127)
    , end_date       = CONVERT(varchar, e.end_date AT TIME ZONE 'UTC' AT TIME ZONE CURRENT_TIMEZONE_ID(), 127)
    , hours          = CONVERT(float, ROUND(datediff(minute, e.start_date, e.end_date) / 60.0 * 4, 0) / 4.0)
    , description    = REPLACE(REPLACE(REPLACE(e.description, '\', '\\'), '"', '\"'), CHAR(13) + CHAR(10), '\n')
    , last_modified  = CONVERT(varchar, e.last_modified, 127)
    , is_deleted     = e.is_deleted
    , created_at     = CONVERT(varchar, e.created_at, 127)
    , updated_at     = CONVERT(varchar, e.updated_at, 127)
    , project        = p.project
    , activity       = a.activity
from [dbo].[calendar_event] e
cross apply (
                SELECT TOP 1 project = TRIM(REPLACE(c.name, '[PROJECT]', ''))
                FROM [dbo].[calendar_event_calendar_category] cecc
                JOIN [calendar_category] c 
                ON cecc.category_id = c.category_id
                WHERE cecc.event_id = e.event_id AND c.is_project = 1
            ) p
cross apply (
                SELECT TOP 1 activity = TRIM(REPLACE(c.name, '[ACTIVITY]', ''))
                FROM [dbo].[calendar_event_calendar_category] cecc
                JOIN [calendar_category] c 
                ON cecc.category_id = c.category_id
                WHERE cecc.event_id = e.event_id AND c.is_activity = 1
            ) a
where e.is_deleted = 0
    and YEAR(e.start_date AT TIME ZONE 'UTC' AT TIME ZONE CURRENT_TIMEZONE_ID()) = @year
order by e.start_date
for json path