(function () {
  "use strict";

  const DATA_URL = "data/prompts.json";

  let dataPromise = null;
  function loadData() {
    if (!dataPromise) {
      dataPromise = fetch(DATA_URL).then((r) => {
        if (!r.ok) throw new Error("Failed to load prompts.json");
        return r.json();
      });
    }
    return dataPromise;
  }

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function getParam(name) {
    return new URLSearchParams(window.location.search).get(name);
  }

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        if (k === "class") node.className = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else if (k === "text") node.textContent = attrs[k];
        else node.setAttribute(k, attrs[k]);
      }
    }
    if (children) {
      for (const c of children) if (c) node.appendChild(c);
    }
    return node;
  }

  // ---------- Home page ----------

  function renderHome(data) {
    $("#stat-prompts").textContent = data.prompts.length;
    $("#stat-categories").textContent = data.categories.length;

    const grid = $("#category-grid");
    grid.innerHTML = "";

    for (const c of data.categories) {
      const card = el("a", {
        class: "cat-card",
        href: `category.html?slug=${encodeURIComponent(c.slug)}`,
      });
      const img = el("img", { src: c.cover_image, alt: "", loading: "lazy" });
      const label = el("div", { class: "cat-label" });
      const title = el("h3");
      if (c.emoji) title.appendChild(el("span", { text: c.emoji }));
      title.appendChild(el("span", { text: c.label }));
      label.appendChild(title);
      label.appendChild(el("span", { class: "count", text: `${c.count} prompts` }));
      card.appendChild(img);
      card.appendChild(label);
      grid.appendChild(card);
    }

    const search = $("#hero-search");
    if (search) {
      search.addEventListener("input", () => {
        const q = search.value.trim();
        if (!q) {
          // Restore category cards
          renderHome(data);
          return;
        }
        renderSearchResults(data, q);
      });
    }
  }

  function renderSearchResults(data, query) {
    const grid = $("#category-grid");
    grid.innerHTML = "";
    const q = query.toLowerCase();
    const matches = data.prompts.filter((p) =>
      p.title.toLowerCase().includes(q) ||
      p.prompt.toLowerCase().includes(q) ||
      p.category_label.toLowerCase().includes(q)
    );

    if (matches.length === 0) {
      grid.appendChild(el("div", { class: "empty", text: `No prompts match "${query}".` }));
      return;
    }

    // Switch grid styling to prompt cards
    grid.className = "prompt-grid";
    for (const p of matches.slice(0, 60)) {
      grid.appendChild(buildPromptCard(p));
    }
    if (matches.length > 60) {
      grid.appendChild(el("div", { class: "empty", text: `+ ${matches.length - 60} more — refine your search to see them.` }));
    }
  }

  // ---------- Category page ----------

  function renderCategory(data) {
    const slug = getParam("slug") || "all";
    const isAll = slug === "all";

    let prompts = data.prompts;
    let title = "All prompts";
    let metaText = `${data.prompts.length} prompts across ${data.categories.length} categories.`;
    let emoji = "";

    if (!isAll) {
      const cat = data.categories.find((c) => c.slug === slug);
      if (!cat) {
        $("#cat-title").textContent = "Category not found";
        $("#cat-meta").textContent = "";
        $("#prompt-grid").innerHTML = "";
        return;
      }
      prompts = data.prompts.filter((p) => p.category_slug === slug);
      title = cat.label;
      emoji = cat.emoji;
      metaText = `${prompts.length} prompts in this category.`;
    }

    document.title = `${title} — GPT Image Gallery`;
    $("#cat-title").textContent = emoji ? `${emoji} ${title}` : title;
    $("#cat-meta").textContent = metaText;

    // Populate orientation filter
    const orientations = Array.from(new Set(prompts.map((p) => p.orientation).filter(Boolean))).sort();
    const select = $("#cat-filter-orient");
    // Clear existing options except first
    while (select.options.length > 1) select.remove(1);
    for (const o of orientations) {
      select.appendChild(el("option", { value: o, text: o }));
    }

    const search = $("#cat-search");
    let promptIndex = prompts;

    function applyFilter() {
      const q = search.value.trim().toLowerCase();
      const orient = select.value;
      const filtered = promptIndex.filter((p) => {
        if (orient && p.orientation !== orient) return false;
        if (q && !(p.title.toLowerCase().includes(q) || p.prompt.toLowerCase().includes(q))) return false;
        return true;
      });
      renderPromptGrid(filtered);
    }

    search.addEventListener("input", applyFilter);
    select.addEventListener("change", applyFilter);

    renderPromptGrid(prompts);

    // Direct prompt link via ?slug=X&id=Y
    const directId = getParam("id");
    if (directId) {
      const p = data.prompts.find((x) => x.id === directId);
      if (p) openModal(data, p);
    }
  }

  function renderPromptGrid(prompts) {
    const grid = $("#prompt-grid");
    grid.innerHTML = "";
    if (prompts.length === 0) {
      grid.appendChild(el("div", { class: "empty", text: "No prompts match those filters." }));
      return;
    }
    for (const p of prompts) {
      grid.appendChild(buildPromptCard(p));
    }
  }

  function buildPromptCard(p) {
    const card = el("article", {
      class: `prompt-card shape-${p.orientation || "landscape"}`,
      "data-id": p.id,
      tabindex: "0",
    });
    const thumb = el("div", { class: "thumb" });
    thumb.appendChild(el("img", { src: p.image_url, alt: p.title, loading: "lazy" }));
    const meta = el("div", { class: "meta" });
    meta.appendChild(el("h3", { text: p.title }));
    const tags = el("div", { class: "tags" });
    tags.appendChild(el("span", { class: "num", text: `№${p.num}` }));
    tags.appendChild(el("span", { text: p.category_label }));
    if (p.orientation) tags.appendChild(el("span", { text: p.orientation }));
    meta.appendChild(tags);
    card.appendChild(thumb);
    card.appendChild(meta);

    card.addEventListener("click", () => {
      loadData().then((data) => openModal(data, p));
    });
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        loadData().then((data) => openModal(data, p));
      }
    });
    return card;
  }

  // ---------- Modal ----------

  function openModal(data, p) {
    const modal = $("#modal");
    if (!modal) return;
    $("#modal-image").src = p.image_url;
    $("#modal-image").alt = p.title;
    $("#modal-image-link").href = p.image_url;
    $("#modal-title").textContent = p.title;
    $("#modal-breadcrumb").innerHTML = `<a href="category.html?slug=${encodeURIComponent(p.category_slug)}">${escapeHtml(p.category_label)}</a> · №${p.num}`;

    const metaList = $("#modal-meta");
    metaList.innerHTML = "";
    if (p.orientation) metaList.appendChild(el("li", { text: p.orientation }));
    if (p.dims) metaList.appendChild(el("li", { text: p.dims }));
    if (p.attribution) metaList.appendChild(el("li", { text: p.attribution }));

    $("#modal-prompt").textContent = p.prompt;

    const copy = $("#modal-copy");
    copy.classList.remove("copied");
    copy.textContent = "Copy";
    copy.onclick = () => {
      navigator.clipboard.writeText(p.prompt).then(() => {
        copy.classList.add("copied");
        copy.textContent = "Copied ✓";
        setTimeout(() => {
          copy.classList.remove("copied");
          copy.textContent = "Copy";
        }, 1600);
      });
    };

    const permalink = `${window.location.pathname}?slug=${encodeURIComponent(p.category_slug)}&id=${encodeURIComponent(p.id)}`;
    $("#modal-permalink").href = permalink;

    const sourceLink = $("#modal-source-link");
    if (p.source_url) {
      sourceLink.href = p.source_url;
      sourceLink.textContent = `Source: ${p.source_label || "link"} ↗`;
      sourceLink.hidden = false;
    } else {
      sourceLink.hidden = true;
    }

    modal.hidden = false;
    document.body.style.overflow = "hidden";
    // Push history state so back button closes the modal
    if (!window.location.search.includes("id=")) {
      const newUrl = `${window.location.pathname}?slug=${encodeURIComponent(p.category_slug)}&id=${encodeURIComponent(p.id)}`;
      window.history.pushState({ modal: true }, "", newUrl);
    }
  }

  function closeModal() {
    const modal = $("#modal");
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = "";
    if (window.history.state && window.history.state.modal) {
      window.history.back();
    } else if (window.location.search.includes("id=")) {
      // Strip ?id without reloading
      const params = new URLSearchParams(window.location.search);
      params.delete("id");
      const qs = params.toString();
      const newUrl = window.location.pathname + (qs ? `?${qs}` : "");
      window.history.replaceState({}, "", newUrl);
    }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  // ---------- Init ----------

  document.addEventListener("click", (e) => {
    if (e.target.matches("[data-close]")) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
  window.addEventListener("popstate", () => {
    const modal = $("#modal");
    if (modal && !modal.hidden && !window.location.search.includes("id=")) {
      modal.hidden = true;
      document.body.style.overflow = "";
    }
  });

  const page = document.body.dataset.page;
  loadData()
    .then((data) => {
      if (page === "home") renderHome(data);
      else if (page === "category") renderCategory(data);
    })
    .catch((err) => {
      console.error(err);
      const main = document.querySelector("main");
      if (main) {
        main.innerHTML =
          '<p class="empty">Could not load prompts.json. If you opened the file directly, serve the site over HTTP — e.g. <code>python3 -m http.server</code>.</p>';
      }
    });
})();
