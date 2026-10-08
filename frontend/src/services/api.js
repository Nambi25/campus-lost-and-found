const STORAGE_KEY = 'campusfind.demo.v1';
export const DEMO_USER_ID = 'demo-student';

function demoPhoto(emoji, color, accent, label) {
  const safeLabel = label.replace(/[<>&]/g, '');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 640"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${color}"/><stop offset="1" stop-color="#101a25"/></linearGradient><radialGradient id="r"><stop stop-color="${accent}" stop-opacity=".25"/><stop offset="1" stop-color="${accent}" stop-opacity="0"/></radialGradient></defs><rect width="900" height="640" fill="url(#g)"/><circle cx="660" cy="230" r="280" fill="url(#r)"/><path d="M0 490 250 390l170 63 210-164 270 101v250H0z" fill="#0c1420" fill-opacity=".5"/><path d="M67 80h140M67 92h85" stroke="${accent}" stroke-width="3" stroke-linecap="round" opacity=".62"/><text x="450" y="375" text-anchor="middle" font-size="180" font-family="sans-serif">${emoji}</text><text x="67" y="570" fill="#eef5f7" font-size="23" font-family="sans-serif" font-weight="700" letter-spacing="3">${safeLabel.toUpperCase()}</text><text x="830" y="92" text-anchor="end" fill="${accent}" font-size="15" font-family="sans-serif" font-weight="700" letter-spacing="3">CAMPUS FIND / DEMO</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function seedItems() {
  const now = Date.now();
  const hoursAgo = (hours) => new Date(now - hours * 60 * 60 * 1000).toISOString();
  return [
    {
      id: 'itm-101', kind: 'found', title: 'Lime-green pencil pouch', category: 'School supplies',
      description: 'Small zip pouch with a white star patch. Found near the long tables after afternoon classes.',
      location: 'Library · ground floor', eventAt: hoursAgo(4), reportedAt: hoursAgo(2), status: 'active',
      imageUrl: demoPhoto('✏️', '#263b38', '#a3ff12', 'Pencil pouch'), imageName: '', posterId: 'student-lee', posterName: 'Lee', claims: [],
    },
    {
      id: 'itm-102', kind: 'lost', title: 'Graphite scientific calculator', category: 'School supplies',
      description: 'Dark grey graphing calculator with a tiny triangle sticker near the solar panel. Last used around the west lecture wing.',
      location: 'West Hall · lecture wing', eventAt: hoursAgo(27), reportedAt: hoursAgo(9), status: 'active',
      imageUrl: demoPhoto('🧮', '#293447', '#76d6e7', 'Graphing calculator'), imageName: '', posterId: 'student-noah', posterName: 'Noah', claims: [],
    },
    {
      id: 'itm-103', kind: 'found', title: 'Wireless earbud charging case', category: 'Electronics',
      description: 'White oval case, no earbuds inside. Picked up beside the student union charging counter.',
      location: 'Student Union', eventAt: hoursAgo(8), reportedAt: hoursAgo(6), status: 'active',
      imageUrl: demoPhoto('🎧', '#34404a', '#a3ff12', 'Earbud case'), imageName: '', posterId: DEMO_USER_ID, posterName: 'You', claims: [],
    },
    {
      id: 'itm-104', kind: 'found', title: 'Canvas tote with blue notebook', category: 'Bags & accessories',
      description: 'Natural canvas tote with a blue spiral notebook. Found by the library north entrance; one stitched detail is being held back for verification.',
      location: 'Library · north entrance', eventAt: hoursAgo(31), reportedAt: hoursAgo(14), status: 'active',
      imageUrl: demoPhoto('👜', '#3b332e', '#ffca70', 'Canvas tote'), imageName: '', posterId: DEMO_USER_ID, posterName: 'You',
      claims: [{ id: 'clm-201', claimantId: 'student-mira', claimantName: 'Mira S.', details: 'There is a stitched wave on the inside pocket and a physics lab label on the notebook.', submittedAt: hoursAgo(3), status: 'pending' }],
    },
    {
      id: 'itm-105', kind: 'lost', title: 'Forest-green water bottle', category: 'Other',
      description: 'Metal bottle with a black lid and a few small climbing-sticker marks. Might have been left after practice.',
      location: 'Athletics Center', eventAt: hoursAgo(52), reportedAt: hoursAgo(18), status: 'active',
      imageUrl: demoPhoto('🧴', '#233d38', '#76d6e7', 'Water bottle'), imageName: '', posterId: 'student-jules', posterName: 'Jules', claims: [],
    },
    {
      id: 'itm-106', kind: 'found', title: 'Graphing calculator', category: 'School supplies',
      description: 'Dark calculator picked up by a lecture-room seat. There is a tiny triangle sticker near the solar strip.',
      location: 'West Hall · lecture wing', eventAt: hoursAgo(22), reportedAt: hoursAgo(4), status: 'active',
      imageUrl: demoPhoto('🧮', '#3a3430', '#ffca70', 'Found calculator'), imageName: '', posterId: 'student-rin', posterName: 'Rin', claims: [],
    },
  ];
}

function readItems() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (error) {
    console.warn('CampusFind local demo data could not be read.', error);
  }
  const items = seedItems();
  writeItems(items);
  return items;
}

function writeItems(items) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    throw new Error('Browser storage is full. Try a smaller photo or remove older demo reports.');
  }
}

function matchesRecency(item, recency) {
  if (recency === 'all') return true;
  const posted = new Date(item.reportedAt).getTime();
  const age = Date.now() - posted;
  const day = 24 * 60 * 60 * 1000;
  if (recency === 'today') return age <= day;
  if (recency === 'week') return age <= 7 * day;
  if (recency === 'month') return age <= 30 * day;
  return true;
}

export async function listItems(filters = {}) {
  const query = (filters.query || '').trim().toLowerCase();
  return readItems()
    .filter((item) => filters.kind === 'all' || !filters.kind || item.kind === filters.kind)
    .filter((item) => filters.category === 'all' || !filters.category || item.category === filters.category)
    .filter((item) => filters.location === 'all' || !filters.location || item.location.toLowerCase().includes(filters.location.toLowerCase()))
    .filter((item) => matchesRecency(item, filters.recency || 'all'))
    .filter((item) => {
      const pending = item.claims.some((claim) => claim.status === 'pending');
      const approved = item.claims.some((claim) => claim.status === 'approved');
      if (filters.claimState === 'none') return item.claims.length === 0;
      if (filters.claimState === 'pending') return pending;
      if (filters.claimState === 'approved') return approved;
      return true;
    })
    .filter((item) => !query || [item.title, item.description, item.location, item.category].some((text) => text.toLowerCase().includes(query)))
    .sort((a, b) => new Date(b.reportedAt) - new Date(a.reportedAt));
}

export async function getItem(id) {
  return readItems().find((item) => item.id === id) || null;
}

export async function createItem(input) {
  const items = readItems();
  const item = {
    id: `itm-${crypto.randomUUID()}`,
    kind: input.kind,
    title: input.title,
    category: input.category,
    description: input.description,
    location: input.location,
    eventAt: input.timestamp ? new Date(input.timestamp).toISOString() : new Date().toISOString(),
    reportedAt: new Date().toISOString(),
    status: 'active',
    imageUrl: input.imageUrl,
    imageName: input.imageName || '',
    posterId: DEMO_USER_ID,
    posterName: 'You',
    claims: [],
  };
  items.unshift(item);
  writeItems(items);
  return item;
}

export async function createClaim(itemId, input) {
  const items = readItems();
  const item = items.find((entry) => entry.id === itemId);
  if (!item) throw new Error('This report is no longer available.');
  if (item.status === 'resolved') throw new Error('This item has already been marked resolved.');
  const duplicate = item.claims.find((claim) => claim.claimantId === DEMO_USER_ID && claim.status === 'pending');
  if (duplicate) throw new Error('You already have a pending claim on this report.');
  const claim = {
    id: `clm-${crypto.randomUUID()}`,
    claimantId: DEMO_USER_ID,
    claimantName: input.claimantName.trim(),
    details: input.details.trim(),
    submittedAt: new Date().toISOString(),
    status: 'pending',
  };
  item.claims.unshift(claim);
  writeItems(items);
  return item;
}

export async function updateClaimStatus(itemId, claimId, status) {
  if (!['approved', 'rejected'].includes(status)) throw new Error('Unsupported claim decision.');
  const items = readItems();
  const item = items.find((entry) => entry.id === itemId);
  if (!item || item.posterId !== DEMO_USER_ID) throw new Error('Only the report owner can review claims.');
  const claim = item.claims.find((entry) => entry.id === claimId);
  if (!claim) throw new Error('This claim could not be found.');
  claim.status = status;
  claim.reviewedAt = new Date().toISOString();
  if (status === 'approved') {
    item.claims.forEach((other) => { if (other.id !== claimId && other.status === 'pending') other.status = 'rejected'; });
  }
  writeItems(items);
  return item;
}

export async function updateItemStatus(itemId, status) {
  if (!['active', 'resolved'].includes(status)) throw new Error('Unsupported report status.');
  const items = readItems();
  const item = items.find((entry) => entry.id === itemId);
  if (!item || item.posterId !== DEMO_USER_ID) throw new Error('Only the report owner can change this status.');
  item.status = status;
  item.updatedAt = new Date().toISOString();
  writeItems(items);
  return item;
}

export async function getMyItems() {
  const all = readItems();
  const reports = all.filter((item) => item.posterId === DEMO_USER_ID).sort((a, b) => new Date(b.reportedAt) - new Date(a.reportedAt));
  const claims = all.flatMap((item) => item.claims
    .filter((claim) => claim.claimantId === DEMO_USER_ID)
    .map((claim) => ({ ...claim, itemId: item.id, itemTitle: item.title, itemImageUrl: item.imageUrl, itemKind: item.kind, itemStatus: item.status })));
  return { reports, claims };
}

function words(text) {
  return new Set(text.toLowerCase().split(/[^a-z0-9]+/).filter((word) => word.length > 3));
}

export async function findPotentialMatches(itemId) {
  const items = readItems();
  const source = items.find((item) => item.id === itemId);
  if (!source) return { mode: 'local-demo-fallback', matches: [] };
  const sourceWords = words(`${source.title} ${source.description}`);
  const matches = items
    .filter((candidate) => candidate.id !== source.id && candidate.kind !== source.kind && candidate.status === 'active')
    .map((candidate) => {
      const candidateWords = words(`${candidate.title} ${candidate.description}`);
      const sharedWords = [...sourceWords].filter((word) => candidateWords.has(word));
      const sameCategory = source.category === candidate.category;
      const sameLocation = source.location.toLowerCase().split(/[·,]/)[0].trim() === candidate.location.toLowerCase().split(/[·,]/)[0].trim();
      const recencyBonus = Math.abs(new Date(source.eventAt) - new Date(candidate.eventAt)) < 7 * 24 * 60 * 60 * 1000 ? 0.07 : 0;
      const score = Math.min(0.97, 0.22 + (sameCategory ? 0.37 : 0) + (sameLocation ? 0.24 : 0) + Math.min(sharedWords.length, 4) * 0.06 + recencyBonus);
      const reasons = [sameCategory && 'same category', sameLocation && 'nearby campus spot', sharedWords.length > 0 && 'shared item details'].filter(Boolean);
      return { item: candidate, score, reason: reasons.join(' · ') || 'related campus report' };
    })
    .filter((entry) => entry.score >= 0.35)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);
  return { mode: 'local-demo-fallback', matches };
}

export async function getBoardStats() {
  const items = readItems();
  return {
    active: items.filter((item) => item.status === 'active').length,
    found: items.filter((item) => item.kind === 'found' && item.status === 'active').length,
    lost: items.filter((item) => item.kind === 'lost' && item.status === 'active').length,
    claims: items.reduce((total, item) => total + item.claims.filter((claim) => claim.status === 'pending').length, 0),
  };
}
