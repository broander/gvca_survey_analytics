-- Set search path to the survey schema
SET search_path to sac_survey_2025;

-- Apply soft deletes to those who didn't fill out any non-mandatory information
WITH responses_by_respondents AS
         (
             SELECT respondent_id,
                    open_response.respondent_id IS NOT NULL AS has_open_response,
                    rank_response.respondent_id IS NOT NULL AS has_rank_response
             FROM respondents
                      LEFT JOIN
                      (SELECT DISTINCT respondent_id FROM question_open_responses) AS open_response
                      USING (respondent_id)
                      LEFT JOIN
                      (SELECT DISTINCT respondent_id FROM question_rank_responses) AS rank_response
                      USING (respondent_id)
         )
UPDATE respondents
SET soft_delete = TRUE
FROM responses_by_respondents
WHERE responses_by_respondents.respondent_id = respondents.respondent_id
  AND NOT has_open_response
  AND NOT has_rank_response
;

-- Look at those who didn't do any ranked choice, but did do open response.  What were their responses?
SELECT respondent_id,
       ROUND(EXTRACT(EPOCH FROM end_datetime - start_datetime) / 60, 1) AS minutes_elapsed,
       question_id,
       question_text,
       grammar,
       middle,
       high,
       whole_school,
       response
FROM respondents
         LEFT JOIN
     question_open_responses USING (respondent_id)
         LEFT JOIN
     questions using (question_id)
WHERE overall_avg IS NULL
  AND NOT soft_delete
;


-- Look at distribution of open and rank responses by question_id.
SELECT question_id,
       question_type,
       COUNT(DISTINCT COALESCE(question_open_responses.respondent_id, question_rank_responses.respondent_id)),
       question_text
FROM questions
         LEFT JOIN
     question_open_responses USING (question_id)
         LEFT JOIN
     question_rank_responses USING (question_id)
GROUP BY question_id, question_type, question_text
ORDER BY question_id
;

-- Ensure each question type is assigned one and only one level
SELECT *
FROM question_open_responses
WHERE grammar::int + middle::int + high::int + whole_school::int <> 1
;
SELECT *
FROM question_rank_responses
WHERE grammar::int + middle::int + high::int <> 1
;

-- Look at distribution of scores
SELECT COUNT(*) FILTER ( WHERE overall_avg >= 3 )                     AS exceeds,
       COUNT(*) FILTER ( WHERE overall_avg >= 2 AND overall_avg < 3 ) AS meets,
       COUNT(*) FILTER ( WHERE overall_avg < 2 )                      AS fails
FROM respondents
;

-- For giggles, take a look at open response for 'fails' group
SELECT respondent_id,
       tenure,
       minority,
       any_support,
       grammar_avg,
       middle_avg,
       high_avg,
       CASE
           WHEN grammar THEN 'Grammar'
           WHEN middle THEN 'Middle'
           WHEN high THEN 'Upper'
           WHEN whole_school THEN 'All'
           END AS response_category,
       response
FROM respondents
         JOIN
     question_open_responses USING (respondent_id)
WHERE overall_avg < 2
ORDER BY respondent_id, question_id
;

-- Null out some responses
SELECT response
FROM question_open_responses
WHERE response ~* '^\s*(?:n.?a|nothing|none)\s*$'
;
UPDATE question_open_responses
SET response = NULL
WHERE response ~* '^\s*(?:n.?a|nothing|none)\s*$'
;

/*******
  See if we can populate some of the "Same" open response values
 ******/
-- Find a regex pattern that works, and filter out ones we don't want to change
--TODO all hard coded respondent IDs need to be updated for 2025
WITH manually_update_responses AS
         (
             SELECT DISTINCT respondent_id --, question_id, grammar, middle, high, whole_school, response
             FROM question_open_responses
             WHERE length(response) < 50
               and response ~* 'same|see|above|below'
               and respondent_id not in ('118519833891', '118525284956', '118520470136') -- "real" responses to leave as-is
         )
SELECT respondent_id as resp_id,
       question_id as q,
--        question_text,
       grammar,
       middle,
       high,
       whole_school,
       response
FROM question_open_responses
         JOIN
     manually_update_responses using (respondent_id)
JOIN
    questions using(question_id)
ORDER BY respondent_id, question_id, grammar desc, middle desc, high desc, whole_school desc
;
-- "same same"
/* UPDATE question_open_responses */
/* SET response = (SELECT response FROM question_open_responses WHERE respondent_id = '118507929834' and question_id = 11 and grammar) */
/* WHERE respondent_id = '118507929834' and question_id = 11 and whole_school; */

-- Final check
SELECT response
FROM question_open_responses
ORDER BY length(response)
