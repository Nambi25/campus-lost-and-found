const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const AUTH_KEY = 'campusfind.auth.v2';
export const DEMO_EMAIL = 'demo@campusfind.app';
export const DEMO_PASSWORD = 'CampusFind123!';

export const DEMO_USER_ID = 'demo-student';

const CATEGORY_TO_API = {
  'Electronics': 'electronics',
  'School supplies': 'calculator',
  'Bags & accessories': 'bag',
  'Clothing': 'clothing',
  'Keys & cards': 'keys',
  'Other': 'other',
};
const CATEGORY_FROM_API = Object.fromEntries(
  Object.entries(CATEGORY_TO_API).map(([label, value]) => [value, label]),
);

function imageUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path) || path.startsWith('data:')) return path;
  return `${API_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

function friendlyStatus(status) {
  return status === 'returned' ? 'resolved' : 'active';
}

function mapItem(raw) {
  if (!raw) return null;
  return {
    id: String(raw.id),
    kind: raw.type,
    title: raw.title,
    category: CATEGORY_FROM_API[raw.category] || raw.category || 'Other',
    description: raw.description || '',
    location: raw.location || '',
    eventAt: raw.event_time,
    reportedAt: raw.created_at,
    status: friendlyStatus(raw.status),
    backendStatus: raw.status,
    imageUrl: imageUrl(raw.image_url),
    imageName: '',
    posterId: String(raw.reporter_id),
    posterName: raw.reporter_name || 'Campus student',
    verificationQuestion: raw.verification_question || '',
    claims: raw.claims || [],
  };
}

function mapClaim(raw) {
  return {
    id: String(raw.id),
    itemId: String(raw.item_id),
    claimantId: String(raw.claimant_id),
    claimantName: raw.claimant_name || 'Campus student',
    details: raw.proof_details || raw.answer || '',
    answer: raw.answer || '',
    submittedAt: raw.created_at,
    resolvedAt: raw.resolved_at,
    handoverCode: raw.handover_code || null,
    status: raw.status,
  };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof body === 'object' && body?.detail
      ? (Array.isArray(body.detail) ? body.detail.map((e) => e.msg).join(', ') : body.detail)
      : `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return body;
}

export function getStoredAuth() {
  try {
    const saved = localStorage.getItem(AUTH_KEY);
    if (!saved) return null;
    const auth = JSON.parse(saved);
    return auth?.token && auth?.user ? auth : null;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  return Boolean(getStoredAuth());
}

export function signOut() {
  localStorage.removeItem(AUTH_KEY);
}

export async function signUp({ name, email, password, rollNo = '', phone = '' }) {
  const auth = await request('/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: name.trim(),
      email: email.trim(),
      password,
      roll_no: rollNo.trim() || null,
      phone: phone.trim() || null,
    }),
  });
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  return auth;
}

export async function signIn(email, password) {
  const auth = await request('/users/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  return auth;
}

export async function demoSignIn() {
  const auth = await request('/users/demo-login', {
    method: 'POST',
  });
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  return auth;
}

async function ensureAuth(forceNew = false) {
  if (forceNew) localStorage.removeItem(AUTH_KEY);
  const saved = localStorage.getItem(AUTH_KEY);
  if (saved) {
    try {
      const auth = JSON.parse(saved);
      if (auth?.token && auth?.user) return auth;
    } catch {
      localStorage.removeItem(AUTH_KEY);
    }
  }

  const id = crypto.randomUUID();
  const email = `demo-${id}@campusfind.app`;
  const password = `CampusFind-${id}`;
  const auth = await request('/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Campus Student',
      email,
      password,
      roll_no: null,
      phone: null,
    }),
  });
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  return auth;
}

async function authRequest(path, options = {}) {
  let auth = await ensureAuth();
  let headers = new Headers(options.headers || {});
  headers.set('Authorization', `Bearer ${auth.token}`);

  try {
    return await request(path, { ...options, headers });
  } catch (error) {
    // The backend stores the demo token in its database. If that database was
    // reset/recreated, the browser may still hold an old token. Refresh the
    // demo identity once and retry instead of showing "Invalid token".
    if (error?.status !== 401) throw error;

    auth = await ensureAuth(true);
    headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${auth.token}`);
    return request(path, { ...options, headers });
  }
}

export async function listItems(filters = {}) {
  const params = new URLSearchParams();
  if (filters.query?.trim()) params.set('q', filters.query.trim());
  if (filters.kind && filters.kind !== 'all') params.set('type', filters.kind);
  if (filters.category && filters.category !== 'all') {
    params.set('category', CATEGORY_TO_API[filters.category] || filters.category);
  }
  if (filters.location && filters.location !== 'all') params.set('location', filters.location);
  params.set('limit', '100');

  const rows = await request(`/items?${params.toString()}`);
  let items = rows.map(mapItem);

  const now = Date.now();
  const days = { today: 1, week: 7, month: 30 };
  if (filters.recency !== 'all' && days[filters.recency]) {
    const cutoff = now - days[filters.recency] * 86400000;
    items = items.filter((item) => new Date(item.reportedAt).getTime() >= cutoff);
  }

  if (filters.claimState && filters.claimState !== 'all') {
    const withClaims = await Promise.all(items.map(async (item) => {
      const claims = await authRequest(`/claims/item/${item.id}`).catch(() => []);
      return { item, claims: claims.map(mapClaim) };
    }));
    items = withClaims
      .filter(({ claims }) => {
        if (filters.claimState === 'none') return claims.length === 0;
        if (filters.claimState === 'pending') return claims.some((c) => c.status === 'pending');
        if (filters.claimState === 'approved') return claims.some((c) => c.status === 'approved');
        return true;
      })
      .map(({ item, claims }) => ({ ...item, claims }));
  }

  return items.sort((a, b) => new Date(b.reportedAt) - new Date(a.reportedAt));
}

export async function getItem(id) {
  const raw = await request(`/items/${encodeURIComponent(id)}`);
  const item = mapItem(raw);
  const auth = await ensureAuth();
  const isOwner = String(raw.reporter_id) === String(auth.user.id);
  let claims = [];
  if (isOwner) {
    claims = (await authRequest(`/claims/item/${id}`)).map(mapClaim);
  } else {
    claims = (await authRequest('/claims/mine'))
      .map(mapClaim)
      .filter((claim) => claim.itemId === String(id));
  }
  return {
    ...item,
    posterId: isOwner ? DEMO_USER_ID : item.posterId,
    claims: claims.map((claim) => (
      String(claim.claimantId) === String(auth.user.id)
        ? { ...claim, claimantId: DEMO_USER_ID }
        : claim
    )),
  };
}

export async function createItem(input) {
  const form = new FormData();
  form.set('type', input.kind);
  form.set('title', input.title.trim());
  form.set('category', CATEGORY_TO_API[input.category] || 'other');
  form.set('description', input.description.trim());
  form.set('location', input.location.trim());
  if (input.timestamp) {
    // datetime-local has no timezone. The form is intentionally shown in IST
    // for CampusFind, so convert the selected IST clock time to a UTC ISO value
    // before sending it to the backend.
    const [datePart, timePart] = input.timestamp.split('T');
    const [year, month, day] = datePart.split('-').map(Number);
    const [hour, minute] = timePart.split(':').map(Number);
    const istAsUtc = new Date(Date.UTC(year, month - 1, day, hour, minute) - (5.5 * 60 * 60 * 1000));
    form.set('event_time', istAsUtc.toISOString());
  }
  if (input.imageFile) form.set('image', input.imageFile, input.imageFile.name);
  const raw = await authRequest('/items', { method: 'POST', body: form });
  return mapItem(raw);
}

export async function createClaim(itemId, input) {
  const raw = await authRequest('/claims', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      item_id: Number(itemId),
      answer: '',
      proof_details: input.details.trim(),
    }),
  });
  return mapClaim(raw);
}

export async function updateClaimStatus(itemId, claimId, status) {
  const action = status === 'approved' ? 'approve' : 'reject';
  const raw = await authRequest(`/claims/${claimId}/${action}`, { method: 'POST' });
  return mapClaim(raw);
}

export async function updateItemStatus(itemId, status) {
  const backendStatus = status === 'resolved' ? 'returned' : 'open';
  const form = new FormData();
  form.set('status', backendStatus);
  const raw = await authRequest(`/items/${itemId}/status`, { method: 'PATCH', body: form });
  return mapItem(raw);
}

export async function getMyItems() {
  const [rawReports, rawClaims] = await Promise.all([
    authRequest('/items/mine'),
    authRequest('/claims/mine'),
  ]);

  const reports = await Promise.all(rawReports.map(async (raw) => {
    const item = mapItem(raw);
    const claims = await authRequest(`/claims/item/${raw.id}`).catch(() => []);
    return { ...item, claims: claims.map(mapClaim) };
  }));

  const auth = await ensureAuth();
  return {
    reports: reports.map((report) => ({ ...report, posterId: DEMO_USER_ID })),
    claims: rawClaims.map(mapClaim).map((claim) => ({
      ...claim,
      claimantId: DEMO_USER_ID,
    })).map((claim) => {
      const item = reports.find((report) => String(report.id) === String(claim.itemId));
      return {
        ...claim,
        itemTitle: item?.title || 'Campus item',
        itemImageUrl: item?.imageUrl || '',
        itemKind: item?.kind || 'found',
        itemStatus: item?.status || 'active',
      };
    }),
  };
}

export async function findPotentialMatches(itemId) {
  const raw = await request(`/items/${itemId}/matches?limit=5`);
  return {
    mode: 'backend-image-and-text-matching',
    matches: raw.map((entry) => ({
      item: mapItem(entry.item),
      score: entry.score,
      reason: entry.image_score != null
        ? `photo similarity ${Math.round(entry.image_score * 100)}% · text ${Math.round(entry.text_score * 100)}%`
        : `text/category similarity ${Math.round(entry.text_score * 100)}%`,
    })),
  };
}

export async function getBoardStats() {
  return request('/items/stats');
}

export async function getCurrentUser() {
  return (await ensureAuth()).user;
}
