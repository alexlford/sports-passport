window.SportsPassportMedia=(()=>{
  const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const items=catalog=>Array.isArray(catalog)?catalog:(Array.isArray(catalog?.items)?catalog.items:[]);
  const mediaById=(catalog,id)=>id?items(catalog).find(item=>item.id===id)||null:null;
  const typeLabel=type=>({ticket_stub:'Ticket stub',credential:'Credential',program:'Program',seat_view:'Seat view',keepsake:'Keepsake',photo:'Photo'}[type]||'Archive artifact');
  const sourceOf=(item,format)=>(item?.sources||[]).find(source=>String(source.format||'').toLowerCase()===format)?.src||'';
  function picture(item,{className='archive-media-picture'}={}){
    if(!item?.src)return '';
    const avif=sourceOf(item,'avif'),webp=sourceOf(item,'webp');
    const dimensions=(Number(item.width)>0&&Number(item.height)>0)?` width="${Number(item.width)}" height="${Number(item.height)}"`:'';
    return `<picture class="${escapeHtml(className)}">${avif?`<source type="image/avif" srcset="${escapeHtml(avif)}">`:''}${webp?`<source type="image/webp" srcset="${escapeHtml(webp)}">`:''}<img src="${escapeHtml(item.src)}" alt="${escapeHtml(item.alt||'')}"${dimensions} loading="lazy" decoding="async"></picture>`;
  }
  function contextItems(catalog,context={}){
    const wanted={
      event_ids:context.eventIds||[],
      team_slugs:context.teamSlugs||[],
      venue_slugs:context.venueSlugs||[],
      phase_keys:context.phaseKeys||[],
      ranking_refs:context.rankingRefs||[]
    };
    return items(catalog).filter(item=>Object.entries(wanted).some(([key,values])=>values.length&&Array.isArray(item.contexts?.[key])&&item.contexts[key].some(value=>values.includes(value))));
  }
  function mediaCard(item){
    const visual=picture(item);
    if(!visual)return '';
    return `<article class="archive-evidence-card media-card"><div class="archive-evidence-visual">${visual}</div><div class="archive-evidence-body"><div class="archive-evidence-chip">Archive image</div>${item.caption?`<p>${escapeHtml(item.caption)}</p>`:''}${item.credit?`<p class="archive-evidence-provenance">${escapeHtml(item.credit)}</p>`:''}</div></article>`;
  }
  function artifactCard(artifact,catalog,{eventHref=''}={}){
    const media=mediaById(catalog,artifact?.media_id),visual=picture(media);
    return `<article class="archive-evidence-card artifact-card" data-artifact-id="${escapeHtml(artifact?.id||'')}">${visual?`<div class="archive-evidence-visual">${visual}</div>`:''}<div class="archive-evidence-body"><div class="archive-evidence-kicker">${escapeHtml(typeLabel(artifact?.type))}</div><h3>${escapeHtml(artifact?.title||'Archive artifact')}</h3><span class="archive-evidence-chip ${media?'digitized':'pending'}">${media?'Digitized source':'Physical artifact cataloged · image pending'}</span>${artifact?.summary?`<p>${escapeHtml(artifact.summary)}</p>`:''}${artifact?.provenance?`<p class="archive-evidence-provenance"><strong>Provenance:</strong> ${escapeHtml(artifact.provenance)}</p>`:''}${eventHref?`<a class="archive-evidence-link" href="${escapeHtml(eventHref)}">Open Event Passport →</a>`:''}</div></article>`;
  }
  return {items,mediaById,picture,contextItems,mediaCard,artifactCard,typeLabel};
})();
