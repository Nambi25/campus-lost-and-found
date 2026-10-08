// CampusFind API client — talks to the FastAPI backend.
// Same exported functions as the old localStorage demo, so no page/component needs to change.
//
// In dev, Vite proxies /api and /uploads to http://localhost:8000 (see vite.config.js).
// To point at a backend elsewhere (e.g. a teammate's laptop), create frontend/.env with:
//   VITE_API_URL=http://192.168.1.25:8000

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const USER_KEY = 'campusfind.userId';
const NAME_KEY = 'campusfind.userName';

// Each browser gets a stable anonymous id (no login screen yet). The backend creates the user on first use.
function getOrCreateUserId() {
  try {
    let id = localStorage.getItem(USER_KEY);
    if (!id) {
      id = `browser-${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`;
      localStorage.setItem(USER_KEY, id);
    }
    return id;
  } catch {
    return `browser-${Math.random().toString(36).slice(2, 14)}`;
  }
}

export const DEMO_USER_ID = getOrCreateUserId();

function userName() {
  try { return localStorage.getItem(NAME_KEY) || ''; } catch { return ''; }
}

function rememberName(name) {
  try { if (name?.trim()) localStorage.setItem(NAME_KEY, name.trim()); } catch { /* ignore */ }
}

async function request(path, { method = 'GET', json, form, params } = {}) {
  const url = new URL(`${API_BASE}/api${path}`, window.location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && url.searchParams.set(k, v));

  const headers = { 'X-User-Id': DEMO_USER_ID };
  const name = userName();
  if (name) headers['X-User-Name'] = name;
  let body;
  if (json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); }
  if (form) body = form; // browser sets the multipart boundary itself

  let res;
  try {
    res = await fetch(url, { method, headers, body });
  } catch {
    throw new Error('Can’t reach the CampusFind server. Is the backend running on port 8000?');
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail) ? detail.map((d) => d.msg).join(' · ') : detail;
    const error = new Error(message || `Request failed (${res.status})`);
    error.status = res.status;
    throw error;
  }
  return data;
}

// Backend returns image paths like /uploads/abc.jpg — make them absolute when the API is on another host.
const withImage = (url) => (url && url.startsWith('/') ? `${API_BASE}${url}` : url);
const fixItem = (item) => item && { ...item, imageUrl: withImage(item.imageUrl) };

export async function listItems(filters = {}) {
  const items = await request('/items', {
    params: {
      query: (filters.query || '').trim(),
      kind: filters.kind || 'all',
      category: filters.category || 'all',
      location: filters.location || 'all',
      recency: filters.recency || 'all',
      claimState: filters.claimState || 'all',
    },
  });
  return items.map(fixItem);
}

export async function getItem(id) {
  try {
    return fixItem(await request(`/items/${encodeURIComponent(id)}`));
  } catch (error) {
    if (error.status === 404 || error.status === 422) return null;
    throw error;
  }
}

export async function createItem(input) {
  const form = new FormData();
  form.append('kind', input.kind);
  form.append('title', input.title);
  form.append('category', input.category);
  form.append('description', input.description);
  form.append('location', input.location);
  if (input.timestamp) form.append('timestamp', input.timestamp);
  if (input.imageUrl) {
    // ItemForm gives us a data: URL — turn it back into a file for upload
    const blob = await (await fetch(input.imageUrl)).blob();
    form.append('image', blob, input.imageName || `photo.${(blob.type.split('/')[1] || 'jpg')}`);
  }
  return fixItem(await request('/items', { method: 'POST', form }));
}

export async function createClaim(itemId, input) {
  rememberName(input.claimantName);
  return fixItem(await request(`/items/${itemId}/claims`, {
    method: 'POST',
    json: { claimantName: input.claimantName.trim(), details: input.details.trim() },
  }));
}

export async function updateClaimStatus(itemId, claimId, status) {
  return fixItem(await request(`/items/${itemId}/claims/${claimId}`, { method: 'PATCH', json: { status } }));
}

export async function updateItemStatus(itemId, status) {
  return fixItem(await request(`/items/${itemId}/status`, { method: 'PATCH', json: { status } }));
}

export async function getMyItems() {
  const data = await request('/items/mine');
  return {
    reports: data.reports.map(fixItem),
    claims: data.claims.map((claim) => ({ ...claim, itemImageUrl: withImage(claim.itemImageUrl) })),
  };
}

export async function findPotentialMatches(itemId) {
  try {
    const data = await request(`/items/${itemId}/matches`);
    return { mode: data.mode, matches: data.matches.map((m) => ({ ...m, item: fixItem(m.item) })) };
  } catch {
    return { mode: 'unavailable', matches: [] };
  }
}

export async function getBoardStats() {
  return request('/items/stats');
}

// Bonus: "find by photo" — not used by any page yet.
export async function searchByImage(file, { kind = 'found', category = 'Other', description = '' } = {}) {
  const form = new FormData();
  form.append('image', file);
  form.append('kind', kind);
  form.append('category', category);
  form.append('description', description);
  const matches = await request('/items/search-by-image', { method: 'POST', form });
  return matches.map((m) => ({ ...m, item: fixItem(m.item) }));
}
