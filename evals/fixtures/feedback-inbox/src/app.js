import "./styles.css";
import { feedbackItems } from "./data.js";

const statusLabels = {
  open: "Open",
  planned: "Planned",
  closed: "Closed",
};

function feedbackCard(item) {
  return `
    <article class="feedback-card" data-feedback-id="${item.id}">
      <div class="feedback-card__meta">
        <span class="status status--${item.status}">${statusLabels[item.status]}</span>
        <span>${item.customer}</span>
      </div>
      <h2>${item.title}</h2>
      <p>${item.summary}</p>
    </article>
  `;
}

document.querySelector("#app").innerHTML = `
  <header class="topbar">
    <a class="brand" href="/" aria-label="Relay home">Relay</a>
    <span class="workspace">Support workspace</span>
  </header>
  <main>
    <section class="page-heading" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">Customer signals</p>
        <h1 id="page-title">Feedback Inbox</h1>
      </div>
      <p class="count">${feedbackItems.length} items</p>
    </section>
    <section class="feedback-list" aria-label="Feedback items">
      ${feedbackItems.map(feedbackCard).join("")}
    </section>
  </main>
`;
