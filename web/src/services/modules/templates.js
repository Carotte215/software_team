export function createTemplatesApi(call) {
  return {
    listWorkbenchTemplates: () => call({ path: "/workbench/templates" }),
    createWorkbenchTemplate: (payload) => call({ path: "/workbench/templates", method: "POST", data: payload }),
    updateWorkbenchTemplate: (id, payload) => call({ path: `/workbench/templates/${id}`, method: "PUT", data: payload }),
    deleteWorkbenchTemplate: (id) => call({ path: `/workbench/templates/${id}`, method: "DELETE" }),
  };
}
