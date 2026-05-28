export function createHonorsApi(call) {
  return {
    listHonors: (query = {}) => call({ path: "/honors", data: query }),
    createHonor: (payload) => call({ path: "/honors", method: "POST", data: payload }),
    updateHonor: (id, payload) => call({ path: `/honors/${id}`, method: "PUT", data: payload }),
    deleteHonor: (id) => call({ path: `/honors/${id}`, method: "DELETE" }),
    setHonorOnline: (id, online) => call({ path: `/honors/${id}/online`, method: "POST", data: { online } }),
    importHonors: (file, options = {}) => {
      const data = new FormData();
      data.append("file", file);
      data.append("dryRun", String(options.dryRun !== false));
      return call({ path: "/honors/workbench/import", method: "POST", data });
    },
  };
}
