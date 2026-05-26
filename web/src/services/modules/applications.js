export function createApplicationsApi(call, { requestBlob, sessionRef }) {
  return {
    listApplications: (query = {}) => call({ path: "/applications", data: query }),
    getApplication: (id) => call({ path: `/applications/${id}` }),
    downloadApplicationDocument: (id, format = "doc") => requestBlob({
      path: `/applications/${id}/document`,
      data: { format },
      session: sessionRef.value,
    }),
    getApplicationDraft: () => call({ path: "/applications/draft" }),
    saveApplicationDraft: (payload) => call({ path: "/applications/draft", method: "POST", data: payload }),
    submitApplication: (payload) => call({ path: "/applications", method: "POST", data: payload }),
    previewApplication: (payload) => call({ path: "/applications/preview", method: "POST", data: payload }),
    submitApplicationById: (id, payload) => call({ path: `/applications/${id}/submit`, method: "POST", data: payload }),
    decideApplication: (id, action, payload) => call({
      path: `/workbench/applications/${id}/${action}`,
      method: "POST",
      data: payload,
    }),
    listApplicationTemplates: () => call({ path: "/workbench/application-templates" }),
    createApplicationTemplate: (payload) => call({ path: "/workbench/application-templates", method: "POST", data: payload }),
    saveApplicationTemplate: (payload) => call({ path: "/workbench/application-templates", method: "POST", data: payload }),
    updateApplicationTemplate: (id, payload) => call({ path: `/workbench/application-templates/${id}`, method: "PUT", data: payload }),
    deleteApplicationTemplate: (id) => call({ path: `/workbench/application-templates/${id}`, method: "DELETE" }),
  };
}
