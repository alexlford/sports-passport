window.SportsPassportData = (() => {
  const cache = {};
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
        events = events.map(e => ({...e, city: normalizeCity(e.city)}));
        return events;
      }
      return value;
    });
    return cache[name];
  }
  const slug = s => s.toLowerCase().replace(/&/g,"and").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
  const score = e => Array.isArray(e.scores) && e.scores.length===2 && e.scores.every(Number.isFinite) ? `${e.scores[0]}–${e.scores[1]}` : "";
  const matchup = e => Array.isArray(e.teams) && e.teams.length===2 ? `${e.teams[0]} vs ${e.teams[1]}` : "Documented event";
  const counts = arr => arr.reduce((o,x)=>(o[x]=(o[x]||0)+1,o),{});
  const venueEvents = (events,key) => events.filter(e => e.venue_key === key);
  const yearEvents = (events,year) => events.filter(e => Number(e.year) === Number(year));
  const teamEvents = (events,team) => events.filter(e => Array.isArray(e.teams) && e.teams.includes(team));
  const phaseEvents = (events,p) => events.filter(e => e.year >= p.start && e.year <= p.end);
  function journeyEvents(events,j) {
    const m=j.match||{};
    if (m.event_ids?.length) return events.filter(e => m.event_ids.includes(e.id));
    if (m.team) return teamEvents(events,m.team);
    if (m.teams_any?.length) return events.filter(e => e.teams?.some(t => m.teams_any.includes(t)));
    return [];
  }
  function recordForTeam(events,team) {
    let w=0,l=0,tie=0,unknown=0;
    events.forEach(e=>{
      const i=e.teams?.indexOf(team);
      if(i<0||!e.scores?.every(Number.isFinite)){unknown++;return}
      const j=i===0?1:0;
      if(e.scores[i]>e.scores[j])w++; else if(e.scores[i]<e.scores[j])l++; else tie++;
    });
    return {w,l,tie,unknown};
  }
  return {load,slug,score,matchup,counts,normalizeCity,venueEvents,yearEvents,teamEvents,phaseEvents,journeyEvents,recordForTeam};
})();
