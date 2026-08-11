window.SportsPassportData = (() => {
  const cache = {};
  let teamAliases = {};

  function ensureStyle(href, marker) {
    if (document.querySelector(`link[${marker}]`)) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.setAttribute(marker, 'true');
    document.head.appendChild(link);
  }
  ensureStyle('assets/readability.css', 'data-sports-passport-readability');
  ensureStyle('assets/chrome.css', 'data-sports-passport-chrome');
  ensureStyle('assets/density.css', 'data-sports-passport-density');

  const STATE_NAMES = {
    Alabama:"AL",Alaska:"AK",Arizona:"AZ",Arkansas:"AR",California:"CA",Colorado:"CO",Connecticut:"CT",Delaware:"DE",Florida:"FL",Georgia:"GA",Hawaii:"HI",Idaho:"ID",Illinois:"IL",Indiana:"IN",Iowa:"IA",Kansas:"KS",Kentucky:"KY",Louisiana:"LA",Maine:"ME",Maryland:"MD",Massachusetts:"MA",Michigan:"MI",Minnesota:"MN",Mississippi:"MS",Missouri:"MO",Montana:"MT",Nebraska:"NE",Nevada:"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND",Ohio:"OH",Oklahoma:"OK",Oregon:"OR",Pennsylvania:"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",Tennessee:"TN",Texas:"TX",Utah:"UT",Vermont:"VT",Virginia:"VA",Washington:"WA","West Virginia":"WV",Wisconsin:"WI",Wyoming:"WY"
  };
  const normalizeCity = value => {
    if (!value || typeof value !== "string") return value;
    const parts = value.split(",").map(x => x.trim());
    if (parts.length < 2) return value.trim();
    const state = STATE_NAMES[parts.at(-1)] || parts.at(-1);
    return `${parts.slice(0,-1).join(", ")}, ${state}`;
  };

  async function load(name) {
    if (!cache[name]) cache[name] = fetch(`data/${name}.json`, {cache:"no-store"}).then(async r => {
      if (!r.ok) throw new Error(`Could not load data/${name}.json`);
      const value = await r.json();
      if (name === "team-aliases" && value && typeof value === "object" && !Array.isArray(value)) {
        teamAliases = value;
        return value;
      }
      if (name === "events" && value && Array.isArray(value.chunks)) {
        const parts = await Promise.all(value.chunks.map(file => fetch(`data/${file}`, {cache:"no-store"}).then(x => {
          if (!x.ok) throw new Error(`Could not load data/${file}`);
          return x.json();
        })));
        let events = parts.flat();
        try {
          const corrections = await fetch("data/corrections.json", {cache:"no-store"}).then(x => x.ok ? x.json() : ({}));
          events = events.map(e => corrections[e.id] ? {...e, ...corrections[e.id]} : e);
        } catch (_) {}
        try {
          const aliases = await fetch("data/team-aliases.json", {cache:"no-store"}).then(x => x.ok ? x.json() : ({}));
          if (aliases && typeof aliases === "object" && !Array.isArray(aliases)) teamAliases = aliases;
        } catch (_) {}
        events = events.map(e => ({
          ...e,
          city: normalizeCity(e.city),
          teams_canonical: Array.isArray(e.teams) ? e.teams.map(t => teamAliases[t] || t) : []
        }));
        return events;
      }
      if (name === "venues" && Array.isArray(value)) {
        let venues = value;
        try {
          const additions = await fetch("data/venue-additions.json", {cache:"no-store"}).then(x => x.ok ? x.json() : ([]));
          if (Array.isArray(additions) && additions.length) {
            const byKey = new Map(venues.map(v => [v.key, v]));
            additions.forEach(v => byKey.set(v.key, {...(byKey.get(v.key)||{}), ...v}));
            venues = [...byKey.values()];
          }
        } catch (_) {}
        try {
          const corrections = await fetch("data/venue-corrections.json", {cache:"no-store"}).then(x => x.ok ? x.json() : ({}));
          return venues.map(v => corrections[v.key] ? {...v, ...corrections[v.key], city: normalizeCity(corrections[v.key].city || v.city)} : {...v, city: normalizeCity(v.city)});
        } catch (_) {
          return venues.map(v => ({...v, city: normalizeCity(v.city)}));
        }
      }
      return value;
    });
    return cache[name];
  }

  const slug = s => s.toLowerCase().replace(/&/g,"and").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
  const score = e => Array.isArray(e.scores) && e.scores.length===2 && e.scores.every(Number.isFinite) ? `${e.scores[0]}–${e.scores[1]}` : "";
  const matchup = e => Array.isArray(e.teams) && e.teams.length===2 ? `${e.teams[0]} vs ${e.teams[1]}` : "Archive event";
  const counts = arr => arr.reduce((o,x)=>(o[x]=(o[x]||0)+1,o),{});

  // Confidence semantics live here so every derived view can use the same rule.
  const isNotionalEvent = e => e?.attendance_status === "notional";
  const isVerifiedEvent = e => e?.attendance_status === "verified";
  const isConfirmedEvent = e => Number(e?.year) >= 2006 || isVerifiedEvent(e);
  const confirmedEvents = events => (events || []).filter(isConfirmedEvent);
  const notionalEvents = events => (events || []).filter(isNotionalEvent);
  const confidenceLabel = e => isNotionalEvent(e) ? "Notional" : (isVerifiedEvent(e) ? "Verified" : "Documented");

  const canonicalTeam = team => teamAliases[team] || team;
  const eventTeams = e => Array.isArray(e.teams_canonical) ? e.teams_canonical : (Array.isArray(e.teams) ? e.teams.map(canonicalTeam) : []);
  const teamPalette = (teamColors, team) => {
    if (teamColors?.[team]) return teamColors[team];
    const source = Object.keys(teamAliases).find(label => teamAliases[label] === team && teamColors?.[label]);
    return source ? teamColors[source] : null;
  };
  const venueByKey = (venues,key) => (venues || []).find(v => v.key === key) || null;
  const venueName = (venues,key,fallback="Venue not recorded") => venueByKey(venues,key)?.display_name || fallback;
  const venueHref = (venues,key) => {
    const venue = venueByKey(venues,key);
    return venue?.slug ? `venue-profile.html?v=${encodeURIComponent(venue.slug)}` : null;
  };
  const venueEvents = (events,key) => events.filter(e => e.venue_key === key);
  const yearEvents = (events,year) => events.filter(e => Number(e.year) === Number(year));
  const teamEvents = (events,team) => events.filter(e => eventTeams(e).includes(team));
  const phaseEvents = (events,p) => events.filter(e => e.year >= p.start && e.year <= p.end);
  function journeyEvents(events,j) {
    const m=j.match||{};
    if (m.event_ids?.length) return events.filter(e => m.event_ids.includes(e.id));
    if (m.team) return teamEvents(events,canonicalTeam(m.team));
    if (m.teams_any?.length) {
      const wanted = m.teams_any.map(canonicalTeam);
      return events.filter(e => eventTeams(e).some(t => wanted.includes(t)));
    }
    return [];
  }
  function recordForTeam(events,team) {
    let w=0,l=0,tie=0,unknown=0;
    events.forEach(e=>{
      const teams=eventTeams(e),i=teams.indexOf(team);
      if(i<0||!e.scores?.every(Number.isFinite)){unknown++;return}
      const j=i===0?1:0;
      if(e.scores[i]>e.scores[j])w++; else if(e.scores[i]<e.scores[j])l++; else tie++;
    });
    return {w,l,tie,unknown};
  }

  function enhanceDensity(root=document) {
    root.querySelectorAll('[data-density]').forEach(container => {
      if (container.dataset.densityReady === 'true') return;
      const limit = Math.max(1, Number(container.dataset.density) || 10);
      const items = [...container.children];
      if (items.length <= limit) {
        container.dataset.densityReady = 'true';
        return;
      }
      const extras = items.slice(limit);
      extras.forEach(el => el.classList.add('density-extra','hidden'));
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'density-toggle';
      button.textContent = `Show all ${items.length}`;
      button.setAttribute('aria-expanded','false');
      button.addEventListener('click', () => {
        const expanded = button.getAttribute('aria-expanded') === 'true';
        extras.forEach(el => el.classList.toggle('hidden', expanded));
        button.setAttribute('aria-expanded', String(!expanded));
        button.textContent = expanded ? `Show all ${items.length}` : 'Show fewer';
      });
      container.insertAdjacentElement('afterend', button);
      const note = document.createElement('div');
      note.className = 'density-note';
      note.textContent = `Showing ${limit} of ${items.length} by default.`;
      button.insertAdjacentElement('afterend', note);
      container.dataset.densityReady = 'true';
    });
  }

  function navKey() {
    const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    if (file === 'index.html' || file === '') return 'home';
    if (['annuals.html','year.html'].includes(file)) return 'years';
    if (['geography.html','venue-map.html','venues.html','venue-profile.html'].includes(file)) return 'geography';
    if (['teams.html','team-profile.html'].includes(file)) return 'teams';
    if (['journeys.html','journey-profile.html','phase.html'].includes(file)) return 'journeys';
    if (file === 'favorites.html') return 'favorites';
    if (file === 'lifetime-analytics.html') return 'analytics';
    if (file === 'hall-of-fame.html') return 'hof';
    return '';
  }

  function hydrateGlobalChrome() {
    const main = document.querySelector('main');
    if (!main) return;
    let header = main.querySelector(':scope > header') || document.querySelector('header.top,header.topbar');
    if (!header) {
      header = document.createElement('header');
      main.prepend(header);
    }
    header.className = 'site-header';
    const active = navKey();
    const links = [
      ['home','index.html','Home'],
      ['years','annuals.html','Years'],
      ['geography','geography.html','Geography'],
      ['teams','teams.html','Teams'],
      ['journeys','journeys.html','Journeys'],
      ['favorites','favorites.html','Favorites'],
      ['analytics','lifetime-analytics.html','Analytics'],
      ['hof','hall-of-fame.html','Hall of Fame']
    ];
    header.innerHTML = `<div class="brand"><a href="index.html" aria-label="Sports Passport home">Sports Passport</a></div><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="global-nav">Menu</button><nav class="nav global-nav" id="global-nav" aria-label="Primary navigation">${links.map(([key,href,label])=>`<a href="${href}"${key===active?' class="active" aria-current="page"':''}>${label}</a>`).join('')}<a class="external" href="https://www.alexlford.com/">Alex Ford ↗</a></nav>`;
    const toggle = header.querySelector('.menu-toggle');
    toggle?.addEventListener('click', () => {
      const open = header.classList.toggle('menu-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Close' : 'Menu';
    });
    header.querySelectorAll('.global-nav a').forEach(a => a.addEventListener('click', () => {
      header.classList.remove('menu-open');
      toggle?.setAttribute('aria-expanded','false');
      if (toggle) toggle.textContent = 'Menu';
    }));

    let footer = main.querySelector(':scope > footer');
    if (!footer) {
      footer = document.createElement('footer');
      main.appendChild(footer);
    }
    footer.className = 'site-footer';
    footer.innerHTML = '<span>Sports Passport · A personal archive of live sports.</span><a href="https://www.alexlford.com/">Back to alexlford.com ↗</a>';
  }

  function boot() {
    hydrateGlobalChrome();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  return {load,slug,score,matchup,counts,normalizeCity,isNotionalEvent,isVerifiedEvent,isConfirmedEvent,confirmedEvents,notionalEvents,confidenceLabel,canonicalTeam,eventTeams,teamPalette,venueByKey,venueName,venueHref,venueEvents,yearEvents,teamEvents,phaseEvents,journeyEvents,recordForTeam,enhanceDensity};
})();
