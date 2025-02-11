-- Run this command to output to CSV:
-- psql -d gvca_survey -U gvcaadmin -f export_open_responses_only.sql > open_responses_only.csv

SET search_path TO sac_survey_2025;
COPY (
-- response_open
WITH all_respondent_questions AS
         (
             SELECT respondent_id,
                    question_id,
                    question_text,
                    num_individuals_in_response,
             FROM respondents
                      CROSS JOIN
                  questions
             WHERE question_type = 'open response'
               AND NOT soft_delete
         )
SELECT respondent_id,
       question_id,
       question_text,
       num_individuals_in_response,
       CASE
           WHEN grammar THEN 'Grammar'
           WHEN middle THEN 'Middle'
           WHEN high THEN 'High'
           WHEN whole_school THEN 'Whole School'
           END AS grade_level,
       response
FROM all_respondent_questions
         LEFT JOIN
     question_open_responses USING (respondent_id, question_id)
ORDER BY respondent_id, question_id, grammar DESC, middle DESC, high DESC, whole_school DESC
) TO STDOUT WITH CSV HEADER;
