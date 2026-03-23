window.dccFunctions = window.dccFunctions || {};

window.dccFunctions.quarterLabel = function (value) {
  const i = Number(value);
  const quarters = window.quarterLookup || [];
  if (Number.isInteger(i) && i >= 0 && i < quarters.length) {
    return quarters[i];
  }
  return String(value);
};

