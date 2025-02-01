-- Run this command to output to CSV:
-- psql -d gvca_survey -U gvcaadmin -f export_open_responses.sql > open_responses.csv

SET search_path to sac_survey_2025;
COPY (
-- flattened respondent_rank_questions
WITH duplicated_respondents AS
         (
             SELECT respondent_id,
                    tenure = 1              AS new_family,
                    minority,
                    any_support,
                    grammar_avg IS NOT NULL AS grammar_respondent,
                    middle_avg IS NOT NULL  AS middle_respondent,
                    high_avg IS NOT NULL    AS high_respondent,
                    overall_avg             AS avg_score,
                    soft_delete
             FROM respondents
             WHERE NOT soft_delete

             UNION ALL

             -- Get a second rows for any respondent which represented two people
             SELECT respondent_id,
                    tenure = 1              AS new_family,
                    minority,
                    any_support,
                    grammar_avg IS NOT NULL AS grammar_respondent,
                    middle_avg IS NOT NULL  AS middle_respondent,
                    high_avg IS NOT NULL    AS high_respondent,
                    overall_avg             AS avg_score,
                    soft_delete
             FROM respondents
             WHERE NOT soft_delete
               AND num_individuals_in_response = 2
         ),
     all_respondent_questions AS
         (
             SELECT respondent_id,
                    question_id,
                    question_text
             FROM respondents
                      CROSS JOIN
                  questions
             WHERE question_type = 'rank'
               AND NOT soft_delete
         ),
     rank_questions AS
         (
             SELECT respondent_id,
                    question_id,
                    question_text,
                    CASE
                        WHEN grammar THEN 'Grammar'
                        WHEN middle THEN 'Middle'
                        WHEN high THEN 'High'
                        END AS grade_level_for_response,
                    response_value,
                    response_text
             FROM all_respondent_questions
                      LEFT JOIN
                  question_rank_responses USING (respondent_id, question_id)
                      LEFT JOIN
                  question_response_mapping USING (question_id, response_value)
         )
SELECT
		-- respondents
       respondent_id,
       new_family,
       minority,
       any_support,
       grammar_respondent,
       middle_respondent,
       high_respondent,
       avg_score,

       -- questions
       question_id,
       question_text,
       grade_level_for_response,
       response_value,
       response_text
    FROM rank_questions
        JOIN
        duplicated_respondents USING (respondent_id)
    ORDER BY respondent_id, question_id, grade_level_for_response
) TO STDOUT WITH CSV HEADER;
