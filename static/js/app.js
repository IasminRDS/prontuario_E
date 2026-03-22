/**
 * app.js — Prontuário Único SUS
 * Utilitários globais e inicialização da UI
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Auto-fechar alertas após 6s ──
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity .4s, transform .4s';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-6px)';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });

  // ── Sidebar mobile toggle ──
  const sidebar = document.getElementById('sidebar');
  const menuBtn = document.getElementById('menu-toggle');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) && e.target !== menuBtn) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Máscara CPF ──
  const inputCpf = document.getElementById('input-cpf');
  if (inputCpf) {
    inputCpf.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '').slice(0, 11);
      if (v.length > 9)      v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
      else if (v.length > 6) v = v.replace(/(\d{3})(\d{3})(\d+)/, '$1.$2.$3');
      else if (v.length > 3) v = v.replace(/(\d{3})(\d+)/, '$1.$2');
      e.target.value = v;
    });
  }

  // ── Máscara CNS ──
  const inputCns = document.getElementById('input-cns');
  if (inputCns) {
    inputCns.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '').slice(0, 15);
      v = v.replace(/(\d{3})(?=\d)/g, '$1 ').trim();
      e.target.value = v;
    });
  }

  // ── Máscaras telefone ──
  ['input-tel1', 'input-tel2'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '').slice(0, 11);
      if (v.length > 10)     v = v.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
      else if (v.length > 6) v = v.replace(/(\d{2})(\d{4})(\d+)/, '($1) $2-$3');
      else if (v.length > 2) v = v.replace(/(\d{2})(\d+)/, '($1) $2');
      e.target.value = v;
    });
  });

  // ── CEP → endereço automático (ViaCEP) ──
  const inputCep = document.getElementById('input-cep');
  if (inputCep) {
    inputCep.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '').slice(0, 8);
      if (v.length > 5) v = v.replace(/(\d{5})(\d+)/, '$1-$2');
      e.target.value = v;
    });

    inputCep.addEventListener('blur', async e => {
      const cep = e.target.value.replace(/\D/g, '');
      if (cep.length !== 8) return;
      e.target.value = cep.replace(/(\d{5})(\d{3})/, '$1-$2');
      try {
        const res  = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await res.json();
        if (data.erro) return;
        setField('campo-logradouro', (data.logradouro || '').toUpperCase());
        setField('campo-bairro',     (data.bairro     || '').toUpperCase());
        setField('campo-municipio',  (data.localidade  || '').toUpperCase());
        setSelectField('campo-uf',    data.uf || '');
      } catch (_) { /* offline */ }
    });
  }

  function setField(id, value) {
    const el = document.getElementById(id);
    if (el && !el.value) el.value = value;
  }
  function setSelectField(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
  }

  // ── Confirmação de ações destrutivas ──
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Busca de paciente com autocomplete ──
  const buscaInput = document.getElementById('busca-paciente');
  const buscaResultados = document.getElementById('busca-resultados');
  if (buscaInput && buscaResultados) {
    let timeout;
    buscaInput.addEventListener('input', () => {
      clearTimeout(timeout);
      const q = buscaInput.value.trim();
      if (q.length < 2) { buscaResultados.innerHTML = ''; buscaResultados.hidden = true; return; }
      timeout = setTimeout(async () => {
        try {
          const res  = await fetch(`/pacientes/buscar?q=${encodeURIComponent(q)}`);
          const data = await res.json();
          renderBusca(data);
        } catch (_) {}
      }, 300);
    });

    function renderBusca(pacientes) {
      if (!pacientes.length) { buscaResultados.hidden = true; return; }
      buscaResultados.innerHTML = pacientes.map(p => `
        <a href="/pacientes/${p.id}" class="busca-item">
          <span class="busca-nome">${p.nome}</span>
          <span class="busca-info">${p.idade} anos · CNS ${p.cns || '—'}</span>
        </a>
      `).join('');
      buscaResultados.hidden = false;
    }

    document.addEventListener('click', e => {
      if (!buscaResultados.contains(e.target) && e.target !== buscaInput) {
        buscaResultados.hidden = true;
      }
    });
  }

});
