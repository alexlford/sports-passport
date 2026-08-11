(() => {
  const parts = location.pathname.split('/').filter(Boolean).map(decodeURIComponent);
  const first = parts[0] || '';
  let template = null;
  let params = {};
  let dynamic = false;

  if (first === 'about' && parts.length === 1) template = 'about.html';
  else if (first === 'years' && parts.length === 1) template = 'annuals.html';
  else if (first === 'years' && parts[1]) { template = 'year.html'; params = {y: parts[1]}; dynamic = true; }
  else if (first === 'events' && parts[1]) { template = 'event.html'; params = {id: parts[1]}; dynamic = true; }
  else if (first === 'teams' && parts.length === 1) template = 'teams.html';
  else if (first === 'teams' && parts[1]) { template = 'team-profile.html'; params = {t: parts[1]}; dynamic = true; }
  else if (first === 'venues' && parts.length === 1) template = 'venues.html';
  else if (first === 'venues' && parts[1]) { template = 'venue-profile.html'; params = {v: parts[1]}; dynamic = true; }
  else if (first === 'geography' && parts.length === 1) template = 'geography.html';
  else if (first === 'geography' && parts[1] === 'map') template = 'venue-map.html';
  else if (first === 'journeys' && parts.length === 1) template = 'journeys.html';
  else if (first === 'journeys' && parts[1]) { template = 'journey-profile.html'; params = {j: parts[1]}; dynamic = true; }
  else if (first === 'chapters' && parts[1]) { template = 'phase.html'; params = {p: parts[1]}; dynamic = true; }
  else if (first === 'favorites' && parts.length === 1) template = 'favorites.html';
  else if (first === 'analytics' && parts.length === 1) template = 'lifetime-analytics.html';
  else if (first === 'hall-of-fame' && parts.length === 1) template = 'hall-of-fame.html';

  if (!template) return;

  const cleanPath = location.pathname.endsWith('/') ? location.pathname : `${location.pathname}/`;
  window.SPORTS_CLEAN_ROUTE = true;
  window.SPORTS_ROUTE_CLEAN_PATH = cleanPath;
  window.SPORTS_ROUTE_PARAMS = params;

  const query = new URLSearchParams(params).toString();
  if (query) history.replaceState(null, '', `${cleanPath}?${query}`);

  fetch(`/${template}`, {cache:'no-store'})
    .then(response => {
      if (!response.ok) throw new Error(`Could not load ${template}`);
      return response.text();
    })
    .then(source => {
      const restore = `<script>(function(){const clean=window.SPORTS_ROUTE_CLEAN_PATH||location.pathname;const dynamic=${dynamic?'true':'false'};let tries=0;function ready(){const app=document.querySelector('#app');return !dynamic||(app&&app.children.length>0)||document.querySelector('.hero');}function finish(){if(ready()||tries++>120){history.replaceState(null,'',clean);return;}setTimeout(finish,25);}finish();})();<\/script>`;
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
