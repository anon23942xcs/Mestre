// =========================================================
// Mestre — Sidebar Unificada Global
// =========================================================

function getCampanhaAtivaId() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('campanha_id')) return params.get('campanha_id');
    const path = window.location.pathname;
    const match = path.match(/\/campanhas\/([^\/]+)/);
    if (match) return decodeURIComponent(match[1]);
    return localStorage.getItem('mestre_campanha_id') || null;
}

function inicializarSidebar(opcoes = {}) {
    const sidebarEl = document.getElementById('app-sidebar');
    if (!sidebarEl) return;

    const path = window.location.pathname;
    const ativoInicio = path === '/' ? 'active' : '';
    const ativoJogo = path === '/jogo' ? 'active' : '';
    const ativoMundos = path.startsWith('/mundos') ? 'active' : '';
    const ativoPersonagens = path.startsWith('/personagens') ? 'active' : '';
    const ativoWiki = (path.includes('/wiki')) ? 'active' : '';

    const cid = opcoes.campanhaId || getCampanhaAtivaId();

    let wikiItemHtml = '';
    if (cid) {
        wikiItemHtml = `
            <a href="/campanhas/${encodeURIComponent(cid)}/wiki" class="sidebar-nav-item ${ativoWiki}" id="sidebar-link-wiki">
                <span class="icon">✦</span> Wiki da Campanha
            </a>
        `;
    }

    sidebarEl.innerHTML = `
        <a href="/" class="sidebar-brand">
            Mestre<span class="dot">.</span>
        </a>

        <div class="sidebar-action-wrap">
            <a href="/jogo?nova=1" class="btn-sidebar-novo">
                <span>+</span> Nova Campanha
            </a>
        </div>

        <div class="sidebar-nav-section">Navegação</div>
        <nav class="sidebar-nav">
            <a href="/" class="sidebar-nav-item ${ativoInicio}">
                <span class="icon">🏠</span> Início
            </a>
            <button type="button" class="sidebar-nav-item" onclick="abrirModalCampanhasGlobal()">
                <span class="icon">🎮</span> Jogos / Campanhas
            </button>
            <a href="/mundos" class="sidebar-nav-item ${ativoMundos}">
                <span class="icon">🌍</span> Mundos
            </a>
            <a href="/personagens" class="sidebar-nav-item ${ativoPersonagens}">
                <span class="icon">👤</span> Personagens
            </a>
            ${wikiItemHtml}
        </nav>

        <div class="sidebar-footer" id="sidebar-footer-area">
            <div class="sidebar-player-card" id="sidebar-player-card" style="display:none;">
                <div class="sidebar-avatar" id="sidebar-avatar">
                    <span id="sidebar-avatar-text">?</span>
                </div>
                <div class="sidebar-player-info">
                    <div class="sidebar-player-name" id="sidebar-player-name">Jogador</div>
                    <div class="sidebar-player-meta" id="sidebar-player-meta">Personagem</div>
                </div>
            </div>
            <button type="button" class="sidebar-nav-item" id="sidebar-btn-ficha-completa" onclick="window.abrirFichaModal && window.abrirFichaModal()" style="display:none;">
                <span class="icon">📋</span> Ficha do Jogador
            </button>
        </div>
    `;

    injetarModalCampanhasGlobal();
}

function atualizarSidebarJogador(jogador) {
    if (!jogador) return;
    const card = document.getElementById('sidebar-player-card');
    const avatar = document.getElementById('sidebar-avatar');
    const name = document.getElementById('sidebar-player-name');
    const meta = document.getElementById('sidebar-player-meta');
    const btnFicha = document.getElementById('sidebar-btn-ficha-completa');

    if (card) card.style.display = 'flex';
    if (btnFicha) btnFicha.style.display = 'flex';

    if (name) name.textContent = jogador.nome || 'Jogador';
    if (meta) meta.textContent = (jogador.idade ? `${jogador.idade} anos` : 'Aventureiro') + (jogador.pv != null ? ` • PV ${jogador.pv}/${jogador.pv_max}` : '');

    if (avatar) {
        if (jogador.imagem && jogador.imagem.trim()) {
            avatar.innerHTML = `<img src="${encodeURI(jogador.imagem.trim())}" alt="${jogador.nome || 'Foto'}" onerror="this.style.display='none'; this.parentElement.innerHTML='${(jogador.nome || 'J')[0].toUpperCase()}';">`;
        } else {
            avatar.textContent = (jogador.nome || 'J')[0].toUpperCase();
        }
    }
}

function injetarModalCampanhasGlobal() {
    if (document.getElementById('modal-global-campanhas')) return;

    const modal = document.createElement('dialog');
    modal.id = 'modal-global-campanhas';
    modal.className = 'clean-dialog';
    modal.innerHTML = `
        <div class="dialog-header">
            <h2>Campanhas Salvas</h2>
            <button type="button" class="btn btn-secondary btn-sm" onclick="fecharModalCampanhasGlobal()">✕</button>
        </div>
        <div id="lista-campanhas-global" style="display:flex; flex-direction:column; gap:8px; max-height:400px; overflow-y:auto; padding:4px;">
            Carregando campanhas...
        </div>
    `;
    document.body.appendChild(modal);
}

async function abrirModalCampanhasGlobal() {
    injetarModalCampanhasGlobal();
    const modal = document.getElementById('modal-global-campanhas');
    const lista = document.getElementById('lista-campanhas-global');
    if (!modal) return;
    modal.showModal();
    lista.innerHTML = 'Carregando campanhas...';

    try {
        const resp = await fetch('/campanhas');
        if (!resp.ok) throw new Error();
        const campanhas = await resp.json();
        if (!campanhas.length) {
            lista.innerHTML = '<p style="color:var(--text-muted); margin:10px 0;">Nenhuma campanha encontrada.</p>';
            return;
        }

        lista.innerHTML = '';
        campanhas.forEach(c => {
            const item = document.createElement('div');
            item.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#1e2029; border:1px solid var(--border-card); border-radius:6px;';
            item.innerHTML = `
                <div>
                    <strong style="color:#fff; font-size:14px;">${escapeHtmlSimple(c.nome_jogador)}</strong>
                    <div style="color:var(--text-muted); font-size:12px; margin-top:2px;">📍 ${escapeHtmlSimple(c.local || 'Início')}</div>
                </div>
                <button class="btn btn-outline-green btn-sm">Jogar →</button>
            `;
            item.querySelector('button').onclick = () => {
                modal.close();
                localStorage.setItem('mestre_campanha_id', c.campanha_id);
                window.location.href = `/jogo?campanha_id=${encodeURIComponent(c.campanha_id)}`;
            };
            lista.appendChild(item);
        });
    } catch (e) {
        lista.innerHTML = '<p style="color:#ff7b90; margin:10px 0;">Erro ao carregar lista de campanhas.</p>';
    }
}

function fecharModalCampanhasGlobal() {
    const modal = document.getElementById('modal-global-campanhas');
    if (modal) modal.close();
}

function escapeHtmlSimple(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

document.addEventListener('DOMContentLoaded', () => {
    inicializarSidebar();
});
