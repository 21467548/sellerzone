// ============================================================
// SellerZone — Complete Frontend Script
// Backend: Flask + MongoDB
// ============================================================

const API_BASE = window.API_BASE || '/api';

// ---------- SVG Icons ----------
const ICONS = {
  all: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  ring_cat: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><circle cx="12" cy="15" r="6"/><path d="M9 9l3-6 3 6"/></svg>`,
  watch_cat: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><circle cx="12" cy="12" r="6"/><path d="M12 9v3l2 2M9 2h6M9 22h6"/></svg>`,
  cosmetic_cat: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><rect x="8" y="8" width="8" height="13" rx="2"/><path d="M10 8V5a2 2 0 0 1 4 0v3"/></svg>`,
  lingerie_cat: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><path d="M4 6c2 3 4 4 8 4s6-1 8-4M4 6l2 13h12l2-13"/></svg>`,
  device_cat: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="3"/></svg>`,
  home_cat: `<svg viewBox="0 0 24 24" fill="none" stroke="#EE4D2D" stroke-width="2"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>`,
};

function catIconFor(k) {
  const map = { all:'all', ring:'ring_cat', watch:'watch_cat', cosmetic:'cosmetic_cat', lingerie:'lingerie_cat', device:'device_cat', home:'home_cat' };
  return ICONS[map[k]] || ICONS.all;
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function imageUrl(src) {
  const value = String(src || '').trim();
  if (!value) return '';
  if (value.startsWith('data:') || value.startsWith('blob:')) return value;
  if (value.startsWith('/') || value.startsWith('./')) return value;
  if (value.startsWith('//')) return `${location.protocol}${value}`;
  return value;
}

function imageProxyUrl(src) {
  const value = String(src || '').trim();
  if (!/^https?:\/\//i.test(value)) return '';
  return `${API_BASE}/image?url=${encodeURIComponent(value)}`;
}

function localProductImage(key) {
  const map = {
    webcam: 'webcam', ring: 'ring', cosmetic_serum: 'cosmetic_serum',
    watch_smart: 'watch_smart', watch_leather: 'watch_leather',
    travelbed: 'travelbed', device_cat: 'device_cat', cosmetic_cream: 'cosmetic_cream'
  };
  return `/images/products/${map[key] || 'all'}.svg`;
}

function handleImageError(img) {
  const proxy = img.dataset.proxy || '';
  const local = img.dataset.local || '/images/products/all.svg';
  if (proxy && img.dataset.fallback !== 'proxy') {
    img.dataset.fallback = 'proxy';
    img.src = proxy;
    return;
  }
  if (local && img.dataset.fallback !== 'local') {
    img.dataset.fallback = 'local';
    img.src = local;
    return;
  }
  img.onerror = null;
  img.src = '/images/products/all.svg';
}

function imageTag(src, alt = '', localFallback = '/images/products/all.svg') {
  const original = String(src || '').trim();
  const url = imageUrl(original) || localFallback;
  const proxy = imageProxyUrl(original);
  return `<img src="${escapeHtml(url)}" alt="${escapeHtml(alt)}" loading="lazy"
    data-proxy="${escapeHtml(proxy)}" data-local="${escapeHtml(localFallback)}"
    onerror="handleImageError(this)">`;
}

function productThumb(p) {
  const local = localProductImage(p.icon_key || p.iconKey);
  return imageTag(p.image, p.name, local);
}

// ---------- State ----------
let products = [];
let cart = [];
let wishlist = [];
let orders = [];
let addresses = [];
let messages = [];
let currentUser = null;
let token = localStorage.getItem('bz_token') || null;
let inviteCode = localStorage.getItem('bz_invite') || null;

// ---------- API Helper ----------
async function api(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method, headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function formatPrice(n) {
  return 'R$ ' + Number(n || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
}

// ============================================================
// NAVIGATION
// ============================================================
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(`screen-${name}`);
  if (!el) return;
  el.classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.screen === name));
  window.scrollTo(0, 0);

  if (name === 'orders') loadOrders();
  if (name === 'cart') renderCartFull();
  if (name === 'account') renderAccount();
  if (name === 'invite') renderInvite();
  if (name === 'addresses') loadAddresses();
  if (name === 'service') loadMessages();
  if (name === 'recharge') renderRecharge();
  if (name === 'withdraw') renderWithdraw();
}

document.getElementById('bottomNav')?.addEventListener('click', (e) => {
  const btn = e.target.closest('.nav-btn');
  if (!btn) return;
  const t = btn.dataset.screen;
  if ((t === 'cart' || t === 'orders' || t === 'account') && !isLoggedIn()) {
    showScreen('login');
    return;
  }
  showScreen(t);
});

document.querySelectorAll('[data-back]').forEach(b => {
  b.addEventListener('click', () => showScreen(b.dataset.back));
});

document.getElementById('moreBtn')?.addEventListener('click', () => {
  document.getElementById('goodsGrid').innerHTML = products.map(p => cardHTML(p)).join('');
  bindCardEvents(document.getElementById('goodsGrid'));
  showScreen('goods');
});

// Me screen buttons
document.getElementById('meOrders')?.addEventListener('click', () => showScreen('orders'));
document.getElementById('meInvite')?.addEventListener('click', () => showScreen('invite'));
document.getElementById('meHelp')?.addEventListener('click', () => showScreen('whyus'));
document.getElementById('quickRecharge')?.addEventListener('click', () => showScreen('recharge'));
document.getElementById('quickWithdraw')?.addEventListener('click', () => showScreen('withdraw'));
document.getElementById('quickAddress')?.addEventListener('click', () => showScreen('addresses'));
document.getElementById('meService')?.addEventListener('click', () => showScreen('service'));
document.getElementById('meWithdrawRecord')?.addEventListener('click', () => showScreen('withdraw'));
document.getElementById('meRechargeRecord')?.addEventListener('click', () => showScreen('recharge'));
document.getElementById('meAccountChange')?.addEventListener('click', () => alert('Account change history'));

// Drawer
document.getElementById('menuBtn')?.addEventListener('click', () => {
  document.getElementById('drawerOverlay').classList.add('open');
});
document.getElementById('drawerClose')?.addEventListener('click', () => {
  document.getElementById('drawerOverlay').classList.remove('open');
});
document.getElementById('drawerOverlay')?.addEventListener('click', (e) => {
  if (e.target.id === 'drawerOverlay') e.currentTarget.classList.remove('open');
});
document.getElementById('drawerLogout')?.addEventListener('click', logout);
document.getElementById('drawerWallet')?.addEventListener('click', () => {
  document.getElementById('drawerOverlay').classList.remove('open');
  showScreen('recharge');
});
document.getElementById('drawerShipping')?.addEventListener('click', () => {
  document.getElementById('drawerOverlay').classList.remove('open');
  showScreen('addresses');
});
document.getElementById('drawerId')?.addEventListener('click', () => alert('ID verification coming soon'));
document.getElementById('drawerCancel')?.addEventListener('click', () => alert('Account cancellation'));

// Auth switch
document.getElementById('goSignup')?.addEventListener('click', () => showScreen('signup'));
document.getElementById('goSignin')?.addEventListener('click', () => showScreen('login'));

// ============================================================
// HERO SLIDER — Auto slide + dots + swipe
// ============================================================
(function heroSlider() {
  const slides = document.querySelectorAll('.hero-slide');
  const dots = document.querySelectorAll('#heroDots span');
  if (!slides.length) return;

  let current = 0;
  let interval;

  function goTo(index) {
    slides.forEach((s, i) => s.classList.toggle('active', i === index));
    dots.forEach((d, i) => d.classList.toggle('active', i === index));
    current = index;
  }

  function next() {
    goTo((current + 1) % slides.length);
  }

  function start() {
    stop();
    interval = setInterval(next, 4000);
  }

  function stop() {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  }

  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => {
      stop();
      goTo(i);
      start();
    });
  });

  let startX = 0;
  const slider = document.getElementById('heroSlider');
  if (slider) {
    slider.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      stop();
    }, { passive: true });

    slider.addEventListener('touchend', (e) => {
      const diff = e.changedTouches[0].clientX - startX;
      if (Math.abs(diff) > 50) {
        if (diff > 0) goTo((current - 1 + slides.length) % slides.length);
        else goTo((current + 1) % slides.length);
      }
      start();
    });

    slider.addEventListener('mouseenter', stop);
    slider.addEventListener('mouseleave', start);
  }

  goTo(0);
  start();
})();

// ============================================================
// LANGUAGE
// ============================================================
document.getElementById('langToggle')?.addEventListener('click', (e) => {
  e.stopPropagation();
  document.getElementById('langDropdown').classList.toggle('open');
});
document.getElementById('langDropdown')?.addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  document.querySelectorAll('.lang-dropdown button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  document.getElementById('langLabel').textContent = b.dataset.lang;
  document.getElementById('langDropdown').classList.remove('open');
});
document.addEventListener('click', () => document.getElementById('langDropdown')?.classList.remove('open'));

// ============================================================
// PRODUCTS
// ============================================================
document.querySelectorAll('.cat-icon').forEach(el => {
  el.innerHTML = catIconFor(el.dataset.icon);
});

document.querySelectorAll('.cat-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.cat-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadProducts(btn.dataset.cat);
  });
});

async function loadProducts(category = 'all') {
  const grid = document.getElementById('productGrid');
  if (!grid) return;
  grid.innerHTML = `<div class="loading-note">Loading products…</div>`;
  try {
    const q = category !== 'all' ? `?category=${encodeURIComponent(category)}` : '';
    const data = await api(`/products${q}`);
    products = data.products || [];
    renderGrid();
  } catch (err) {
    grid.innerHTML = `<div class="loading-note">Backend not reachable at ${API_BASE}<br>${err.message}</div>`;
  }
}

function cardHTML(p) {
  return `
    <div class="p-card" data-id="${p.id}">
      <div class="p-thumb">
        ${p.tag ? `<span class="p-tag">${escapeHtml(p.tag)}</span>` : ''}
        <button class="p-wish ${wishlist.includes(p.id) ? 'active' : ''}" data-wish="${p.id}">
          <svg viewBox="0 0 24 24"><path d="M12 21s-7-4.4-9.5-9C.7 8.3 2.5 4 6.3 4 9 4 11 6 12 7.5 13 6 15 4 17.7 4 21.5 4 23.3 8.3 21.5 12 19 16.6 12 21 12 21z"/></svg>
        </button>
        ${productThumb(p)}
      </div>
      <div class="p-info">
        <div class="p-name">${escapeHtml(p.name)}</div>
        <div class="p-price">${formatPrice(p.price)}</div>
      </div>
    </div>`;
}

function bindCardEvents(grid) {
  grid.querySelectorAll('.p-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('.p-wish')) return;
      openProductDetail(Number(card.dataset.id));
    });
  });
  grid.querySelectorAll('.p-wish').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleWishlist(Number(btn.dataset.wish));
    });
  });
}

function renderGrid() {
  const grid = document.getElementById('productGrid');
  if (!grid) return;
  if (!products.length) {
    grid.innerHTML = `<div class="loading-note">No products yet.</div>`;
    return;
  }
  grid.innerHTML = products.map(cardHTML).join('');
  bindCardEvents(grid);
}

function openProductDetail(id) {
  const p = products.find(x => x.id === id);
  if (!p) return;
  const container = document.getElementById('productDetail');
  container.innerHTML = `
    <div class="p-detail-img">${productThumb(p)}</div>
    <div class="p-detail-body">
      <div class="p-detail-price">${formatPrice(p.price)}</div>
      <div class="p-detail-name">${escapeHtml(p.name)}</div>
      <div class="p-detail-desc">${escapeHtml(p.description || '')}</div>
      <div class="p-detail-qty">
        <span style="font-size:12px;color:#666;">Quantity:</span>
        <button class="qty-btn" id="qtyMinus">−</button>
        <span class="qty-value" id="qtyValue">1</span>
        <button class="qty-btn" id="qtyPlus">+</button>
      </div>
    </div>
    <div class="detail-actions">
      <button class="add-cart-btn" id="pdAdd">Add to cart</button>
      <button class="buy-btn" id="pdBuy">Buy now</button>
    </div>
  `;
  let qty = 1;
  document.getElementById('qtyMinus').addEventListener('click', () => {
    if (qty > 1) { qty--; document.getElementById('qtyValue').textContent = qty; }
  });
  document.getElementById('qtyPlus').addEventListener('click', () => {
    qty++; document.getElementById('qtyValue').textContent = qty;
  });
  document.getElementById('pdAdd').addEventListener('click', async () => {
    await addToCart(id, qty);
    document.getElementById('pdAdd').textContent = 'Added ✓';
    setTimeout(() => document.getElementById('pdAdd').textContent = 'Add to cart', 1200);
  });
  document.getElementById('pdBuy').addEventListener('click', async () => {
    const ok = await addToCart(id, qty);
    if (ok) showScreen('cart');
  });
  showScreen('product');
}

// ============================================================
// AUTH
// ============================================================
function isLoggedIn() { return !!token; }

function setSession(t, u) {
  token = t;
  currentUser = u;
  localStorage.setItem('bz_token', t);
  localStorage.setItem('bz_user', JSON.stringify(u));
}

function logout() {
  token = null; currentUser = null; cart = []; wishlist = []; orders = [];
  localStorage.removeItem('bz_token');
  localStorage.removeItem('bz_user');
  updateCartBadge();
  showScreen('home');
  renderAccount();
}

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const data = await api('/auth/login', { method: 'POST', body: { email, password } });
    setSession(data.token, data.user);
    await afterLogin();
    showScreen('account');
  } catch (err) { alert(err.message); }
});

document.getElementById('signupForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const p1 = document.getElementById('signupPassword').value;
  const p2 = document.getElementById('signupPassword2').value;
  if (p1 !== p2) return alert('Passwords do not match');
  try {
    const body = {
      name: document.getElementById('signupName').value,
      email: document.getElementById('signupEmail').value,
      password: p1,
      inviteCode: document.getElementById('signupInvite').value || null,
    };
    const data = await api('/auth/register', { method: 'POST', body });
    if (data.requiresConfirmation || !data.token) {
      return alert(data.message || 'Check your email to confirm your account, then sign in.');
    }
    setSession(data.token, data.user);
    await afterLogin();
    showScreen('account');
  } catch (err) { alert(err.message); }
});

async function afterLogin() {
  await Promise.all([loadCart(), loadWishlist(), loadAddresses()]);
  renderAccount();
  renderGrid();
  updateCartBadge();
}

function renderAccount() {
  const nameEl = document.getElementById('meName');
  const balEl = document.getElementById('meBalance');
  const ptEl = document.getElementById('mePoints');
  if (!nameEl) return;
  if (currentUser) {
    nameEl.textContent = currentUser.name;
    balEl.textContent = formatPrice(currentUser.balance);
    ptEl.textContent = currentUser.points;
  } else {
    nameEl.textContent = 'Not signed in';
    balEl.textContent = 'R$ 0.00';
    ptEl.textContent = '0';
  }
}

// ============================================================
// CART
// ============================================================
async function loadCart() {
  if (!isLoggedIn()) { cart = []; updateCartBadge(); return; }
  try {
    const data = await api('/cart', { auth: true });
    cart = data.items || [];
  } catch (err) { cart = []; }
  updateCartBadge();
}

async function addToCart(productId, qty = 1) {
  if (!isLoggedIn()) { showScreen('login'); return false; }
  try {
    const data = await api('/cart', { method: 'POST', auth: true, body: { productId, qty } });
    cart = data.items || [];
    updateCartBadge();
    return true;
  } catch (err) { alert(err.message); return false; }
}

async function removeFromCart(productId) {
  try {
    const data = await api(`/cart/${productId}`, { method: 'DELETE', auth: true });
    cart = data.items || [];
    updateCartBadge();
    renderCartFull();
  } catch (err) { alert(err.message); }
}

function updateCartBadge() {
  const badge = document.getElementById('navCartBadge');
  if (!badge) return;
  const count = cart.reduce((n, i) => n + i.qty, 0);
  badge.textContent = count;
  badge.style.display = count > 0 ? 'flex' : 'none';
}

function renderCartFull() {
  const el = document.getElementById('cartItemsFull');
  if (!el) return;
  if (!cart.length) {
    el.innerHTML = `<div class="cart-empty"><div class="empty-icon">📄</div>No data</div>`;
  } else {
    el.innerHTML = cart.map(i => `
      <div class="cart-row">
        <div class="c-thumb">${imageTag(i.image, i.name, localProductImage(i.iconKey))}</div>
        <div style="flex:1;">
          <div class="c-name">${escapeHtml(i.name)}</div>
          <div class="c-meta">Qty ${i.qty}</div>
          <button class="c-remove" data-id="${i.productId}">Delete</button>
        </div>
        <div class="p-price">${formatPrice(i.price * i.qty)}</div>
      </div>
    `).join('');
    el.querySelectorAll('.c-remove').forEach(b => b.addEventListener('click', () => removeFromCart(Number(b.dataset.id))));
  }
  const subtotal = cart.reduce((s, i) => s + i.price * i.qty, 0);
  document.getElementById('cartSubtotal').textContent = formatPrice(subtotal);
}

document.getElementById('goCheckoutBtn')?.addEventListener('click', async () => {
  if (!cart.length) return alert('Cart is empty');
  try {
    const user = currentUser || {};
    const body = {
      name: user.name || '',
      email: user.email || '',
      address: addresses[0]?.address || '',
      city: addresses[0]?.city || '',
      postal: addresses[0]?.postal || '',
    };
    const data = await api('/orders', { method: 'POST', auth: true, body });
    currentUser = data.user;
    localStorage.setItem('bz_user', JSON.stringify(currentUser));
    cart = [];
    updateCartBadge();
    renderCartFull();
    renderAccount();
    alert(`Order #${data.order.id} placed!`);
    showScreen('orders');
  } catch (err) { alert(err.message); }
});

// ============================================================
// WISHLIST
// ============================================================
async function loadWishlist() {
  if (!isLoggedIn()) { wishlist = []; return; }
  try {
    const data = await api('/wishlist', { auth: true });
    wishlist = (data.items || []).map(p => p.id);
  } catch (err) { wishlist = []; }
}
async function toggleWishlist(productId) {
  if (!isLoggedIn()) { showScreen('login'); return; }
  try {
    const data = await api(`/wishlist/${productId}/toggle`, { method: 'POST', auth: true });
    wishlist = (data.items || []).map(p => p.id);
    renderGrid();
  } catch (err) { alert(err.message); }
}

// ============================================================
// ORDERS
// ============================================================
async function loadOrders(statusFilter = 'all') {
  const list = document.getElementById('ordersList');
  if (!list) return;
  list.innerHTML = `<div class="loading-note">Loading…</div>`;
  try {
    const data = await api('/orders', { auth: true });
    orders = data.orders || [];
    renderOrders(statusFilter);
  } catch (err) {
    list.innerHTML = `<div class="loading-note">${err.message}</div>`;
  }
}

function renderOrders(statusFilter = 'all') {
  const list = document.getElementById('ordersList');
  if (!list) return;
  const filtered = statusFilter === 'all' ? orders : orders.filter(o => o.status === statusFilter);
  if (!filtered.length) {
    list.innerHTML = `<div class="orders-empty">No orders yet.</div>`;
    return;
  }
  list.innerHTML = filtered.map(o => `
    <div class="order-card">
      <div class="o-head">
        <span>#${o.id}</span>
        <span class="o-status">${o.status}</span>
      </div>
      ${(o.items || []).map(i => {
        const p = products.find(x => x.id === i.product_id);
        const thumb = (p && p.image) ? `${imageTag(p.image)}` : '📦';
        return `
        <div class="o-row">
          <div class="o-thumb">${thumb}</div>
          <div style="flex:1;">
            <div class="o-name">${escapeHtml(i.name)}</div>
            <div class="o-meta">R$ ${Number(i.price).toFixed(2)} ×${i.qty}</div>
          </div>
        </div>`;
      }).join('')}
      <div class="o-actions">
        <button class="o-btn" data-detail="${o.id}">Detalhes</button>
        <button class="o-btn primary" data-buyback="${o.id}">Solicitar uma recompra</button>
      </div>
    </div>
  `).join('');

  list.querySelectorAll('[data-buyback]').forEach(b => b.addEventListener('click', async () => {
    const order = orders.find(x => x.id === Number(b.dataset.buyback));
    if (!order || !order.items.length) return;
    const pid = order.items[0].product_id;
    try {
      await api('/buybacks', { method: 'POST', auth: true, body: { productId: pid, qty: 1 } });
      alert('Buyback request sent');
    } catch (e) { alert(e.message); }
  }));
  list.querySelectorAll('[data-detail]').forEach(b => b.addEventListener('click', () => {
    const o = orders.find(x => x.id === Number(b.dataset.detail));
    alert(`Order #${o.id}\nTotal: ${formatPrice(o.total)}\nStatus: ${o.status}`);
  }));
}

document.getElementById('orderTabs')?.addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  document.querySelectorAll('#orderTabs button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  renderOrders(b.dataset.status);
});

// ============================================================
// RECHARGE
// ============================================================
async function renderRecharge() {
  if (!currentUser) return;
  const balEl = document.getElementById('rechargeBalance');
  if (balEl) balEl.textContent = formatPrice(currentUser.balance);
  try {
    const s = await api('/settings');
    document.getElementById('pixName').textContent = s.pixName || 'SellerZone Store';
    document.getElementById('pixKey').textContent = s.pixKey || '';
  } catch (e) {}
}

document.querySelectorAll('.copy-btn').forEach(b => {
  b.addEventListener('click', () => {
    const id = b.dataset.copy;
    const val = document.getElementById(id).textContent;
    navigator.clipboard?.writeText(val).catch(() => {});
    b.textContent = 'Copied';
    setTimeout(() => b.textContent = 'Copy', 1200);
  });
});

document.getElementById('uploadBox')?.addEventListener('click', () => {
  document.getElementById('receiptInput').click();
});
document.getElementById('receiptInput')?.addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    document.getElementById('uploadBox').innerHTML = `<img src="${reader.result}" alt="">`;
    document.getElementById('uploadBox').dataset.receipt = reader.result;
  };
  reader.readAsDataURL(f);
});

document.getElementById('submitDeposit')?.addEventListener('click', async () => {
  const amount = Number(document.getElementById('depositAmount').value);
  const receipt = document.getElementById('uploadBox').dataset.receipt || '';
  if (!amount) return alert('Enter amount');
  try {
    await api('/wallet/deposits', { method: 'POST', auth: true, body: { amount, receipt } });
    alert('Deposit slip submitted!');
    showScreen('account');
  } catch (e) { alert(e.message); }
});

// ============================================================
// WITHDRAW
// ============================================================
async function renderWithdraw() {
  if (!currentUser) return;
  document.getElementById('wBalance').textContent = formatPrice(currentUser.balance);
  document.getElementById('wName').value = currentUser.name || '';
}

document.getElementById('submitWithdraw')?.addEventListener('click', async () => {
  const amount = Number(document.getElementById('wAmount').value);
  const pix = document.getElementById('wPix').value;
  if (!amount) return alert('Enter amount');
  try {
    await api('/wallet/withdrawals', { method: 'POST', auth: true, body: { amount, pixKey: pix } });
    alert('Withdrawal request sent');
    showScreen('account');
  } catch (e) { alert(e.message); }
});

// ============================================================
// ADDRESSES
// ============================================================
async function loadAddresses() {
  try {
    const data = await api('/addresses', { auth: true });
    addresses = data.addresses || [];
  } catch (e) { addresses = []; }
}
document.getElementById('saveAddress')?.addEventListener('click', async () => {
  const body = {
    label: 'Home',
    fullName: `${document.getElementById('addrFirst').value} ${document.getElementById('addrLast').value}`,
    address: document.getElementById('addrAddress').value,
    city: document.getElementById('addrCity').value,
    postal: document.getElementById('addrZip').value,
    isDefault: true,
  };
  try {
    await api('/addresses', { method: 'POST', auth: true, body });
    alert('Address saved');
    showScreen('account');
  } catch (e) { alert(e.message); }
});

// ============================================================
// INVITE / QR
// ============================================================
function renderInvite() {
  if (!currentUser) return;
  inviteCode = currentUser.inviteCode || 'BZR-XXXXX';
  document.getElementById('inviteCode').textContent = inviteCode;
  document.getElementById('inviteLink').textContent = `${location.origin}/invite?code=${inviteCode}`;
  drawFakeQr(document.getElementById('qrCanvas'), inviteCode);
}

function drawFakeQr(canvas, seed) {
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cells = 21;
  const cell = size / cells;
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#1A1A1A';
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  function rand() { h = (h * 1103515245 + 12345) >>> 0; return (h >>> 8) % 100; }
  for (let y = 0; y < cells; y++) {
    for (let x = 0; x < cells; x++) {
      const inF = (x < 5 && y < 5) || (x > cells - 6 && y < 5) || (x < 5 && y > cells - 6);
      if (inF) continue;
      if (rand() < 46) ctx.fillRect(x * cell, y * cell, cell, cell);
    }
  }
  [[0,0],[cells-5,0],[0,cells-5]].forEach(([fx,fy]) => {
    ctx.fillStyle = '#1A1A1A'; ctx.fillRect(fx*cell, fy*cell, 5*cell, 5*cell);
    ctx.fillStyle = '#fff'; ctx.fillRect((fx+1)*cell, (fy+1)*cell, 3*cell, 3*cell);
    ctx.fillStyle = '#1A1A1A'; ctx.fillRect((fx+2)*cell, (fy+2)*cell, 1*cell, 1*cell);
  });
}

document.getElementById('copyCodeBtn')?.addEventListener('click', () => {
  navigator.clipboard?.writeText(inviteCode).catch(() => {});
  const b = document.getElementById('copyCodeBtn');
  b.textContent = 'Copied';
  setTimeout(() => b.textContent = 'Copy', 1200);
});
document.getElementById('copyLinkBtn')?.addEventListener('click', () => {
  navigator.clipboard?.writeText(document.getElementById('inviteLink').textContent).catch(() => {});
  const b = document.getElementById('copyLinkBtn');
  b.textContent = 'Copied';
  setTimeout(() => b.textContent = 'Copy', 1200);
});

// ============================================================
// MESSAGES
// ============================================================
async function loadMessages() {
  const el = document.getElementById('messagesList');
  if (!el) return;
  el.innerHTML = `<div class="loading-note">Loading…</div>`;
  try {
    const data = await api('/messages', { auth: true });
    messages = data.messages || [];
    if (!messages.length) {
      el.innerHTML = `<div class="loading-note">No messages yet.</div>`;
      return;
    }
    el.innerHTML = messages.map(m => `
      <div class="msg-card">
        <div class="msg-head"><span>${new Date(m.created_at).toLocaleString('pt-BR')}</span><span>${m.status}</span></div>
        <div>${escapeHtml(m.text)}</div>
        ${m.reply ? `<div class="msg-reply"><strong>Admin:</strong> ${escapeHtml(m.reply)}</div>` : ''}
      </div>
    `).join('');
  } catch (e) { el.innerHTML = `<div class="loading-note">${e.message}</div>`; }
}

document.getElementById('sendMessage')?.addEventListener('click', async () => {
  const text = document.getElementById('messageText').value.trim();
  if (!text) return;
  try {
    await api('/messages', { method: 'POST', auth: true, body: { text } });
    document.getElementById('messageText').value = '';
    loadMessages();
  } catch (e) { alert(e.message); }
});

// ============================================================
// INIT — BOOT
// ============================================================
(async function init() {
  console.log('🚀 SellerZone app booting...');
  const inviteEl = document.getElementById('inviteLink');
  if (inviteEl && !inviteEl.textContent.includes('?code=')) inviteEl.textContent = `${location.origin}/invite`;
  await loadProducts('all');
  console.log('✅ Products loaded:', products.length);
  
  if (isLoggedIn()) {
    try {
      const data = await api('/wallet/me', { auth: true });
      currentUser = data.user;
      localStorage.setItem('bz_user', JSON.stringify(currentUser));
    } catch (e) {}
    await Promise.all([loadCart(), loadWishlist(), loadAddresses()]);
    renderAccount();
    updateCartBadge();
  }
})();