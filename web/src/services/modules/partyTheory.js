export function createPartyTheoryApi(call) {
  return {
    getPartyProgress: () => call({ path: "/party/progress" }),
    listPartyProgress: () => call({ path: "/workbench/party/progress" }),
    completePartyTask: (taskId) => call({ path: `/party/tasks/${taskId}/done`, method: "POST" }),
    advancePartyStage: (payload) => call({ path: "/workbench/party/advance", method: "POST", data: payload }),
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
