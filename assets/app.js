(function () {
  "use strict";

  const DATA_URL = "data/prompts.json";
  const PAGE_SIZE = 36;

  const state = {
    data: null,
    slug: "all",
    orient: "",
    query: "",
    filtered: [],
    rendered: 0,
  };

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.from((r || document).querySelectorAll(s)); }
  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      if (k === "class") n.className = attrs[k];
      else if (k === "text") n.textContent = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    if (children) for (const c of children) if (c) n.appendChild(c);
    return n;
  }
  function getParams() { return new URLSearchParams(window.location.search); }
  function setParams(updates, replace) {
    const p = getParams();
    for (const k in updates) {
      if (updates[k] === null || updates[k] === "" || (k === "cat" && updates[k] === "all")) p.delete(k);
      else p.set(k, updates[k]);
    }
    const qs = p.toString();
    const url = window.location.pathname + (qs ? `?${qs}` : "") + window.location.hash;
    if (replace) window.history.replaceState({}, "", url);
    else window.history.pushState({}, "", url);
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  }

  /* ---------- Data ---------- */

  fetch(DATA_URL)
    .then((r) => r.json())
    .then((data) => { state.data = data; bootstrap(); })
    .catch((err) => {
      console.error(err);
      $("#grid").innerHTML = '<div class="empty">Could not load <code>data/prompts.json</code>. If you opened the file directly, serve over HTTP: <code>python3 -m http.server</code></div>';
    });

  /* ---------- Sidebar ---------- */

  function buildSidebar() {
    const list = $("#category-list");
    $("#count-all").textContent = state.data.prompts.length;
    for (const c of state.data.categories) {
      const li = el("li");
      const a = el("a", { class: "cat-link", href: `?cat=${encodeURIComponent(c.slug)}`, "data-slug": c.slug });
      a.appendChild(el("span", { class: "cat-icon", text: c.emoji || "•" }));
      a.appendChild(el("span", { class: "cat-name", text: c.label }));
      a.appendChild(el("span", { class: "cat-count", text: String(c.count) }));
      a.addEventListener("click", (e) => {
        e.preventDefault();
        selectCategory(c.slug);
        closeSidebar();
      });
      li.appendChild(a);
      list.appendChild(li);
    }
    $$('.cat-link[data-slug="all"]').forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        selectCategory("all");
        closeSidebar();
      });
    });
  }

  function selectCategory(slug) {
    state.slug = slug;
    $$(".cat-link").forEach((a) => a.classList.toggle("active", a.dataset.slug === slug));
    setParams({ cat: slug, id: null });
    applyFilters();
  }

  function openSidebar() {
    $("#sidebar").classList.add("open");
    $("#sidebar-backdrop").classList.add("open");
    $("#sidebar-backdrop").hidden = false;
  }
  function closeSidebar() {
    $("#sidebar").classList.remove("open");
    $("#sidebar-backdrop").classList.remove("open");
    $("#sidebar-backdrop").hidden = true;
  }

  /* ---------- Filters & rendering ---------- */

  function applyFilters() {
    const q = state.query.toLowerCase();
    state.filtered = state.data.prompts.filter((p) => {
      if (state.slug !== "all" && p.category_slug !== state.slug) return false;
      if (state.orient && p.orientation !== state.orient) return false;
      if (q && !(p.title.toLowerCase().includes(q) || p.prompt.toLowerCase().includes(q) || p.category_label.toLowerCase().includes(q))) return false;
      return true;
    });
    state.rendered = 0;

    let title = "All prompts";
    let metaText = "";
    if (state.slug !== "all") {
      const cat = state.data.categories.find((c) => c.slug === state.slug);
      if (cat) title = `${cat.emoji ? cat.emoji + " " : ""}${cat.label}`;
    }
    if (state.query) {
      title = `Search: “${state.query}”`;
    }
    metaText = `${state.filtered.length} ${state.filtered.length === 1 ? "prompt" : "prompts"}`;
    if (state.slug === "all" && !state.query) {
      metaText += ` · ${state.data.categories.length} categories`;
    }
    $("#view-title").textContent = title;
    $("#view-meta").textContent = metaText;
    $("#result-count").textContent = state.filtered.length ? `Showing ${Math.min(PAGE_SIZE, state.filtered.length)} of ${state.filtered.length}` : "";

    document.title = state.slug === "all" && !state.query
      ? "GPT Image Prompt Gallery"
      : `${title} — GPT Image Gallery`;

    const grid = $("#grid");
    grid.innerHTML = "";
    if (state.filtered.length === 0) {
      grid.appendChild(el("div", { class: "empty", text: "No prompts match those filters." }));
      $("#end-marker").hidden = true;
      return;
    }
    renderNextPage();
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function renderNextPage() {
    const slice = state.filtered.slice(state.rendered, state.rendered + PAGE_SIZE);
    const grid = $("#grid");
    for (const p of slice) grid.appendChild(buildCard(p));
    state.rendered += slice.length;
    $("#result-count").textContent = `Showing ${state.rendered} of ${state.filtered.length}`;
    $("#end-marker").hidden = state.rendered < state.filtered.length;
  }

  function buildCard(p) {
    const card = el("article", { class: "card", "data-id": p.id, tabindex: "0" });
    const thumb = el("div", { class: "card-thumb" });
    // Reserve space using aspect-ratio inferred from dims to reduce reflow
    const ar = aspectRatio(p);
    if (ar) thumb.style.aspectRatio = ar;
    const img = el("img", { src: p.image_url, alt: p.title, loading: "lazy", decoding: "async" });
    img.addEventListener("error", () => { img.style.opacity = "0.2"; });
    thumb.appendChild(img);
    const overlay = el("div", { class: "card-overlay" });
    const inner = el("div", { class: "card-overlay-inner" });
    inner.appendChild(el("h3", { text: p.title }));
    const sub = el("div", { class: "sub" });
    sub.appendChild(el("span", { class: "num", text: `№${p.num}` }));
    sub.appendChild(el("span", { text: p.category_label }));
    inner.appendChild(sub);
    overlay.appendChild(inner);
    thumb.appendChild(overlay);
    card.appendChild(thumb);
    card.addEventListener("click", () => openModal(p));
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openModal(p); }
    });
    return card;
  }

  function aspectRatio(p) {
    if (p.dims && /^\d+x\d+$/i.test(p.dims)) {
      const [w, h] = p.dims.toLowerCase().split("x").map(Number);
      if (w && h) return `${w} / ${h}`;
    }
    const map = { landscape: "3/2", portrait: "2/3", square: "1/1", wide: "21/9" };
    return map[p.orientation] || "4/3";
  }

  /* ---------- Modal ---------- */

  function openModal(p) {
    const modal = $("#modal");
    $("#modal-image").src = p.image_url;
    $("#modal-image").alt = p.title;
    $("#modal-image-link").href = p.image_url;
    $("#modal-title").textContent = p.title;
    $("#modal-breadcrumb").innerHTML =
      `<a href="?cat=${encodeURIComponent(p.category_slug)}" data-cat-link="${escapeHtml(p.category_slug)}">${escapeHtml(p.category_label)}</a> · №${p.num}`;
    $("#modal-breadcrumb a").addEventListener("click", (e) => {
      e.preventDefault();
      closeModal();
      selectCategory(p.category_slug);
    });

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
        setTimeout(() => { copy.classList.remove("copied"); copy.textContent = "Copy"; }, 1600);
      });
    };

    const sourceLink = $("#modal-source-link");
    if (p.source_url) {
      sourceLink.href = p.source_url;
      sourceLink.textContent = `Source: ${p.source_label || "link"} ↗`;
      sourceLink.hidden = false;
    } else {
      sourceLink.hidden = true;
    }

    const permaBtn = $("#modal-permalink");
    permaBtn.textContent = "Copy link";
    permaBtn.onclick = (e) => {
      e.preventDefault();
      const url = window.location.origin + window.location.pathname +
        `?cat=${encodeURIComponent(p.category_slug)}&id=${encodeURIComponent(p.id)}`;
      navigator.clipboard.writeText(url).then(() => {
        permaBtn.textContent = "Link copied ✓";
        setTimeout(() => { permaBtn.textContent = "Copy link"; }, 1600);
      });
    };

    setParams({ id: p.id });
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    const modal = $("#modal");
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = "";
    setParams({ id: null }, true);
  }

  /* ---------- Bootstrap ---------- */

  function bootstrap() {
    buildSidebar();

    const params = getParams();
    state.slug = params.get("cat") || "all";
    state.query = params.get("q") || "";
    state.orient = params.get("orient") || "";
    if (state.query) $("#search").value = state.query;
    $$(".chip").forEach((c) => c.classList.toggle("active", (c.dataset.orient || "") === state.orient));
    $$(".cat-link").forEach((a) => a.classList.toggle("active", a.dataset.slug === state.slug));

    applyFilters();

    const id = params.get("id");
    if (id) {
      const p = state.data.prompts.find((x) => x.id === id);
      if (p) openModal(p);
    }

    // Search
    let searchTimer = null;
    $("#search").addEventListener("input", (e) => {
      clearTimeout(searchTimer);
      const val = e.target.value;
      searchTimer = setTimeout(() => {
        state.query = val.trim();
        setParams({ q: state.query || null, id: null });
        applyFilters();
      }, 140);
    });

    // Orientation chips
    $$(".chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        $$(".chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        state.orient = chip.dataset.orient || "";
        setParams({ orient: state.orient || null, id: null });
        applyFilters();
      });
    });

    // Sidebar toggle (mobile)
    $("#sidebar-toggle").addEventListener("click", () => {
      const sb = $("#sidebar");
      if (sb.classList.contains("open")) closeSidebar();
      else openSidebar();
    });
    $("#sidebar-backdrop").addEventListener("click", closeSidebar);

    // Infinite scroll
    const sentinel = $("#sentinel");
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting && state.rendered < state.filtered.length) {
          renderNextPage();
        }
      }
    }, { rootMargin: "600px 0px" });
    io.observe(sentinel);

    // Keyboard: "/" focuses search, Esc closes modal
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
      if (e.key === "/" && document.activeElement !== $("#search")) {
        e.preventDefault();
        $("#search").focus();
        $("#search").select();
      }
    });

    // Modal close interactions
    document.addEventListener("click", (e) => {
      if (e.target.matches("[data-close]")) closeModal();
    });

    // Browser back/forward
    window.addEventListener("popstate", () => {
      const p = getParams();
      const slug = p.get("cat") || "all";
      const orient = p.get("orient") || "";
      const query = p.get("q") || "";
      const id = p.get("id");
      const filtersChanged = slug !== state.slug || orient !== state.orient || query !== state.query;
      state.slug = slug; state.orient = orient; state.query = query;
      $("#search").value = query;
      $$(".chip").forEach((c) => c.classList.toggle("active", (c.dataset.orient || "") === orient));
      $$(".cat-link").forEach((a) => a.classList.toggle("active", a.dataset.slug === slug));
      if (filtersChanged) applyFilters();
      const modal = $("#modal");
      if (id) {
        const promptObj = state.data.prompts.find((x) => x.id === id);
        if (promptObj) openModal(promptObj);
      } else if (!modal.hidden) {
        modal.hidden = true;
        document.body.style.overflow = "";
      }
    });
  }
})();
