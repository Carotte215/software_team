import { configureApi, getApiConfig, request as rawRequest, requestBlob } from "../api/client.js";

function apiPath(path) {
  if (!path) return "";
  return path.startsWith("/api/") ? path.slice(4) : path;
}

export function createApi(sessionRef) {
  const call = (options) => rawRequest({
    ...options,
    session: sessionRef.value,
  });

  return {
    request: call,
    getApiConfig,
    configureApi,
    login: (payload) => call({ path: "/auth/login", method: "POST", data: payload }),
    getRuntime: () => call({ path: "/runtime" }),
    getSessionInfo: () => call({ path: "/session" }),
    getCurrentStudent: () => call({ path: "/student/me" }),
    listStudents: () => call({ path: "/students" }),
    getStudentFieldPolicy: () => call({ path: "/students/field-policy" }),
    updateStudent: (id, payload) => call({ path: `/students/${id}`, method: "PATCH", data: payload }),
    exportStudents: () => requestBlob({ path: "/students/export", session: sessionRef.value }),
    importStudents: (file, options = {}) => {
      const data = new FormData();
      data.append("file", file);
      data.append("dryRun", String(options.dryRun !== false));
      data.append("overwrite", String(Boolean(options.overwrite)));
      return call({ path: "/students/import", method: "POST", data });
    },

    searchKnowledge: (query) => call({ path: "/knowledge", data: query }),
    recordKnowledgeMiss: (keyword) => call({ path: "/knowledge/miss", method: "POST", data: { keyword } }),
    listKnowledgeAdmin: () => call({ path: "/knowledge/admin/list" }),
    createKnowledge: (payload) => call({ path: "/knowledge", method: "POST", data: payload }),
    updateKnowledge: (id, payload) => call({ path: `/knowledge/${id}`, method: "PUT", data: payload }),
    setKnowledgeOnline: (id, online) => call({ path: `/knowledge/${id}/online`, method: "POST", data: { online } }),
    downloadTemplate: (template) => requestBlob({
      path: `/templates/${template.id}/download`,
      data: { name: template.name },
      session: sessionRef.value,
    }),

    getPartyProgress: () => call({ path: "/party/progress" }),
    completePartyTask: (taskId) => call({ path: `/party/tasks/${taskId}/done`, method: "POST" }),
    advancePartyStage: (payload) => call({ path: "/workbench/party/advance", method: "POST", data: payload }),
    getPartyTimeline: () => call({ path: "/workbench/party/timeline" }),
    updatePartyTimeline: (rules) => call({ path: "/workbench/party/timeline", method: "PUT", data: { rules } }),
    refreshPartyReminders: () => call({ path: "/workbench/party/reminders/refresh", method: "POST" }),
    listTheoryQuestions: () => call({ path: "/theory/questions" }),
    submitTheoryAttempt: (answers) => call({ path: "/theory/attempt", method: "POST", data: { answers } }),
    listTheoryQuestionAdmin: () => call({ path: "/theory/workbench/questions" }),
    saveTheoryQuestions: (questions) => call({ path: "/theory/workbench/questions", method: "PUT", data: { questions } }),
    importTheoryQuestions: (file, options = {}) => {
      const data = new FormData();
      data.append("file", file);
      data.append("dryRun", String(options.dryRun !== false));
      return call({ path: "/theory/workbench/questions/import", method: "POST", data });
    },

    listApplications: (query = {}) => call({ path: "/applications", data: query }),
    getApplication: (id) => call({ path: `/applications/${id}` }),
    downloadApplicationDocument: (id) => requestBlob({ path: `/applications/${id}/document`, data: { format: "doc" }, session: sessionRef.value }),
    getApplicationDraft: () => call({ path: "/applications/draft" }),
    saveApplicationDraft: (payload) => call({ path: "/applications/draft", method: "POST", data: payload }),
    submitApplication: (payload) => call({ path: "/applications", method: "POST", data: payload }),
    submitApplicationById: (id, payload) => call({ path: `/applications/${id}/submit`, method: "POST", data: payload }),
    uploadFile: (file, business = "application") => {
      const data = new FormData();
      data.append("file", file);
      data.append("business", business);
      return call({ path: "/files/upload", method: "POST", data });
    },
    downloadFile: (file) => requestBlob({
      path: apiPath(file.url || `/files/${file.id}/download`),
      data: { name: file.name },
      session: sessionRef.value,
    }),
    decideApplication: (id, action, payload) => call({
      path: `/workbench/applications/${id}/${action}`,
      method: "POST",
      data: payload,
    }),

    listNotices: () => call({ path: "/notices" }),
    getInbox: () => call({ path: "/messages/inbox" }),
    markMessageRead: (id) => call({ path: `/messages/${id}/read`, method: "POST" }),
    publishNotice: (payload) => call({ path: "/workbench/notices/publish", method: "POST", data: payload }),
    dispatchScheduledNotices: () => call({ path: "/workbench/notices/scheduled/dispatch", method: "POST" }),

    listHonors: (query = {}) => call({ path: "/honors", data: query }),
    createHonor: (payload) => call({ path: "/honors", method: "POST", data: payload }),
    updateHonor: (id, payload) => call({ path: `/honors/${id}`, method: "PUT", data: payload }),

    getAcademicReport: () => call({ path: "/academic/report" }),
    getAcademicPlan: () => call({ path: "/academic/plan" }),
    listAcademicPlans: () => call({ path: "/academic/workbench/plans" }),
    saveAcademicPlan: (payload) => call({ path: "/academic/workbench/plans", method: "PUT", data: payload }),
    importAcademicPlans: (file, options = {}) => {
      const data = new FormData();
      data.append("file", file);
      data.append("dryRun", String(options.dryRun !== false));
      return call({ path: "/academic/workbench/plans/import", method: "POST", data });
    },
    saveAcademicProgress: (modules) => call({ path: "/academic/progress", method: "PUT", data: { modules } }),
    uploadTranscript: (meta) => call({ path: "/academic/transcript", method: "POST", data: { meta } }),

    getWorkbenchSummary: () => call({ path: "/workbench/summary" }),
    listWorkbenchBatches: (query = {}) => call({ path: "/workbench/batches", data: query }),
    listKnowledgeMisses: () => call({ path: "/workbench/knowledge/misses" }),
    listSmsSimulations: () => call({ path: "/workbench/sms" }),
    listAcademicRisks: () => call({ path: "/workbench/academic/risks" }),
    listAuditLogs: (query = {}) => call({ path: "/audit/logs", data: query }),
    getLeaderDashboard: () => call({ path: "/leader/dashboard" }),
  };
}
