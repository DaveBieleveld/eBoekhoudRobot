select 
      event_id       = e.event_id
    , user_email     = e.user_email
    , user_name      = e.user_name
    , subject        = e.subject
    , start_date     = CONVERT(varchar, e.start_date AT TIME ZONE 'UTC' AT TIME ZONE CURRENT_TIMEZONE_ID(), 127)
    , end_date       = CONVERT(varchar, e.end_date AT TIME ZONE 'UTC' AT TIME ZONE CURRENT_TIMEZONE_ID(), 127)
    , description    = REPLACE(REPLACE(REPLACE(e.description, '\', '\\'), '"', '\"'), CHAR(13) + CHAR(10), '\n')
    , last_modified  = CONVERT(varchar, e.last_modified, 127)
    , is_deleted     = e.is_deleted
    , created_at     = CONVERT(varchar, e.created_at, 127)
    , updated_at     = CONVERT(varchar, e.updated_at, 127)
    , categories     = ISNULL((
        SELECT 
            JSON_QUERY((
                SELECT c.name as name
                FROM [dbo].[calendar_event_calendar_category] cecc
                LEFT JOIN [calendar_category] c 
                    ON cecc.category_id = c.category_id
                WHERE cecc.event_id = e.event_id
                FOR JSON PATH
            ))
        ), '[]')
from [dbo].[calendar_event] e
where CAST(e.start_date AS DATE) = CAST(GETDATE() AS DATE)
and e.is_deleted = 0
order by e.start_date
for json path