# Database Layer

This directory contains the first SQLite database layer for the curriculum
recommendation system.

## Files

- `schema.sql`: database schema for courses, prerequisites, requirements,
  students, and non-course records.
- `seed.sql`: initial seed data for graduation requirements,
  teaching-certification requirements, expanded course data, choice groups,
  non-course requirements, and one sample student.
- `../curriculum/graph.py`: prerequisite DAG loading, validation, topological
  sort, and prerequisite lookup functions.
- `../scripts/verify_dag.py`: simple DAG verification script.

## Course Categories

The `courses.category` column uses these values:

- `MAJOR`: Computer Education major courses and related major-recognized courses.
- `TEACHING`: teaching certification roadmap courses.
- `GENERAL`: general education or other non-major courses.

The `courses.sub_category` column gives a more specific role when known:

- `BASIC_REQUIRED`: mandatory basic major requirement course.
- `BASIC_REQUIRED_CHOICE`: Algorithm / Artificial Intelligence choice-group course.
- `SUBJECT_EDUCATION`: subject education area course.
- `MAJOR_COMMON`: common major course.
- `PROFESSIONAL_TRACK`: professional career track course.
- `TEACHER_TRACK`: teacher career track course.
- `TEACHING_THEORY`: teaching theory course.
- `TEACHING_FOUNDATION`: teaching foundation course.
- `TEACHING_PRACTICUM`: teaching practicum course.

## Courses And Prerequisites As A DAG

Each course is stored in `courses`. Each prerequisite relationship is stored in
`prerequisites` as a directed edge.

The edge direction is:

```text
prerequisite course -> later course
```

For example, if course A must be completed before course B, the row should use
course A as `from_course_id` and course B as `to_course_id`.

These prerequisite edges must form a DAG. A cycle would mean that a course is
eventually required before itself, so later graph validation logic should reject
cycles.

## Required And Recommended Edges

The `prerequisites.relation_type` column distinguishes edge strength:

- `REQUIRED`: the prerequisite course should be completed before the later
  course. Later recommendation logic can treat this as a strict blocker.
- `RECOMMENDED`: the prerequisite course is helpful background but should not
  strictly block a later recommendation.

Both edge types are still graph edges and are included in DAG validation and
topological sorting.

## DAG Validation

Run the simple verification script from the project root:

```powershell
python scripts/verify_dag.py
```

The script loads `database/schema.sql` and `database/seed.sql` into an in-memory
SQLite database, then verifies:

- total course count,
- total prerequisite edge count,
- whether the graph is acyclic,
- a topological order preview,
- direct and indirect prerequisite lookups for key courses.

Example output:

```text
Total courses: 74
Total prerequisite edges: 52
Valid DAG: True
Topological order preview: AAI2014, AAI3006, AAI3017, AAI3028, CHS2003, ...
Direct prerequisites of COM3026: COM2012
All prerequisites of COM3026: COM2002, COM2012
Direct prerequisites of COM3005: COM3004
Direct prerequisites of CFTD067: COM3009
Direct prerequisites of CFTD010: CFTD119, CFTD122
Direct prerequisites of CFTD103: CFTD007
DAG verification passed.
```

## Requirements Are Not DAG Edges

Graduation requirements and teaching-certification requirements are stored
separately from prerequisite edges.

Credit requirements, required course counts, CPR training, aptitude tests, and
graduation administrative checks do not represent "course A before course B."
They are rule-checking data, so they belong in `requirements`,
`requirement_courses`, `choice_groups`, `choice_group_courses`,
`non_course_requirements`, and `student_non_course_records`.

## Choice Groups

Choice groups represent rules such as:

```text
Choose at least 1 course from Algorithm or Artificial Intelligence.
```

The parent requirement is stored in `requirements`. The group itself is stored
in `choice_groups`, and candidate courses are stored in
`choice_group_courses`.

For the initial seed, `BASIC_REQUIRED_ALGORITHM_AI` requires at least 1 course
from:

- `COM3026` Algorithm
- `COM3022` Artificial Intelligence

## Non-Course Requirements

Non-course requirements are stored in `non_course_requirements`. A student's
progress is stored in `student_non_course_records`.

These records are separate from `courses` because they are not lecture courses
and should not be used as prerequisite graph nodes.

## Sample SQL Queries

List all courses:

```sql
SELECT course_id, course_name, credit, category, sub_category
FROM courses
ORDER BY course_id;
```

List all basic required courses:

```sql
SELECT c.course_id, c.course_name, c.credit
FROM requirement_courses rc
JOIN courses c ON c.course_id = rc.course_id
WHERE rc.requirement_id = 'BASIC_REQUIRED'
ORDER BY c.course_id;
```

List all subject education area courses:

```sql
SELECT c.course_id, c.course_name, c.credit
FROM requirement_courses rc
JOIN courses c ON c.course_id = rc.course_id
WHERE rc.requirement_id = 'SUBJECT_EDUCATION'
ORDER BY c.course_id;
```

List all prerequisite edges:

```sql
SELECT from_course_id, to_course_id, relation_type, weight, reason
FROM prerequisites
ORDER BY from_course_id, to_course_id;
```

List non-course requirements:

```sql
SELECT requirement_id, requirement_name, required_count, recommended_timing
FROM non_course_requirements
ORDER BY requirement_id;
```

List all offered major courses:

```sql
SELECT course_id, course_name, credit, sub_category, recommended_year, recommended_semester
FROM courses
WHERE category = 'MAJOR'
  AND is_offered = 1
ORDER BY course_id;
```

List all non-offered courses:

```sql
SELECT course_id, course_name, category, sub_category
FROM courses
WHERE is_offered = 0
ORDER BY course_id;
```

List all teacher track courses:

```sql
SELECT course_id, course_name, credit, recommended_year, recommended_semester
FROM courses
WHERE sub_category = 'TEACHER_TRACK'
ORDER BY course_id;
```

List all teaching certification courses:

```sql
SELECT course_id, course_name, credit, sub_category, recommended_year, recommended_semester
FROM courses
WHERE category = 'TEACHING'
ORDER BY sub_category, course_id;
```
