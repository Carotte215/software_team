export function createWorkbenchApi(call, { requestBlob, sessionRef } = {}) {
  return {
    getWorkbenchSummary: () => call({ path: "/workbench/summary" }),
    listKnowledgeMisses: () => call({ path: "/workbench/knowledge/misses" }),
    listAuditLogs: (query = {}) => call({ path: "/audit/logs", data: query }),
    exportAuditLogs: () => requestBlob?.({ path: "/audit/logs/export", session: sessionRef?.value }),
    exportApplications: () => requestBlob?.({ path: "/workbench/applications/export", session: sessionRef?.value }),
    getLeaderDashboard: () => call({ path: "/leader/dashboard" }),
  };
}

