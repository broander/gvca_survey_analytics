-- filepath: /workspaces/gvca_survey_analytics/export_open_responses.sql
-- Run this command to output to CSV:
-- psql -d gvca_survey -U gvcaadmin -f export_open_responses.sql > open_responses.csv

SET search_path TO sac_survey_2025;
COPY (
-- response_open
WITH all_respondent_questions AS
         (
             SELECT respondent_id,
                    question_id,
                    question_text
             FROM respondents
                      CROSS JOIN
                  questions
             WHERE question_type = 'open response'
               AND NOT soft_delete
         )
SELECT arq.respondent_id,
       arq.question_id,
       arq.question_text,
       grade_level.grade_level,
       qor.response,
       ar.categories
FROM all_respondent_questions arq
         LEFT JOIN question_open_responses qor USING (respondent_id, question_id)
         LEFT JOIN (
            SELECT *,
                   CASE
                     WHEN grammar THEN 'Grammar'
                     WHEN middle THEN 'Middle'
                     WHEN high THEN 'High'
                     WHEN whole_school THEN 'Whole School'
                   END AS grade_level
            FROM question_open_responses
         ) AS grade_level
         ON grade_level.respondent_id = qor.respondent_id
         AND grade_level.question_id = qor.question_id
         LEFT JOIN ai_survey_analysis ar
           ON ar.respondent_id = qor.respondent_id
          AND ar.question_id = qor.question_id
          AND ar.grade_level = grade_level.grade_level
ORDER BY arq.respondent_id, arq.question_id, qor.grammar DESC, qor.middle DESC, qor.high DESC, qor.whole_school DESC
) TO STDOUT WITH CSV HEADER;
