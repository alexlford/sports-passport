(() => {
  const parts = location.pathname.split('/').filter(Boolean).map(decodeURIComponent);
  const first = parts[0] || '';
  const publicQuery = new URLSearchParams(location.search);
  let template = null;
  let params = {};
  let dynamic = false;

  if (first === 'about') template = 'about.html';
  else if (first === 'artifacts') template = 'artifacts.html';
  else if (first === 'years') {
    const year = publicQuery.get('year') || publicQuery.get('y') || parts[1];
    if (year) { template = 'year.html'; params = {y: year}; dynamic = true; }
    else template = 'annuals.html';
  }
  else if (first === 'events') {
    const event = publicQuery.get('event') || publicQuery.get('id') || parts[1];
    if (event) { template = 'event.html'; params = {id: event}; dynamic = true; }
    else template = 'annuals.html';
  }
  else if (first === 'teams') {
    const team = publicQuery.get('team') || publicQuery.get('t') || parts[1];
    if (team) { template = 'team-profile.html'; params = {t: team}; dynamic = true; }
    else template = 'teams.html';
  }
  else if (first === 'venues') {
    const venue = publicQuery.get('venue') || publicQuery.get('v') || parts[1];
    if (venue) { template = 'venue-profile.html'; params = {v: venue}; dynamic = true; }
    else template = 'venues.html';
  }
  else if (first === 'geography' && parts[1] === 'map') template = 'venue-map.html';
  else if (first === 'geography') template = 'geography.html';
  else if (first === 'journeys') {
    const journey = publicQuery.get('journey') || publicQuery.get('j') || parts[1];
    if (journey) { template = 'journey-profile.html'; params = {j: journey}; dynamic = true; }
    else template = 'journeys.html';
  }
  else if (first === 'chapters') {
    const chapter = publicQuery.get('chapter') || publicQuery.get('p') || parts[1];
    if (chapter) { template = 'phase.html'; params = {p: chapter}; dynamic = true; }
    else template = 'journeys.html';
  }
  else if (first === 'favorites') template = 'favorites.html';
  else if (first === 'analytics') template = 'lifetime-analytics.html';
  else if (first === 'hall-of-fame') template = 'hall-of-fame.html';

  if (!template) return;

  const cleanPath = location.pathname.endsWith('/') ? location.pathname : `${location.pathname}/`;
  const cleanPublicUrl = `${cleanPath}${location.search || ''}${location.hash || ''}`;
  window.SPORTS_CLEAN_ROUTE = true;
  window.SPORTS_ROUTE_PUBLIC_URL = cleanPublicUrl;
  window.SPORTS_ROUTE_PARAMS = params;

  const legacyQuery = new URLSearchParams(params).toString();
  if (legacyQuery) history.replaceState(null, '', `${cleanPath}?${legacyQuery}${location.hash || ''}`);

  fetch(`/${template}`, {cache:'no-store'})
    .then(response => {
      if (!response.ok) throw new Error(`Could not load ${template}`);
      return response.text();
    })
    .then(source => {
      const restore = `<script>(function(){const clean=window.SPORTS_ROUTE_PUBLIC_URL||location.pathname;const dynamic=${dynamic?'true':'false'};let tries=0;function ready(){const app=document.querySelector('#app');return !dynamic||(app&&app.children.length>0)||document.querySelector('.hero');}function finish(){if(ready()||tries++>160){history.replaceState(null,'',clean);return;}setTimeout(finish,25);}finish();})();<\/script>`;
      let html = source.replace(/<head>/i, '<head><base href="/">');
      html = html.replace(/<\/body>/i, '<script src="/assets/clean-urls.js"><\/script>' + restore + '</body>');
      document.open();
      document.write(html);
      document.close();
    })
    .catch(() => {
      document.body.innerHTML = '<main style="max-width:760px;margin:64px auto;padding:24px;font-family:system-ui"><h1>Sports Passport route unavailable</h1><p>This clean archive route could not load its underlying page.</p><p><a href="/">Return to Sports Passport</a></p></main>';
    });
})();
