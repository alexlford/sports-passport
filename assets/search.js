(async()=>{
  const D=window.SportsPassportData;
  const input=document.querySelector('#global-search');
  const clear=document.querySelector('#clear-search');
  const typeButtons=[...document.querySelectorAll('#type-filters button')];
  const sportSelect=document.querySelector('#sport-filter');
  const yearSelect=document.querySelector('#year-filter');
  const status=document.querySelector('#search-status');
  const results=document.querySelector('#search-results');
  if(!D||!input||!results)return;

  const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const normalize=value=>String(value??'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  const labelType=type=>({event:'Event',team:'Team',venue:'Venue',city:'City',year:'Year'}[type]||type);
  const params=new URLSearchParams(location.search);
  let activeType=['event','team','venue','city','year'].includes(params.get('type'))?params.get('type'):'all';

  const [events,venues,aliases,config]=await Promise.all([
    D.load('events'),
    D.load('venues'),
    D.load('team-aliases').catch(()=>({})),
    D.load('config').catch(()=>null)
  ]);
  const venueByKey=new Map(venues.map(v=>[v.key,v]));
  const eventSports=new Set(events.map(e=>e.sport).filter(Boolean));
  [...eventSports].sort((a,b)=>a.localeCompare(b)).forEach(sport=>{
    const option=document.createElement('option');option.value=sport;option.textContent=sport;sportSelect.appendChild(option);
  });
  const archiveStart=Number(config?.archive_start_year)||Math.min(...events.map(e=>Number(e.year)).filter(Number.isFinite));
  const archiveEnd=Number(config?.current_year)||Math.max(...events.map(e=>Number(e.year)).filter(Number.isFinite));
  for(let year=archiveEnd;year>=archiveStart;year--){const option=document.createElement('option');option.value=String(year);option.textContent=String(year);yearSelect.appendChild(option)}

  const teamMap=new Map();
  events.forEach(event=>D.eventTeams(event).forEach(team=>{
    if(!teamMap.has(team))teamMap.set(team,[]);
    teamMap.get(team).push(event);
  }));
  const aliasMap=new Map();
  Object.entries(aliases||{}).forEach(([alias,canonical])=>{
    if(!aliasMap.has(canonical))aliasMap.set(canonical,[]);
    aliasMap.get(canonical).push(alias);
  });
  const cityMap=new Map();
  events.forEach(event=>{
    if(!event.city)return;
    if(!cityMap.has(event.city))cityMap.set(event.city,[]);
    cityMap.get(event.city).push(event);
  });
  const yearMap=new Map();
  events.forEach(event=>{
    const year=String(event.year);
    if(!yearMap.has(year))yearMap.set(year,[]);
    yearMap.get(year).push(event);
  });

  const setFor=(items,key)=>new Set(items.map(item=>item[key]).filter(Boolean).map(String));
  const records=[];
  events.forEach(event=>{
    const teams=D.eventTeams(event);
    const venue=venueByKey.get(event.venue_key);
    const originalTeams=Array.isArray(event.teams)?event.teams:[];
    const title=teams.length===2?`${teams[0]} vs ${teams[1]}`:D.matchup(event);
    const meta=[event.date,venue?.display_name||event.venue_recorded,event.city,event.sport].filter(Boolean).join(' · ');
    records.push({type:'event',title,meta,href:`/events/${encodeURIComponent(event.id)}/`,sports:new Set(event.sport?[String(event.sport)]:[]),years:new Set([String(event.year)]),search:[title,...originalTeams,...teams,event.date,event.city,event.sport,event.league,venue?.display_name,venue?.key,venue?.slug,event.venue_recorded].filter(Boolean).join(' ')});
  });
  [...teamMap.entries()].forEach(([team,teamEvents])=>{
    const sports=setFor(teamEvents,'sport'),years=new Set(teamEvents.map(e=>String(e.year)));
    records.push({type:'team',title:team,meta:`Team · ${teamEvents.length} archive appearance${teamEvents.length===1?'':'s'} · ${[...sports].sort().join(', ')}`,href:`/teams/${D.slug(team)}/`,sports,years,search:[team,...(aliasMap.get(team)||[]),...teamEvents.flatMap(e=>[e.city,e.sport,e.league])].filter(Boolean).join(' ')});
  });
  venues.forEach(venue=>{
    const venueEvents=D.venueEvents(events,venue.key),sports=setFor(venueEvents,'sport'),years=new Set(venueEvents.map(e=>String(e.year)));
    records.push({type:'venue',title:venue.display_name,meta:[venue.city,`${venueEvents.length} archive visit${venueEvents.length===1?'':'s'}`,[...sports].sort().join(', ')].filter(Boolean).join(' · '),href:`/venues/${encodeURIComponent(venue.slug)}/`,sports,years,search:[venue.display_name,venue.city,venue.key,venue.slug,...venueEvents.flatMap(e=>[...D.eventTeams(e),e.sport,e.league])].filter(Boolean).join(' ')});
  });
  [...cityMap.entries()].forEach(([city,cityEvents])=>{
    const venueKeys=new Set(cityEvents.map(e=>e.venue_key).filter(Boolean)),sports=setFor(cityEvents,'sport'),years=new Set(cityEvents.map(e=>String(e.year)));
    records.push({type:'city',title:city,meta:`City · ${cityEvents.length} archive event${cityEvents.length===1?'':'s'} · ${venueKeys.size} venue${venueKeys.size===1?'':'s'}`,href:'/geography/',sports,years,search:[city,...cityEvents.flatMap(e=>[...D.eventTeams(e),e.sport,e.league,venueByKey.get(e.venue_key)?.display_name])].filter(Boolean).join(' ')});
  });
  for(let year=archiveStart;year<=archiveEnd;year++){
    const yearEvents=yearMap.get(String(year))||[],sports=setFor(yearEvents,'sport');
    records.push({type:'year',title:String(year),meta:`Annual edition · ${yearEvents.length} event${yearEvents.length===1?'':'s'}${sports.size?` · ${[...sports].sort().join(', ')}`:''}`,href:`/years/${year}/`,sports,years:new Set([String(year)]),search:[year,...yearEvents.flatMap(e=>[...D.eventTeams(e),e.city,e.sport,e.league,venueByKey.get(e.venue_key)?.display_name])].filter(Boolean).join(' ')});
  }
  records.forEach(record=>{record.titleNorm=normalize(record.title);record.searchNorm=normalize(`${record.title} ${record.search}`)});

  const initialSport=params.get('sport');
  const initialYear=params.get('year');
  if(initialSport&&[...sportSelect.options].some(o=>o.value===initialSport))sportSelect.value=initialSport;
  if(initialYear&&[...yearSelect.options].some(o=>o.value===initialYear))yearSelect.value=initialYear;
  input.value=params.get('q')||'';

  function setType(type){
    activeType=type;
    typeButtons.forEach(button=>{const active=button.dataset.type===type;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active))});
  }
  setType(activeType);

  function score(record,query){
    if(!query)return 20;
    const tokens=normalize(query).split(/\s+/).filter(Boolean);
    if(!tokens.every(token=>record.searchNorm.includes(token)))return null;
    const q=normalize(query);
    if(record.titleNorm===q)return 0;
    if(record.titleNorm.startsWith(q))return 1;
    if(record.titleNorm.split(' ').some(word=>word.startsWith(q)))return 2;
    if(record.titleNorm.includes(q))return 3;
    return 4;
  }
  function syncUrl(){
    const p=new URLSearchParams();
    if(input.value.trim())p.set('q',input.value.trim());
    if(activeType!=='all')p.set('type',activeType);
    if(sportSelect.value!=='all')p.set('sport',sportSelect.value);
    if(yearSelect.value!=='all')p.set('year',yearSelect.value);
    const query=p.toString();history.replaceState(null,'',`/search/${query?`?${query}`:''}`);
  }
  function render(){
    const query=input.value.trim(),sport=sportSelect.value,year=yearSelect.value;
    const matches=records.map(record=>({record,score:score(record,query)})).filter(item=>item.score!==null)
      .filter(({record})=>activeType==='all'||record.type===activeType)
      .filter(({record})=>sport==='all'||record.sports.has(sport))
      .filter(({record})=>year==='all'||record.years.has(year))
      .sort((a,b)=>a.score-b.score||a.record.title.localeCompare(b.record.title));
    syncUrl();
    if(!query&&activeType==='all'&&sport==='all'&&year==='all'){
      status.textContent='';
      results.innerHTML='<div class="search-empty"><strong>Search the whole archive.</strong>Start with a team, venue, city, year, sport, or league. The filters can also browse a slice of the collection without a text query.</div>';
      return;
    }
    status.innerHTML=`<strong>${matches.length}</strong> result${matches.length===1?'':'s'}${query?` for “${esc(query)}”`:''}`;
    if(!matches.length){results.innerHTML='<div class="search-empty"><strong>No archive matches.</strong>Try a broader term or clear one of the filters.</div>';return}
    results.innerHTML=matches.slice(0,100).map(({record})=>`<a class="search-result" data-result-type="${record.type}" href="${esc(record.href)}"><div class="result-main"><div class="result-topline"><span class="result-type">${labelType(record.type)}</span></div><h3>${esc(record.title)}</h3><div class="result-meta">${esc(record.meta)}</div></div><span class="result-arrow" aria-hidden="true">→</span></a>`).join('');
  }
  input.addEventListener('input',render);
  clear.addEventListener('click',()=>{input.value='';input.focus();render()});
  typeButtons.forEach(button=>button.addEventListener('click',()=>{setType(button.dataset.type);render()}));
  sportSelect.addEventListener('change',render);
  yearSelect.addEventListener('change',render);
  document.querySelector('#archive-search-form')?.addEventListener('submit',event=>event.preventDefault());
  render();
})();
