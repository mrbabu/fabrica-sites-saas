/* Fábrica de Sites AI — helpers compartilhados (vendas.html + index.html)
   Script clássico, sem build. Precisa carregar ANTES do <script> inline de
   cada página (a ordem importa: render() chama estas funções). Ao editar,
   incrementar a query string de cache-busting no <script src="..."> que
   referencia este arquivo (motion.js?v=1 -> ?v=2).

   Funções que dependem do shape específico do JSON de cada página
   (renderNavigation, renderHero, todas as render*) continuam em cada HTML —
   não fazem parte deste arquivo. */

const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function setFavicon(emoji) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="0.9em" font-size="90">${emoji}</text></svg>`;
    document.getElementById('favicon-link').setAttribute('href', 'data:image/svg+xml,' + encodeURIComponent(svg));
}

function waLink(numeroRaw, mensagem) {
    const numero = (numeroRaw || '').replace(/\D/g, '');
    return `https://wa.me/${numero}?text=${encodeURIComponent(mensagem)}`;
}

const WHATSAPP_ICON = `<svg viewBox="0 0 32 32" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="M16.02 3C9.4 3 4 8.38 4 15c0 2.34.64 4.53 1.76 6.42L4 29l7.76-1.7A11.9 11.9 0 0 0 16.02 27C22.64 27 28 21.62 28 15S22.64 3 16.02 3Zm6.98 16.9c-.3.85-1.72 1.63-2.38 1.72-.61.09-1.36.13-2.2-.14-.5-.16-1.15-.37-1.98-.73-3.5-1.51-5.78-5.05-5.96-5.29-.17-.24-1.43-1.9-1.43-3.62s.9-2.57 1.22-2.92c.32-.35.7-.44.93-.44.23 0 .47 0 .67.01.22.01.51-.08.79.6.3.72 1.02 2.49 1.11 2.67.09.18.15.39.03.63-.12.24-.18.39-.36.6-.18.21-.38.47-.54.63-.18.18-.37.37-.16.73.21.36.94 1.55 2.02 2.51 1.39 1.24 2.56 1.62 2.92 1.8.36.18.57.15.78-.09.21-.24.9-1.05 1.14-1.41.24-.36.48-.3.81-.18.33.12 2.1.99 2.46 1.17.36.18.6.27.69.42.09.15.09.85-.21 1.7Z"/></svg>`;

function staggerWords(text) {
    return text.split(' ').map((w, i) => `<span class="word-reveal" style="animation-delay:${(i * 0.045).toFixed(2)}s">${w}&nbsp;</span>`).join('');
}

function initScrollReveal() {
    const items = document.querySelectorAll('.reveal');
    if (prefersReducedMotion() || !('IntersectionObserver' in window)) {
        items.forEach(el => el.classList.add('is-visible'));
        return;
    }
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    items.forEach(el => io.observe(el));
}

function initWhatsAppLabel() {
    const label = document.getElementById('wa-label');
    if (!label || prefersReducedMotion()) return;
    const phrases = ['Fale agora', 'Resposta rápida'];
    let i = 0;
    setInterval(() => {
        i = (i + 1) % phrases.length;
        label.style.opacity = '0';
        setTimeout(() => { label.textContent = phrases[i]; label.style.opacity = '1'; }, 350);
    }, 3400);
}

function initParallax() {
    const media = document.getElementById('hero-media-img');
    if (!media || prefersReducedMotion()) return;
    let ticking = false;
    const update = () => {
        const y = Math.min(window.scrollY, 900) * 0.14;
        media.style.transform = `translateY(${y}px)`;
        ticking = false;
    };
    window.addEventListener('scroll', () => {
        if (!ticking) { requestAnimationFrame(update); ticking = true; }
    });
    update();
}

function initMagnetic() {
    if (prefersReducedMotion()) return;
    document.querySelectorAll('.magnetic').forEach(el => {
        el.addEventListener('mousemove', (e) => {
            const r = el.getBoundingClientRect();
            const x = (e.clientX - r.left - r.width / 2) * 0.25;
            const y = (e.clientY - r.top - r.height / 2) * 0.35;
            el.style.transform = `translate(${x}px, ${y}px)`;
        });
        el.addEventListener('mouseleave', () => { el.style.transform = 'translate(0, 0)'; });
    });
}

/* Generalizado (era hardcoded a #trust-rating-value só em index.html):
   agora anima qualquer elemento com [data-countup], lendo o valor alvo de
   data-target e as casas decimais de data-decimals (default: 0 se o alvo
   for inteiro, 1 caso contrário). Marcar o elemento com data-countup="1"
   além do id, se precisar manter o id por outro motivo (index.html faz
   isso pra não quebrar nada que dependa do id existente). */
function initCountUp(selector) {
    const items = document.querySelectorAll(selector || '[data-countup]');
    items.forEach(el => {
        const target = parseFloat(el.dataset.target || '0');
        const decimals = el.dataset.decimals !== undefined ? parseInt(el.dataset.decimals, 10) : (Number.isInteger(target) ? 0 : 1);
        if (prefersReducedMotion() || !('IntersectionObserver' in window)) {
            el.textContent = target.toFixed(decimals);
            return;
        }
        const io = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                io.unobserve(entry.target);
                const start = performance.now();
                const duration = 900;
                const step = (now) => {
                    const p = Math.min((now - start) / duration, 1);
                    el.textContent = (target * (1 - Math.pow(1 - p, 3))).toFixed(decimals);
                    if (p < 1) requestAnimationFrame(step);
                };
                requestAnimationFrame(step);
            });
        }, { threshold: 0.4 });
        io.observe(el);
    });
}

/* Generalizado (era só em index.html, lendo config.colors do escopo global):
   agora recebe o objeto colors explicitamente, pra funcionar com qualquer
   config (vendas-config.json ou site-config.json). */
function applyThemeColors(colors) {
    const style = document.createElement('style');
    style.textContent = `
        :root {
            --color-primary: ${colors.primary};
            --color-primary-dark: ${colors.primaryDark};
            --color-secondary: ${colors.secondary};
            --color-accent: ${colors.accent};
        }
        .btn-primary { background-color: var(--color-primary); }
        .btn-primary:hover { background-color: var(--color-primary-dark); }
        .text-primary { color: var(--color-primary); }
        .border-primary { border-color: var(--color-primary); }
        .bg-primary { background-color: var(--color-primary); }
        .bg-accent { background-color: var(--color-accent); }
        .text-accent { color: var(--color-accent); }
        details[open] summary { border-color: ${colors.border}; }
    `;
    document.head.appendChild(style);
}

/* Só a marcação/CSS do ticker — o que entra na lista (tickerItems()) é
   page-specific e continua em cada HTML. */
function renderTickerMarkup(items, bgColor) {
    if (!items || items.length === 0) return '';
    const row = items.map(item => `
        <span class="font-display font-bold uppercase tracking-wide text-sm sm:text-base text-white whitespace-nowrap px-6">${item}</span>
        <span class="text-white/50 text-sm">✦</span>
    `).join('');
    return `
        <div class="ticker-clip relative z-10 -mt-8 sm:-mt-10">
            <div class="ticker-wrap py-4 sm:py-5" style="background-color: ${bgColor}">
                <div class="ticker-track">
                    <div class="flex items-center">${row}</div>
                    <div class="flex items-center" aria-hidden="true">${row}</div>
                </div>
            </div>
        </div>
    `;
}
