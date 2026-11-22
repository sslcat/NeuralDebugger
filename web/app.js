"use strict";
const el = (id) => document.getElementById(id);
const examples = {
  price: [
    "def total_prices(prices):\n    amount = ''\n    for price in prices:\n        amount += price\n    return amount",
    'total_prices([4, 5])\nTypeError: can only concatenate str (not "int") to str',
  ],
  minute: [
    "def clock_parts(minutes):\n    hours, rest = minutes // 60\n    return [hours, rest]",
    "clock_parts(90)\nTypeError: cannot unpack non-iterable int object",
  ],
};
function loadExample(name) {
  [el("code").value, el("trace").value] = examples[name];
}
el("examples").onchange = (e) => {
  if (e.target.value) loadExample(e.target.value);
};
loadExample("price");
async function status() {
  try {
    const s = await (await fetch("/api/status")).json();
    const mode =
      s.mode === "unloaded"
        ? s.configured === "base"
          ? "Base · on demand"
          : "Adapter · pending load"
        : s.mode === "adapter"
          ? "LoRA adapter active"
          : "Base model active";
    el("status").textContent = mode;
    el("status").title = s.model + " @ " + s.revision;
    el("device").textContent = [s.device?.toUpperCase(), s.warning]
      .filter(Boolean)
      .join(" · ");
  } catch {
    el("status").textContent = "Backend offline";
  }
}
function showMessage(title, detail) {
  const message = el("message");
  message.hidden = false;
  message.querySelector("h3").textContent = title;
  message.querySelector("p").textContent = detail;
  el("result").hidden = true;
  el("category").textContent = "OUTPUT";
}
el("form").onsubmit = async (event) => {
  event.preventDefault();
  if (el("analyze").disabled) return;
  el("analyze").disabled = true;
  showMessage(
    "Analyzing locally…",
    "The first request loads the model into memory.",
  );
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: el("code").value,
        traceback: el("trace").value,
      }),
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(
        Array.isArray(data.detail)
          ? data.detail.map((e) => e.msg).join(". ")
          : data.detail,
      );
    const a = data.diagnosis;
    el("message").hidden = true;
    el("result").hidden = false;
    el("cause").textContent = a.root_cause;
    el("reason").textContent = a.explanation;
    el("fixed").textContent = a.corrected_code;
    el("category").textContent = a.category;
    el("copy").textContent = "Copy code";
  } catch (error) {
    showMessage(
      "Analysis interrupted",
      error.message || "Could not reach the local service.",
    );
  } finally {
    el("analyze").disabled = false;
    await status();
  }
};
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    el("form").requestSubmit();
  }
});
el("copy").onclick = async () => {
  try {
    await navigator.clipboard.writeText(el("fixed").textContent);
    el("copy").textContent = "Copied";
  } catch {
    el("copy").textContent = "Select code to copy";
  }
};
status();
