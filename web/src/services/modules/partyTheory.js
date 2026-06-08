export function createPartyTheoryApi(call, { requestBlob, apiPath, sessionRef } = {}) {
  const blobCall = requestBlob || call;
  return {
    getPartyProgress: () => call({ path: "/party/progress" }),
    getLeagueProgress: () => call({ path: "/league/progress" }),
    getPartyOfficialDocs: () => call({ path: "/party/official-docs" }),
    getPartyOfficialGuide: () => call({ path: "/party/official-guide" }),
    downloadPartyOfficialDoc: (docId) => blobCall({
      path: `/party/official-docs/${docId}/download`,
      session: sessionRef?.value,
    }),
    previewPartyOfficialDoc: async (docId) => {
      const blob = await blobCall({
        path: `/party/official-docs/${docId}/preview`,
        session: sessionRef?.value,
      });
      return URL.createObjectURL(blob);
    },
    listPartyProgress: (query = {}) => call({ path: "/workbench/party/progress", data: query }),
    listLeagueProgress: () => call({ path: "/workbench/league/progress" }),
    attachPartyStepMaterial: (stepId, attachments) =>
      call({ path: `/party/steps/${stepId}/materials`, method: "POST", data: { attachments } }),
    removePartyStepMaterial: (stepId, fileId) =>
      call({ path: `/party/steps/${stepId}/materials/${fileId}`, method: "DELETE" }),
    attachLeagueStepMaterial: (stepId, attachments) =>
      call({ path: `/league/steps/${stepId}/materials`, method: "POST", data: { attachments } }),
    removeLeagueStepMaterial: (stepId, fileId) =>
      call({ path: `/league/steps/${stepId}/materials/${fileId}`, method: "DELETE" }),
    listThoughtReports: () => call({ path: "/party/thought-reports" }),
    submitThoughtReport: (payload) => call({ path: "/party/thought-reports", method: "POST", data: payload }),
    getPartyCalendarEvents: () => call({ path: "/party/calendar-events" }),
    listPartyCalendarAdmin: () => call({ path: "/workbench/party/calendar" }),
    savePartyCalendarAdmin: (events) => call({ path: "/workbench/party/calendar", method: "PUT", data: { events } }),
    completePartyTask: (taskId) => call({ path: `/party/tasks/${taskId}/done`, method: "POST" }),
    completePartyStep: (stepId) => call({ path: `/party/steps/${stepId}/done`, method: "POST" }),
    completeLeagueStep: (stepId) => call({ path: `/league/steps/${stepId}/done`, method: "POST" }),
    completeLeagueTask: (taskId) => call({ path: `/league/tasks/${taskId}/done`, method: "POST" }),
    advancePartyStage: (payload) => call({ path: "/workbench/party/advance", method: "POST", data: payload }),
    advanceLeagueStage: (payload) => call({ path: "/workbench/league/advance", method: "POST", data: payload }),
    verifyPartyStep: (payload) => call({ path: "/workbench/party/steps/verify", method: "POST", data: payload }),
    getStudentPartyPendingSteps: (studentId) => call({ path: `/workbench/party/students/${studentId}` }),
    getStudentLeaguePendingSteps: (studentId) => call({ path: `/workbench/league/students/${studentId}` }),
    verifyLeagueStep: (payload) => call({ path: "/workbench/league/steps/verify", method: "POST", data: payload }),
    exportPartyProgress: () => blobCall({ path: "/workbench/party/export", session: sessionRef?.value }),
    refreshLeagueReminders: () => call({ path: "/workbench/league/reminders/refresh", method: "POST" }),
    getPartyTimeline: () => call({ path: "/workbench/party/timeline" }),
    updatePartyTimeline: (rules) => call({ path: "/workbench/party/timeline", method: "PUT", data: { rules } }),
    updatePartyStages: (stages) => call({ path: "/workbench/party/stages", method: "PUT", data: { stages } }),
    refreshPartyReminders: () => call({ path: "/workbench/party/reminders/refresh", method: "POST" }),
    listTheoryQuestions: () => call({ path: "/theory/questions" }),
    submitTheoryAttempt: (answers, questionIds = []) =>
      call({ path: "/theory/attempt", method: "POST", data: { answers, questionIds } }),
    listTheoryQuestionAdmin: () => call({ path: "/theory/workbench/questions" }),
    saveTheoryQuestions: (questions) => call({ path: "/theory/workbench/questions", method: "PUT", data: { questions } }),
    importTheoryQuestions: (file, options = {}) => {
      const data = new FormData();
      data.append("file", file);
      data.append("dryRun", String(options.dryRun !== false));
      return call({ path: "/theory/workbench/questions/import", method: "POST", data });
    },
  };
}
