const API = '/api/admin';
let adminToken = localStorage.getItem('bz_admin_token') || null;

function imageUrl(src) {
  const value = String(src || '').trim();
  if (!value) return '';
  if (value.startsWith('data:') || value.startsWith('blob:') || value.startsWith('/') || value.startsWith('./')) return value;
  if (value.startsWith('//')) return `${location.protocol}${value}`;
  return value;
}

function imageProxyUrl(src) {
  const value = String(src || '').trim();
  return /^https?:\/\//i.test(value) ? `/api/image?url=${encodeURIComponent(value)}` : '';
}

function localProductImage(key) {
  const map = { webcam:'webcam', ring:'ring', cosmetic_serum:'cosmetic_serum', watch_smart:'watch_smart', watch_leather:'watch_leather', travelbed:'travelbed', device_cat:'device_cat', cosmetic_cream:'cosmetic_cream' };
  return `/images/products/${map[key] || 'all'}.svg`;
}

function handleImageError(img) {
  const proxy = img.dataset.proxy || '';
  const local = img.dataset.local || '/images/products/all.svg';
  if (proxy && img.dataset.fallback !== 'proxy') { img.dataset.fallback = 'proxy'; img.src = proxy; return; }
  if (local && img.dataset.fallback !== 'local') { img.dataset.fallback = 'local'; img.src = local; return; }
  img.onerror = null;
}

function imageTag(src, alt = '', localFallback = '/images/products/all.svg') {
  const original = String(src || '').trim();
  const url = imageUrl(original) || localFallback;
  return `<img src="${url.replace(/"/g, '&quot;')}" alt="${String(alt).replace(/"/g, '&quot;')}" loading="lazy" data-proxy="${imageProxyUrl(original).replace(/"/g, '&quot;')}" data-local="${localFallback}" onerror="handleImageError(this)">`;
}

async function adminApi(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (adminToken) headers.Authorization = adminToken;
  const res = await fetch(`${API}${path}`, {
    method, headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) throw new Error(data.error || `Failed (${res.status})`);
  return data;
}

document.getElementById('adminLoginBtn').addEventListener('click', async () => {
  const password = document.getElementById('adminPassword').value;
  try {
    const data = await adminApi('/login', { method: 'POST', body: { password } });
    adminToken = data.token;
    localStorage.setItem('bz_admin_token', adminToken);
    enterAdmin();
  } catch (e) {
    document.getElementById('loginError').textContent = e.message;
  }
});

document.getElementById('adminLogout').addEventListener('click', () => {
  localStorage.removeItem('bz_admin_token');
  location.reload();
});

function enterAdmin() {
  document.getElementById('loginScreen').style.display = 'none';
  document.getElementById('adminApp').style.display = 'flex';
  loadStats(); loadUsers(); loadProducts();
  loadWithdrawals(); loadDeposits(); loadBuybacks();
  loadMessages(); loadInviteCodes(); loadSettings();
}

document.querySelectorAll('.side-item[data-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.side-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab').forEach(t => t.style.display = 'none');
    document.getElementById(`tab-${btn.dataset.tab}`).style.display = 'block';
  });
});

async function loadStats() {
  try {
    const s = await adminApi('/stats');
    document.getElementById('statsGrid').innerHTML = `
      <div class="stat-card"><div class="label">Total Users</div><div class="value">${s.totalUsers}</div></div>
      <div class="stat-card"><div class="label">Products</div><div class="value">${s.totalProducts}</div></div>
      <div class="stat-card"><div class="label">Orders</div><div class="value">${s.totalOrders}</div></div>
      <div class="stat-card"><div class="label">Pending Withdrawals</div><div class="value">${s.pendingWithdrawals}</div></div>
      <div class="stat-card"><div class="label">Pending Deposits</div><div class="value">${s.pendingDeposits}</div></div>
      <div class="stat-card"><div class="label">Open Messages</div><div class="value">${s.openMessages}</div></div>
      <div class="stat-card"><div class="label">Buybacks</div><div class="value">${s.totalBuybacks}</div></div>
      <div class="stat-card"><div class="label">Frozen Users</div><div class="value">${s.frozenUsers}</div></div>
    `;
  } catch (e) { console.error(e); }
}

async function loadUsers(search = '') {
  try {
    const data = await adminApi(`/users?search=${encodeURIComponent(search)}`);
    document.getElementById('usersList').innerHTML = data.users.map(u => `
      <div class="user-card">
        <div class="info">
          <div class="name">${u.name}
            <span class="badge ${u.frozen ? 'frozen' : 'active'}">${u.frozen ? 'FROZEN' : 'ACTIVE'}</span>
          </div>
          <div class="meta">#${u.id} · ${u.email}</div>
          <div class="meta">Balance: R$ ${u.balance.toFixed(2)} · Points: ${u.points}</div>
        </div>
        <div>
          <button class="btn" data-act="points" data-id="${u.id}" data-delta="100">+100 pts</button>
          <button class="btn" data-act="points" data-id="${u.id}" data-delta="-100">-100 pts</button>
          <button class="btn" data-act="balance" data-id="${u.id}" data-delta="50">+50 R$</button>
          <button class="btn" data-act="balance" data-id="${u.id}" data-delta="-50">-50 R$</button>
          <button class="btn ${u.frozen ? 'success' : 'danger'}" data-act="freeze" data-id="${u.id}" data-frozen="${!u.frozen}">
            ${u.frozen ? 'Unfreeze' : 'Freeze'}
          </button>
          <button class="btn" data-act="reset" data-id="${u.id}">Reset Password</button>
        </div>
      </div>
    `).join('');
    document.querySelectorAll('#usersList .btn').forEach(b => b.addEventListener('click', handleUserAction));
  } catch (e) { alert(e.message); }
}

async function handleUserAction(e) {
  const b = e.target;
  const id = b.dataset.id;
  const act = b.dataset.act;
  try {
    if (act === 'points') {
      await adminApi(`/users/${id}/points`, { method: 'POST', body: { delta: Number(b.dataset.delta) } });
    } else if (act === 'balance') {
      await adminApi(`/users/${id}/balance`, { method: 'POST', body: { delta: Number(b.dataset.delta) } });
    } else if (act === 'freeze') {
      await adminApi(`/users/${id}/freeze`, { method: 'POST', body: { frozen: b.dataset.frozen === 'true' } });
    } else if (act === 'reset') {
      const np = prompt('New password (empty = "sellerzone123"):');
      const r = await adminApi(`/users/${id}/reset-password`, { method: 'POST', body: { newPassword: np || null } });
      alert(`Password reset to: ${r.newPassword}`);
    }
    loadUsers(document.getElementById('userSearch').value);
    loadStats();
  } catch (err) { alert(err.message); }
}

document.getElementById('userSearch').addEventListener('input', (e) => loadUsers(e.target.value));

async function loadProducts(search = '') {
  try {
    const data = await adminApi(`/products?search=${encodeURIComponent(search)}`);
    document.getElementById('productsList').innerHTML = data.products.map(p => `
      <div class="product-card">
        <div class="product-thumb">${imageTag(p.image, p.name, localProductImage(p.icon_key))}</div>
        <div class="info">
          <div class="name">${p.name}</div>
          <div class="meta">#${p.id} · ${p.category} · R$ ${p.price.toFixed(2)}</div>
        </div>
        <div>
          <button class="btn" data-pact="inc" data-pid="${p.id}">+R$10</button>
          <button class="btn" data-pact="dec" data-pid="${p.id}">-R$10</button>
          <button class="btn danger" data-pact="del" data-pid="${p.id}">Delete</button>
        </div>
      </div>
    `).join('');
    document.querySelectorAll('#productsList .btn').forEach(b => b.addEventListener('click', handleProductAction));
  } catch (e) { alert(e.message); }
}

async function handleProductAction(e) {
  const b = e.target;
  const id = b.dataset.pid;
  const act = b.dataset.pact;
  try {
    if (act === 'inc') await adminApi(`/products/${id}/price`, { method: 'POST', body: { delta: 10 } });
    if (act === 'dec') await adminApi(`/products/${id}/price`, { method: 'POST', body: { delta: -10 } });
    if (act === 'del' && confirm('Delete this product?')) await adminApi(`/products/${id}`, { method: 'DELETE' });
    loadProducts(document.getElementById('prodSearch').value);
  } catch (err) { alert(err.message); }
}

document.getElementById('prodSearch').addEventListener('input', (e) => loadProducts(e.target.value));

document.getElementById('addProductBtn').addEventListener('click', async () => {
  const name = prompt('Product name:'); if (!name) return;
  const price = prompt('Price:'); if (!price) return;
  const category = prompt('Category (jewelry/watches/cosmetics/electronics/home):') || 'home';
  const image = prompt('Image URL (optional):') || '';
  const description = prompt('Description (optional):') || '';
  try {
    await adminApi('/products', { method: 'POST', body: { name, price: Number(price), category, image, description } });
    loadProducts();
  } catch (e) { alert(e.message); }
});

document.getElementById('priceSearchBtn').addEventListener('click', async () => {
  const amount = document.getElementById('priceSearch').value;
  if (!amount) return;
  try {
    const data = await adminApi(`/products/search-by-price?amount=${amount}`);
    document.getElementById('productsList').innerHTML = data.products.length
      ? data.products.map(p => `
        <div class="product-card">
          <div class="product-thumb">${imageTag(p.image, p.name, localProductImage(p.icon_key))}</div>
          <div class="info">
            <div class="name">${p.name}</div>
            <div class="meta">#${p.id} · R$ ${p.price.toFixed(2)}</div>
          </div>
        </div>`).join('')
      : '<p>No products with that exact price.</p>';
  } catch (e) { alert(e.message); }
});

async function loadWithdrawals(status = '') {
  try {
    const data = await adminApi(`/withdrawals${status ? `?status=${status}` : ''}`);
    document.getElementById('withdrawalsList').innerHTML = data.withdrawals.length
      ? data.withdrawals.map(w => `
        <div class="item-card">
          <div class="info">
            <div class="name">#${w.id} · ${w.userName} <span class="badge ${w.status}">${w.status}</span></div>
            <div class="meta">Amount: R$ ${w.amount.toFixed(2)} · ${new Date(w.created_at).toLocaleString('pt-BR')}</div>
          </div>
          <div>
            ${w.status === 'pending' ? `
              <button class="btn success" data-wact="approved" data-wid="${w.id}">Allow</button>
              <button class="btn danger" data-wact="rejected" data-wid="${w.id}">Reject</button>
            ` : ''}
          </div>
        </div>`).join('')
      : '<p>No withdrawals.</p>';
    document.querySelectorAll('#withdrawalsList .btn').forEach(b => b.addEventListener('click', async () => {
      try {
        await adminApi(`/withdrawals/${b.dataset.wid}/status`, { method: 'POST', body: { status: b.dataset.wact } });
        loadWithdrawals(); loadStats();
      } catch (e) { alert(e.message); }
    }));
  } catch (e) { alert(e.message); }
}

document.querySelectorAll('#tab-withdrawals .tab-btn').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('#tab-withdrawals .tab-btn').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  loadWithdrawals(b.dataset.wstatus);
}));

async function loadDeposits(status = '') {
  try {
    const data = await adminApi(`/deposits${status ? `?status=${status}` : ''}`);
    document.getElementById('depositsList').innerHTML = data.deposits.length
      ? data.deposits.map(d => `
        <div class="item-card">
          <div class="info">
            <div class="name">#${d.id} · ${d.userName} <span class="badge ${d.status}">${d.status}</span></div>
            <div class="meta">Amount: R$ ${d.amount.toFixed(2)} · ${new Date(d.created_at).toLocaleString('pt-BR')}</div>
            ${d.receipt ? `<div style="margin-top:8px;"><img src="${d.receipt}" style="max-width:120px;border-radius:6px;"></div>` : ''}
          </div>
          <div>
            ${d.status === 'pending' ? `
              <button class="btn success" data-dact="approved" data-did="${d.id}">Allow</button>
              <button class="btn danger" data-dact="rejected" data-did="${d.id}">Reject</button>
            ` : ''}
          </div>
        </div>`).join('')
      : '<p>No deposits.</p>';
    document.querySelectorAll('#depositsList .btn').forEach(b => b.addEventListener('click', async () => {
      try {
        await adminApi(`/deposits/${b.dataset.did}/status`, { method: 'POST', body: { status: b.dataset.dact } });
        loadDeposits(); loadStats();
      } catch (e) { alert(e.message); }
    }));
  } catch (e) { alert(e.message); }
}

document.querySelectorAll('#tab-deposits .tab-btn').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('#tab-deposits .tab-btn').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  loadDeposits(b.dataset.dstatus);
}));

async function loadBuybacks() {
  try {
    const data = await adminApi('/buybacks');
    document.getElementById('buybacksList').innerHTML = data.buybacks.length
      ? data.buybacks.map(b => `
        <div class="item-card">
          <div class="info">
            <div class="name">#${b.id} · ${b.userName} <span class="badge ${b.status}">${b.status}</span></div>
            <div class="meta">${b.productName} ×${b.qty} · R$ ${b.price.toFixed(2)}</div>
          </div>
          <div>
            ${b.status === 'pending' ? `
              <button class="btn success" data-bact="approved" data-bid="${b.id}">Approve</button>
              <button class="btn danger" data-bact="rejected" data-bid="${b.id}">Reject</button>
            ` : ''}
          </div>
        </div>`).join('')
      : '<p>No buybacks.</p>';
    document.querySelectorAll('#buybacksList .btn').forEach(b => b.addEventListener('click', async () => {
      try {
        await adminApi(`/buybacks/${b.dataset.bid}/status`, { method: 'POST', body: { status: b.dataset.bact } });
        loadBuybacks(); loadStats();
      } catch (e) { alert(e.message); }
    }));
  } catch (e) { alert(e.message); }
}

async function loadMessages() {
  try {
    const data = await adminApi('/messages');
    document.getElementById('messagesList').innerHTML = data.messages.length
      ? data.messages.map(m => `
        <div class="msg-card">
          <div class="head"><span>#${m.id} · ${m.userName}</span><span>${new Date(m.created_at).toLocaleString('pt-BR')}</span></div>
          <div>${m.text}</div>
          ${m.reply ? `<div style="background:#FFEDE8;padding:8px;border-radius:6px;margin-top:8px;"><b>Reply:</b> ${m.reply}</div>` : `
            <div class="msg-reply-input">
              <input placeholder="Type reply..." id="reply-${m.id}">
              <button class="btn primary" data-mid="${m.id}">Reply</button>
            </div>
          `}
        </div>`).join('')
      : '<p>No messages.</p>';
    document.querySelectorAll('#messagesList .btn').forEach(b => b.addEventListener('click', async () => {
      const mid = b.dataset.mid;
      const reply = document.getElementById(`reply-${mid}`).value;
      if (!reply) return;
      try {
        await adminApi(`/messages/${mid}/reply`, { method: 'POST', body: { reply } });
        loadMessages();
      } catch (e) { alert(e.message); }
    }));
  } catch (e) { alert(e.message); }
}

async function loadInviteCodes() {
  try {
    const data = await adminApi('/invite-codes');
    document.getElementById('inviteList').innerHTML = data.codes.length
      ? data.codes.map(c => `
        <div class="item-card">
          <div class="info">
            <div class="name">${c.code}</div>
            <div class="meta">Created: ${new Date(c.created_at).toLocaleString('pt-BR')} · Used: ${c.usedBy || 'No'}</div>
          </div>
        </div>`).join('')
      : '<p>No invite codes yet.</p>';
  } catch (e) { alert(e.message); }
}

document.getElementById('genInviteBtn').addEventListener('click', async () => {
  const count = Number(document.getElementById('inviteCount').value) || 1;
  try {
    await adminApi('/invite-codes/generate', { method: 'POST', body: { count } });
    loadInviteCodes();
  } catch (e) { alert(e.message); }
});

async function loadSettings() {
  try {
    const s = await adminApi('/settings');
    document.getElementById('setPixKey').value = s.pixKey || '';
    document.getElementById('setPixName').value = s.pixName || '';
    document.getElementById('setInvitePrefix').value = s.invitePrefix || '';
  } catch (e) { alert(e.message); }
}
document.getElementById('saveSettings').addEventListener('click', async () => {
  const body = {
    pixKey: document.getElementById('setPixKey').value,
    pixName: document.getElementById('setPixName').value,
    invitePrefix: document.getElementById('setInvitePrefix').value,
  };
  try {
    await adminApi('/settings', { method: 'POST', body });
    alert('Settings saved');
  } catch (e) { alert(e.message); }
});

if (adminToken) enterAdmin();