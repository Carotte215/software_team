export const routes = [
  { id: "home", label: "首页" },
  { id: "knowledge", label: "政策知识库" },
  { id: "party", label: "党团流程" },
  { id: "apply", label: "办事申请" },
  { id: "notices", label: "通知消息" },
  { id: "honors", label: "奖励荣誉" },
  { id: "academic", label: "学业分析" },
  { id: "profile", label: "学生画像" },
  { id: "workbench", label: "管理工作台" },
];

export const mobileRouteIds = ["home", "knowledge", "party", "apply", "profile"];

export function readRoute() {
  return window.location.hash.replace(/^#\/?/, "") || "home";
}

export function go(routeId) {
  window.location.hash = `#/${routeId}`;
}
