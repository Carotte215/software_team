export function createKnowledgeApi(call, { requestBlob, sessionRef } = {}) {
  return {
    searchKnowledge: (query) => call({ path: "/knowledge", data: query }),
    getKnowledge: (id) => call({ path: `/knowledge/${id}` }),
    listKnowledgeFavorites: () => call({ path: "/knowledge/favorites" }),
    listKnowledgeRecent: () => call({ path: "/knowledge/recent" }),
    listKnowledgeTrending: () => call({ path: "/knowledge/trending" }),
    toggleKnowledgeFavorite: (id) => call({ path: `/knowledge/favorites/${id}`, method: "POST" }),
    removeKnowledgeFavorite: (id) => call({ path: `/knowledge/favorites/${id}`, method: "DELETE" }),
    recordKnowledgeMiss: (keyword) => call({ path: "/knowledge/miss", method: "POST", data: { keyword } }),
    listKnowledgeAdmin: () => call({ path: "/knowledge/admin/list" }),
    createKnowledge: (payload) => call({ path: "/knowledge", method: "POST", data: payload }),
    updateKnowledge: (id, payload) => call({ path: `/knowledge/${id}`, method: "PUT", data: payload }),
    setKnowledgeOnline: (id, online) => call({ path: `/knowledge/${id}/online`, method: "POST", data: { online } }),
    exportKnowledge: () => requestBlob?.({ path: "/knowledge/export", session: sessionRef?.value }),
  };
}
