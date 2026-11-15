// view_field_hubs.js — hubs: entities drawn as smaller dots out from the centre with their parts circling them (empty until THINGS/HUBS are supplied).
//
// view_v4 (SPEC_V8.md, SCP Substrate): view_v3 with your orbs (HUBS[i].yours)
// in their own colour (pink) and held at half the orbit radius, close round you;
// parts on a ring sized to their number, named inside the orb; other orbs held
// firmly on the outer shell; hubReach() for the camera (view_field_world.js).
// Before that, view_v3 (SPEC_V7.md): view_v2 with #entity: links that open the
// orb, and orb names that never overlap (they piled up on a phone).
// Before that, view_v2 (SPEC_V6.md): a copy of the frozen static/view with
// orbs that move freely in 3D (hubs), dependency threads at full strength,
// and each orb named once. static/view is not edited.
//
// Function:
//     One fragment of the cube field. serve.py joins the six view_field_*.js
//     files, in the order world, form, hubs, draw, time, move, inside one
//     function, so they share scope. Canvas 2D with its own 3D maths; no network.
//
// Tier:     Tier 1 — Consumer (SCP Substrate)
// Licence:  MSL-1.0
// Author:   James Gilbert (Giblets Forge)
  // Entities you are building sit out from you as smaller green dots, with
  // their parts circling them and each part's claims gathered round it
  // view_v2: each orb is a body moving freely in 3D round you. Orbs push each
  // other apart, a soft pull keeps them at orbit distance, your links pull
  // related orbs together, and the whole system turns slowly on a tilted axis.
  const PART_R = 190, ORBIT_R = Math.max(520, Math.sqrt(HUBS.length) * 260), GREEN = "94,235,130";
  // view_v4: yours — pink, and held at INNER × the orbit radius
  const YOURS = "255,120,200", INNER = .5, orbitOf = h => h.yours ? ORBIT_R * INNER : ORBIT_R;
  const partR = h => h.parts.length ? Math.max(PART_R, 60 + 22 * h.parts.length) : PART_R;
  const orbTint = h => h.yours ? { c: YOURS, hi: "255,175,225", core: "255,220,240" } : { c: GREEN, hi: "150,255,175", core: "205,255,216" };
  const hubGroup = (topic, reach) => ({ group: "", topic, rgb: "110,190,255", rigid: true, loose: true, hub: true,
                                        turn: .05, angle: 0, home: [0, 0, 0], nodes: [], c: [0, 0, 0], half: 40, reach });
  const hubs = HUBS.map((h, i) => ({
    ...h, angle: .8 + i * Math.PI * 2 / HUBS.length, spin: 0, turn: -.06, home: [0, 0, 0],
    own: hubGroup(h.name, 50), parts: h.parts.map(p => ({ ...p, cl: hubGroup(p.name, 60) })),
  }));
  hubs.forEach(h => { if (h.yours) [h.own, ...h.parts.map(p => p.cl)].forEach(cl => { cl.rgb = YOURS; }); });  // view_v4: your orbs' claims glow pink too
  const hubGroups = () => hubs.flatMap(h => [h.own, ...h.parts.map(p => p.cl)]);
  // Start spread over a sphere (golden angle), then let the forces settle it
  hubs.forEach((h, i) => {
    const y = 1 - (2 * i + 1) / hubs.length, r = Math.sqrt(1 - y * y), a = i * 2.399963;
    const R = orbitOf(h);  // view_v4
    h.pos = [Math.cos(a) * r * R, y * R * .9, Math.sin(a) * r * R];
    h.vel = [0, 0, 0];
    h.seed = i * 1.7;
  });
  // Springs between orbs, from the cubes' own links (one per pair of orbs)
  const hubLinks = (() => {
    const at = new Map(hubs.map((h, i) => [h.id, i])), of = new Map(), out = [], seen = new Set();
    CUBES.forEach(c => { if (c.hub && at.has(c.hub.entity)) of.set(c.id, at.get(c.hub.entity)); });
    CUBES.forEach(c => (c.neighbours || []).forEach(id => {
      const a = of.get(c.id), b = of.get(id);
      if (a === undefined || b === undefined || a === b) return;
      const key = Math.min(a, b) + "-" + Math.max(a, b);
      if (!seen.has(key)) { seen.add(key); out.push([a, b]); }
    }));
    return out;
  })();
  const vlen = v => Math.hypot(v[0], v[1], v[2]);
  const K_REP = .12 * ORBIT_R ** 3, REST = ORBIT_R * .45, K_LINK = .6, MAX_V = 320, SPIN = .04;
  const AXIS = (() => { const a = [.35, 1, .2], l = vlen(a); return a.map(x => x / l); })();
  const spun = (p, ang) => {
    const [x, y, z] = AXIS, c = Math.cos(ang), s = Math.sin(ang), d = x * p[0] + y * p[1] + z * p[2];
    const cr = [y * p[2] - z * p[1], z * p[0] - x * p[2], x * p[1] - y * p[0]];
    return [0, 1, 2].map(k => p[k] * c + cr[k] * s + AXIS[k] * d * (1 - c));
  };
  let hubClock = 0;
  function stepHubs(dt) {
    hubClock += dt;
    const t = hubClock, f = hubs.map(() => [0, 0, 0]);
    hubs.forEach((h, i) => {
      const d = vlen(h.pos) || 1;
      for (let k = 0; k < 3; k++) f[i][k] += h.pos[k] / d * (orbitOf(h) - d) * (h.yours ? 2.4 : 3) + Math.sin(t * (.11 + k * .03) + h.seed * (1 + k * .3)) * 8;
      for (let j = i + 1; j < hubs.length; j++) {
        const v = [0, 1, 2].map(k => h.pos[k] - hubs[j].pos[k]), dd = Math.max(vlen(v), 60), m = K_REP / (dd * dd * dd);
        for (let k = 0; k < 3; k++) { f[i][k] += v[k] * m; f[j][k] -= v[k] * m; }
      }
    });
    hubLinks.forEach(([i, j]) => {
      const v = [0, 1, 2].map(k => hubs[j].pos[k] - hubs[i].pos[k]), dd = Math.max(vlen(v), 1), m = (dd - REST) * K_LINK / dd;
      for (let k = 0; k < 3; k++) { f[i][k] += v[k] * m; f[j][k] -= v[k] * m; }
    });
    const damp = Math.exp(-2.5 * dt);
    hubs.forEach((h, i) => {
      for (let k = 0; k < 3; k++) h.vel[k] = (h.vel[k] + f[i][k] * dt) * damp;
      const s = vlen(h.vel);
      if (s > MAX_V) h.vel = h.vel.map(x => x * MAX_V / s);
      h.pos = spun([0, 1, 2].map(k => h.pos[k] + h.vel[k] * dt), SPIN * dt);
      h.vel = spun(h.vel, SPIN * dt);
      // view_v4: each kind of orb keeps to its shell (pushing apart would
      // otherwise carry yours out past the repos); they still drift round it
      const r = vlen(h.pos) || 1, [lo, hi] = h.yours ? [.4, .6] : [.9, 1.1];
      const held = Math.min(hi * ORBIT_R, Math.max(lo * ORBIT_R, r));
      if (held !== r) h.pos = h.pos.map(x => x * held / r);
    });
  }
  for (let i = 0; i < 600; i++) stepHubs(.05);  // natural clusters have formed by the first frame
  hubReach = () => Math.max(...hubs.map(h => vlen(h.pos) + partR(h)));  // view_v4: the camera fits this

  const hubOf = c => {
    const h = c.hub && hubs.find(x => x.id === c.hub.entity);
    if (!h) return null;
    const part = h.parts.find(p => p.id === c.hub.part);
    return part ? part.cl : h.own;
  };

  function placeHubs() {
    hubs.forEach(h => {
      h.home = add(world.c, h.pos);
      h.own.home = [...h.home];
      h.parts.forEach((p, k) => {
        p.cl.home = add(h.home, turned([partR(h), Math.sin(k * 2.1) * 40, 0], h.spin + k * Math.PI * 2 / h.parts.length));
      });
    });
  }

  function orbitHubs(dt) {
    const held = focus.hub || (focus.cluster && hubGroups().includes(focus.cluster));
    if (!calm && !held) stepHubs(Math.min(dt, .05));
    placeHubs();
    if (calm) return;
    hubs.forEach(h => {
      if (!held) h.spin += h.turn * dt;
      [h.own, ...h.parts.map(p => p.cl)].forEach(cl => { if (focus.cluster !== cl) cl.angle += cl.turn * dt; });
    });
  }

  // Hubs hold their claims in the opening view, by tags and by entity. A
  // single lens or repos is about that mode's clusters, so the hubs step aside.
  const hubsShown = () => mode === "ALL" || mode === "TAGS" || mode === "PLACES";
  // Claims about a hub's parts leave their word clusters for the hub
  function gatherHubs(placed) {
    hubGroups().forEach(cl => { cl.nodes = []; });
    if (!hubsShown()) return;
    const moved = nodes.filter(n => !placed.includes(n) && hubOf(n.c));
    if (!moved.length) return;
    const kept = clusters.filter(cl => (cl.nodes = cl.nodes.filter(n => !moved.includes(n))).length);
    clusters.length = 0;
    clusters.push(...kept);
    moved.forEach(n => { n.cluster = hubOf(n.c); n.cluster.nodes.push(n); });
    hubGroups().forEach(cl => { if (cl.nodes.length) clusters.push(cl); });
    placeHubs();
  }

  // A green strand from you to each hub and from the hub to each part
  const hidden = h => !hubsShown() || (view.entity && view.entity !== h.id);
  function drawHubs(you, dim, time) {
    hubs.forEach(h => {
      if (hidden(h)) return;
      const q = project(h.home);
      if (!q) return;
      const t = orbTint(h);  // view_v4
      const strand = (a, b, alpha) => {
        ctx.strokeStyle = `rgba(${t.c},${alpha * dim})`;
        ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      };
      if (you) strand(you, q, .35);
      h.parts.forEach(p => {
        const pq = project(p.cl.home);
        if (!pq) return;
        strand(q, pq, .5);
        glow(pq, 14 * pq.k, t.c, .4 * dim);
        ctx.fillStyle = `rgba(${t.core},${.85 * dim})`;
        ctx.beginPath(); ctx.arc(pq.x, pq.y, 3.2 * Math.max(pq.k, .6), 0, 7); ctx.fill();
      });
      const r = 15 * q.k * (calm ? 1 : 1 + Math.sin(time * 1.3 + 1) * .07);
      glow(q, r * 5, t.c, .3 * dim);
      glow(q, r * 2, t.hi, .7 * dim);
      ctx.fillStyle = `rgba(${t.core},${dim})`;
      ctx.beginPath(); ctx.arc(q.x, q.y, r * .62, 0, 7); ctx.fill();
    });
  }

  // The hub's name under its dot, and each part's name by its point
  // view_v3: nearest first; a name that would land on one already drawn waits
  // until its orb moves clear (the orb you are in is always named)
  let namedBoxes = [];
  const textBox = (text, x, y, size) => {
    ctx.font = `700 ${size}px system-ui, "Segoe UI", sans-serif`;
    const w = ctx.measureText(text).width / 2 + 4;
    return [x - w, y - size - 1, x + w, y + 5];
  };
  // reserved: names already placed this frame (you, the group titles)
  function nameHubs(dim, reserved = []) {
    const taken = [...reserved], over = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
    hubs.map(h => [h, !hidden(h) && project(h.home)]).filter(([, q]) => q)
      .sort((a, b) => (b[0] === focus.hub) - (a[0] === focus.hub) || a[1].d - b[1].d).forEach(([h, q]) => {
      const y = q.y + 15 * q.k + 18, box = textBox(h.name, q.x, y, 14);
      if (h !== focus.hub && taken.some(b => over(b, box))) return;
      taken.push(box);
      label(h.name, { x: q.x, y }, 14, .95 * dim, 700);
      h.parts.forEach(p => {
        const pq = project(p.cl.home);
        if (!pq || !(h === focus.hub || !p.cl.nodes.length)) return;
        const pbox = textBox(p.name, pq.x, pq.y + 16, 12);  // view_v4: parts keep clear of every name too
        if (taken.some(b => over(b, pbox))) return;
        taken.push(pbox);
        label(p.name, { x: pq.x, y: pq.y + 16 }, 12, .85 * dim, 600);
      });
    });
    namedBoxes = taken;
  }

  function hubAt(x, y) {
    for (const h of hubs) {
      if (hidden(h)) continue;
      const q = project(h.home);
      if (q && Math.hypot(q.x - x, q.y - y) < Math.max(22 * q.k, 14)) return h;
    }
    return null;
  }

  function goHub(h) {
    focus.cluster = focus.node = focus.lens = focus.link = null;
    focus.hub = h;
    cam.toDist = (partR(h) + 150) * 2.6;
    hubPanel(h); setCrumbs();
  }

  // An overview of the entity: who builds it, its parts, its claims and its wiring
  function hubPanel(h) {
    const groups = [h.own, ...h.parts.map(p => p.cl)], all = groups.flatMap(cl => cl.nodes);
    const count = test => all.filter(n => test(n.c)).length;
    panel.replaceChildren();
    const shut = el("button", "shut", "×");
    shut.setAttribute("aria-label", "Back out");
    shut.addEventListener("click", goHome);
    panel.append(shut, el("h3", "", h.name), el("p", "id", h.id));
    const who = h.builders.length ? ` · ${h.builders.join(", ")} is building it` : "";
    panel.append(el("p", "facts", (h.kind ? h.kind[0].toUpperCase() + h.kind.slice(1) : "Entity") + who));
    panel.append(el("p", "facts", `${all.length} claims · ${count(c => c.score > 0)} started · `
      + `${count(c => c.status === "attested")} attested`));
    panel.append(el("p", "facts", "Parts"));
    h.parts.forEach(p => {
      const card = el("button", "lens");
      card.style.setProperty("--c", `rgb(${h.yours ? YOURS : GREEN})`);  // view_v4
      const head = el("b", "", (p.count > 1 ? `${p.count} × ` : "") + p.name);
      head.append(el("em", "", ` · ${p.cl.nodes.length} claim${p.cl.nodes.length === 1 ? "" : "s"}`));
      card.append(head, document.createTextNode(p.role || "No role given"));
      if (p.cl.nodes.length) card.addEventListener("click", () => goCluster(p.cl));
      else card.disabled = true;
      panel.append(card);
    });
    if (h.own.nodes.length) {
      panel.append(el("p", "facts", `About ${h.name} as a whole`));
      h.own.nodes.forEach(n => {
        const b = el("button", "hop", shorten(n.c.content, 60));
        b.addEventListener("click", () => goNode(n));
        panel.append(b);
      });
    }
    if (h.nets.length) {
      panel.append(el("p", "facts", "Wiring, traced from its wiring claims"));
      h.nets.forEach(net => {
        const card = el("div", "lens");
        card.style.setProperty("--c", net.ground ? `rgb(${GREEN})` : "rgb(150,215,255)");
        card.append(el("b", "", net.ground ? (net.pins.length > 2 ? "Common ground" : "Ground") : "Joined"),
                    document.createTextNode(net.pins.join(" · ")));
        panel.append(card);
      });
    }
    const grid = el("button", "hop", `Open ${h.name} in the grid`);
    grid.addEventListener("click", () => { state.about = h.id; document.getElementById("togrid").click(); draw(); });
    panel.append(grid);
    panel.append(el("p", "facts", "Click a part to go to its claims. Esc or a click on empty space backs out."));
    panel.hidden = false;
  }

  // Clustered by entity: pick an entity to see only its claims, then one of
  // its subjects to go to it
  function inEntity(c, id) {
    return (c.hub && c.hub.entity === id) || (c.entities || []).includes(id);
  }
  function renderPicker() {
    let bar = document.getElementById("picker");
    if (!bar) {
      bar = el("div", "");
      bar.id = "picker";
      document.getElementById("modes").after(bar);
    }
    bar.replaceChildren();
    bar.hidden = mode !== "PLACES" || !(THINGS.entities || []).length;
    if (bar.hidden) return;
    const row = el("div", "row");
    row.append(el("span", "", "Entity"));
    THINGS.entities.forEach(e => {
      const chip = el("button", "chip", e.name);
      chip.setAttribute("aria-pressed", view.entity === e.id);
      chip.addEventListener("click", () => pickEntity(view.entity === e.id ? null : e));
      row.append(chip);
    });
    bar.append(row);
    const e = view.entity && THINGS.entities.find(x => x.id === view.entity);
    if (!e) return;
    const mine = clusters.filter(cl => cl.nodes.some(n => inEntity(n.c, e.id)));
    const name = cl => cl.topic === e.name ? "No subject" : cl.topic.replace(e.name + " · ", "");
    const list = el("div", "row");
    list.append(el("span", "", "Subjects"));
    mine.sort((a, b) => (name(a) === "No subject") - (name(b) === "No subject") || name(a).localeCompare(name(b)))
      .forEach(cl => {
        const chip = el("button", "chip", `${name(cl)} · ${cl.nodes.length}`);
        chip.setAttribute("aria-pressed", focus.cluster === cl);
        chip.addEventListener("click", () => (focus.cluster === cl ? pickEntity(e) : goCluster(cl)));
        list.append(chip);
      });
    bar.append(list);
  }
  function pickEntity(e) {
    view.entity = e ? e.id : null;
    const hub = e && hubs.find(h => h.id === e.id);
    if (hub) goHub(hub); else goHome();
  }
