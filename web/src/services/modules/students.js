export function createStudentsApi(call, { requestBlob, sessionRef }) {
  return {
    getCurrentStudent: () => call({ path: "/student/me" }),
    listStudents: () => call({ path: "/students" }),
    getStudentFieldPolicy: () => call({ path: "/students/field-policy" }),
    updateStudent: (id, payload) => call({ path: `/students/${id}`, method: "PATCH", data: payload }),
    updateMyProfile: (payload) => call({ path: "/student/me", method: "PATCH", data: payload }),
    exportStudents: (format = "csv") => requestBlob({ path: "/students/export", data: { format }, session: sessionRef.value }),
    importStudents: (file, options = {}) => {
      const data = new FormData();
      data.append("file", file);
      data.append("dryRun", String(options.dryRun !== false));
      data.append("overwrite", String(Boolean(options.overwrite)));
      return call({ path: "/students/import", method: "POST", data });
    },
  };
}
