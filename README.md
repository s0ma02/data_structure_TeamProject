# Curriculum Recommendation System

SQLite 기반 컴퓨터교육과 교육과정 추천 시스템입니다. 현재 구현은 DB seed,
선수과목 DAG, 졸업/교직 요건 검사, 과목 추천 CLI를 포함합니다.

## Structure

- `database/schema.sql`: SQLite table schema
- `database/seed.sql`: course, requirement, prerequisite, sample student data
- `curriculum/graph.py`: prerequisite DAG loading, validation, topological sort
- `curriculum/requirements.py`: graduation, teaching, and non-course requirement checker
- `curriculum/recommender.py`: transparent scoring-based course recommender
- `scripts/verify_dag.py`: standalone DAG verification script
- `cli.py`: command-based CLI

## Database And DAG

Courses are graph vertices. Rows in `prerequisites` are directed edges from
the prerequisite course to the later course.

`REQUIRED` edges block recommendation until completed. `RECOMMENDED` edges do
not block recommendation, but they affect score and explanation.

Graduation credits, course-count requirements, and non-course requirements are
not graph edges. They are checked separately by `RequirementChecker`.

## Recommendation Scoring

The recommender only recommends offered courses that the student has not
completed and whose REQUIRED prerequisites are satisfied.

Score signals include:

- unmet graduation or teaching requirement relevance,
- satisfied REQUIRED prerequisites,
- recommended year and semester match,
- target track match,
- completed RECOMMENDED prerequisites,
- penalty for courses recommended much later than the target year.

Each recommendation includes reasons, requirement relevance, missing required
prerequisites, completed recommended prerequisites, and missing recommended
prerequisites.

## Commands

Initialize a local SQLite database:

```powershell
python cli.py init-db
```

Run DAG validation:

```powershell
python scripts/verify_dag.py
python cli.py check-dag
python cli.py topo
python cli.py prereq COM3026
```

Inspect student state and requirements:

```powershell
python cli.py list-courses
python cli.py completed S001
python cli.py requirements S001
python cli.py non-course-status S001
```

Recommend courses:

```powershell
python cli.py recommend S001 --limit 10
python cli.py recommend-semester S001 --year 1 --semester 2 --limit 10
```

Run tests:

```powershell
python -m unittest
```

## Example Recommendation Output

```text
Recommendations for S001
 1. EDU_THEORY_001 교육학개론 (2cr, score 105, 1Y/2S)
    reasons: 미충족 졸업/교직 요건에 직접 기여, 필수 선수과목 충족, 1학년 권장 과목, 2학기 권장 과목, COMMON 트랙과 관련
    requirement relevance: 교직과목, 교직이론
    prerequisites: required missing=none; recommended completed=none; recommended missing=none
```

## Sample Student

`S001` is seeded as a first-year, second-semester student on the `COMMON` track.
Completed courses are `COM2002` and `COM2003`.
