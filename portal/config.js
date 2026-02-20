// These values are substituted at image build time by the Dockerfile.
// If the placeholders are still present (local dev without a build),
// sensible defaults are used so the portal still renders correctly.
(function () {
  function orDefault(val, fallback) {
    return val.startsWith('__') ? fallback : val;
  }
  window.FORGEKEEPER_HANDLE        = orDefault('__FORGEKEEPER_HANDLE__',       'forgekeeper');
  window.FORGEKEEPER_USER_EMAIL    = orDefault('__FORGEKEEPER_USER_EMAIL__',   'dev@example.com');
  window.FORGEKEEPER_WORKSPACE     = orDefault('__FORGEKEEPER_WORKSPACE__',    'workspace');
})();
