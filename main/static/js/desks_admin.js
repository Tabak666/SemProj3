// Minimal helper: call initDesksAdmin() from pages that include this file.
async function apiGet(path){ return fetch(path, {credentials:'same-origin'}).then(r=>r.json()); }
async function apiPost(path, body){
  return fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body), credentials:'same-origin'}).then(r=>r.json());
}
async function apiDelete(path){ return fetch(path, {method:'DELETE', credentials:'same-origin'}).then(r=>r.json()); }

function createDeskRow(table, onDelete){
  const li = document.createElement('li');
  li.className = 'desk-row';
  li.dataset.id = table.id;
  li.textContent = table.name || ('Table ' + table.id);
  if(onDelete){
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'desk-remove-btn';
    btn.textContent = 'Remove';
    btn.addEventListener('click', async (e)=>{
      e.stopPropagation();
      btn.disabled = true;
      const res = await apiDelete('/api/desks/' + table.id);
      // ignore errors; caller will refresh
      await onDelete(table.id);
    });
    li.appendChild(btn);
  }
  return li;
}

export async function initDesksAdmin(opts = {}){
  // opts: { approvalsListSelector, approvalsAddInputSelector, homeSidepanelListSelector, enableAdminControls }
  const approvalsList = document.querySelector(opts.approvalsListSelector || '#desks-list-approvals');
  const approvalsInput = document.querySelector(opts.approvalsAddInputSelector || '#desks-add-input');
  const approvalsAddBtn = document.querySelector(opts.approvalsAddInputSelector ? (opts.approvalsAddInputSelector + '-btn') : '#desks-add-btn');
  const homeList = document.querySelector(opts.homeSidepanelListSelector || '#sidepanel-desks-list');

  async function refresh(){
    const desks = await apiGet('/api/desks');
    if(approvalsList){
      approvalsList.innerHTML = '';
      desks.forEach(d => approvalsList.appendChild(createDeskRow(d, opts.enableAdminControls ? onDelete : null)));
    }
    if(homeList){
      homeList.innerHTML = '';
      desks.forEach(d => {
        const item = document.createElement('div');
        item.className = 'side-desk';
        item.dataset.id = d.id;
        item.textContent = d.name;
        if(opts.enableAdminControls){
          const rm = document.createElement('button'); rm.className='side-desk-remove'; rm.textContent='x';
          rm.addEventListener('click', async (e)=>{ e.stopPropagation(); await onDelete(d.id); });
          item.appendChild(rm);
        }
        homeList.appendChild(item);
      });
    }
  }

  async function onDelete(id){
    await apiDelete('/api/desks/' + id);
    await refresh();
  }

  if(approvalsAddBtn && approvalsInput && opts.enableAdminControls){
    approvalsAddBtn.addEventListener('click', async ()=>{
      const name = approvalsInput.value && approvalsInput.value.trim();
      if(!name) return;
      approvalsAddBtn.disabled = true;
      await apiPost('/api/desks', { name });
      approvalsInput.value = '';
      approvalsAddBtn.disabled = false;
      await refresh();
    });
  }

  // initial load
  await refresh();
}
