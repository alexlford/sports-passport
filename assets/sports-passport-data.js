window.SportsPassportData = (() => {
  const cache = {};
  let teamAliases = {};
  const PUBLIC_ORIGIN = 'https://sports.alexlford.com';

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
  ensureStyle('/assets/accessibility.css', 'data-sports-passport-accessibility');

  function upsertMeta(attribute, key, content) {
    if (!content) return;
    let meta = document.head.querySelector(`meta[${attribute}="${key}"]`);
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute(attribute, key);
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', content);
  }

  function upsertLink(rel, href) {
    let link = document.head.querySelector(`link[rel="${rel}"]`);
    if (!link) {
      link = document.createElement('link');
      link.rel = rel;
      document.head.appendChild(link);
    }
    link.href = href;
  }

  upsertLink('icon', 'favicon.svg');

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

  let cacheManifestPromise = null;

async function cacheManifest() {
  if (!cacheManifestPromise) {
    cacheManifestPromise = fetch('/data/cache-manifest.json', {cache:'no-cache'})
      .then(async response => {
        if (!response.ok) throw new Error('Could not load data/cache-manifest.json');
        const manifest = await response.json();
        return manifest && typeof manifest.version === 'string' ? manifest : null;
      })
      .catch(() => null);
  }
  return cacheManifestPromise;
}

async function versionedDataRequest(path) {
  const manifest = await cacheManifest();
  if (!manifest?.version) return {url:path, options:{cache:"no-cache"}};
  const url = new URL(path, location.origin);
  url.searchParams.set('v', manifest.version);
  return {url:`${url.pathname}${url.search}`, options:{cache:"force-cache"}};
}

async function fetchJson(path, fallback) {
  const {url,options} = await versionedDataRequest(path);
  const response = await fetch(url, options);
  if (!response.ok) {
    if (arguments.length > 1) return fallback;
    throw new Error(`Could not load ${path}`);
  }
  return response.json();
}

async function load(name) {
  if (!cache[name]) {
    if (name === "events") {
      cache[name] = Promise.all([
        fetchJson("/data/resolved-events.json"),
        fetchJson("/data/team-aliases.json", {})
      ]).then(([events,aliases]) => {
        if (aliases && typeof aliases === "object" && !Array.isArray(aliases)) teamAliases = aliases;
        return events;
      });
    } else if (name === "venues") {
      cache[name] = fetchJson("/data/resolved-venues.json");
    } else {
      cache[name] = fetchJson(`/data/${name}.json`).then(value => {
        if (name === "team-aliases" && value && typeof value === "object" && !Array.isArray(value)) teamAliases = value;
        return value;
      });
    }
  }
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
  const EVIDENCE_LABELS = {
    ticket_stub: "Ticket-stub evidence",
    attendance_record: "Attendance record",
    direct_confirmation: "Direct confirmation",
    verified_archive: "Verified archive evidence",
    reconstructed_archive: "Reconstructed early archive",
    documented_archive: "Documented archive record"
  };
  const evidenceType = e => e?.evidence?.type || null;
  const evidenceLabel = e => EVIDENCE_LABELS[evidenceType(e)] || "Archive evidence";
  const evidenceProvenance = e => e?.evidence?.provenance || "";

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

  function canonicalUrlForPage(file, params) {
    const dynamicParam = {
      'year.html':'y',
      'phase.html':'p',
      'journey-profile.html':'j',
      'team-profile.html':'t',
      'venue-profile.html':'v'
    }[file];
    if (file === 'index.html' || file === '') return `${PUBLIC_ORIGIN}/`;
    if (dynamicParam && params.get(dynamicParam)) {
      return `${PUBLIC_ORIGIN}/${file}?${dynamicParam}=${encodeURIComponent(params.get(dynamicParam))}`;
    }
    return `${PUBLIC_ORIGIN}/${file}`;
  }

  function setPublicationMeta(title, description, canonicalUrl) {
    if (title) document.title = title;
    upsertMeta('name','description',description);
    upsertMeta('name','author','Alex Ford');
    upsertMeta('property','og:site_name','Sports Passport');
    upsertMeta('property','og:type','website');
    upsertMeta('property','og:title',title);
    upsertMeta('property','og:description',description);
    upsertMeta('property','og:url',canonicalUrl);
    upsertMeta('name','twitter:card','summary');
    upsertMeta('name','twitter:title',title);
    upsertMeta('name','twitter:description',description);
    upsertLink('canonical',canonicalUrl);
  }

  async function polishPublicationMetadata() {
    const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    const params = new URLSearchParams(location.search);
    const canonicalUrl = canonicalUrlForPage(file,params);
    const staticMeta = {
      'index.html':['Sports Passport | Alex Ford','Alex Ford’s personal archive of live sports, organized through annual editions, venues, teams, life chapters, maps, rankings, and lifetime analytics.'],
      'annuals.html':['Annual Editions | Sports Passport','Browse Sports Passport year by year, from the reconstructed early archive through the current live season.'],
      'favorites.html':['Personal Canon | Sports Passport','Alex Ford’s curated Top 10 sports experiences, favorite venues, and best venues visited.'],
      'geography.html':['Sports Geography | Sports Passport','Explore the cities and venues in Alex Ford’s live-sports archive through maps, rankings, and venue profiles.'],
      'venue-map.html':['Venue Map | Sports Passport','Explore the physical footprint of Alex Ford’s live-sports archive on an interactive venue map.'],
      'venues.html':['Venue Profiles | Sports Passport','Browse every stadium and arena in Alex Ford’s Sports Passport archive.'],
      'teams.html':['Team Explorer | Sports Passport','Browse favorite-team dossiers and every canonical team represented in Alex Ford’s live-sports archive.'],
      'journeys.html':['Life Chapters & Journeys | Sports Passport','Follow Alex Ford’s sports life through five chronological chapters and recurring family and team threads.'],
      'lifetime-analytics.html':['Lifetime Analytics | Sports Passport','Explore the cumulative patterns in Alex Ford’s live-sports archive across years, sports, teams, venues, and cities.'],
      'hall-of-fame.html':['Record Book | Sports Passport','Archive records and Alex Ford’s curated Personal Canon of top live-sports experiences.'],
      'search.html':['Archive Search | Sports Passport','Search Alex Ford’s Sports Passport archive across live events, teams, venues, cities, and years.']
    };
    let [title,description] = staticMeta[file] || [document.title || 'Sports Passport','A personal archive of live sports by Alex Ford.'];
    try {
      if (file === 'year.html') {
        const year = params.get('y');
        if (year) {
          title = `${year} Annual Edition | Sports Passport`;
          description = `Alex Ford’s ${year} Sports Passport annual edition, with documented live games, venues, teams, and year-specific analytics.`;
        }
      } else if (file === 'phase.html') {
        const phases = await load('phases');
        const phase = phases.find(p => p.key === params.get('p'));
        if (phase) {
          title = `${phase.title} | Sports Passport Life Chapters`;
          description = phase.deck;
        }
      } else if (file === 'journey-profile.html') {
        const journeys = await load('journeys');
        const journey = journeys.find(j => j.key === params.get('j'));
        if (journey) {
          title = `${journey.title} | Sports Passport`;
          description = journey.description;
        }
      } else if (file === 'venue-profile.html') {
        const venues = await load('venues');
        const venue = venues.find(v => v.slug === params.get('v'));
        if (venue) {
          title = `${venue.display_name} | Sports Passport`;
          description = `${venue.display_name} in ${venue.city}: visits, teams, signature moments, and archive history from Alex Ford’s Sports Passport.`;
        }
      } else if (file === 'team-profile.html') {
        const events = await load('events');
        const requested = params.get('t');
        const teams = [...new Set(events.flatMap(eventTeams))];
        const team = teams.find(t => slug(t) === requested);
        if (team) {
          title = `${team} | Sports Passport`;
          description = `${team} appearances, venues, annual records, and signature moments in Alex Ford’s Sports Passport archive.`;
        }
      }
    } catch (_) {}
    setPublicationMeta(title,description,canonicalUrl);
  }

  async function polishAnnualVenueLeaders() {
    const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    if (file !== 'year.html') return;
    const venueHeading = [...document.querySelectorAll('.panel h3')].find(h => h.textContent.trim() === 'Venue leaders');
    if (!venueHeading) return;
    let venues;
    try { venues = await load('venues'); } catch (_) { return; }
    let row = venueHeading.nextElementSibling;
    while (row?.classList?.contains('leader')) {
      const label = row.querySelector('span');
      if (label) {
        const key = label.textContent.trim();
        const venue = venueByKey(venues,key);
        if (venue) {
          const link = document.createElement('a');
          link.href = venueHref(venues,key);
          link.textContent = venue.display_name;
          label.replaceChildren(link);
        }
      }
      row = row.nextElementSibling;
    }
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
      ['hof','hall-of-fame.html','Record Book']
    ];
    header.innerHTML = `<div class="brand"><a href="index.html" aria-label="Sports Passport home">Sports Passport</a></div><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="global-nav">Menu</button><nav class="nav global-nav" id="global-nav" aria-label="Primary navigation">${links.map(([key,href,label])=>`<a href="${href}"${key===active?' class="active" aria-current="page"':''}>${label}</a>`).join('')}<a class="external" href="https://www.alexlford.com/">Alex Ford ↗</a></nav>`;
    const toggle = header.querySelector('.menu-toggle');
    const tools = document.createElement('div');
    tools.className = 'site-header-tools';
    const searchLink = document.createElement('a');
    searchLink.className = 'global-search-link';
    searchLink.href = '/search/';
    searchLink.textContent = 'Search';
    tools.appendChild(searchLink);
    if (toggle) tools.appendChild(toggle);
    header.appendChild(tools);
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
    polishPublicationMetadata();
    polishAnnualVenueLeaders();
    if (!document.querySelector('script[data-sports-passport-accessibility]')) {
      const script = document.createElement('script');
      script.src = '/assets/accessibility.js';
      script.defer = true;
      script.dataset.sportsPassportAccessibility = 'true';
      document.head.appendChild(script);
    }
    if (!document.querySelector('script[data-sports-passport-seo]')) {
      const seo = document.createElement('script');
      seo.src = '/assets/seo.js';
      seo.defer = true;
      seo.dataset.sportsPassportSeo = 'true';
      document.head.appendChild(seo);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  return {load,slug,score,matchup,counts,normalizeCity,isNotionalEvent,isVerifiedEvent,isConfirmedEvent,confirmedEvents,notionalEvents,confidenceLabel,evidenceType,evidenceLabel,evidenceProvenance,canonicalTeam,eventTeams,teamPalette,venueByKey,venueName,venueHref,venueEvents,yearEvents,teamEvents,phaseEvents,journeyEvents,recordForTeam,enhanceDensity};
})();
