(() => {
  const ORIGIN = 'https://sports.alexlford.com';
  const SOCIAL_IMAGE = `${ORIGIN}/assets/social-card.svg`;

  function upsertMeta(attribute, key, content) {
    let node = document.head.querySelector(`meta[${attribute}="${key}"]`);
    if (!node) {
      node = document.createElement('meta');
      node.setAttribute(attribute, key);
      document.head.appendChild(node);
    }
    node.setAttribute('content', content);
  }

  function addJsonLd(id, value) {
    let script = document.head.querySelector(`script[type="application/ld+json"][data-seo-id="${id}"]`);
    if (!script) {
      script = document.createElement('script');
      script.type = 'application/ld+json';
      script.dataset.seoId = id;
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify(value);
  }

  const canonicalPath = () => window.SPORTS_ROUTE_PUBLIC_URL || location.pathname;
  const absolute = path => new URL(path, ORIGIN).href;

  function breadcrumbName(part, index, parts) {
    const section = {
      years: 'Years', events: 'Events', teams: 'Teams', venues: 'Places', geography: 'Places',
      journeys: 'Life Chapters', chapters: 'Life Chapters', favorites: 'Personal Canon',
      analytics: 'Analytics', 'hall-of-fame': 'Hall of Fame', search: 'Search', about: 'About'
    }[part];
    if (section) return section;
    if (index === parts.length - 1) {
      const h1 = document.querySelector('h1');
      if (h1?.textContent?.trim()) return h1.textContent.trim().replace(/\s+/g, ' ');
    }
    return part.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function addGlobalSchemas() {
    addJsonLd('website', {
      '@context': 'https://schema.org', '@type': 'WebSite',
      '@id': `${ORIGIN}/#website`, url: `${ORIGIN}/`, name: 'Sports Passport',
      description: 'Alex Ford’s personal archive of live sports.',
      author: { '@id': 'https://www.alexlford.com/#person' },
      potentialAction: {
        '@type': 'SearchAction', target: `${ORIGIN}/search/?q={search_term_string}`,
        'query-input': 'required name=search_term_string'
      }
    });
    addJsonLd('person', {
      '@context': 'https://schema.org', '@type': 'Person',
      '@id': 'https://www.alexlford.com/#person', name: 'Alex Ford', url: 'https://www.alexlford.com/'
    });

    const parts = canonicalPath().split('/').filter(Boolean);
    const items = [{ '@type': 'ListItem', position: 1, name: 'Sports Passport', item: `${ORIGIN}/` }];
    parts.forEach((part, index) => {
      const path = '/' + parts.slice(0, index + 1).map(encodeURIComponent).join('/') + '/';
      items.push({ '@type': 'ListItem', position: index + 2, name: breadcrumbName(part, index, parts), item: absolute(path) });
    });
    if (items.length > 1) addJsonLd('breadcrumbs', { '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: items });
  }

  async function addRouteSchema() {
    const D = window.SportsPassportData;
    if (!D?.load) return;
    const parts = canonicalPath().split('/').filter(Boolean).map(decodeURIComponent);
    if (parts[0] === 'events' && parts[1]) {
      const events = await D.load('events');
      const event = events.find(e => String(e.id) === parts[1]);
      if (!event) return;
      if (D.isNotionalEvent(event)) {
        upsertMeta('name', 'robots', 'noindex,follow');
        return;
      }
      const venues = await D.load('venues');
      const venue = D.venueByKey(venues, event.venue_key);
      addJsonLd('sports-event', {
        '@context': 'https://schema.org', '@type': 'SportsEvent',
        '@id': `${ORIGIN}/events/${encodeURIComponent(event.id)}/#event`,
        url: `${ORIGIN}/events/${encodeURIComponent(event.id)}/`,
        name: D.matchup(event), startDate: event.date,
        eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
        location: venue ? {
          '@type': 'Place', name: venue.display_name,
          address: { '@type': 'PostalAddress', addressLocality: venue.city || event.city || '' }
        } : { '@type': 'Place', name: event.venue_recorded || 'Venue', address: event.city || '' },
        competitor: D.eventTeams(event).map(name => ({ '@type': 'SportsTeam', name }))
      });
    }
    if (parts[0] === 'venues' && parts[1]) {
      const venues = await D.load('venues');
      const venue = venues.find(v => v.slug === parts[1]);
      if (!venue) return;
      const place = {
        '@context': 'https://schema.org', '@type': 'Place',
        '@id': `${ORIGIN}/venues/${encodeURIComponent(venue.slug)}/#place`,
        url: `${ORIGIN}/venues/${encodeURIComponent(venue.slug)}/`, name: venue.display_name,
        address: { '@type': 'PostalAddress', addressLocality: venue.city || '' }
      };
      if (Number.isFinite(venue.latitude) && Number.isFinite(venue.longitude)) {
        place.geo = { '@type': 'GeoCoordinates', latitude: venue.latitude, longitude: venue.longitude };
      }
      addJsonLd('place', place);
    }
  }

  function boot() {
    upsertMeta('property', 'og:image', SOCIAL_IMAGE);
    upsertMeta('property', 'og:image:alt', 'Sports Passport — Alex Ford’s live sports archive');
    upsertMeta('name', 'twitter:image', SOCIAL_IMAGE);
    upsertMeta('name', 'twitter:card', 'summary_large_image');
    addGlobalSchemas();
    addRouteSchema().catch(() => {});
  }

  window.SportsPassportSeo = { addJsonLd, addGlobalSchemas, addRouteSchema };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
