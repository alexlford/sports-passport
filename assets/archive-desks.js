(()=>{
  const source=(window.SPORTS_ROUTE_SOURCE||'').toLowerCase();
  const path=location.pathname.toLowerCase();
  const key=source.includes('favorites')||path==='/favorites/'||path.endsWith('/favorites.html')?'canon':source.includes('lifetime-analytics')||path==='/analytics/'||path.endsWith('/lifetime-analytics.html')?'analytics':source.includes('hall-of-fame')||path==='/hall-of-fame/'||path.endsWith('/hall-of-fame.html')?'records':null;
  if(!key)return;

  const pages={
    canon:{title:'Personal Canon',summary:'Subjective rankings: the moments I would most want to relive and the venues I value most.',href:'/favorites/'},
    analytics:{title:'Analytics',summary:'Patterns and trends: how the archive changes across years, sports, teams, places, and life chapters.',href:'/analytics/'},
    records:{title:'Record Book',summary:'Objective record book: leaders, superlatives, and milestones calculated from confirmed/documented records.',href:'/hall-of-fame/'}
  };

  const render=()=>{
    if(document.querySelector('.archive-desk-guide'))return;
    const main=document.querySelector('main.shell,main.home-shell,main');
    if(!main)return;
    const header=main.querySelector('header');
    const guide=document.createElement('section');
    guide.className='archive-desk-guide';
    guide.setAttribute('aria-labelledby','archive-desk-guide-title');
    guide.innerHTML=`<div class="archive-desk-kicker">Three complementary archive desks</div><h2 id="archive-desk-guide-title">Different questions, different lenses.</h2><p>Personal Canon is editorial, Analytics explains patterns, and Record Book is the objective record book. None of the three replaces the underlying Event Passports, annual editions, team dossiers, or venue profiles.</p><nav class="archive-desk-links" aria-label="Archive desk guide">${Object.entries(pages).map(([id,page])=>`<a class="archive-desk-link" href="${page.href}"${id===key?' aria-current="page"':''}><strong>${page.title}</strong><span>${page.summary}</span></a>`).join('')}</nav>`;
    if(header)header.insertAdjacentElement('afterend',guide);else main.prepend(guide);
  };

  const link=document.createElement('link');
  link.rel='stylesheet';
  link.href='/assets/archive-desks.css';
  link.dataset.sportsPassportArchiveDesks='true';
  if(!document.querySelector('link[data-sports-passport-archive-desks]'))document.head.appendChild(link);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',render,{once:true});else render();
})();
