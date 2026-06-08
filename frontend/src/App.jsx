import { memo, useCallback, useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  AlertCircle,
  BookOpen,
  Check,
  ClipboardList,
  GitBranch,
  GraduationCap,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
} from "lucide-react";

const STUDENT_ID = "S001";
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

const categoryLabels = {
  MAJOR: "전공",
  TEACHING: "교직",
  major: "전공",
  teaching: "교직",
  non_course: "비교과",
};

const nodeTypes = {
  course: memo(CourseNode),
};

function App() {
  const [activeView, setActiveView] = useState("completed");
  const [student, setStudent] = useState(null);
  const [courses, setCourses] = useState([]);
  const [selectedCourseIds, setSelectedCourseIds] = useState(new Set());
  const [savedCourseIds, setSavedCourseIds] = useState(new Set());
  const [recommendations, setRecommendations] = useState([]);
  const [requirements, setRequirements] = useState(null);
  const [nonCourseRequirements, setNonCourseRequirements] = useState([]);
  const [nonCourseDrafts, setNonCourseDrafts] = useState({});
  const [savedNonCourseDrafts, setSavedNonCourseDrafts] = useState({});
  const [graphData, setGraphData] = useState(null);
  const [selectedGraphCourse, setSelectedGraphCourse] = useState(null);
  const [selectedCourseRelations, setSelectedCourseRelations] = useState(null);
  const [searchText, setSearchText] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [offeredOnly, setOfferedOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isResetting, setIsResetting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingNonCourse, setIsSavingNonCourse] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadInitialData();
  }, []);

  const selectedCount = selectedCourseIds.size;
  const savedCount = savedCourseIds.size;
  const hasUnsavedChanges = !sameSet(selectedCourseIds, savedCourseIds);
  const hasNonCourseUnsavedChanges = !sameNonCourseDrafts(
    nonCourseDrafts,
    savedNonCourseDrafts,
  );
  const recommendedCourseIds = useMemo(
    () => new Set(recommendations.map((course) => course.course_id)),
    [recommendations],
  );

  const filteredCourses = useMemo(() => {
    const keyword = searchText.trim().toLowerCase();
    return courses.filter((course) => {
      const matchesKeyword =
        !keyword ||
        course.course_id.toLowerCase().includes(keyword) ||
        course.course_name.toLowerCase().includes(keyword);
      const matchesCategory =
        categoryFilter === "ALL" || course.category === categoryFilter;
      const matchesOffered = !offeredOnly || course.is_offered;
      return matchesKeyword && matchesCategory && matchesOffered;
    });
  }, [categoryFilter, courses, offeredOnly, searchText]);

  async function loadInitialData() {
    setIsLoading(true);
    setError("");
    try {
      const [
        studentData,
        coursesData,
        completedData,
        recommendationsData,
        requirementsData,
        nonCourseData,
        graphDataResult,
      ] =
        await Promise.all([
          requestJson(`/api/students/${STUDENT_ID}`),
          requestJson("/api/courses"),
          requestJson(`/api/students/${STUDENT_ID}/completed`),
          requestJson(`/api/students/${STUDENT_ID}/recommendations?limit=10`),
          requestJson(`/api/students/${STUDENT_ID}/requirements`),
          requestJson(`/api/students/${STUDENT_ID}/non-course-requirements`),
          requestJson("/api/graph"),
        ]);
      const completedIds = new Set(completedData.map((course) => course.course_id));
      setStudent(studentData);
      setCourses(coursesData);
      setSelectedCourseIds(completedIds);
      setSavedCourseIds(new Set(completedIds));
      setRecommendations(recommendationsData);
      setRequirements(requirementsData);
      applyNonCourseItems(nonCourseData.items);
      setGraphData(graphDataResult);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshRecommendations() {
    setIsRefreshing(true);
    setError("");
    try {
      const [nextRecommendations, nextRequirements, nextNonCourse] = await Promise.all([
        requestJson(`/api/students/${STUDENT_ID}/recommendations?limit=10`),
        requestJson(`/api/students/${STUDENT_ID}/requirements`),
        requestJson(`/api/students/${STUDENT_ID}/non-course-requirements`),
      ]);
      setRecommendations(nextRecommendations);
      setRequirements(nextRequirements);
      applyNonCourseItems(nextNonCourse.items);
      setMessage("추천 과목과 요건 요약을 갱신했습니다.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRefreshing(false);
    }
  }

  async function resetSampleStudent() {
    setIsResetting(true);
    setError("");
    setMessage("");
    try {
      const result = await requestJson(`/api/students/${STUDENT_ID}/reset-sample`, {
        method: "POST",
      });
      await syncStudentOutputs(result.completed_course_ids);
      setSelectedGraphCourse(null);
      setSelectedCourseRelations(null);
      setMessage("샘플 학생을 초기 상태로 되돌렸습니다.");
      setActiveView("completed");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsResetting(false);
    }
  }

  async function saveCompletedCourses() {
    setIsSaving(true);
    setError("");
    setMessage("");
    try {
      const sortedCourseIds = [...selectedCourseIds].sort();
      const result = await requestJson(`/api/students/${STUDENT_ID}/completed`, {
        method: "PUT",
        body: JSON.stringify({ course_ids: sortedCourseIds }),
      });
      const nextSavedIds = new Set(result.completed_course_ids);
      setSelectedCourseIds(nextSavedIds);
      setSavedCourseIds(new Set(nextSavedIds));
      await syncStudentOutputs(result.completed_course_ids);
      setMessage("이수 과목을 저장했고 추천 과목과 요건 요약을 갱신했습니다.");
      setActiveView("recommendations");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function syncStudentOutputs(completedCourseIds) {
    const [nextRecommendations, nextRequirements, nextNonCourse] = await Promise.all([
      requestJson(`/api/students/${STUDENT_ID}/recommendations?limit=10`),
      requestJson(`/api/students/${STUDENT_ID}/requirements`),
      requestJson(`/api/students/${STUDENT_ID}/non-course-requirements`),
    ]);
    const nextCompletedIds = new Set(completedCourseIds);
    setSelectedCourseIds(nextCompletedIds);
    setSavedCourseIds(new Set(nextCompletedIds));
    setRecommendations(nextRecommendations);
    setRequirements(nextRequirements);
    applyNonCourseItems(nextNonCourse.items);
  }

  async function saveNonCourseRequirements() {
    setIsSavingNonCourse(true);
    setError("");
    setMessage("");
    try {
      const result = await requestJson(
        `/api/students/${STUDENT_ID}/non-course-requirements`,
        {
          method: "PUT",
          body: JSON.stringify({
            items: nonCourseRequirements.map((item) => {
              const draft = nonCourseDrafts[item.key] ?? nonCourseItemToDraft(item);
              return {
                key: item.key,
                completed: draft.completed,
                value: draft.value,
                note: draft.note,
              };
            }),
          }),
        },
      );
      applyNonCourseItems(result.items);
      const nextRequirements = await requestJson(
        `/api/students/${STUDENT_ID}/requirements`,
      );
      setRequirements(nextRequirements);
      setMessage("비교과 요건을 저장했고 요건 요약을 갱신했습니다.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSavingNonCourse(false);
    }
  }

  function applyNonCourseItems(items) {
    const nextItems = items ?? [];
    const drafts = nonCourseItemsToDrafts(nextItems);
    setNonCourseRequirements(nextItems);
    setNonCourseDrafts(drafts);
    setSavedNonCourseDrafts(drafts);
  }

  function updateNonCourseCompleted(key, completed) {
    setMessage("");
    const item = nonCourseRequirements.find((requirement) => requirement.key === key);
    setNonCourseDrafts((current) => {
      const draft = current[key] ?? nonCourseItemToDraft(item);
      const requiredValue = item?.required_value ?? 1;
      return {
        ...current,
        [key]: {
          ...draft,
          completed,
          value: completed ? Math.max(draft.value, requiredValue) : 0,
        },
      };
    });
  }

  function updateNonCourseValue(key, value) {
    setMessage("");
    const item = nonCourseRequirements.find((requirement) => requirement.key === key);
    setNonCourseDrafts((current) => {
      const draft = current[key] ?? nonCourseItemToDraft(item);
      const nextValue = Math.max(Number(value) || 0, 0);
      const requiredValue = item?.required_value ?? 1;
      return {
        ...current,
        [key]: {
          ...draft,
          value: nextValue,
          completed: nextValue >= requiredValue,
        },
      };
    });
  }

  function updateNonCourseNote(key, note) {
    setMessage("");
    const item = nonCourseRequirements.find((requirement) => requirement.key === key);
    setNonCourseDrafts((current) => {
      const draft = current[key] ?? nonCourseItemToDraft(item);
      return {
        ...current,
        [key]: {
          ...draft,
          note,
        },
      };
    });
  }

  function toggleCourse(courseId) {
    setMessage("");
    setSelectedCourseIds((current) => {
      const next = new Set(current);
      if (next.has(courseId)) {
        next.delete(courseId);
      } else {
        next.add(courseId);
      }
      return next;
    });
  }

  if (isLoading) {
    return (
      <main className="shell loading-shell">
        <Loader2 className="spin" aria-hidden="true" />
        <p>과목 정보를 불러오는 중입니다.</p>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Curriculum Recommendation</p>
          <h1>이수 과목 기반 추천</h1>
        </div>
        {student && (
          <section className="student-summary" aria-label="학생 정보">
            <div>
              <span>학생</span>
              <strong>{student.student_name ?? student.student_id}</strong>
            </div>
            <div>
              <span>현재</span>
              <strong>
                {student.current_year}학년 {student.current_semester}학기
              </strong>
            </div>
            <div>
              <span>트랙</span>
              <strong>{student.target_track ?? "-"}</strong>
            </div>
          </section>
        )}
      </header>

      {error && (
        <div className="alert error" role="alert">
          <AlertCircle size={18} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
      {message && (
        <div className="alert success" role="status">
          <Check size={18} aria-hidden="true" />
          <span>{message}</span>
        </div>
      )}

      <nav className="view-tabs" aria-label="화면 선택">
        <button
          className={activeView === "completed" ? "active" : ""}
          type="button"
          onClick={() => setActiveView("completed")}
        >
          <BookOpen size={18} aria-hidden="true" />
          이수 과목 체크
        </button>
        <button
          className={activeView === "non-course" ? "active" : ""}
          type="button"
          onClick={() => setActiveView("non-course")}
        >
          <ClipboardList size={18} aria-hidden="true" />
          비교과 요건
        </button>
        <button
          className={activeView === "recommendations" ? "active" : ""}
          type="button"
          onClick={() => setActiveView("recommendations")}
        >
          <GraduationCap size={18} aria-hidden="true" />
          추천 과목
        </button>
        <button
          className={activeView === "graph" ? "active" : ""}
          type="button"
          onClick={() => setActiveView("graph")}
        >
          <GitBranch size={18} aria-hidden="true" />
          선수과목 그래프
        </button>
      </nav>

      <RequirementsDashboard requirements={requirements} />

      {activeView === "completed" ? (
        <section className="content-section" aria-labelledby="completed-title">
          <div className="section-toolbar">
            <div>
              <h2 id="completed-title">이수 과목 체크</h2>
              <p>
                선택 {selectedCount}개, 저장됨 {savedCount}개
                {hasUnsavedChanges ? " · 저장 필요" : ""}
              </p>
            </div>
            <div className="toolbar-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={resetSampleStudent}
                disabled={isResetting || isSaving}
              >
                {isResetting ? (
                  <Loader2 className="spin" size={18} aria-hidden="true" />
                ) : (
                  <RotateCcw size={18} aria-hidden="true" />
                )}
                초기화
              </button>
              <button
                className="primary-button"
                type="button"
                onClick={saveCompletedCourses}
                disabled={isSaving || isResetting}
              >
                {isSaving ? (
                  <Loader2 className="spin" size={18} aria-hidden="true" />
                ) : (
                  <Save size={18} aria-hidden="true" />
                )}
                저장
              </button>
            </div>
          </div>

          <div className="filters" aria-label="과목 필터">
            <label className="search-field">
              <Search size={18} aria-hidden="true" />
              <input
                type="search"
                placeholder="과목명 또는 과목 ID 검색"
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
              />
            </label>
            <label>
              <span>구분</span>
              <select
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value="ALL">전체</option>
                <option value="MAJOR">전공</option>
                <option value="TEACHING">교직</option>
              </select>
            </label>
            <label className="switch-field">
              <input
                type="checkbox"
                checked={offeredOnly}
                onChange={(event) => setOfferedOnly(event.target.checked)}
              />
              개설 과목만
            </label>
          </div>

          <div className="course-grid">
            {filteredCourses.map((course) => {
              const checked = selectedCourseIds.has(course.course_id);
              return (
                <label
                  className={`course-item ${checked ? "checked" : ""}`}
                  data-course-id={course.course_id}
                  key={course.course_id}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleCourse(course.course_id)}
                  />
                  <span className="course-copy">
                    <strong>{course.course_name}</strong>
                    <small>
                      {course.course_id} · {course.credit}학점 ·{" "}
                      {categoryLabels[course.category] ?? course.category}
                    </small>
                  </span>
                  <span className={course.is_offered ? "badge offered" : "badge muted"}>
                    {course.is_offered ? "개설" : "미개설"}
                  </span>
                </label>
              );
            })}
          </div>
        </section>
      ) : activeView === "non-course" ? (
        <NonCourseRequirementsView
          drafts={nonCourseDrafts}
          hasUnsavedChanges={hasNonCourseUnsavedChanges}
          isSaving={isSavingNonCourse}
          items={nonCourseRequirements}
          onCompletedChange={updateNonCourseCompleted}
          onNoteChange={updateNonCourseNote}
          onSave={saveNonCourseRequirements}
          onValueChange={updateNonCourseValue}
        />
      ) : activeView === "recommendations" ? (
        <section className="content-section" aria-labelledby="recommendations-title">
          <div className="section-toolbar">
            <div>
              <h2 id="recommendations-title">추천 과목</h2>
              <p>
                저장된 {savedCount}개 이수 과목을 기준으로 계산했습니다.
                {hasUnsavedChanges ? " 변경 사항은 저장 후 반영됩니다." : ""}
              </p>
            </div>
            <button
              className="secondary-button"
              type="button"
              onClick={refreshRecommendations}
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <Loader2 className="spin" size={18} aria-hidden="true" />
              ) : (
                <RefreshCw size={18} aria-hidden="true" />
              )}
              갱신
            </button>
          </div>

          <div className="recommendation-list">
            {recommendations.length === 0 ? (
              <div className="empty-state">추천 가능한 과목이 없습니다.</div>
            ) : (
              recommendations.map((course, index) => (
                <article className="recommendation-card" key={course.course_id}>
                  <div className="recommendation-rank">{index + 1}</div>
                  <div className="recommendation-body">
                    <div className="recommendation-title">
                      <div>
                        <h3>{course.course_name}</h3>
                        <p>
                          {course.course_id} · {course.credit}학점 ·{" "}
                          {categoryLabels[course.category] ?? course.category}
                        </p>
                      </div>
                      <strong className="score">{course.score}점</strong>
                    </div>

                    <div className="reason-list">
                      {course.reasons.map((reason) => (
                        <span key={reason}>{reason}</span>
                      ))}
                    </div>

                    <dl className="prerequisite-list">
                      <div>
                        <dt>필수 미이수</dt>
                        <dd>
                          {formatList(course.missing_required_prerequisites)}
                        </dd>
                      </div>
                      <div>
                        <dt>권장 이수</dt>
                        <dd>
                          {formatList(course.completed_recommended_prerequisites)}
                        </dd>
                      </div>
                      <div>
                        <dt>권장 미이수</dt>
                        <dd>
                          {formatList(course.missing_recommended_prerequisites)}
                        </dd>
                      </div>
                    </dl>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      ) : (
        <GraphView
          completedCourseIds={savedCourseIds}
          graphData={graphData}
          recommendedCourseIds={recommendedCourseIds}
          selectedCourse={selectedGraphCourse}
          selectedCourseRelations={selectedCourseRelations}
          setError={setError}
          setSelectedCourse={setSelectedGraphCourse}
          setSelectedCourseRelations={setSelectedCourseRelations}
        />
      )}
    </main>
  );
}

function NonCourseRequirementsView({
  drafts,
  hasUnsavedChanges,
  isSaving,
  items,
  onCompletedChange,
  onNoteChange,
  onSave,
  onValueChange,
}) {
  return (
    <section className="content-section non-course-section" aria-labelledby="non-course-title">
      <div className="section-toolbar">
        <div>
          <h2 id="non-course-title">비교과 요건</h2>
          <p>
            비교과는 과목 체크와 분리해서 관리합니다.
            {hasUnsavedChanges ? " 변경 사항은 저장 후 반영됩니다." : ""}
          </p>
        </div>
        <button
          className="primary-button"
          type="button"
          onClick={onSave}
          disabled={isSaving}
        >
          {isSaving ? (
            <Loader2 className="spin" size={18} aria-hidden="true" />
          ) : (
            <Save size={18} aria-hidden="true" />
          )}
          저장
        </button>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">등록된 비교과 요건이 없습니다.</div>
      ) : (
        <div className="non-course-grid">
          {items.map((item) => {
            const draft = drafts[item.key] ?? nonCourseItemToDraft(item);
            const percent = progressPercent(draft.value, item.required_value);
            return (
              <article
                className={`non-course-card ${
                  draft.completed ? "satisfied" : "needed"
                }`}
                key={item.key}
              >
                <div className="non-course-card-header">
                  <label>
                    <input
                      type="checkbox"
                      checked={draft.completed}
                      onChange={(event) =>
                        onCompletedChange(item.key, event.target.checked)
                      }
                    />
                    <span>
                      <strong>{item.name}</strong>
                      <small>{item.recommended_timing ?? item.description ?? "-"}</small>
                    </span>
                  </label>
                  <strong>{draft.completed ? "충족" : "부족"}</strong>
                </div>

                <label className="non-course-value">
                  <span>완료 수치</span>
                  <div>
                    <input
                      min="0"
                      type="number"
                      value={draft.value}
                      onChange={(event) =>
                        onValueChange(item.key, event.target.value)
                      }
                    />
                    <em>
                      / {item.required_value} {item.unit}
                    </em>
                  </div>
                </label>

                <div className="progress-track" aria-hidden="true">
                  <span style={{ width: `${percent}%` }} />
                </div>
                <p className="progress-copy">진행률 {percent}%</p>

                <label className="non-course-note">
                  <span>메모</span>
                  <input
                    type="text"
                    placeholder="선택 입력"
                    value={draft.note}
                    onChange={(event) => onNoteChange(item.key, event.target.value)}
                  />
                </label>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function GraphView({
  completedCourseIds,
  graphData,
  recommendedCourseIds,
  selectedCourse,
  selectedCourseRelations,
  setError,
  setSelectedCourse,
  setSelectedCourseRelations,
}) {
  const selectedCourseId = selectedCourse?.course_id ?? null;
  const highlightedCourseIds = useMemo(() => {
    const ids = new Set();
    if (!selectedCourseId || !selectedCourseRelations) {
      return ids;
    }
    ids.add(selectedCourseId);
    selectedCourseRelations.prerequisites.forEach((course) => ids.add(course.course_id));
    selectedCourseRelations.dependents.forEach((course) => ids.add(course.course_id));
    return ids;
  }, [selectedCourseId, selectedCourseRelations]);

  const flowNodes = useMemo(
    () =>
      buildFlowNodes(
        graphData?.nodes ?? [],
        completedCourseIds,
        recommendedCourseIds,
        highlightedCourseIds,
        selectedCourseId,
      ),
    [completedCourseIds, graphData, highlightedCourseIds, recommendedCourseIds, selectedCourseId],
  );

  const flowEdges = useMemo(
    () => buildFlowEdges(graphData?.edges ?? [], selectedCourseId),
    [graphData, selectedCourseId],
  );

  const handleNodeClick = useCallback(
    async (_event, node) => {
      const course = node.data.course;
      setSelectedCourse(course);
      setSelectedCourseRelations(null);
      setError("");
      try {
        const relations = await requestJson(
          `/api/courses/${course.course_id}/prerequisites`,
        );
        setSelectedCourseRelations(relations);
      } catch (err) {
        setError(err.message);
      }
    },
    [setError, setSelectedCourse, setSelectedCourseRelations],
  );

  if (!graphData) {
    return (
      <section className="content-section graph-section" aria-labelledby="graph-title">
        <div className="empty-state">그래프 정보를 불러오는 중입니다.</div>
      </section>
    );
  }

  return (
    <section className="content-section graph-section" aria-labelledby="graph-title">
      <div className="section-toolbar">
        <div>
          <h2 id="graph-title">선수과목 그래프</h2>
          <p>
            과목 {graphData.nodes.length}개, 방향 간선 {graphData.edges.length}개
            {graphData.is_dag ? " · 전체 관계는 DAG입니다." : " · 순환 관계 확인 필요"}
          </p>
        </div>
      </div>

      <div className="graph-legend" aria-label="그래프 범례">
        <span className="legend-item completed">이수 완료</span>
        <span className="legend-item recommended">추천 과목</span>
        <span className="legend-item normal">일반 과목</span>
      </div>

      <div className="graph-layout">
        <div className="graph-canvas">
          <ReactFlow
            edges={flowEdges}
            fitView
            maxZoom={1.4}
            minZoom={0.18}
            nodeTypes={nodeTypes}
            nodes={flowNodes}
            onNodeClick={handleNodeClick}
          >
            <Background gap={28} />
            <MiniMap pannable zoomable />
            <Controls />
          </ReactFlow>
        </div>

        <GraphDetailCard
          completedCourseIds={completedCourseIds}
          recommendedCourseIds={recommendedCourseIds}
          relations={selectedCourseRelations}
          selectedCourse={selectedCourse}
        />
      </div>
    </section>
  );
}

function CourseNode({ data }) {
  const course = data.course;
  return (
    <div className={`course-flow-node ${data.status}`}>
      <Handle className="node-handle target" position={Position.Left} type="target" />
      <strong>{course.name}</strong>
      <span>{course.course_id}</span>
      <small>{statusLabel(data.status)}</small>
      <Handle className="node-handle source" position={Position.Right} type="source" />
    </div>
  );
}

function GraphDetailCard({
  completedCourseIds,
  recommendedCourseIds,
  relations,
  selectedCourse,
}) {
  if (!selectedCourse) {
    return (
      <aside className="graph-detail-card">
        <h3>과목 상세</h3>
        <p className="detail-empty">선택된 과목 없음</p>
      </aside>
    );
  }

  const status = courseStatus(
    selectedCourse.course_id,
    completedCourseIds,
    recommendedCourseIds,
  );

  return (
    <aside className="graph-detail-card">
      <div className="detail-heading">
        <div>
          <h3>{selectedCourse.name}</h3>
          <p>{selectedCourse.course_id}</p>
        </div>
        <span className={`detail-status ${status}`}>{statusLabel(status)}</span>
      </div>

      <dl className="detail-list">
        <div>
          <dt>학점</dt>
          <dd>{selectedCourse.credits}학점</dd>
        </div>
        <div>
          <dt>카테고리</dt>
          <dd>{categoryLabels[selectedCourse.category] ?? selectedCourse.category}</dd>
        </div>
        <div>
          <dt>권장 학년/학기</dt>
          <dd>
            {formatTiming(
              selectedCourse.recommended_year_label,
              selectedCourse.recommended_semester_label,
            )}
          </dd>
        </div>
      </dl>

      <div className="relation-block">
        <h4>직접 선수과목</h4>
        <CourseChipList courses={relations?.prerequisites ?? []} />
      </div>
      <div className="relation-block">
        <h4>후속 과목</h4>
        <CourseChipList courses={relations?.dependents ?? []} />
      </div>
    </aside>
  );
}

function CourseChipList({ courses }) {
  if (!courses.length) {
    return <p className="relation-empty">없음</p>;
  }
  return (
    <div className="relation-chip-list">
      {courses.map((course) => (
        <span className="relation-chip" key={course.course_id}>
          <strong>{course.name}</strong>
          <small>{course.course_id}</small>
        </span>
      ))}
    </div>
  );
}

function RequirementsDashboard({ requirements }) {
  if (!requirements) {
    return null;
  }

  const missingCourses = requirements.missing_courses ?? [];
  const courseRequirements = requirements.summary.filter(
    (item) => item.type !== "non_course" && item.category !== "non_course",
  );
  const nonCourseRequirements = requirements.summary.filter(
    (item) => item.type === "non_course" || item.category === "non_course",
  );

  return (
    <section className="dashboard-section" aria-labelledby="requirements-title">
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">Requirement Status</p>
          <h2 id="requirements-title">졸업/교직 요건 요약</h2>
        </div>
        <div className="dashboard-overview">
          <span
            className={
              requirements.course_requirements_satisfied
                ? "status-pill satisfied"
                : "status-pill needed"
            }
          >
            전공/교직 {requirements.course_requirements_satisfied ? "충족" : "부족"}
          </span>
          <span
            className={
              requirements.non_course_requirements_satisfied
                ? "status-pill satisfied"
                : "status-pill needed"
            }
          >
            비교과 {requirements.non_course_requirements_satisfied ? "충족" : "부족"}
          </span>
        </div>
      </div>

      <RequirementCardGroup
        badgeLabel="과목"
        items={courseRequirements}
        title="과목 기반 요건"
      />
      <RequirementCardGroup
        badgeLabel="비교과"
        items={nonCourseRequirements}
        title="비교과 요건"
      />

      <div className="missing-panel">
        <div className="missing-title">
          <ClipboardList size={18} aria-hidden="true" />
          <h3>부족한 과목</h3>
        </div>
        {missingCourses.length === 0 ? (
          <p className="missing-empty">부족한 과목이 없습니다.</p>
        ) : (
          <div className="missing-course-list">
            {missingCourses.map((course) => (
              <span className="missing-course" key={course.course_id}>
                <strong>{course.name}</strong>
                <small>
                  {course.course_id} · {course.requirement_names.join(", ")}
                </small>
              </span>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function RequirementCardGroup({ badgeLabel, items, title }) {
  if (!items.length) {
    return null;
  }
  return (
    <div className="requirement-group">
      <div className="requirement-group-heading">
        <h3>{title}</h3>
      </div>
      <div className="requirement-grid">
        {items.map((item) => (
          <article
            className={`requirement-card ${item.satisfied ? "satisfied" : "needed"}`}
            key={item.requirement_id}
          >
            <div className="requirement-card-title">
              <div>
                <span>{requirementCategoryLabel(item.category)}</span>
                <h3>{item.name}</h3>
              </div>
              <div className="requirement-badges">
                <span className="requirement-kind-badge">{badgeLabel}</span>
                <strong>{item.status}</strong>
              </div>
            </div>
            <p className="requirement-count">
              {item.completed} / {item.required} {item.unit}
            </p>
            <div className="progress-track" aria-hidden="true">
              <span style={{ width: `${item.progress_percent}%` }} />
            </div>
            <p className="progress-copy">진행률 {item.progress_percent}%</p>
          </article>
        ))}
      </div>
    </div>
  );
}

function buildFlowNodes(
  courses,
  completedCourseIds,
  recommendedCourseIds,
  highlightedCourseIds,
  selectedCourseId,
) {
  const bucketCounts = new Map();
  return courses.map((course) => {
    const year = course.recommended_year ?? 5;
    const semester = course.recommended_semester ?? 0;
    const bucketKey = `${year}-${semester}`;
    const index = bucketCounts.get(bucketKey) ?? 0;
    bucketCounts.set(bucketKey, index + 1);
    const status = courseStatus(
      course.course_id,
      completedCourseIds,
      recommendedCourseIds,
    );

    return {
      id: course.course_id,
      type: "course",
      position: {
        x: Math.max(year - 1, 0) * 280,
        y: semesterBaseY(semester) + index * 92,
      },
      data: {
        course,
        status,
      },
      className: [
        "course-node",
        status,
        highlightedCourseIds.has(course.course_id) ? "connected" : "",
        selectedCourseId === course.course_id ? "selected" : "",
      ]
        .filter(Boolean)
        .join(" "),
    };
  });
}

function buildFlowEdges(edges, selectedCourseId) {
  return edges.map((edge) => {
    const highlighted =
      selectedCourseId &&
      (edge.source === selectedCourseId || edge.target === selectedCourseId);
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "smoothstep",
      label: edge.relation_type === "REQUIRED" ? "필수" : "권장",
      markerEnd: {
        type: MarkerType.ArrowClosed,
      },
      animated: Boolean(highlighted),
      className: highlighted ? "graph-edge highlighted" : "graph-edge",
      style: {
        stroke: highlighted ? "#1f6f64" : "#91a2ad",
        strokeWidth: highlighted ? 2.6 : 1.6,
      },
    };
  });
}

function courseStatus(courseId, completedCourseIds, recommendedCourseIds) {
  if (completedCourseIds.has(courseId)) {
    return "completed";
  }
  if (recommendedCourseIds.has(courseId)) {
    return "recommended";
  }
  return "normal";
}

function statusLabel(status) {
  if (status === "completed") {
    return "이수 완료";
  }
  if (status === "recommended") {
    return "추천 과목";
  }
  return "미이수";
}

function semesterBaseY(semester) {
  if (semester === 1) {
    return 0;
  }
  if (semester === 2) {
    return 260;
  }
  return 520;
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? `Request failed: ${response.status}`);
  }

  return response.json();
}

function sameSet(left, right) {
  if (left.size !== right.size) {
    return false;
  }
  for (const value of left) {
    if (!right.has(value)) {
      return false;
    }
  }
  return true;
}

function sameNonCourseDrafts(left, right) {
  const leftKeys = Object.keys(left).sort();
  const rightKeys = Object.keys(right).sort();
  if (leftKeys.length !== rightKeys.length) {
    return false;
  }
  return leftKeys.every(
    (key, index) =>
      key === rightKeys[index] &&
      JSON.stringify(normalizeNonCourseDraft(left[key])) ===
        JSON.stringify(normalizeNonCourseDraft(right[key])),
  );
}

function nonCourseItemsToDrafts(items) {
  return Object.fromEntries(
    items.map((item) => [item.key, nonCourseItemToDraft(item)]),
  );
}

function nonCourseItemToDraft(item) {
  if (!item) {
    return { completed: false, value: 0, note: "" };
  }
  return normalizeNonCourseDraft({
    completed: item.completed,
    value: item.value,
    note: item.note,
  });
}

function normalizeNonCourseDraft(draft) {
  return {
    completed: Boolean(draft?.completed),
    value: Math.max(Number(draft?.value) || 0, 0),
    note: draft?.note ?? "",
  };
}

function progressPercent(completed, required) {
  if (!required || required <= 0) {
    return 100;
  }
  return Math.min(Math.round((completed / required) * 100), 100);
}

function formatList(values) {
  return values?.length ? values.join(", ") : "없음";
}

function requirementCategoryLabel(category) {
  if (category === "major") {
    return "전공";
  }
  if (category === "teaching") {
    return "교직";
  }
  return "비교과";
}

function formatTiming(year, semester) {
  if (year && semester) {
    return `${year}학년 / ${semester}학기`;
  }
  if (year) {
    return `${year}학년`;
  }
  if (semester) {
    return `${semester}학기`;
  }
  return "-";
}

export default App;
