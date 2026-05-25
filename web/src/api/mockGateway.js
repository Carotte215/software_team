import { APPROVAL, FLOW_STAGES, ROLES } from "../data/seed.js";
import { maskPhone, rank, uid } from "../utils.js";
import { readDb, readMeta, resetDb, withDb } from "./store.js";

const WINDOW_MS = 48 * 3600000;

export async function mockRequest({ path, method = "GET", data = {}, session }) {
  const verb = method.toUpperCase();
  const parts = path.replace(/^\//, "").split("/").filter(Boolean);
  await new Promise((resolve) => setTimeout(resolve, 60));

  if (parts[0] === "auth" && parts[1] === "login" && verb === "POST") return login(data);
  if (parts[0] === "runtime") return { ok: true, appName: "学院学生综合服务与党团管理平台", env: "mock", authMode: "mock", tokenHours: 12 };
  if (parts[0] === "session") return { studentId: session.studentId, role: session.role, authMode: "mock", hasToken: Boolean(session.token) };

  if (parts[0] === "student" && parts[1] === "me") return getMe(session);
  if (parts[0] === "students" && parts[1] === "import" && verb === "POST") return importStudents(data, session);
  if (parts[0] === "students" && parts[1] === "field-policy") return studentFieldPolicy(session);
  if (parts[0] === "students" && parts[1] && verb === "PATCH") return updateStudent(parts[1], data, session);
  if (parts[0] === "students") return { list: readDb().students.map((s) => publicStudent(s, ROLES.TEACHER)) };

  if (parts[0] === "knowledge" && parts.length === 1 && verb === "GET") return knowledgeList(data);
  if (parts[0] === "knowledge" && parts.length === 1 && verb === "POST") return createKnowledge(data, session);
  if (parts[0] === "knowledge" && parts[1] === "admin" && parts[2] === "list") return knowledgeAdminList(session);
  if (parts[0] === "knowledge" && parts[1] === "miss" && verb === "POST") return recordMiss(data.keyword, session);
  if (parts[0] === "knowledge" && parts[2] === "online" && verb === "POST") return setKnowledgeOnline(parts[1], data, session);
  if (parts[0] === "knowledge" && parts[1] && verb === "PUT") return updateKnowledge(parts[1], data, session);
  if (parts[0] === "knowledge" && parts[1]) return knowledgeDetail(parts[1], session);

  if (parts[0] === "files" && parts[1] === "upload" && verb === "POST") return uploadFileMeta(data, session);

  if (parts[0] === "party" && parts[1] === "progress") return partyProgress(session.studentId);
  if (parts[0] === "party" && parts[1] === "tasks" && parts[3] === "done" && verb === "POST") return completePartyTask(session.studentId, parts[2]);
  if (parts[0] === "theory" && parts[1] === "questions" && verb === "GET") return theoryQuestions(session);
  if (parts[0] === "theory" && parts[1] === "attempt" && verb === "POST") return submitTheoryAttempt(data, session);
  if (parts[0] === "theory" && parts[1] === "workbench" && parts[2] === "questions" && parts.length === 3 && verb === "GET") return theoryQuestionAdmin(session);
  if (parts[0] === "theory" && parts[1] === "workbench" && parts[2] === "questions" && parts.length === 3 && verb === "PUT") return saveTheoryQuestions(data, session);
  if (parts[0] === "theory" && parts[1] === "workbench" && parts[2] === "questions" && parts[3] === "import") return importTheoryQuestions(data, session);

  if (parts[0] === "notices" && parts.length === 1) return { list: readDb().notices.filter((item) => item.publishedAt <= Date.now()).slice().sort((a, b) => b.publishedAt - a.publishedAt) };
  if (parts[0] === "notices" && parts[1]) return readDb().notices.find((n) => n.id === parts[1]);
  if (parts[0] === "messages" && parts[1] === "inbox") return inbox(session.studentId);
  if (parts[0] === "messages" && parts[2] === "read" && verb === "POST") return markRead(session.studentId, parts[1]);

  if (parts[0] === "applications" && parts.length === 1 && verb === "GET") return applicationsList(data, session);
  if (parts[0] === "applications" && parts.length === 1 && verb === "POST") return createApplication(data, session);
  if (parts[0] === "applications" && parts[1] === "draft" && verb === "GET") return readDb().applicationDraftsByStudent?.[session.studentId] || null;
  if (parts[0] === "applications" && parts[1] === "draft" && verb === "POST") return saveDraft(data, session);
  if (parts[0] === "applications" && parts[2] === "submit" && verb === "POST") return submitExistingApplication(parts[1], data, session);
  if (parts[0] === "applications" && parts[1]) return applicationDetail(parts[1], session);

  if (parts[0] === "honors" && parts.length === 1 && verb === "GET") return honors(data, session);
  if (parts[0] === "honors" && parts.length === 1 && verb === "POST") return createHonor(data, session);
  if (parts[0] === "honors" && parts[1] && verb === "PUT") return updateHonor(parts[1], data, session);
  if (parts[0] === "academic" && parts[1] === "workbench" && parts[2] === "plans" && parts.length === 3 && verb === "GET") return listAcademicPlans(session);
  if (parts[0] === "academic" && parts[1] === "workbench" && parts[2] === "plans" && parts.length === 3 && verb === "PUT") return saveAcademicPlan(data, session);
  if (parts[0] === "academic" && parts[1] === "workbench" && parts[2] === "plans" && parts[3] === "import") return importAcademicPlans(data, session);
  if (parts[0] === "academic" && parts[1] === "report") return academicReport(session.studentId);
  if (parts[0] === "academic" && parts[1] === "plan") return academicPlan(session.studentId);
  if (parts[0] === "academic" && parts[1] === "progress" && verb === "PUT") return saveAcademicProgress(data, session);
  if (parts[0] === "academic" && parts[1] === "transcript" && verb === "POST") return saveTranscript(data, session);

  if (parts[0] === "workbench" && parts[1] === "summary") return workbenchSummary(session);
  if (parts[0] === "workbench" && parts[1] === "knowledge" && parts[2] === "misses") return { list: readDb().missKeywords.sort((a, b) => b.count - a.count) };
  if (parts[0] === "workbench" && parts[1] === "academic" && parts[2] === "risks") return academicRisks(session);
  if (parts[0] === "workbench" && parts[1] === "notices" && parts[2] === "publish" && verb === "POST") return publishNotice(data, session);
  if (parts[0] === "workbench" && parts[1] === "notices" && parts[2] === "scheduled" && parts[3] === "dispatch") return dispatchScheduledNotices(session);
  if (parts[0] === "workbench" && parts[1] === "batches") return { list: batchesWithReadStats(data) };
  if (parts[0] === "workbench" && parts[1] === "sms") return { list: readDb().smsSimulation };
  if (parts[0] === "workbench" && parts[1] === "party" && parts[2] === "advance" && verb === "POST") return advanceParty(data, session);
  if (parts[0] === "workbench" && parts[1] === "party" && parts[2] === "timeline" && verb === "GET") return partyTimeline(session);
  if (parts[0] === "workbench" && parts[1] === "party" && parts[2] === "timeline" && verb === "PUT") return updatePartyTimeline(data, session);
  if (parts[0] === "workbench" && parts[1] === "party" && parts[2] === "reminders" && parts[3] === "refresh") return refreshPartyReminders(session);
  if (parts[0] === "workbench" && parts[1] === "applications" && parts[2]) return decideApplication(parts[2], parts[3], data, session);

  if (parts[0] === "leader" && parts[1] === "dashboard") return leaderDashboard(session);
  if (parts[0] === "audit" && parts[1] === "logs") return { list: readDb().auditLogs.slice(0, data.limit || 200) };
  if (parts[0] === "danger" && parts[1] === "reset-db" && verb === "POST") return resetDb();

  throw new Error(`ROUTE_NOT_FOUND:${path}`);
}

function login(data) {
  const db = readDb();
  const student = db.students.find((s) => s.studentId === data.studentId);
  if (!student) throw new Error("UNKNOWN_IDENTITY");
  if (data.password && data.password !== "demo123456") throw new Error("INVALID_CREDENTIAL");
  return {
    token: `mock-token-${student.studentId}-${Date.now()}`,
    studentId: student.studentId,
    role: data.role || ROLES.STUDENT,
    student: publicStudent(student, data.role || ROLES.STUDENT),
    expiresInHours: 12,
  };
}

function getMe(session) {
  const db = readDb();
  const student = db.students.find((s) => s.studentId === session.studentId);
  return student ? publicStudent(student, session.role) : null;
}

function publicStudent(s, role) {
  const base = {
    studentId: s.studentId,
    name: s.name,
    grade: s.grade,
    major: s.major,
    className: s.className,
    nation: s.nation,
    politicalStatus: s.politicalStatus,
    tutor: s.tutor,
    extension: s.extension,
  };
  if (role === ROLES.TEACHER) return { ...base, phone: s.phone, phoneMasked: maskPhone(s.phone), hometown: s.hometown, idCardMasked: "**************" };
  if (role === ROLES.LEADER) return { ...base, phoneMasked: maskPhone(s.phone), hometown: s.hometown?.slice(0, 1) + "**" };
  return { ...base, phoneMasked: maskPhone(s.phone) };
}

function studentFieldPolicy(session) {
  const policy = {
    teacher: {
      visible: ["studentId", "name", "grade", "major", "className", "nation", "phone", "politicalStatus", "tutor", "hometown", "extension"],
      editable: ["name", "grade", "major", "className", "nation", "phone", "politicalStatus", "tutor", "hometown", "extension"],
      exportable: ["studentId", "name", "grade", "major", "className", "nation", "phoneMasked", "politicalStatus", "tutor"],
    },
    coordinator: {
      visible: ["studentId", "name", "grade", "major", "className", "nation", "politicalStatus", "extension"],
      editable: ["politicalStatus", "extension"],
      exportable: [],
    },
    leader: { visible: ["studentId", "name", "grade", "major", "className", "nation", "phoneMasked", "politicalStatus", "tutor", "hometown", "extension"], editable: [], exportable: [] },
  }[session.role];
  if (!policy) throw new Error("FORBIDDEN");
  return { role: session.role, ...policy };
}

function updateStudent(studentId, data, session) {
  const policy = studentFieldPolicy(session);
  const rejected = Object.keys(data || {}).filter((field) => !policy.editable.includes(field));
  if (rejected.length) throw new Error(`FIELD_NOT_EDITABLE:${rejected.join(",")}`);
  let row;
  withDb((db) => {
    row = db.students.find((student) => student.studentId === studentId);
    if (!row) throw new Error("NOT_FOUND");
    if (session.role === ROLES.COORDINATOR) {
      const current = db.students.find((student) => student.studentId === session.studentId);
      if (!current || current.className !== row.className) throw new Error("FORBIDDEN");
    }
    Object.assign(row, data);
    appendAudit(db, session, "student_update", studentId);
  });
  return publicStudent(row, session.role);
}

async function importStudents(data, session) {
  requireTeacher(session);
  const file = typeof FormData !== "undefined" && data instanceof FormData ? data.get("file") : null;
  const dryRun = data.get("dryRun") !== "false";
  const overwrite = data.get("overwrite") === "true";
  const rows = parseStudentCsv(file ? await file.text() : "");
  const errors = [];
  const seen = new Set();
  const validRows = [];
  const db = readDb();
  rows.forEach((row) => {
    const missing = ["studentId", "name", "grade", "major", "className"].filter((key) => !row.data[key]);
    if (missing.length) {
      errors.push({ row: row.row, field: missing.join(","), message: "必填字段缺失" });
      return;
    }
    if (seen.has(row.data.studentId)) {
      errors.push({ row: row.row, field: "studentId", message: "导入文件内学号重复" });
      return;
    }
    seen.add(row.data.studentId);
    if (db.students.some((item) => item.studentId === row.data.studentId) && !overwrite) {
      errors.push({ row: row.row, field: "studentId", message: "学号已存在，需勾选覆盖更新" });
      return;
    }
    validRows.push(row.data);
  });
  const existing = new Set(db.students.map((item) => item.studentId));
  const result = {
    ok: !errors.length,
    dryRun: true,
    total: rows.length,
    created: validRows.filter((item) => !existing.has(item.studentId)).length,
    updated: validRows.filter((item) => existing.has(item.studentId)).length,
    errors,
    preview: validRows.slice(0, 5),
  };
  if (dryRun || errors.length) return result;
  withDb((draft) => {
    validRows.forEach((item) => {
      const found = draft.students.find((student) => student.studentId === item.studentId);
      if (found) Object.assign(found, item);
      else draft.students.push({ ...item, extension: {} });
    });
    appendAudit(draft, session, "students_import", file?.name || "students.csv");
  });
  return { ...result, ok: true, dryRun: false, errors: [] };
}

function parseStudentCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const headers = lines[0].split(",").map((item) => item.trim());
  const aliases = {
    studentId: ["studentId", "student_id", "学号"],
    name: ["name", "姓名"],
    grade: ["grade", "年级"],
    major: ["major", "专业"],
    className: ["className", "class_name", "班级"],
    nation: ["nation", "民族"],
    phone: ["phone", "手机号", "联系方式"],
    politicalStatus: ["politicalStatus", "political_status", "政治面貌"],
    tutor: ["tutor", "导师"],
    hometown: ["hometown", "生源地", "户籍地"],
  };
  return lines.slice(1).map((line, index) => {
    const values = line.split(",").map((item) => item.trim());
    const raw = Object.fromEntries(headers.map((header, i) => [header, values[i] || ""]));
    const normalized = {};
    Object.entries(aliases).forEach(([target, names]) => {
      normalized[target] = names.map((name) => raw[name]).find(Boolean) || "";
    });
    return { row: index + 2, data: normalized };
  });
}

function knowledgeList({ q, category }) {
  const db = readDb();
  const categories = ["全部", ...new Set(db.knowledge.map((k) => k.category))];
  let list = db.knowledge.filter((k) => k.online !== false);
  if (category && category !== "全部") list = list.filter((k) => k.category === category);
  list = q ? rank(q, list, (k) => [k.title, k.category, k.summary, k.body, (k.tags || []).join(",")]) : list;
  return { list, categories, templates: db.templates };
}

function requireTeacher(session) {
  if (session.role !== ROLES.TEACHER) throw new Error("FORBIDDEN");
}

function knowledgePayload(data) {
  return {
    title: data.title,
    category: data.category || "未分类",
    tags: data.tags || [],
    summary: data.summary || "",
    body: data.body || "",
    sensitiveHint: Boolean(data.sensitiveHint),
    attachments: data.attachments || [],
    online: data.online !== false,
  };
}

function knowledgeAdminList(session) {
  if (![ROLES.TEACHER, ROLES.LEADER].includes(session.role)) throw new Error("FORBIDDEN");
  return { list: readDb().knowledge.slice().sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)) };
}

function createKnowledge(data, session) {
  requireTeacher(session);
  let row;
  withDb((db) => {
    row = {
      id: uid("k"),
      ...knowledgePayload(data),
      attachments: data.attachments || [],
      hitCount: 0,
      updatedAt: Date.now(),
    };
    db.knowledge.unshift(row);
    appendAudit(db, session, "knowledge_create", row.id);
  });
  return row;
}

function updateKnowledge(id, data, session) {
  requireTeacher(session);
  let row;
  withDb((db) => {
    row = db.knowledge.find((item) => item.id === id);
    if (!row) throw new Error("NOT_FOUND");
    Object.assign(row, knowledgePayload(data), { updatedAt: Date.now() });
    appendAudit(db, session, "knowledge_update", id);
  });
  return row;
}

function setKnowledgeOnline(id, data, session) {
  requireTeacher(session);
  let row;
  withDb((db) => {
    row = db.knowledge.find((item) => item.id === id);
    if (!row) throw new Error("NOT_FOUND");
    row.online = data.online;
    row.updatedAt = Date.now();
    appendAudit(db, session, data.online ? "knowledge_online" : "knowledge_offline", id);
  });
  return row;
}

function recordMiss(keyword, session) {
  const k = (keyword || "").trim();
  if (!k) return { ok: false };
  withDb((db) => {
    const found = db.missKeywords.find((x) => x.keyword === k);
    if (found) {
      found.count += 1;
      found.lastAt = Date.now();
    } else {
      db.missKeywords.unshift({ id: uid("miss"), keyword: k, count: 1, lastAt: Date.now() });
    }
    appendAudit(db, session, "knowledge_miss", k);
  });
  return { ok: true };
}

function knowledgeDetail(id, session) {
  let item;
  withDb((db) => {
    item = db.knowledge.find((k) => k.id === id);
    if (item) item.hitCount = (item.hitCount || 0) + 1;
    appendAudit(db, session, "knowledge_read", id);
  });
  return item;
}

function uploadFileMeta(data, session) {
  const file = typeof FormData !== "undefined" && data instanceof FormData ? data.get("file") : null;
  const business = typeof FormData !== "undefined" && data instanceof FormData ? data.get("business") : "general";
  const meta = {
    id: uid("file"),
    name: file?.name || "uploaded-file",
    size: file?.size || 0,
    contentType: file?.type || "application/octet-stream",
    business,
    url: "",
    uploadedAt: Date.now(),
  };
  withDb((db) => appendAudit(db, session, "file_upload", meta.id));
  return meta;
}

function partyProgress(studentId) {
  const db = readDb();
  return { flowName: "入党流程", stages: FLOW_STAGES, timelineRules: getPartyRules(db), ...db.partyByStudent[studentId] };
}

function completePartyTask(studentId, taskId) {
  withDb((db) => {
    const progress = db.partyByStudent[studentId];
    const task = progress?.tasks.find((t) => t.id === taskId);
    if (task) task.done = true;
  });
  return { ok: true };
}

function defaultTheoryQuestions() {
  return [
    { id: "theory_q1", stem: "入党申请人递交申请书后，通常应接受党组织的谈话和培养教育。", type: "single", options: ["正确", "错误"], answer: "正确", explanation: "入党申请提交后，党组织会安排谈话并开展培养教育。", category: "入党流程", online: true },
    { id: "theory_q2", stem: "发展对象阶段通常需要完成政审、公示和集中培训等材料或环节。", type: "single", options: ["正确", "错误"], answer: "正确", explanation: "发展对象阶段需按组织要求完成相关审查和培训材料。", category: "发展对象", online: true },
  ];
}

function theoryBank(db = readDb()) {
  db.theory = db.theory || { questions: defaultTheoryQuestions(), attempts: [] };
  db.theory.questions = db.theory.questions?.length ? db.theory.questions : defaultTheoryQuestions();
  db.theory.attempts = db.theory.attempts || [];
  return db.theory;
}

function publicTheoryQuestion(item) {
  const { answer, ...rest } = item;
  return rest;
}

function theoryQuestions(session) {
  const bank = theoryBank();
  const attempts = bank.attempts.filter((item) => item.studentId === session.studentId);
  return { list: bank.questions.filter((item) => item.online !== false).map(publicTheoryQuestion), latestAttempt: attempts[0] || null };
}

function submitTheoryAttempt(data, session) {
  let result;
  withDb((db) => {
    const bank = theoryBank(db);
    const questions = bank.questions.filter((item) => item.online !== false);
    let correct = 0;
    const details = questions.map((question) => {
      const answer = data.answers?.[question.id] || "";
      const ok = answer === question.answer;
      if (ok) correct += 1;
      return { id: question.id, stem: question.stem, answer, correctAnswer: question.answer, correct: ok, explanation: question.explanation };
    });
    result = { id: uid("attempt"), studentId: session.studentId, at: Date.now(), total: questions.length, correct, score: questions.length ? Math.round((correct * 1000) / questions.length) / 10 : 0, details };
    bank.attempts.unshift(result);
    appendAudit(db, session, "theory_attempt", result.id);
  });
  return result;
}

function theoryQuestionAdmin(session) {
  if (![ROLES.TEACHER, ROLES.LEADER].includes(session.role)) throw new Error("FORBIDDEN");
  return { list: theoryBank().questions };
}

function saveTheoryQuestions(data, session) {
  requireTeacher(session);
  const questions = (data.questions || []).map(normalizeTheoryQuestion);
  withDb((db) => {
    theoryBank(db).questions = questions;
    appendAudit(db, session, "theory_questions_save", "theory");
  });
  return { ok: true, list: questions };
}

async function importTheoryQuestions(data, session) {
  requireTeacher(session);
  const file = typeof FormData !== "undefined" && data instanceof FormData ? data.get("file") : null;
  const dryRun = data.get("dryRun") !== "false";
  const rows = parseTheoryCsv(file ? await file.text() : "");
  const errors = validateTheoryRows(rows);
  const questions = errors.length ? [] : rows.map(normalizeTheoryQuestion);
  if (dryRun || errors.length) return { ok: !errors.length, dryRun: true, total: rows.length, questions, errors };
  withDb((db) => {
    theoryBank(db).questions = questions;
    appendAudit(db, session, "theory_questions_import", file?.name || "theory.csv");
  });
  return { ok: true, dryRun: false, total: rows.length, questions, errors: [] };
}

function normalizeTheoryQuestion(row) {
  const options = Array.isArray(row.options) ? row.options : String(row.options || "").replace("；", ";").split(";").map((item) => item.trim()).filter(Boolean);
  return { id: row.id || uid("theory"), stem: row.stem || "", type: row.type || "single", options, answer: row.answer || "", explanation: row.explanation || "", category: row.category || "理论知识", online: row.online !== false };
}

function parseTheoryCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const headers = lines[0].split(",").map((item) => item.trim());
  return lines.slice(1).map((line, index) => {
    const values = line.split(",").map((item) => item.trim());
    const raw = Object.fromEntries(headers.map((header, i) => [header, values[i] || ""]));
    return { row: index + 2, stem: raw["题干"] || raw.stem || "", options: raw["选项"] || raw.options || "", answer: raw["答案"] || raw.answer || "", explanation: raw["解析"] || raw.explanation || "", category: raw["分类"] || raw.category || "理论知识", online: !["false", "0", "否"].includes(raw["上线"] || raw.online || "true") };
  });
}

function validateTheoryRows(rows) {
  const errors = [];
  rows.forEach((row) => {
    const options = String(row.options || "").replace("；", ";").split(";").map((item) => item.trim()).filter(Boolean);
    if (!row.stem || !row.answer) errors.push({ row: row.row, field: "stem,answer", message: "题干和答案必填" });
    else if (options.length < 2) errors.push({ row: row.row, field: "options", message: "至少需要 2 个选项，使用分号分隔" });
    else if (!options.includes(row.answer)) errors.push({ row: row.row, field: "answer", message: "答案必须包含在选项中" });
  });
  return errors;
}

function getPartyRules(db = readDb()) {
  return db.partyTimelineRules || [
    { stageKey: "applicant", durationDays: 30, remindBeforeDays: 7, material: "入党申请书、谈话记录" },
    { stageKey: "activist", durationDays: 365, remindBeforeDays: 30, material: "培养考察登记表、思想汇报" },
    { stageKey: "candidate", durationDays: 90, remindBeforeDays: 14, material: "政审材料、公示记录、培训结业材料" },
    { stageKey: "probationary", durationDays: 365, remindBeforeDays: 30, material: "预备党员考察表、转正申请" },
    { stageKey: "member", durationDays: 0, remindBeforeDays: 0, material: "归档材料" },
  ];
}

function partyTimeline(session) {
  if (![ROLES.TEACHER, ROLES.LEADER].includes(session.role)) throw new Error("FORBIDDEN");
  return { stages: FLOW_STAGES, rules: getPartyRules() };
}

function updatePartyTimeline(data, session) {
  requireTeacher(session);
  let rules;
  withDb((db) => {
    rules = getPartyRules(db).map((rule) => {
      const next = (data.rules || []).find((item) => item.stageKey === rule.stageKey) || {};
      return {
        stageKey: rule.stageKey,
        durationDays: Math.max(0, Number(next.durationDays ?? rule.durationDays) || 0),
        remindBeforeDays: Math.max(0, Number(next.remindBeforeDays ?? rule.remindBeforeDays) || 0),
        material: next.material ?? rule.material,
      };
    });
    db.partyTimelineRules = rules;
    appendAudit(db, session, "party_timeline_update", "party_timeline");
  });
  return { ok: true, rules };
}

function refreshPartyReminders(session) {
  requireTeacher(session);
  let changed = 0;
  let total = 0;
  withDb((db) => {
    const rules = getPartyRules(db);
    Object.values(db.partyByStudent).forEach((progress) => {
      total += 1;
      const rule = rules.find((item) => item.stageKey === progress.currentKey);
      if (!rule || rule.durationDays <= 0) return;
      const taskId = `timeline_${progress.studentId}_${progress.currentKey}`;
      const existing = progress.tasks.find((task) => task.id === taskId);
      const stage = FLOW_STAGES.find((item) => item.key === progress.currentKey);
      const startAt = Math.max(...progress.history.filter((item) => item.stageKey === progress.currentKey).map((item) => item.at), Date.now());
      const task = {
        id: taskId,
        title: `${stage?.name || progress.currentKey}阶段材料提醒`,
        body: `标准时间线约 ${rule.durationDays} 天，请准备：${rule.material}`,
        dueAt: startAt + rule.durationDays * 86400000,
        remindAt: startAt + Math.max(0, rule.durationDays - rule.remindBeforeDays) * 86400000,
        done: Boolean(existing?.done),
        source: "timeline",
      };
      if (existing) Object.assign(existing, task);
      else progress.tasks.unshift(task);
      changed += 1;
    });
    appendAudit(db, session, "party_reminders_refresh", "party_progress");
  });
  return { ok: true, students: total, changed };
}

function inbox(studentId) {
  const list = readDb().inboxByStudent[studentId] || [];
  return { list: list.slice().sort((a, b) => b.createdAt - a.createdAt), unread: list.filter((m) => !m.readAt).length };
}

function markRead(studentId, id) {
  withDb((db) => {
    const msg = (db.inboxByStudent[studentId] || []).find((m) => m.id === id);
    if (msg && !msg.readAt) msg.readAt = Date.now();
  });
  return { ok: true };
}

function batchesWithReadStats(query = {}) {
  const db = readDb();
  const messages = Object.values(db.inboxByStudent || {}).flat();
  let list = db.batches.map((batch) => {
    const read = messages.filter((item) => item.batchId === batch.id && item.readAt).length;
    return {
      ...batch,
      channels: (batch.channels || []).map((channel) => (channel.name === "站内" ? { ...channel, read } : channel)),
    };
  });
  if (query.title) list = list.filter((item) => item.title.includes(query.title));
  if (query.batchId) list = list.filter((item) => item.id.includes(query.batchId));
  if (query.status) list = list.filter((item) => item.status === query.status);
  if (query.fromMs) list = list.filter((item) => item.createdAt >= Number(query.fromMs));
  if (query.toMs) list = list.filter((item) => item.createdAt <= Number(query.toMs));
  return list;
}

function applicationsList(data, session) {
  const db = readDb();
  let list = data.scope === "workbench" && [ROLES.TEACHER, ROLES.LEADER, ROLES.COORDINATOR].includes(session.role)
    ? db.applications.slice()
    : db.applications.filter((a) => a.studentId === session.studentId);
  if (data.scope === "workbench" && session.role === ROLES.COORDINATOR) {
    const me = db.students.find((s) => s.studentId === session.studentId);
    const classIds = db.students.filter((s) => s.className === me?.className).map((s) => s.studentId);
    list = list.filter((a) => classIds.includes(a.studentId));
  }
  const draft = db.applicationDraftsByStudent?.[session.studentId];
  if (draft && data.scope !== "workbench") list = [draft, ...list];
  if (data.status) list = list.filter((a) => a.status === data.status);
  return { list: list.sort((a, b) => b.createdAt - a.createdAt) };
}

function createApplication(data, session) {
  const created = {
    id: uid("app"),
    studentId: session.studentId,
    type: data.type,
    subtype: data.subtype,
    status: APPROVAL.PENDING,
    createdAt: Date.now(),
    form: data.form || {},
    attachments: data.attachments || [],
    teacherComment: "",
    decidedAt: null,
    auditTrail: [
      { at: Date.now(), actor: "学生", action: "提交", remark: data.remark || "" },
      { at: Date.now() + 500, actor: "系统", action: "进入审批队列", remark: "" },
    ],
  };
  withDb((db) => {
    db.applications.unshift(created);
    db.applicationDraftsByStudent = db.applicationDraftsByStudent || {};
    delete db.applicationDraftsByStudent[session.studentId];
    appendAudit(db, session, "application_create", created.id);
  });
  return created;
}

function saveDraft(data, session) {
  let draft;
  withDb((db) => {
    db.applicationDraftsByStudent = db.applicationDraftsByStudent || {};
    const previous = db.applicationDraftsByStudent[session.studentId] || {};
    draft = {
      id: previous.id || uid("draft"),
      studentId: session.studentId,
      type: data.type,
      subtype: data.subtype,
      status: APPROVAL.DRAFT,
      createdAt: previous.createdAt || Date.now(),
      updatedAt: Date.now(),
      form: data.form || {},
      attachments: data.attachments || [],
      teacherComment: "",
      decidedAt: null,
      auditTrail: [
        ...(previous.auditTrail || []),
        { at: Date.now(), actor: "学生", action: "保存草稿", remark: data.remark || "" },
      ],
    };
    db.applicationDraftsByStudent[session.studentId] = draft;
    appendAudit(db, session, "application_draft_save", session.studentId);
  });
  return draft;
}

function submitExistingApplication(id, data, session) {
  let result;
  withDb((db) => {
    const draft = db.applicationDraftsByStudent?.[session.studentId];
    let app = db.applications.find((a) => a.id === id);
    if (!app && draft?.id === id) {
      app = { ...draft };
      db.applications.unshift(app);
      delete db.applicationDraftsByStudent[session.studentId];
    }
    if (!app || app.studentId !== session.studentId) throw new Error("NOT_FOUND");
    if (![APPROVAL.DRAFT, APPROVAL.REJECTED].includes(app.status)) throw new Error("INVALID_STATE");
    if (data.type === "盖章申请" && !(data.attachments || []).length) throw new Error("SEAL_ATTACHMENT_REQUIRED");
    const wasRejected = app.status === APPROVAL.REJECTED;
    Object.assign(app, {
      type: data.type,
      subtype: data.subtype,
      status: APPROVAL.PENDING,
      form: data.form || {},
      attachments: data.attachments || [],
      teacherComment: "",
      decidedAt: null,
      auditTrail: [
        ...(app.auditTrail || []),
        { at: Date.now(), actor: "学生", action: wasRejected ? "重提" : "已提交", remark: data.remark || "" },
        { at: Date.now() + 500, actor: "系统", action: "进入审批队列", remark: "" },
      ],
    });
    appendAudit(db, session, wasRejected ? "application_resubmit" : "application_submit", id);
    result = app;
  });
  return result;
}

function applicationDetail(id, session) {
  const app = readDb().applications.find((a) => a.id === id);
  if (!app) throw new Error("NOT_FOUND");
  if (app.studentId !== session.studentId && ![ROLES.TEACHER, ROLES.LEADER, ROLES.COORDINATOR].includes(session.role)) throw new Error("FORBIDDEN");
  return app;
}

function honors(data, session) {
  let list = readDb().honors.slice();
  if (data.year) list = list.filter((h) => String(h.year) === String(data.year));
  if (data.category) list = list.filter((h) => h.category === data.category);
  if (data.major) list = list.filter((h) => h.major.includes(data.major));
  return { list: list.map((item) => filterHonorAttachments(item, session.role)) };
}

function honorPayload(data) {
  return {
    title: data.title,
    winner: data.winner,
    year: Number(data.year),
    major: data.major || "",
    grade: data.grade || "",
    category: data.category || "",
    intro: data.intro || "",
    visibility: data.visibility || "public",
    attachments: (data.attachments || []).map((item) => ({ ...item, visibility: item.visibility || data.visibility || "public" })),
  };
}

function filterHonorAttachments(item, role) {
  if ([ROLES.TEACHER, ROLES.LEADER].includes(role)) return item;
  return { ...item, attachments: (item.attachments || []).filter((file) => file.visibility !== "restricted") };
}

function createHonor(data, session) {
  requireTeacher(session);
  let row;
  withDb((db) => {
    row = { id: uid("honor"), ...honorPayload(data) };
    db.honors.unshift(row);
    appendAudit(db, session, "honor_create", row.id);
  });
  return row;
}

function updateHonor(id, data, session) {
  requireTeacher(session);
  let row;
  withDb((db) => {
    row = db.honors.find((item) => item.id === id);
    if (!row) throw new Error("NOT_FOUND");
    Object.assign(row, honorPayload(data));
    appendAudit(db, session, "honor_update", id);
  });
  return row;
}

function academicPlan(studentId) {
  const db = readDb();
  const s = db.students.find((x) => x.studentId === studentId);
  const key = `${s.grade}|${s.major}`;
  return { plan: db.academic.plansByKey[key], progress: db.academic.progressByStudent[studentId] };
}

function listAcademicPlans(session) {
  if (![ROLES.TEACHER, ROLES.LEADER].includes(session.role)) throw new Error("FORBIDDEN");
  return { list: Object.entries(readDb().academic.plansByKey).map(([key, plan]) => ({ key, ...plan })) };
}

function saveAcademicPlan(data, session) {
  requireTeacher(session);
  const key = `${data.grade}|${data.major}`;
  const plan = {
    key,
    grade: data.grade,
    major: data.major,
    modules: (data.modules || []).map((item) => ({ key: item.key, name: item.name, required: Number(item.required || 0) })),
  };
  withDb((db) => {
    db.academic.plansByKey[key] = plan;
    appendAudit(db, session, "academic_plan_save", key);
  });
  return plan;
}

async function importAcademicPlans(data, session) {
  requireTeacher(session);
  const file = typeof FormData !== "undefined" && data instanceof FormData ? data.get("file") : null;
  const dryRun = data.get("dryRun") !== "false";
  const rows = parseAcademicPlanCsv(file ? await file.text() : "");
  const errors = validateAcademicPlanRows(rows);
  const plans = errors.length ? [] : groupAcademicPlanRows(rows);
  if (dryRun || errors.length) return { ok: !errors.length, dryRun: true, total: rows.length, plans, errors };
  withDb((db) => {
    plans.forEach((plan) => {
      db.academic.plansByKey[`${plan.grade}|${plan.major}`] = { key: `${plan.grade}|${plan.major}`, ...plan };
    });
    appendAudit(db, session, "academic_plan_import", file?.name || "academic_plans.csv");
  });
  return { ok: true, dryRun: false, total: rows.length, plans, errors: [] };
}

function parseAcademicPlanCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const headers = lines[0].split(",").map((item) => item.trim());
  return lines.slice(1).map((line, index) => {
    const values = line.split(",").map((item) => item.trim());
    const raw = Object.fromEntries(headers.map((header, i) => [header, values[i] || ""]));
    return {
      row: index + 2,
      grade: raw["年级"] || raw.grade || "",
      major: raw["专业"] || raw.major || "",
      key: raw["模块key"] || raw.key || "",
      name: raw["模块名称"] || raw.name || "",
      required: raw["要求学分"] || raw.required || "",
    };
  });
}

function validateAcademicPlanRows(rows) {
  const errors = [];
  const seen = new Set();
  rows.forEach((row) => {
    const missing = ["grade", "major", "key", "name", "required"].filter((field) => !row[field]);
    if (missing.length) {
      errors.push({ row: row.row, field: missing.join(","), message: "必填字段缺失" });
      return;
    }
    if (Number.isNaN(Number(row.required))) {
      errors.push({ row: row.row, field: "required", message: "要求学分必须是数字" });
      return;
    }
    const dedup = `${row.grade}|${row.major}|${row.key}`;
    if (seen.has(dedup)) errors.push({ row: row.row, field: "key", message: "同一培养方案内模块 key 重复" });
    seen.add(dedup);
  });
  return errors;
}

function groupAcademicPlanRows(rows) {
  const grouped = {};
  rows.forEach((row) => {
    const id = `${row.grade}|${row.major}`;
    grouped[id] = grouped[id] || { grade: row.grade, major: row.major, modules: [] };
    grouped[id].modules.push({ key: row.key, name: row.name, required: Number(row.required) });
  });
  return Object.values(grouped);
}

function academicReport(studentId) {
  const { plan, progress } = academicPlan(studentId);
  if (!plan || !progress) return { ok: false, message: "缺少培养方案或学业进度。" };
  const modules = plan.modules.map((m) => {
    const got = progress.modules.find((x) => x.key === m.key);
    const earned = Number(got?.earned || 0);
    const gap = Math.max(0, m.required - earned);
    return { ...m, earned, gap, risk: gap >= 4 ? "高" : gap >= 2 ? "中" : "低" };
  });
  return {
    ok: true,
    modules,
    riskLevel: modules.some((m) => m.risk === "高") ? "高" : modules.some((m) => m.risk === "中") ? "中" : "低",
    suggestions: modules.filter((m) => m.gap > 0).map((m) => ({ focus: m.name, hint: `仍需约 ${m.gap} 学分，请关注 ${m.name} 相关课程。` })),
    uploads: progress.uploads || [],
  };
}

function academicRisks(session) {
  if (![ROLES.TEACHER, ROLES.LEADER].includes(session.role)) throw new Error("FORBIDDEN");
  const rows = readDb().students.map((student) => {
    const report = academicReport(student.studentId);
    if (!report.ok) {
      return { ...student, riskLevel: "数据缺失", totalGap: 0, gaps: [] };
    }
    const gaps = report.modules.filter((item) => item.gap > 0);
    return {
      studentId: student.studentId,
      name: student.name,
      grade: student.grade,
      major: student.major,
      className: student.className,
      riskLevel: report.riskLevel,
      totalGap: gaps.reduce((sum, item) => sum + item.gap, 0),
      gaps,
    };
  });
  const order = { 高: 0, 中: 1, 低: 2, 数据缺失: 3 };
  return { list: rows.sort((a, b) => (order[a.riskLevel] ?? 9) - (order[b.riskLevel] ?? 9) || b.totalGap - a.totalGap) };
}

function saveAcademicProgress(data, session) {
  withDb((db) => {
    db.academic.progressByStudent[session.studentId].modules = data.modules || [];
    appendAudit(db, session, "academic_progress_put", session.studentId);
  });
  return { ok: true };
}

function saveTranscript(data, session) {
  withDb((db) => {
    const progress = db.academic.progressByStudent[session.studentId];
    progress.uploads = progress.uploads || [];
    progress.uploads.unshift({ ...data.meta, at: Date.now() });
    appendAudit(db, session, "academic_transcript_meta", session.studentId);
  });
  return { ok: true };
}

function workbenchSummary(session) {
  if (session.role === ROLES.STUDENT) throw new Error("FORBIDDEN");
  const db = readDb();
  return {
    students: db.students.length,
    pendingApps: db.applications.filter((a) => a.status === APPROVAL.PENDING).length,
    miss: db.missKeywords.length,
    batches: db.batches.length,
    sms: db.smsSimulation.length,
  };
}

function publishNotice(data, session) {
  if (![ROLES.TEACHER, ROLES.COORDINATOR].includes(session.role)) throw new Error("FORBIDDEN");
  const now = Date.now();
  const scheduledAt = Number(data.scheduledAt || 0);
  const scheduled = scheduledAt > now;
  const notice = { id: uid("n"), title: data.title, tags: data.tags || [], summary: data.summary || data.title, content: data.content || data.summary, source: "Web 工作台", publishedAt: scheduled ? scheduledAt : now };
  const batchId = uid("batch");
  let reach = 0;
  withDb((db) => {
    const targets = db.students.filter((s) => matchRule(data.targetRule, s, session));
    reach = targets.length;
    db.notices.unshift(notice);
    db.batches.unshift({
      id: batchId,
      title: notice.title,
      targetRule: data.targetRule || { kind: "all" },
      noticeId: notice.id,
      status: scheduled ? "scheduled" : "sent",
      scheduledAt: scheduled ? scheduledAt : now,
      createdAt: now,
      channels: scheduled ? scheduledChannels(reach) : sentChannels(reach),
    });
    if (!scheduled) deliverMockNotice(db, notice, batchId, targets);
    appendAudit(db, session, scheduled ? "notice_schedule" : "notice_publish", batchId);
  });
  return { notice, batchId, reach, scheduled };
}

function dispatchScheduledNotices(session) {
  requireTeacher(session);
  let dispatched = 0;
  withDb((db) => {
    db.batches.filter((batch) => batch.status === "scheduled" && batch.scheduledAt <= Date.now()).forEach((batch) => {
      const notice = db.notices.find((item) => item.id === batch.noticeId);
      if (!notice) return;
      const targets = db.students.filter((s) => matchRule(batch.targetRule, s, session));
      deliverMockNotice(db, notice, batch.id, targets);
      batch.status = "sent";
      batch.channels = sentChannels(targets.length);
      dispatched += 1;
    });
    appendAudit(db, session, "notice_scheduled_dispatch", "notice_batches");
  });
  return { ok: true, dispatched };
}

function sentChannels(count) {
  return [
    { name: "站内", sendOk: count, sendFail: 0, deliverOk: count, deliverFail: 0, read: 0, observability: "可读" },
    { name: "邮件", sendOk: count, sendFail: 0, deliverOk: 0, deliverFail: 0, read: 0, observability: "不可观测" },
    { name: "短信", sendOk: count, sendFail: 0, deliverOk: 0, deliverFail: 0, read: 0, observability: "发送记录" },
  ];
}

function scheduledChannels(count) {
  return [
    { name: "站内", sendOk: 0, sendFail: 0, deliverOk: 0, deliverFail: 0, read: 0, target: count, observability: "待发送" },
    { name: "邮件", sendOk: 0, sendFail: 0, deliverOk: 0, deliverFail: 0, read: 0, target: count, observability: "待发送" },
    { name: "短信", sendOk: 0, sendFail: 0, deliverOk: 0, deliverFail: 0, read: 0, target: count, observability: "待发送" },
  ];
}

function deliverMockNotice(db, notice, batchId, targets) {
  targets.forEach((s) => {
    db.inboxByStudent[s.studentId] = db.inboxByStudent[s.studentId] || [];
    db.inboxByStudent[s.studentId].unshift({ id: uid("msg"), noticeId: notice.id, title: notice.title, summary: notice.summary, batchId, createdAt: Date.now(), readAt: null, channels: [{ name: "站内", state: "发送请求成功", detail: "送达成功" }, { name: "邮件", state: "发送请求成功", detail: "不可观测" }] });
  });
  db.smsSimulation.unshift({ id: uid("sms"), batchId, at: Date.now(), audience: targets.map((s) => s.studentId), text: `[短信通知] ${notice.title}` });
}

function matchRule(rule, student, session) {
  if (session.role === ROLES.COORDINATOR) {
    const me = readDb().students.find((s) => s.studentId === session.studentId);
    return me?.className === student.className;
  }
  if (!rule || rule.kind === "all") return true;
  if (rule.kind === "grade") return student.grade === rule.value;
  if (rule.kind === "major") return student.major.includes(rule.value || "");
  if (rule.kind === "class") return student.className === rule.value;
  return true;
}

function advanceParty(data, session) {
  if (session.role !== ROLES.TEACHER) throw new Error("FORBIDDEN");
  withDb((db) => {
    const p = db.partyByStudent[data.studentId];
    p.currentKey = data.nextKey;
    p.history.push({ stageKey: data.nextKey, at: Date.now(), remark: data.remark || "管理端推进阶段" });
    appendAudit(db, session, "party_advance", data.studentId);
  });
  return { ok: true };
}

function decideApplication(id, action, data, session) {
  if (session.role !== ROLES.TEACHER) throw new Error("FORBIDDEN");
  let result;
  withDb((db) => {
    const app = db.applications.find((a) => a.id === id);
    if (!app) throw new Error("NOT_FOUND");
    const trail = (act, remark) => app.auditTrail.push({ at: Date.now(), actor: "管理老师", action: act, remark });
    if (action === "approve" && app.status === APPROVAL.PENDING) {
      app.status = APPROVAL.APPROVED;
      app.teacherComment = data.comment || "同意。";
      app.decidedAt = Date.now();
      trail("通过", app.teacherComment);
    } else if (action === "reject" && app.status === APPROVAL.PENDING) {
      app.status = APPROVAL.REJECTED;
      app.teacherComment = data.reason || "材料不全，请补充后重提。";
      app.decidedAt = Date.now();
      trail("驳回", app.teacherComment);
    } else if (["revoke", "reapprove"].includes(action) && [APPROVAL.APPROVED, APPROVAL.REJECTED].includes(app.status)) {
      if (Date.now() - app.decidedAt > WINDOW_MS) throw new Error("WINDOW_CLOSED");
      app.status = action === "revoke" ? APPROVAL.REVOKED : APPROVAL.RE_APPROVED;
      app.teacherComment = data.reason || data.comment || "规则窗口内调整结论。";
      trail(action === "revoke" ? "撤回结论" : "重批", app.teacherComment);
    } else {
      throw new Error("INVALID_STATE");
    }
    appendAudit(db, session, `application_${action}`, id);
    result = app;
  });
  return result;
}

function leaderDashboard(session) {
  if (session.role !== ROLES.LEADER) throw new Error("FORBIDDEN");
  const db = readDb();
  const byStatus = {};
  db.applications.forEach((a) => { byStatus[a.status] = (byStatus[a.status] || 0) + 1; });
  return {
    students: db.students.length,
    knowledgeCount: db.knowledge.length,
    noticeCount: db.notices.length,
    pendingApps: db.applications.filter((a) => a.status === APPROVAL.PENDING).length,
    applicationsByStatus: byStatus,
    missKeywordsTop: db.missKeywords.slice(0, 5),
    academicHighRiskStudents: db.students.filter((s) => academicReport(s.studentId).riskLevel === "高").length,
    batches: db.batches.length,
    lastReset: readMeta(),
  };
}

function appendAudit(db, session, action, target) {
  db.auditLogs = db.auditLogs || [];
  db.auditLogs.unshift({ id: uid("log"), at: Date.now(), actorId: session?.studentId || "unknown", role: session?.role || "unknown", action, target, result: "ok" });
}
