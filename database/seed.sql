PRAGMA foreign_keys = ON;

INSERT INTO courses (
    course_id,
    course_name,
    credit,
    category,
    sub_category,
    recommended_year,
    recommended_semester,
    is_offered,
    language,
    note
) VALUES
    ('COM2002', '기본프로그래밍', 3, 'MAJOR', 'BASIC_REQUIRED', '1', '2', 1, '한,영', '기본이수과목'),
    ('COM2003', '컴퓨터교육개론', 3, 'MAJOR', 'BASIC_REQUIRED', '1-2', '2', 1, '영', '기본이수과목'),
    ('COM2012', '자료구조', 3, 'MAJOR', 'BASIC_REQUIRED', '2-3', '1', 1, '한', '기본이수과목'),
    ('COM2014', 'Social Learning과 인터넷', 3, 'MAJOR', 'MAJOR_COMMON', '1-4', NULL, 0, NULL, NULL),
    ('COM2015', '피지컬컴퓨팅', 3, 'MAJOR', 'MAJOR_COMMON', '2-3', NULL, 1, '영', NULL),
    ('COM2016', '리눅스시스템', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '2', NULL, 0, NULL, NULL),
    ('COM2017', '인공지능융합수업설계', 3, 'MAJOR', 'TEACHER_TRACK', '2-4', NULL, 1, '한', NULL),
    ('COM2018', '인공지능과교육', 3, 'MAJOR', 'TEACHER_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM2019', '웹프로그래밍', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 0, NULL, NULL),
    ('COM2020', '머신러닝', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM2021', '디지털비디오처리', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM2022', '게임프로그래밍', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM2023', '자연어처리', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', NULL),
    ('COM3001', '교육용멀티미디어', 3, 'MAJOR', 'TEACHER_TRACK', '2-3', NULL, 1, '한', NULL),
    ('COM3002', '데이터통신기술', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '2-3', NULL, 1, '한', NULL),
    ('COM3003', '데이터베이스', 3, 'MAJOR', 'BASIC_REQUIRED', '3', '1', 1, '한', '기본이수과목'),
    ('COM3004', '컴퓨터구조', 3, 'MAJOR', 'BASIC_REQUIRED', '3-4', '1', 1, '영', '기본이수과목'),
    ('COM3005', '운영체제', 3, 'MAJOR', 'BASIC_REQUIRED', '3-4', '2', 1, '영', '기본이수과목'),
    ('COM3006', '컴퓨터네트워크', 3, 'MAJOR', 'BASIC_REQUIRED', '3-4', '2', 1, '한', '기본이수과목'),
    ('COM3007', '소프트웨어공학', 3, 'MAJOR', 'BASIC_REQUIRED', '3-4', '2', 1, '한', '기본이수과목'),
    ('COM3008', '프로그래밍언어론', 3, 'MAJOR', 'MAJOR_COMMON', '3-4', NULL, 1, '한', NULL),
    ('COM3009', '컴퓨터교과교육론', 3, 'MAJOR', 'SUBJECT_EDUCATION', '3-4', '2', 1, '한', '교과교육영역'),
    ('COM3012', '교육용소프트웨어개발', 3, 'MAJOR', 'TEACHER_TRACK', '3-4', NULL, 0, NULL, NULL),
    ('COM3015', '수업과소프트웨어활용', 3, 'MAJOR', 'TEACHER_TRACK', '3-4', NULL, 0, NULL, NULL),
    ('COM3019', '네트워크운영관리', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '4', NULL, 0, NULL, NULL),
    ('COM3022', '인공지능', 3, 'MAJOR', 'BASIC_REQUIRED_CHOICE', '4', '1', 1, '영', '기본이수과목 선택군'),
    ('COM3023', '컴퓨터보안', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '4', NULL, 1, '한', NULL),
    ('COM3024', '컴퓨터교육세미나', 3, 'MAJOR', 'TEACHER_TRACK', '4', NULL, 0, NULL, NULL),
    ('COM3026', '알고리즘', 3, 'MAJOR', 'BASIC_REQUIRED_CHOICE', '3', '2', 1, '한', '기본이수과목 선택군'),
    ('COM3028', '가상및증강현실처리', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '3-4', NULL, 0, NULL, NULL),
    ('COM3029', '클라우드컴퓨팅개론', 3, 'MAJOR', 'TEACHER_TRACK', '3-4', NULL, 1, '한', NULL),
    ('COM3030', '모바일프로그래밍입문', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '3-4', NULL, 0, NULL, NULL),
    ('COM3033', '빅데이터시각화', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '3-4', NULL, 1, '한', NULL),
    ('COM3034', '지능형비전', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', NULL),
    ('COM3035', '데이터과학및분석소개', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '3-4', NULL, 1, '한', NULL),
    ('COM3036', '소프트웨어설계', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM3037', '글로벌인공지능교육트렌드분석', 3, 'MAJOR', 'TEACHER_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM3038', '3차원비전의이해및프로그래밍', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM3039', '컴퓨터그래픽스', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', NULL),
    ('COM3040', '인공지능소프트웨어프로젝트', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '3-4', NULL, 1, '한', NULL),
    ('COM3041', '인공지능융합캡스톤프로젝트', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '3-4', NULL, 1, '영', NULL),
    ('AAI2014', '강화학습', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', '인공지능융합전공'),
    ('AAI3005', '데이터마이닝', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 0, NULL, '인공지능융합전공'),
    ('AAI3006', '기계학습', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', '인공지능융합전공'),
    ('AAI3013', '빅데이터처리', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 0, NULL, '인공지능융합전공'),
    ('AAI3017', '인간인공지능상호작용', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', '인공지능융합전공'),
    ('AAI3028', '인공지능기반3D콘텐츠개발', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', '인공지능융합전공'),
    ('CHS2003', '빅데이터와인공지능을활용한시스템강건설계', 2, 'MAJOR', 'PROFESSIONAL_TRACK', '1-4', NULL, 0, NULL, '도전학기'),
    ('CHS2008', '4차산업혁명과창업비즈니스', 1, 'MAJOR', 'PROFESSIONAL_TRACK', '1-4', NULL, 0, NULL, '도전학기'),
    ('CHS2015', '인공지능기반뇌과학융합기술', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '1-4', NULL, 0, NULL, '도전학기'),
    ('CHS2017', '신인류포노사피엔스경험디자인', 3, 'MAJOR', 'PROFESSIONAL_TRACK', '1-4', NULL, 0, NULL, '도전학기'),
    ('CHS7002', '머신러닝과딥러닝', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 0, NULL, '도전학기(대학원)'),
    ('CHS7003', '인공지능응용', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 0, NULL, '도전학기(대학원)'),
    ('CHS7004', 'Python활용인문사회과학논문쓰기', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', '도전학기(대학원)'),
    ('CHS7008', 'AI기반전략적의사결정', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '한', '도전학기(대학원)'),
    ('ISS3198', 'Artificial Intelligence', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', '국제하계대학'),
    ('IWS3034', 'Artificial Intelligence', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 0, NULL, '국제동계대학'),
    ('MAE3029', '인공지능수학', 3, 'MAJOR', 'PROFESSIONAL_TRACK', NULL, NULL, 1, '영', '수학교육과'),
    ('CFTD067', '컴퓨터교재연구및지도법', 3, 'MAJOR', 'SUBJECT_EDUCATION', NULL, '1', 1, NULL, '교과교육영역'),
    ('CFTD082', '상업정보교과논리논술', 2, 'MAJOR', 'SUBJECT_EDUCATION', NULL, '1,2', 1, NULL, '교과교육영역'),
    ('CFTD094', '교육학개론', 2, 'TEACHING', 'TEACHING_THEORY', '1', '1,2', 1, NULL, '교직이론'),
    ('CFTD008', '교육의역사철학적이해', 2, 'TEACHING', 'TEACHING_THEORY', '2', '2', 1, NULL, '교직이론'),
    ('CFTD009', '교육의사회학적이해', 2, 'TEACHING', 'TEACHING_THEORY', '4', '1', 1, NULL, '교직이론'),
    ('CFTD007', '교육의심리학적이해', 2, 'TEACHING', 'TEACHING_THEORY', '2', '1', 1, NULL, '교직이론'),
    ('CFTD103', '교육과정', 2, 'TEACHING', 'TEACHING_THEORY', '3', '1', 1, NULL, '교직이론'),
    ('CFTD104', '교육평가', 2, 'TEACHING', 'TEACHING_THEORY', '3', '2', 1, NULL, '교직이론'),
    ('CFTD005', '교육방법및교육공학', 2, 'TEACHING', 'TEACHING_THEORY', '3', '2', 1, NULL, '교직이론'),
    ('CFTD006', '교육행정및교육경영', 2, 'TEACHING', 'TEACHING_THEORY', '4', '2', 1, NULL, '교직이론'),
    ('CFTD093', '특수교육학개론', 2, 'TEACHING', 'TEACHING_FOUNDATION', '3', '1', 1, NULL, '교직소양'),
    ('CFTD123', '디지털교육', 1, 'TEACHING', 'TEACHING_FOUNDATION', '3', '1', 1, NULL, '교직소양'),
    ('CFTD122', '교직실무', 1, 'TEACHING', 'TEACHING_FOUNDATION', '3', '2', 1, NULL, '교직소양'),
    ('CFTD119', '학교폭력예방및학생의이해', 2, 'TEACHING', 'TEACHING_FOUNDATION', '2', '2', 1, NULL, '교직소양'),
    ('CFTD010', '교육실습', 2, 'TEACHING', 'TEACHING_PRACTICUM', '4', '1', 1, NULL, '교육실습'),
    ('CFTD078', '교육봉사활동', 2, 'TEACHING', 'TEACHING_PRACTICUM', '4', '2', 1, NULL, '교육실습')
ON CONFLICT(course_id) DO UPDATE SET
    course_name = excluded.course_name,
    credit = excluded.credit,
    category = excluded.category,
    sub_category = excluded.sub_category,
    recommended_year = excluded.recommended_year,
    recommended_semester = excluded.recommended_semester,
    is_offered = excluded.is_offered,
    language = excluded.language,
    note = excluded.note;

INSERT INTO requirements (
    requirement_id,
    requirement_name,
    category,
    required_credits,
    required_course_count,
    description
) VALUES
    ('MAJOR_CREDITS', '전공 과목', 'MAJOR', 50, NULL, '전공 과목 50학점 이상'),
    ('BASIC_REQUIRED', '기본이수과목', 'MAJOR', 21, 7, '기본이수과목 7과목 및 21학점 이상'),
    ('SUBJECT_EDUCATION', '교과교육영역', 'MAJOR', 8, 3, '교과교육영역 3과목 및 8학점 이상'),
    ('TEACHING_CREDITS', '교직과목', 'TEACHING', 22, NULL, '교직과목 22학점 이상'),
    ('TEACHING_THEORY', '교직이론', 'TEACHING', 12, 6, '교직이론 6과목 및 12학점 이상'),
    ('TEACHING_FOUNDATION', '교직소양', 'TEACHING', 6, NULL, '교직소양 6학점 이상'),
    ('TEACHING_PRACTICUM', '교육실습', 'TEACHING', 4, NULL, '교육실습 4학점 이상')
ON CONFLICT(requirement_id) DO UPDATE SET
    requirement_name = excluded.requirement_name,
    category = excluded.category,
    required_credits = excluded.required_credits,
    required_course_count = excluded.required_course_count,
    description = excluded.description;

INSERT INTO requirement_courses (
    requirement_id,
    course_id,
    is_mandatory
) VALUES
    ('BASIC_REQUIRED', 'COM2003', 1),
    ('BASIC_REQUIRED', 'COM2002', 1),
    ('BASIC_REQUIRED', 'COM3003', 1),
    ('BASIC_REQUIRED', 'COM2012', 1),
    ('BASIC_REQUIRED', 'COM3006', 1),
    ('BASIC_REQUIRED', 'COM3005', 1),
    ('BASIC_REQUIRED', 'COM3004', 1),
    ('BASIC_REQUIRED', 'COM3007', 1),
    ('SUBJECT_EDUCATION', 'COM3009', 1),
    ('SUBJECT_EDUCATION', 'CFTD067', 1),
    ('SUBJECT_EDUCATION', 'CFTD082', 1),
    ('TEACHING_THEORY', 'CFTD094', 0),
    ('TEACHING_THEORY', 'CFTD008', 0),
    ('TEACHING_THEORY', 'CFTD009', 0),
    ('TEACHING_THEORY', 'CFTD007', 0),
    ('TEACHING_THEORY', 'CFTD103', 0),
    ('TEACHING_THEORY', 'CFTD104', 0),
    ('TEACHING_THEORY', 'CFTD005', 0),
    ('TEACHING_THEORY', 'CFTD006', 0),
    ('TEACHING_FOUNDATION', 'CFTD093', 1),
    ('TEACHING_FOUNDATION', 'CFTD123', 1),
    ('TEACHING_FOUNDATION', 'CFTD122', 1),
    ('TEACHING_FOUNDATION', 'CFTD119', 1),
    ('TEACHING_PRACTICUM', 'CFTD010', 1),
    ('TEACHING_PRACTICUM', 'CFTD078', 1)
ON CONFLICT(requirement_id, course_id) DO UPDATE SET
    is_mandatory = excluded.is_mandatory;

INSERT INTO choice_groups (
    choice_group_id,
    requirement_id,
    group_name,
    required_select_count,
    description
) VALUES
    ('BASIC_REQUIRED_ALGORITHM_AI', 'BASIC_REQUIRED', '알고리즘/인공지능 선택', 1, '알고리즘 또는 인공지능 중 최소 1과목 선택')
ON CONFLICT(choice_group_id) DO UPDATE SET
    requirement_id = excluded.requirement_id,
    group_name = excluded.group_name,
    required_select_count = excluded.required_select_count,
    description = excluded.description;

INSERT OR IGNORE INTO choice_group_courses (
    choice_group_id,
    course_id
) VALUES
    ('BASIC_REQUIRED_ALGORITHM_AI', 'COM3026'),
    ('BASIC_REQUIRED_ALGORITHM_AI', 'COM3022');

INSERT INTO non_course_requirements (
    requirement_id,
    requirement_name,
    required_count,
    recommended_timing,
    description
) VALUES
    ('TEACHING_APTITUDE_CHARACTER', '교직 적성 및 인성검사', 2, '재학 중', '최소 2회 필요'),
    ('CPR_TRAINING', '응급처치 및 심폐소생술', 2, '재학 중', '최소 2회 필요'),
    ('GENDER_SENSITIVITY_EDUCATION', '성인지교육', 4, '재학 중', '최소 4회 필요'),
    ('CRIMINAL_RECORD_CHECK', '성범죄 경력조회', 1, '졸업 직전', '졸업 전 1회 필요'),
    ('DRUG_TEST', '마약류 검사', 1, '졸업 직전', '졸업 전 1회 필요')
ON CONFLICT(requirement_id) DO UPDATE SET
    requirement_name = excluded.requirement_name,
    required_count = excluded.required_count,
    recommended_timing = excluded.recommended_timing,
    description = excluded.description;

-- Demo profile used by the web form and sample reset endpoint.
INSERT INTO students (
    student_id,
    student_name,
    current_year,
    current_semester,
    target_track
) VALUES
    ('S001', 'Sample Student', 1, 2, 'COMMON')
ON CONFLICT(student_id) DO UPDATE SET
    student_name = excluded.student_name,
    current_year = excluded.current_year,
    current_semester = excluded.current_semester,
    target_track = excluded.target_track;

INSERT INTO completed_courses (
    student_id,
    course_id,
    completed_year,
    completed_semester,
    grade,
    score
) VALUES
    ('S001', 'COM2002', 2026, 1, 'P', NULL),
    ('S001', 'COM2003', 2026, 1, 'P', NULL)
ON CONFLICT(student_id, course_id) DO UPDATE SET
    completed_year = excluded.completed_year,
    completed_semester = excluded.completed_semester,
    grade = excluded.grade,
    score = excluded.score;

INSERT INTO student_non_course_records (
    student_id,
    requirement_id,
    completed_count,
    completed,
    note
) VALUES
    ('S001', 'TEACHING_APTITUDE_CHARACTER', 2, 1, ''),
    ('S001', 'CPR_TRAINING', 2, 1, ''),
    ('S001', 'GENDER_SENSITIVITY_EDUCATION', 4, 1, ''),
    ('S001', 'CRIMINAL_RECORD_CHECK', 1, 1, ''),
    ('S001', 'DRUG_TEST', 1, 1, '')
ON CONFLICT(student_id, requirement_id) DO UPDATE SET
    completed_count = excluded.completed_count,
    completed = excluded.completed,
    note = excluded.note;

INSERT OR IGNORE INTO prerequisites (
    from_course_id,
    to_course_id,
    relation_type,
    weight,
    reason
) VALUES
    ('COM2002', 'COM2012', 'REQUIRED', 5, 'Programming basics are required before Data Structures.'),
    ('COM2012', 'COM3026', 'REQUIRED', 5, 'Data Structures are required before Algorithms.'),
    ('COM2002', 'COM3003', 'RECOMMENDED', 4, 'Programming basics help with Database practice.'),
    ('COM2012', 'COM3003', 'RECOMMENDED', 3, 'Data structure concepts help with Database design.'),
    ('COM2002', 'COM3007', 'RECOMMENDED', 3, 'Programming basics help with Software Engineering.'),
    ('COM2012', 'COM3007', 'RECOMMENDED', 3, 'Data Structures help with Software Engineering implementation.'),
    ('COM2002', 'COM3008', 'RECOMMENDED', 3, 'Programming basics help with Programming Languages.'),
    ('COM2012', 'COM3008', 'RECOMMENDED', 3, 'Data Structures help with Programming Languages.'),
    ('COM2002', 'COM3004', 'RECOMMENDED', 3, 'Programming basics help with Computer Architecture.'),
    ('COM3004', 'COM3005', 'REQUIRED', 5, 'Computer Architecture is required before Operating Systems.'),
    ('COM3005', 'COM3006', 'RECOMMENDED', 4, 'Operating Systems help with Computer Networks.'),
    ('COM3004', 'COM3006', 'RECOMMENDED', 3, 'Computer Architecture helps with Computer Networks.'),
    ('COM2002', 'COM2020', 'RECOMMENDED', 4, 'Programming basics help with Machine Learning.'),
    ('COM2012', 'COM2020', 'RECOMMENDED', 4, 'Data Structures help with Machine Learning.'),
    ('COM3026', 'COM2020', 'RECOMMENDED', 4, 'Algorithms help with Machine Learning.'),
    ('COM2020', 'COM3022', 'RECOMMENDED', 4, 'Machine Learning helps with Artificial Intelligence.'),
    ('COM2020', 'COM2023', 'RECOMMENDED', 4, 'Machine Learning helps with Natural Language Processing.'),
    ('COM2020', 'COM3034', 'RECOMMENDED', 4, 'Machine Learning helps with Intelligent Vision.'),
    ('COM3003', 'COM3035', 'RECOMMENDED', 4, 'Database background helps with Data Science and Analytics.'),
    ('COM3035', 'AAI3005', 'RECOMMENDED', 4, 'Data Science and Analytics help with Data Mining.'),
    ('COM3035', 'AAI3013', 'RECOMMENDED', 4, 'Data Science and Analytics help with Big Data Processing.'),
    ('COM3035', 'COM3033', 'RECOMMENDED', 4, 'Data Science and Analytics help with Big Data Visualization.'),
    ('COM3004', 'COM2016', 'RECOMMENDED', 3, 'Computer Architecture helps with Linux Systems.'),
    ('COM3005', 'COM2016', 'RECOMMENDED', 4, 'Operating Systems help with Linux Systems.'),
    ('COM3006', 'COM3019', 'RECOMMENDED', 4, 'Computer Networks help with Network Operation Management.'),
    ('COM3006', 'COM3023', 'RECOMMENDED', 4, 'Computer Networks help with Computer Security.'),
    ('COM3005', 'COM3023', 'RECOMMENDED', 3, 'Operating Systems help with Computer Security.'),
    ('COM3002', 'COM3006', 'RECOMMENDED', 3, 'Data Communication Technology helps with Computer Networks.'),
    ('COM2002', 'COM2019', 'RECOMMENDED', 3, 'Programming basics help with Web Programming.'),
    ('COM2002', 'COM3030', 'RECOMMENDED', 3, 'Programming basics help with Mobile Programming.'),
    ('COM2002', 'COM2022', 'RECOMMENDED', 3, 'Programming basics help with Game Programming.'),
    ('COM2002', 'COM3036', 'RECOMMENDED', 3, 'Programming basics help with Software Design.'),
    ('COM3007', 'COM3036', 'RECOMMENDED', 4, 'Software Engineering helps with Software Design.'),
    ('COM2002', 'COM3039', 'RECOMMENDED', 3, 'Programming basics help with Computer Graphics.'),
    ('COM3039', 'COM3028', 'RECOMMENDED', 3, 'Computer Graphics helps with VR and AR Processing.'),
    ('COM2003', 'COM3009', 'REQUIRED', 5, 'Computer Education Introduction is required before Computer Subject Education.'),
    ('COM3009', 'CFTD067', 'RECOMMENDED', 4, 'Computer Subject Education helps with Teaching Materials and Methods.'),
    ('COM3009', 'CFTD082', 'RECOMMENDED', 4, 'Computer Subject Education helps with Subject Logic and Essay Writing.'),
    ('COM2003', 'COM2018', 'RECOMMENDED', 3, 'Computer Education Introduction helps with AI and Education.'),
    ('COM2018', 'COM2017', 'RECOMMENDED', 4, 'AI and Education helps with AI Convergence Lesson Design.'),
    ('COM2018', 'COM3037', 'RECOMMENDED', 4, 'AI and Education helps with Global AI Education Trend Analysis.'),
    ('COM2002', 'COM3012', 'RECOMMENDED', 3, 'Programming basics help with Educational Software Development.'),
    ('COM3007', 'COM3012', 'RECOMMENDED', 3, 'Software Engineering helps with Educational Software Development.'),
    ('COM2018', 'COM3015', 'RECOMMENDED', 3, 'AI and Education helps with Class and Software Use.'),
    ('CFTD094', 'CFTD007', 'RECOMMENDED', 2, 'Introduction to Education helps with Educational Psychology.'),
    ('CFTD094', 'CFTD008', 'RECOMMENDED', 2, 'Introduction to Education helps with History and Philosophy of Education.'),
    ('CFTD007', 'CFTD103', 'RECOMMENDED', 2, 'Educational Psychology helps with Curriculum.'),
    ('CFTD103', 'CFTD104', 'RECOMMENDED', 2, 'Curriculum helps with Educational Evaluation.'),
    ('CFTD103', 'CFTD005', 'RECOMMENDED', 2, 'Curriculum helps with Educational Methods and Technology.'),
    ('CFTD119', 'CFTD010', 'RECOMMENDED', 3, 'School Violence Prevention helps before Teaching Practicum.'),
    ('CFTD122', 'CFTD010', 'RECOMMENDED', 3, 'Teaching Profession Practice helps before Teaching Practicum.'),
    ('CFTD010', 'CFTD078', 'RECOMMENDED', 2, 'Teaching Practicum helps before Educational Volunteer Work.');
