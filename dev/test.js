() => {
  const modules = Object.values(
    webpackChunkdiscord_app.push([[Symbol()], {}, (e) => e.c]),
  );

  const found = [];

  modules.forEach((mod, index) => {
    if (!mod?.exports) return;
    const exports = mod.exports;
    const methods = Object.keys(exports).filter(
      (key) => typeof exports[key] === "function",
    );

    if (methods.length > 0) {
      const related = methods.filter(
        (m) =>
          m.toLowerCase().includes("guild") ||
          m.toLowerCase().includes("channel") ||
          m.toLowerCase().includes("message") ||
          m.toLowerCase().includes("user"),
      );
      found.push({
        moduleIndex: index,
        allMethods: related,
      });
    }
  });
  return found;
};
